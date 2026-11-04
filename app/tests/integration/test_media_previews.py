"""Private preview lifecycle on restricted PostgreSQL roles and real HTTP routes."""

import asyncio
import hashlib
import io
import json
from datetime import date, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from PIL import Image
from sqlalchemy import text

from app.adapters.material_media import MaterialError
from app.adapters.static_preview import TEMPLATE_VERSION
from app.adapters.video_preview import VIDEO_TEMPLATE_VERSION
from app.db.session import Database
from app.main import create_app
from app.schemas.media_previews import PreviewRequest
from app.services.auth import AuthError
from app.services.media_dispatch import claim_previews, finish_preview_dispatch, reconcile_stale_previews
from app.services.media_previews import MediaPreviewService, _digest
from app.services.media_retention import claim_expired_previews, finish_preview_purge, purge_expired_previews
from app.services.visual_references import VisualReferenceService
from app.tests.integration.test_business_collection import Store
from app.tests.integration.test_editorial_proposals import _business
from app.tests.integration.test_visual_admission import _ready
from app.tests.unit.test_core import access_token

pytestmark = pytest.mark.integration


async def _accepted_case(admin, seeded):
    business = await _business(admin, seeded)
    tenant, actor, fact, proposal = seeded["t1"], seeded["a1"], uuid4(), uuid4()
    document = {
        "title": "Lanche do dia",
        "format": "photo",
        "angle": "Mostre o lanche artesanal.",
        "fact_ids": [str(fact)],
        "hypotheses": [],
        "questions": [],
        "scene_plan": ["fact", "cta"],
        "script": [
            {
                "role": "fact",
                "visual": "brand_card",
                "on_screen_text": "Cachorro-quente artesanal.",
                "voiceover": "Cachorro-quente artesanal.",
                "fact_ids": [str(fact)],
                "source_asset_id": None,
            },
            {
                "role": "cta",
                "visual": "brand_card",
                "on_screen_text": "Fale com o negócio",
                "voiceover": "Entre em contato para saber mais.",
                "fact_ids": [],
                "source_asset_id": None,
            },
        ],
    }
    async with admin.begin() as conn:
        await conn.execute(
            text("INSERT INTO business_context_heads(tenant_id,business_id,version) VALUES(:t,:b,1)"),
            {"t": tenant, "b": business},
        )
        await conn.execute(
            text("""INSERT INTO business_context_versions
          (tenant_id,business_id,version,operation_id,actor_id,request_hash,document)
          VALUES(:t,:b,1,:o,:a,:h,CAST(:d AS jsonb))"""),
            {
                "t": tenant,
                "b": business,
                "o": uuid4(),
                "a": actor,
                "h": "f" * 64,
                "d": json.dumps(
                    {
                        "facts": [
                            {
                                "id": str(fact),
                                "kind": "product",
                                "statement": "Cachorro-quente artesanal",
                                "source_detail": "Dono",
                                "valid_until": None,
                            }
                        ],
                        "preferences": {"goal": "sales", "tone": None, "avoided_topics": [], "posts_per_week": None},
                    }
                ),
            },
        )
        await conn.execute(
            text("""INSERT INTO editorial_proposals
          (id,tenant_id,business_id,actor_id,operation_id,request_hash,context_version,
           state,review_state,document) VALUES(:id,:t,:b,:a,:o,:h,1,'completed','accepted',CAST(:d AS jsonb))"""),
            {
                "id": proposal,
                "t": tenant,
                "b": business,
                "a": actor,
                "o": uuid4(),
                "h": "e" * 64,
                "d": json.dumps(document),
            },
        )
    return tenant, business, actor, fact, proposal, document


async def _attach_source(admin, tenant, business, proposal, document, media: bytes, *, kind="image"):
    asset = uuid4()
    document["scene_plan"] = ["material", "fact", "cta"]
    document["script"].insert(
        0,
        {
            "role": "material",
            "visual": "source_material",
            "on_screen_text": "Material do negócio",
            "voiceover": "Conheça nosso negócio.",
            "fact_ids": [],
            "source_asset_id": str(asset),
        },
    )
    async with admin.begin() as conn:
        await conn.execute(
            text("""INSERT INTO whatsapp_material_assets
          (id,tenant_id,business_id,kind,ciphertext,object_key,mime_type,size_bytes,sha256)
          VALUES(:id,:t,:b,:kind,'ciphertext',:key,:mime,:size,:sha)"""),
            {
                "id": asset,
                "t": tenant,
                "b": business,
                "key": f"materials/{asset}.{'mp4' if kind == 'video' else 'png'}",
                "kind": kind,
                "mime": "video/mp4" if kind == "video" else "image/png",
                "size": len(media),
                "sha": hashlib.sha256(media).hexdigest(),
            },
        )
        await conn.execute(
            text("""UPDATE editorial_proposals SET source_asset_id=:asset,
          document=CAST(:d AS jsonb) WHERE id=:id"""),
            {"asset": asset, "d": json.dumps(document), "id": proposal},
        )
    return asset


async def _historical_completed_preview(
    admin, tenant, business, actor, proposal, settings, *, parent=None, emphasis="balanced", revision=1, operation=None
):
    """Seed a completed pre-cutover artifact with its genuine historical render key."""
    owner = Database(settings)
    try:
        async with owner.transaction(tenant, actor) as session:
            original = (
                (await session.execute(text("SELECT * FROM editorial_proposals WHERE id=:id"), {"id": proposal}))
                .mappings()
                .one()
            )
            inputs = await MediaPreviewService(settings, owner)._inputs(
                session, original, historical_access=True, parent_preview_id=parent, emphasis=emphasis
            )
        preview = uuid4()
        operation = operation or uuid4()
        request = {"proposal_id": proposal}
        if parent:
            request.update(parent_preview_id=parent, emphasis=emphasis)
        is_video = original["document"]["format"] == "short_video"
        key = f"previews/{tenant}/{business}/{preview}/historical.{('mp4' if is_video else 'jpg')}"
        async with admin.begin() as conn:
            await conn.execute(
                text("""INSERT INTO media_previews
                  (id,tenant_id,business_id,proposal_id,actor_id,operation_id,request_hash,render_key,
                   context_version,script_version,template_version,source_asset_id,fact_ids,state,object_key,sha256,
                   expires_at,mime_type,duration_ms,parent_preview_id,emphasis,revision)
                  VALUES(:id,:tenant,:business,:proposal,:actor,:operation,:hash,:render_key,
                   :context_version,:script_version,:template,:source,CAST(:facts AS jsonb),'completed',:key,:sha,
                   now()+interval '1 day',:mime,:duration,:parent,:emphasis,:revision)"""),
                {
                    "id": preview,
                    "tenant": tenant,
                    "business": business,
                    "proposal": proposal,
                    "actor": actor,
                    "operation": operation,
                    "hash": _digest(request),
                    "render_key": inputs.render_key,
                    "context_version": original["context_version"],
                    "script_version": original["script_version"],
                    "template": VIDEO_TEMPLATE_VERSION if is_video else TEMPLATE_VERSION,
                    "source": inputs.source_id,
                    "facts": json.dumps([str(inputs.fact_id)]),
                    "key": key,
                    "sha": "b" * 64,
                    "mime": "video/mp4" if is_video else "image/jpeg",
                    "duration": 8000 if is_video else None,
                    "parent": parent,
                    "emphasis": emphasis,
                    "revision": revision,
                },
            )
        assert await MediaPreviewService(settings, owner).file_key(tenant, business, actor, preview) == key
        return preview
    finally:
        await owner.close()


async def test_historical_preview_remains_private_and_reviewable_when_visual_execution_is_disabled(
    admin, api, seeded, settings, monkeypatch
):
    tenant, business, actor, fact, proposal, _ = await _accepted_case(admin, seeded)
    preview = uuid4()
    key = f"previews/{tenant}/{business}/{preview}/historical.jpg"
    async with admin.begin() as conn:
        await conn.execute(
            text("""INSERT INTO media_previews
              (id,tenant_id,business_id,actor_id,proposal_id,operation_id,request_hash,render_key,
               context_version,fact_ids,state,object_key,sha256,expires_at)
              VALUES(:id,:t,:b,:actor,:proposal,:operation,:request_hash,:render_key,1,
                CAST(:facts AS jsonb),'completed',:key,:sha,now()+interval '1 day')"""),
            {
                "id": preview,
                "t": tenant,
                "b": business,
                "actor": actor,
                "proposal": proposal,
                "operation": uuid4(),
                "request_hash": "a" * 64,
                "render_key": "b" * 64,
                "facts": json.dumps([str(fact)]),
                "key": key,
                "sha": "c" * 64,
            },
        )
        await conn.execute(
            text("UPDATE business_context_heads SET version=version+1 WHERE tenant_id=:t AND business_id=:b"),
            {"t": tenant, "b": business},
        )
    assert settings.visual_ai_mode == "disabled"
    signed = AsyncMock(return_value="https://private.test/historical")
    monkeypatch.setattr("app.api.v1.media_previews.MaterialStore.signed_url", signed)
    url = f"/api/v1/organizations/{tenant}/businesses/{business}/media-previews/{preview}/download-link"
    viewer = {"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"}
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    assert (await api.get(url, headers=viewer)).status_code == 403
    signed.assert_not_awaited()
    response = await api.get(url, headers=owner)
    assert response.status_code == 200
    assert response.json()["url"] == "https://private.test/historical"
    signed.assert_awaited_once_with(key, "image/jpeg")


async def test_automatic_candidate_is_private_and_does_not_accept_script(
    admin, api, seeded, settings, database, monkeypatch
):
    from app.api.v1 import media_previews as routes

    tenant, business, actor, _, admission = await _ready(admin, database, seeded, settings)
    proposal = admission.proposal
    cfg = admission.settings.model_copy(
        update={
            "visual_ai_reservation_usd_micros": 70,
            "visual_ai_monthly_budget_usd_micros": 100,
            "visual_ai_global_monthly_budget_usd_micros": 100,
        }
    )
    app_db = Database(cfg)
    worker_db = Database(cfg, correlator=True)
    store = Store()
    service = MediaPreviewService(cfg, app_db, store)
    monkeypatch.setattr(routes, "service", lambda _request: service)
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    path = f"/api/v1/organizations/{tenant}/businesses/{business}/media-previews"
    payload = PreviewRequest(operation_id=uuid4(), proposal_id=proposal, generation_mode="visual_fake")
    assert (await api.post(path, headers=owner, json=payload.model_dump(mode="json"))).json()[
        "error_code"
    ] == "PREVIEW_SCRIPT_NOT_ACCEPTED"
    try:
        candidate = await service.request_candidate(tenant, business, actor, payload)
        assert candidate.candidate and candidate.state == "pending"
        assert (await service.request_candidate(tenant, business, actor, payload)).id == candidate.id
        assert any(item.id == candidate.id for item in await service.list(tenant, business, actor))
        claim = (await claim_previews(worker_db, uuid4(), visual_enabled=True))[0]
        assert await MediaPreviewService(cfg, worker_db, store, app_db).render(claim.id, claim.fence) == "completed"
        assert await service.file_key(tenant, business, actor, candidate.id)
        async with admin.begin() as conn:
            state = await conn.scalar(
                text("SELECT review_state FROM editorial_proposals WHERE id=:id"), {"id": proposal}
            )
        assert state is None
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE editorial_proposals SET review_state='changes_requested' WHERE id=:id"),
                {"id": proposal},
            )
        assert any(item.id == candidate.id for item in await service.list(tenant, business, actor))
        assert await service.file_key(tenant, business, actor, candidate.id, review=True)
        with pytest.raises(AuthError) as error:
            await service.file_key(tenant, business, actor, candidate.id)
        assert error.value.code == "PREVIEW_NOT_READY"
    finally:
        await worker_db.close()
        await app_db.close()


@pytest.mark.parametrize(
    "change,code",
    [
        ("unaccepted", "PREVIEW_SCRIPT_NOT_ACCEPTED"),
        ("expired", "PREVIEW_SCRIPT_EXPIRED"),
        ("consent", "EDITORIAL_AI_CONSENT_REQUIRED"),
        ("plan", "PLAN_REQUIRED"),
        ("format", "PREVIEW_FORMAT_UNSUPPORTED"),
        ("no_fact", "PREVIEW_FACT_REQUIRED"),
        ("context_head", "PREVIEW_CONTEXT_CHANGED"),
        ("context_missing", "PREVIEW_CONTEXT_CHANGED"),
        ("fact_expired", "PREVIEW_FACT_EXPIRED"),
        ("fact_changed", "PREVIEW_FACT_CHANGED"),
        ("two_materials", "PREVIEW_MATERIAL_INVALID"),
    ],
)
async def test_invalid_script_or_current_inputs_block_preview(admin, api, seeded, settings, change, code):
    tenant, business, actor, _, proposal, document = await _accepted_case(admin, seeded)
    preview = await _historical_completed_preview(admin, tenant, business, actor, proposal, settings)
    params = {"id": proposal, "t": tenant, "b": business}
    async with admin.begin() as conn:
        if change == "unaccepted":
            await conn.execute(text("UPDATE editorial_proposals SET review_state=NULL WHERE id=:id"), params)
        elif change == "expired":
            await conn.execute(
                text("UPDATE editorial_proposals SET expires_at=now()-interval '1 day' WHERE id=:id"), params
            )
        elif change == "consent":
            await conn.execute(text("UPDATE editorial_proposals SET model='test-model' WHERE id=:id"), params)
        elif change == "plan":
            await conn.execute(text("UPDATE billing_sponsorships SET revoked_at=now() WHERE tenant_id=:t"), params)
        elif change == "format":
            document["format"] = "carousel"
        elif change == "no_fact":
            document["script"] = document["script"][1:]
        elif change == "context_head":
            await conn.execute(
                text("UPDATE business_context_heads SET version=2 WHERE tenant_id=:t AND business_id=:b"), params
            )
        elif change == "context_missing":
            await conn.execute(
                text("UPDATE business_context_heads SET version=2 WHERE tenant_id=:t AND business_id=:b"), params
            )
            await conn.execute(text("UPDATE editorial_proposals SET context_version=2 WHERE id=:id"), params)
        elif change == "fact_expired":
            yesterday = str(date.today() - timedelta(days=1))
            await conn.execute(
                text("""UPDATE business_context_versions SET document=jsonb_set(document,
              '{facts,0,valid_until}',to_jsonb(CAST(:y AS text))) WHERE tenant_id=:t AND business_id=:b"""),
                {**params, "y": yesterday},
            )
        elif change == "fact_changed":
            document["script"][0]["on_screen_text"] = "Preço inventado"
        elif change == "two_materials":
            document["script"] = [
                {
                    "role": "material",
                    "visual": "source_material",
                    "on_screen_text": "Foto do negócio",
                    "voiceover": "Veja nossa foto",
                    "fact_ids": [],
                    "source_asset_id": None,
                },
                {
                    "role": "material",
                    "visual": "source_material",
                    "on_screen_text": "Outra foto",
                    "voiceover": "Veja outra foto",
                    "fact_ids": [],
                    "source_asset_id": None,
                },
                document["script"][0],
            ]
        if change in {"format", "no_fact", "fact_changed", "two_materials"}:
            await conn.execute(
                text("UPDATE editorial_proposals SET document=CAST(:d AS jsonb) WHERE id=:id"),
                {"id": proposal, "d": json.dumps(document)},
            )
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    response = await api.post(
        f"/api/v1/organizations/{tenant}/businesses/{business}/media-previews",
        headers=owner,
        json={"operation_id": str(uuid4()), "proposal_id": str(proposal), "generation_mode": "local"},
    )
    # New photo/story creation is retired; carousel still reaches its own format guard.
    assert response.json()["error_code"] == (code if change == "format" else "PREVIEW_LEGACY_CREATION_DISABLED"), (
        response.text
    )
    direct = Database(settings)
    try:
        async with direct.transaction(tenant, actor) as session:
            historical = (
                (await session.execute(text("SELECT * FROM editorial_proposals WHERE id=:id"), {"id": proposal}))
                .mappings()
                .one()
            )
            with pytest.raises(AuthError) as error:
                await MediaPreviewService(settings, direct)._inputs(session, historical, historical_access=True)
            assert error.value.code == code
        with pytest.raises(AuthError, match="PREVIEW_NOT_READY"):
            await MediaPreviewService(settings, direct).file_key(tenant, business, actor, preview)
    finally:
        await direct.close()


@pytest.mark.parametrize("bad_hash", [False, True])
async def test_source_photo_is_private_and_verified_before_render(admin, database, seeded, settings, bad_hash):
    tenant, business, actor, _, admission = await _ready(admin, database, seeded, settings)
    proposal, cfg = admission.proposal, admission.settings
    picture = io.BytesIO()
    Image.new("RGB", (100, 100), "#ffbb33").save(picture, format="PNG")
    media = picture.getvalue()
    async with admin.begin() as connection:
        await connection.execute(
            text("""UPDATE whatsapp_material_assets SET kind='image',object_key='private/source.png',
              mime_type='image/png',sha256=:sha,size_bytes=:size
              WHERE id=(SELECT source_asset_id FROM editorial_proposals WHERE id=:proposal)"""),
            {"sha": hashlib.sha256(media).hexdigest(), "size": len(media), "proposal": proposal},
        )
    owner = Database(cfg)
    try:
        store = AsyncMock()
        store.get_image.return_value = b"changed" if bad_hash else media
        service = VisualReferenceService(cfg, owner, store)
        if bad_hash:
            with pytest.raises(AuthError, match="VISUAL_REFERENCE_HASH_MISMATCH"):
                await service.load(tenant, business, actor, proposal, candidate=True)
        else:
            bundle = await service.load(tenant, business, actor, proposal, candidate=True)
            assert len(bundle.references) == 1 and bundle.references[0].mime_type == "image/png"
            assert bundle.sources[0].source_sha256 == hashlib.sha256(media).hexdigest()
        store.get_image.assert_awaited_once()
        store.put.assert_not_awaited()
        with pytest.raises(AuthError):
            await service.load(seeded["t2"], business, seeded["a2"], proposal, candidate=True)
    finally:
        await owner.close()


@pytest.mark.parametrize("invalid", ["mime", "key", "hash", "proposal_source"])
async def test_source_must_still_be_usable_and_belong_to_proposal(admin, seeded, settings, invalid):
    tenant, business, actor, _, proposal, document = await _accepted_case(admin, seeded)
    asset = await _attach_source(admin, tenant, business, proposal, document, b"image")
    preview = await _historical_completed_preview(admin, tenant, business, actor, proposal, settings)
    async with admin.begin() as conn:
        if invalid == "mime":
            await conn.execute(
                text("UPDATE whatsapp_material_assets SET mime_type='video/mp4' WHERE id=:id"), {"id": asset}
            )
        elif invalid == "key":
            await conn.execute(text("UPDATE whatsapp_material_assets SET object_key=NULL WHERE id=:id"), {"id": asset})
        elif invalid == "hash":
            await conn.execute(text("UPDATE whatsapp_material_assets SET sha256=NULL WHERE id=:id"), {"id": asset})
        else:
            await conn.execute(
                text("UPDATE editorial_proposals SET source_asset_id=NULL WHERE id=:id"), {"id": proposal}
            )
    owner_db = Database(settings)
    try:
        async with owner_db.transaction(tenant, actor) as session:
            historical = (
                (await session.execute(text("SELECT * FROM editorial_proposals WHERE id=:id"), {"id": proposal}))
                .mappings()
                .one()
            )
            with pytest.raises(AuthError, match="PREVIEW_MATERIAL_NOT_READY"):
                await MediaPreviewService(settings, owner_db)._inputs(session, historical, historical_access=True)
        with pytest.raises(AuthError, match="PREVIEW_NOT_READY"):
            await MediaPreviewService(settings, owner_db).file_key(tenant, business, actor, preview)
        with pytest.raises(AuthError, match="PREVIEW_LEGACY_CREATION_DISABLED"):
            await MediaPreviewService(settings, owner_db).request(
                tenant,
                business,
                actor,
                PreviewRequest(operation_id=uuid4(), proposal_id=proposal, generation_mode="local"),
            )
    finally:
        await owner_db.close()


@pytest.mark.parametrize(
    "failure,expected",
    [
        ("changed_before", "failed"),
        ("storage_retry", "failed"),
        ("render_error", "failed"),
        ("changed_after", "failed"),
        ("fence_superseded", "skipped"),
        ("deleted_after", "failed"),
    ],
)
async def test_render_rechecks_inputs_and_cleans_partial_output(
    admin, database, seeded, settings, monkeypatch, failure, expected
):
    tenant, business, actor, _, admission = await _ready(admin, database, seeded, settings)
    cfg = admission.settings.model_copy(update={"visual_ai_monthly_budget_usd_micros": 100})
    owner = Database(cfg)
    worker = Database(cfg, correlator=True)
    try:
        preview = await MediaPreviewService(cfg, owner).request_candidate(
            tenant,
            business,
            actor,
            PreviewRequest(operation_id=uuid4(), proposal_id=admission.proposal, generation_mode="visual_fake"),
        )
        claim = (await claim_previews(worker, uuid4()))[0]
        assert claim.id == preview.id
        store = AsyncMock()
        if failure == "changed_before":
            async with admin.begin() as conn:
                await conn.execute(
                    text("UPDATE business_brand_kit_heads SET confirmed_version=NULL WHERE business_id=:b"),
                    {"b": business},
                )
        elif failure == "storage_retry":
            store.put.side_effect = MaterialError("MATERIAL_STORAGE_UNAVAILABLE", retryable=True)
        elif failure == "render_error":
            monkeypatch.setattr(
                "app.services.visual_brand_finish.VisualBrandFinishService.finish",
                AsyncMock(side_effect=AuthError("VISUAL_SOURCE_CHANGED", 409)),
            )
        elif failure in {"changed_after", "fence_superseded", "deleted_after"}:

            async def change_after_put(*_):
                async with admin.begin() as conn:
                    if failure == "changed_after":
                        await conn.execute(
                            text("UPDATE business_brand_kit_heads SET confirmed_version=NULL WHERE business_id=:b"),
                            {"b": business},
                        )
                    elif failure == "fence_superseded":
                        await conn.execute(
                            text("UPDATE media_previews SET dispatch_fence=dispatch_fence+1 WHERE id=:id"),
                            {"id": claim.id},
                        )
                    else:
                        await conn.execute(
                            text("DELETE FROM editorial_proposals WHERE id=:id"), {"id": admission.proposal}
                        )

            store.put.side_effect = change_after_put
        result = await MediaPreviewService(cfg, worker, store, owner).render(claim.id, claim.fence)
        assert result == expected
        if failure in {"storage_retry", "changed_after", "fence_superseded", "deleted_after"}:
            store.delete.assert_awaited_once()
        else:
            store.delete.assert_not_awaited()
        if failure == "deleted_after":
            async with admin.connect() as conn:
                row = (
                    (
                        await conn.execute(
                            text("SELECT state,object_key FROM media_previews WHERE id=:id"), {"id": preview.id}
                        )
                    )
                    .mappings()
                    .one()
                )
                assert row["state"] != "completed" and row["object_key"] is None
            with pytest.raises(AuthError, match="PREVIEW_NOT_READY"):
                await MediaPreviewService(cfg, owner).file_key(tenant, business, actor, preview.id)
    finally:
        await owner.close()
        await worker.close()


async def test_stale_render_does_not_delete_the_newer_attempts_object(admin, database, seeded, settings):
    tenant, business, actor, _, admission = await _ready(admin, database, seeded, settings)
    cfg = admission.settings.model_copy(update={"visual_ai_monthly_budget_usd_micros": 100})
    owner, worker = Database(cfg), Database(cfg, correlator=True)
    try:
        preview = await MediaPreviewService(cfg, owner).request_candidate(
            tenant,
            business,
            actor,
            PreviewRequest(operation_id=uuid4(), proposal_id=admission.proposal, generation_mode="visual_fake"),
        )
        claim = (await claim_previews(worker, uuid4()))[0]
        entered, release = asyncio.Event(), asyncio.Event()
        objects = {}

        async def put(key, media):
            objects[key] = media.data
            entered.set()
            await release.wait()

        async def delete(key):
            objects.pop(key, None)

        store = AsyncMock()
        store.put.side_effect = put
        store.delete.side_effect = delete
        service = MediaPreviewService(cfg, worker, store, owner)
        first = asyncio.create_task(service.render(claim.id, claim.fence))
        winner_key = f"previews/{tenant}/{business}/{preview.id}/attempt-{claim.fence + 1}/winner.jpg"
        try:
            await asyncio.wait_for(entered.wait(), timeout=20)
            objects[winner_key] = b"newer protected output"
            async with admin.begin() as conn:
                await conn.execute(
                    text("""UPDATE media_previews SET dispatch_fence=dispatch_fence+1,
                      state='completed',object_key=:key,sha256=:sha WHERE id=:id"""),
                    {"id": preview.id, "key": winner_key, "sha": "b" * 64},
                )
        finally:
            release.set()
        assert await first == "skipped"
        async with admin.connect() as conn:
            stored_key = await conn.scalar(
                text("SELECT object_key FROM media_previews WHERE id=:id"), {"id": preview.id}
            )
        assert stored_key == winner_key and objects == {winner_key: b"newer protected output"}
        store.delete.assert_awaited_once()
        assert store.delete.await_args.args[0] != winner_key
    finally:
        await worker.close()
        await owner.close()


@pytest.mark.parametrize("terminal", ["failed_dispatch", "stale_worker"])
async def test_dispatch_retries_are_fenced_and_bounded(admin, seeded, settings, database, terminal):
    tenant, business, actor, _, admission = await _ready(admin, database, seeded, settings)
    cfg = admission.settings
    owner_db = Database(cfg)
    worker = Database(cfg, correlator=True)
    try:
        preview = await MediaPreviewService(cfg, owner_db).request_candidate(
            tenant,
            business,
            actor,
            PreviewRequest(operation_id=uuid4(), proposal_id=admission.proposal, generation_mode="visual_fake"),
        )
        assert (await claim_previews(worker, uuid4(), limit=0)) == []
        first = (await claim_previews(worker, uuid4()))[0]
        assert (await claim_previews(worker, uuid4())) == []
        await finish_preview_dispatch(worker, first, True)
        await finish_preview_dispatch(worker, first, False)
        second = (await claim_previews(worker, uuid4()))[0]
        assert second.fence == first.fence + 1 and second.attempt == 2
        await finish_preview_dispatch(worker, first, False)
        await finish_preview_dispatch(worker, second, False)
        third = (await claim_previews(worker, uuid4()))[0]
        assert third.attempt == 3
        if terminal == "failed_dispatch":
            await finish_preview_dispatch(worker, third, False)
        else:
            async with admin.begin() as conn:
                await conn.execute(
                    text("""UPDATE media_previews SET
                  dispatch_lease_until=now()-interval '1 second' WHERE id=:id"""),
                    {"id": preview.id},
                )
            assert await reconcile_stale_previews(worker) == 1
            assert await reconcile_stale_previews(worker) == 0
        assert (await claim_previews(worker, uuid4())) == []
        assert (await MediaPreviewService(cfg, owner_db).list(tenant, business, actor))[0].state == "failed"
    finally:
        await owner_db.close()
        await worker.close()


@pytest.mark.parametrize("cause", ["expired", "source_deleted", "proposal_deleted"])
async def test_retention_hides_and_erases_private_output(admin, seeded, settings, database, cause):
    tenant, business, actor, _, admission = await _ready(admin, database, seeded, settings)
    proposal, cfg = admission.proposal, admission.settings
    async with admin.connect() as conn:
        asset = await conn.scalar(
            text("SELECT source_asset_id FROM editorial_proposals WHERE id=:id"), {"id": proposal}
        )
    owner_db = Database(cfg)
    worker = Database(cfg, correlator=True)
    try:
        service = MediaPreviewService(cfg, owner_db)
        preview = await service.request_candidate(
            tenant,
            business,
            actor,
            PreviewRequest(operation_id=uuid4(), proposal_id=proposal, generation_mode="visual_fake"),
        )
        async with admin.begin() as conn:
            if cause == "expired":
                await conn.execute(
                    text("UPDATE media_previews SET expires_at=now()-interval '1 day' WHERE id=:id"), {"id": preview.id}
                )
            elif cause == "source_deleted":
                await conn.execute(
                    text("UPDATE whatsapp_material_assets SET delete_requested_at=now() WHERE id=:id"), {"id": asset}
                )
            else:
                await conn.execute(text("DELETE FROM editorial_proposals WHERE id=:id"), {"id": proposal})
        assert await service.list(tenant, business, actor) == []
        with pytest.raises(AuthError, match="PREVIEW_NOT_READY"):
            await service.file_key(tenant, business, actor, preview.id)
        store = AsyncMock()
        assert (await claim_expired_previews(worker, uuid4(), limit=0)) == []
        claim = (await claim_expired_previews(worker, uuid4()))[0]
        assert claim.object_key.startswith(f"previews/{tenant}/{business}/{preview.id}/")
        assert (await claim_expired_previews(worker, uuid4())) == []
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE media_previews SET dispatch_lease_until=now()-interval '1 second' WHERE id=:id"),
                {"id": preview.id},
            )
        store.delete.side_effect = MaterialError("MATERIAL_STORAGE_UNAVAILABLE", retryable=True)
        assert await purge_expired_previews(worker, store, uuid4()) == 0
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE media_previews SET dispatch_lease_until=now()-interval '1 second' WHERE id=:id"),
                {"id": preview.id},
            )
        store.delete.side_effect = None
        assert await purge_expired_previews(worker, store, uuid4()) == 1
        assert await finish_preview_purge(worker, claim) is False
        assert await service.list(tenant, business, actor) == []
    finally:
        await owner_db.close()
        await worker.close()


@pytest.mark.parametrize("mode", ["local", "visual_fake"])
async def test_retention_deletes_the_recorded_abandoned_attempt_key(admin, seeded, settings, mode):
    tenant, business, actor, fact, proposal, _ = await _accepted_case(admin, seeded)
    worker = Database(settings, correlator=True)
    try:
        # Retention also covers historical previews that cannot be created anymore.
        preview_id = uuid4()
        stored_key = f"previews/{tenant}/{business}/{preview_id}/attempt-3/committed.jpg"
        async with admin.begin() as conn:
            await conn.execute(
                text("""INSERT INTO media_previews
                  (id,tenant_id,business_id,actor_id,proposal_id,operation_id,request_hash,render_key,
                   context_version,fact_ids,state,object_key,expires_at,generation_mode,visual_fingerprint)
                  VALUES(:id,:tenant,:business,:actor,:proposal,:operation,:request_hash,:render_key,
                   1,CAST(:facts AS jsonb),'failed',:key,now()-interval '1 second',:mode,
                   CASE WHEN :mode='visual_fake' THEN CAST(:fingerprint AS char(64)) ELSE NULL END)"""),
                {
                    "id": preview_id,
                    "tenant": tenant,
                    "business": business,
                    "actor": actor,
                    "proposal": proposal,
                    "operation": uuid4(),
                    "request_hash": "a" * 64,
                    "render_key": "b" * 64,
                    "facts": json.dumps([str(fact)]),
                    "key": stored_key,
                    "fingerprint": "c" * 64,
                    "mode": mode,
                },
            )
        store = AsyncMock()
        assert await purge_expired_previews(worker, store, uuid4()) == 1
        store.delete.assert_awaited_once_with(stored_key)
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT count(*) FROM media_previews WHERE id=:id"), {"id": preview_id}) == 0
    finally:
        await worker.close()


async def test_static_preview_owner_lifecycle_and_tenant_isolation(admin, database, seeded, settings, monkeypatch):
    tenant, business, actor, _, admission = await _ready(admin, database, seeded, settings)
    cfg = admission.settings.model_copy(
        update={"visual_ai_monthly_budget_usd_micros": 100, "visual_skill_experiment_enabled": True}
    )
    owner_db, worker = Database(cfg), Database(cfg, correlator=True)
    owner = {"Authorization": f"Bearer {access_token(cfg, actor)}"}
    viewer = {"Authorization": f"Bearer {access_token(cfg, seeded['viewer'])}"}
    base = f"/api/v1/organizations/{tenant}/businesses/{business}/media-previews"
    store = AsyncMock()
    app = create_app(cfg, owner_db)
    try:
        service = MediaPreviewService(cfg, owner_db)
        request = PreviewRequest(operation_id=uuid4(), proposal_id=admission.proposal, generation_mode="visual_fake")
        preview, replay = await asyncio.gather(
            service.request_candidate(tenant, business, actor, request),
            service.request_candidate(tenant, business, actor, request),
        )
        assert preview.id == replay.id and preview.state == "pending"
        with pytest.raises(AuthError, match="PREVIEW_OPERATION_CONFLICT"):
            await service.request_candidate(
                tenant, business, actor, request.model_copy(update={"visual_skill_id": "instagram-feed-v1"})
            )
        with pytest.raises(AuthError, match="PREVIEW_NOT_READY"):
            await service.file_key(tenant, business, actor, preview.id)
        async with database.transaction(seeded["t2"], seeded["a2"]) as session:
            assert await session.scalar(text("SELECT count(*) FROM media_previews")) == 0
        claim = (await claim_previews(worker, uuid4()))[0]
        renderer = MediaPreviewService(cfg, worker, store, owner_db)
        assert await renderer.render(preview.id, claim.fence) == "completed"
        assert await renderer.render(preview.id, claim.fence) == "skipped"
        store.put.assert_awaited_once()
        assert store.put.await_args.args[1].mime_type == "image/jpeg"
        monkeypatch.setattr(
            "app.api.v1.media_previews.MaterialStore.signed_url", AsyncMock(return_value="https://example.test/private")
        )
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client,
        ):
            assert (await client.get(base, headers=viewer)).status_code == 403
            assert (await client.get(base + f"/{preview.id}/download-link", headers=viewer)).status_code == 403
            listed = await client.get(base, headers=owner)
            assert listed.status_code == 200 and listed.json()[0]["id"] == str(preview.id)
            link = await client.get(base + f"/{preview.id}/download-link", headers=owner)
            assert link.status_code == 200 and link.json()["url"] == "https://example.test/private"
            assert (await client.get(base + f"/{uuid4()}/download-link", headers=owner)).status_code == 404
    finally:
        await worker.close()
        await owner_db.close()


async def test_historical_short_video_remains_private_and_reviewable(admin, api, seeded, settings, monkeypatch):
    tenant, business, actor, _, proposal, document = await _accepted_case(admin, seeded)
    photo = io.BytesIO()
    Image.new("RGB", (100, 100), "#ffbb33").save(photo, format="PNG")
    await _attach_source(admin, tenant, business, proposal, document, photo.getvalue())
    document["format"] = "short_video"
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE editorial_proposals SET document=CAST(:doc AS jsonb) WHERE id=:id"),
            {"id": proposal, "doc": json.dumps(document)},
        )
        await conn.execute(
            text("""UPDATE business_context_versions SET document=jsonb_set(document,
          '{facts,0,valid_until}',to_jsonb(CAST(:today AS text)))
          WHERE tenant_id=:tenant AND business_id=:business AND version=1"""),
            {"tenant": tenant, "business": business, "today": date.today().isoformat()},
        )
    preview = await _historical_completed_preview(admin, tenant, business, actor, proposal, settings)
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    viewer = {"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"}
    url = f"/api/v1/organizations/{tenant}/businesses/{business}/media-previews"
    signed = AsyncMock(return_value="https://example.test/video")
    monkeypatch.setattr("app.api.v1.media_previews.MaterialStore.signed_url", signed)
    assert (await api.get(url + f"/{preview}/download-link", headers=viewer)).status_code == 403
    link = await api.get(url + f"/{preview}/download-link", headers=owner)
    assert link.status_code == 200 and link.json()["url"].endswith("video")
    assert signed.await_args.args[1] == "video/mp4"
    listed = await api.get(url, headers=owner)
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == str(preview) and listed.json()[0]["generation_mode"] == "local"
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE media_previews SET expires_at=now()-interval '1 second' WHERE id=:id"), {"id": preview}
        )
    assert (await api.get(url + f"/{preview}/download-link", headers=owner)).status_code == 200
    worker = Database(settings, correlator=True)
    try:
        store = AsyncMock()
        assert await purge_expired_previews(worker, store, uuid4()) == 0
        store.delete.assert_not_awaited()
    finally:
        await worker.close()


async def test_retired_new_short_video_does_not_read_or_render_source(admin, api, seeded, settings, monkeypatch):
    tenant, business, actor, _, proposal, document = await _accepted_case(admin, seeded)
    document["format"] = "short_video"
    await _attach_source(admin, tenant, business, proposal, document, b"synthetic-video", kind="video")
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE editorial_proposals SET document=CAST(:doc AS jsonb) WHERE id=:id"),
            {"id": proposal, "doc": json.dumps(document)},
        )
    renderer, reader = AsyncMock(), AsyncMock()
    monkeypatch.setattr("app.adapters.video_preview.render_video_preview", renderer)
    monkeypatch.setattr("app.adapters.material_media.MaterialStore.get_video", reader)
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    url = f"/api/v1/organizations/{tenant}/businesses/{business}/media-previews"
    response = await api.post(
        url,
        headers=owner,
        json={"operation_id": str(uuid4()), "proposal_id": str(proposal), "generation_mode": "local"},
    )
    assert response.status_code == 409 and response.json()["error_code"] == "PREVIEW_LEGACY_CREATION_DISABLED"
    renderer.assert_not_awaited()
    reader.assert_not_awaited()
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM media_previews")) == 0


async def test_historical_adjustments_are_private_versioned_and_idempotent(admin, api, seeded, settings):
    tenant, business, actor, _, proposal, _ = await _accepted_case(admin, seeded)
    base = await _historical_completed_preview(admin, tenant, business, actor, proposal, settings)
    operation = uuid4()
    adjusted = await _historical_completed_preview(
        admin,
        tenant,
        business,
        actor,
        proposal,
        settings,
        parent=base,
        emphasis="photo",
        revision=2,
        operation=operation,
    )
    owner = Database(settings)
    try:
        service = MediaPreviewService(settings, owner)
        replay = await service.request(
            tenant,
            business,
            actor,
            PreviewRequest(
                operation_id=operation,
                proposal_id=proposal,
                parent_preview_id=base,
                emphasis="photo",
                generation_mode="local",
            ),
        )
        assert replay.id == adjusted and replay.parent_preview_id == base and replay.revision == 2
        with pytest.raises(AuthError, match="PREVIEW_OPERATION_CONFLICT"):
            await service.request(
                tenant,
                business,
                actor,
                PreviewRequest(
                    operation_id=operation,
                    proposal_id=proposal,
                    parent_preview_id=base,
                    emphasis="text",
                    generation_mode="local",
                ),
            )
        assert await service.file_key(tenant, business, actor, base)
        assert await service.file_key(tenant, business, actor, adjusted)
        viewer = {"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"}
        url = f"/api/v1/organizations/{tenant}/businesses/{business}/media-previews/{adjusted}/download-link"
        assert (await api.get(url, headers=viewer)).status_code == 403
        with pytest.raises(AuthError, match="PREVIEW_LEGACY_CREATION_DISABLED"):
            await service.request(
                tenant,
                business,
                actor,
                PreviewRequest(
                    operation_id=uuid4(),
                    proposal_id=proposal,
                    parent_preview_id=adjusted,
                    emphasis="text",
                    generation_mode="local",
                ),
            )
    finally:
        await owner.close()


async def test_retired_adjustments_cannot_start_new_visual_work(admin, api, seeded, settings):
    from pydantic import ValidationError

    tenant, business, actor, _, proposal, _ = await _accepted_case(admin, seeded)
    base = await _historical_completed_preview(admin, tenant, business, actor, proposal, settings)
    with pytest.raises(ValidationError, match="VISUAL_ADJUSTMENT_UNAVAILABLE"):
        PreviewRequest(
            operation_id=uuid4(),
            proposal_id=proposal,
            parent_preview_id=base,
            emphasis="photo",
            generation_mode="visual_fake",
        )
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    url = f"/api/v1/organizations/{tenant}/businesses/{business}/media-previews"
    for emphasis in ("balanced", "photo", "text"):
        response = await api.post(
            url,
            headers=owner,
            json={
                "operation_id": str(uuid4()),
                "proposal_id": str(proposal),
                "parent_preview_id": str(base),
                "emphasis": emphasis,
                "generation_mode": "local",
            },
        )
        assert response.status_code == 409 and response.json()["error_code"] == "PREVIEW_LEGACY_CREATION_DISABLED"
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM media_previews")) == 1


@pytest.mark.parametrize("changed_version", ["script", "context"])
async def test_historical_adjustment_blocks_delivery_when_source_version_changes(
    admin, seeded, settings, changed_version
):
    tenant, business, actor, _, proposal, _ = await _accepted_case(admin, seeded)
    base = await _historical_completed_preview(admin, tenant, business, actor, proposal, settings)
    adjusted = await _historical_completed_preview(
        admin, tenant, business, actor, proposal, settings, parent=base, emphasis="photo", revision=2
    )
    async with admin.begin() as conn:
        column = "script_version" if changed_version == "script" else "context_version"
        await conn.execute(text(f"UPDATE editorial_proposals SET {column}={column}+1 WHERE id=:id"), {"id": proposal})
    owner = Database(settings)
    try:
        service = MediaPreviewService(settings, owner)
        with pytest.raises(AuthError, match="PREVIEW_NOT_READY"):
            await service.file_key(tenant, business, actor, adjusted)
        assert (await service.file_key(tenant, business, actor, adjusted, review=True)).endswith(".jpg")
    finally:
        await owner.close()


async def test_claimed_legacy_video_fails_durably_without_reading_or_uploading(admin, seeded, settings):
    tenant, business, actor, _, proposal, document = await _accepted_case(admin, seeded)
    document["format"] = "short_video"
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE editorial_proposals SET document=CAST(:doc AS jsonb) WHERE id=:id"),
            {"id": proposal, "doc": json.dumps(document)},
        )
    preview = await _historical_completed_preview(admin, tenant, business, actor, proposal, settings)
    async with admin.begin() as connection:
        await connection.execute(
            text("""UPDATE media_previews SET state='rendering',dispatch_fence=4,attempts=1,
              object_key=NULL,sha256=NULL WHERE id=:id"""),
            {"id": preview},
        )
    worker = Database(settings, correlator=True)
    store = AsyncMock()
    try:
        assert await MediaPreviewService(settings, worker, store).render(preview, 4) == "failed"
        store.get_image.assert_not_awaited()
        store.get_video.assert_not_awaited()
        store.put.assert_not_awaited()
        store.delete.assert_not_awaited()
        async with admin.connect() as connection:
            row = (
                (
                    await connection.execute(
                        text("SELECT state,error_code,object_key,sha256 FROM media_previews WHERE id=:id"),
                        {"id": preview},
                    )
                )
                .mappings()
                .one()
            )
            assert row == {
                "state": "failed",
                "error_code": "PREVIEW_LEGACY_CREATION_DISABLED",
                "object_key": None,
                "sha256": None,
            }
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM audit_events WHERE operation_id=:id AND action='media.preview_failed'"),
                    {"id": preview},
                )
                == 1
            )
    finally:
        await worker.close()
