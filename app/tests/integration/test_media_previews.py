"""Private preview lifecycle on restricted PostgreSQL roles and real HTTP routes."""

import asyncio
import hashlib
import io
import json
from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from PIL import Image
from sqlalchemy import text

from app.adapters.material_media import FetchedMedia, MaterialError
from app.adapters.static_preview import TEMPLATE_VERSION, PreviewRenderError
from app.db.session import Database
from app.schemas.media_previews import PreviewRequest
from app.services.auth import AuthError
from app.services.editorial_dispatch import claim_proposals
from app.services.editorial_proposals import EditorialProposalService
from app.services.media_dispatch import claim_previews, finish_preview_dispatch, reconcile_stale_previews
from app.services.media_previews import MediaPreviewService
from app.services.media_retention import claim_expired_previews, finish_preview_purge, purge_expired_previews
from app.tests.integration.test_editorial_proposals import _business
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


async def test_automatic_candidate_is_private_and_does_not_accept_script(admin, api, seeded, settings):
    tenant, business, actor, _, proposal, _ = await _accepted_case(admin, seeded)
    async with admin.begin() as conn:
        await conn.execute(text("UPDATE editorial_proposals SET review_state=NULL WHERE id=:id"), {"id": proposal})
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    path = f"/api/v1/organizations/{tenant}/businesses/{business}/media-previews"
    payload = PreviewRequest(operation_id=uuid4(), proposal_id=proposal)
    assert (await api.post(path, headers=owner, json=payload.model_dump(mode="json"))).json()[
        "error_code"
    ] == "PREVIEW_SCRIPT_NOT_ACCEPTED"
    app_db = Database(settings)
    worker_db = Database(settings, correlator=True)
    try:
        service = MediaPreviewService(settings, app_db)
        candidate = await service.request_candidate(tenant, business, actor, payload)
        assert candidate.candidate and candidate.state == "pending"
        assert (await service.request_candidate(tenant, business, actor, payload)).id == candidate.id
        assert any(item.id == candidate.id for item in await service.list(tenant, business, actor))
        claim = (await claim_previews(worker_db, uuid4()))[0]
        store = AsyncMock()
        assert await MediaPreviewService(settings, worker_db, store).render(claim.id, claim.fence) == "completed"
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
        assert all(item.id != candidate.id for item in await service.list(tenant, business, actor))
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
        json={"operation_id": str(uuid4()), "proposal_id": str(proposal)},
    )
    assert response.json()["error_code"] == code, response.text
    direct = Database(settings)
    try:
        with pytest.raises(AuthError) as error:
            await MediaPreviewService(settings, direct).request(
                tenant, business, actor, PreviewRequest(operation_id=uuid4(), proposal_id=proposal)
            )
        assert error.value.code == code
    finally:
        await direct.close()


@pytest.mark.parametrize("bad_hash", [False, True])
async def test_source_photo_is_private_and_verified_before_render(admin, api, seeded, settings, bad_hash):
    tenant, business, actor, _, proposal, document = await _accepted_case(admin, seeded)
    picture = io.BytesIO()
    Image.new("RGB", (100, 100), "#ffbb33").save(picture, format="PNG")
    media = picture.getvalue()
    await _attach_source(admin, tenant, business, proposal, document, media)
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    url = f"/api/v1/organizations/{tenant}/businesses/{business}/media-previews"
    response = await api.post(url, headers=owner, json={"operation_id": str(uuid4()), "proposal_id": str(proposal)})
    assert response.status_code == 202, response.text
    worker = Database(settings, correlator=True)
    try:
        claim = (await claim_previews(worker, uuid4()))[0]
        store = AsyncMock()
        store.get_image.return_value = b"changed" if bad_hash else media
        result = await MediaPreviewService(settings, worker, store).render(claim.id, claim.fence)
        assert result == ("failed" if bad_hash else "completed")
        store.get_image.assert_awaited_once()
        assert store.put.await_count == (0 if bad_hash else 1)
    finally:
        await worker.close()


@pytest.mark.parametrize("invalid", ["mime", "key", "hash", "proposal_source"])
async def test_source_must_still_be_usable_and_belong_to_proposal(admin, seeded, settings, invalid):
    tenant, business, actor, _, proposal, document = await _accepted_case(admin, seeded)
    asset = await _attach_source(admin, tenant, business, proposal, document, b"image")
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
        with pytest.raises(AuthError, match="PREVIEW_MATERIAL_NOT_READY"):
            await MediaPreviewService(settings, owner_db).request(
                tenant, business, actor, PreviewRequest(operation_id=uuid4(), proposal_id=proposal)
            )
    finally:
        await owner_db.close()


@pytest.mark.parametrize(
    "failure,expected",
    [
        ("changed_before", "failed"),
        ("storage_retry", "pending"),
        ("render_error", "failed"),
        ("changed_after", "skipped"),
        ("fence_superseded", "skipped"),
        ("deleted_after", "skipped"),
    ],
)
async def test_render_rechecks_inputs_and_cleans_partial_output(
    admin, api, seeded, settings, monkeypatch, failure, expected
):
    tenant, business, actor, _, proposal, _ = await _accepted_case(admin, seeded)
    url = f"/api/v1/organizations/{tenant}/businesses/{business}/media-previews"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    preview = await api.post(url, headers=owner, json={"operation_id": str(uuid4()), "proposal_id": str(proposal)})
    assert preview.status_code == 202, preview.text
    worker = Database(settings, correlator=True)
    try:
        claim = (await claim_previews(worker, uuid4()))[0]
        store = AsyncMock()
        if failure == "changed_before":
            async with admin.begin() as conn:
                await conn.execute(
                    text("UPDATE business_profiles SET brand_color='#112233' WHERE business_id=:b"), {"b": business}
                )
        elif failure == "storage_retry":
            store.put.side_effect = MaterialError("MATERIAL_STORAGE_UNAVAILABLE", retryable=True)
        elif failure == "render_error":
            monkeypatch.setattr(
                "app.services.media_previews.render_static_preview",
                lambda **_: (_ for _ in ()).throw(PreviewRenderError("PREVIEW_TEXT_OVERFLOW")),
            )
        elif failure in {"changed_after", "fence_superseded", "deleted_after"}:

            async def change_after_put(*_):
                async with admin.begin() as conn:
                    if failure == "changed_after":
                        await conn.execute(
                            text("UPDATE business_profiles SET brand_color='#112233' WHERE business_id=:b"),
                            {"b": business},
                        )
                    elif failure == "fence_superseded":
                        await conn.execute(
                            text("UPDATE media_previews SET dispatch_fence=dispatch_fence+1 WHERE id=:id"),
                            {"id": claim.id},
                        )
                    else:
                        await conn.execute(text("DELETE FROM editorial_proposals WHERE id=:id"), {"id": proposal})

            store.put.side_effect = change_after_put
        result = await MediaPreviewService(settings, worker, store).render(claim.id, claim.fence)
        assert result == expected
        if failure in {"changed_after", "fence_superseded", "deleted_after"}:
            store.delete.assert_awaited_once()
        else:
            store.delete.assert_not_awaited()
    finally:
        await worker.close()


async def test_stale_render_does_not_delete_the_newer_attempts_object(admin, seeded, settings):
    tenant, business, actor, _, proposal, _ = await _accepted_case(admin, seeded)
    owner, worker = Database(settings), Database(settings, correlator=True)
    try:
        preview = await MediaPreviewService(settings, owner).request(
            tenant, business, actor, PreviewRequest(operation_id=uuid4(), proposal_id=proposal)
        )
        claim = (await claim_previews(worker, uuid4()))[0]
        entered, release = asyncio.Event(), asyncio.Event()
        objects = {}

        async def put(key, media):
            objects[key] = media.data
            if f"/attempt-{claim.fence}/" in key:
                entered.set()
                await release.wait()

        async def delete(key):
            objects.pop(key, None)

        store = AsyncMock()
        store.put.side_effect = put
        store.delete.side_effect = delete
        service = MediaPreviewService(settings, worker, store)
        first = asyncio.create_task(service.render(claim.id, claim.fence))
        try:
            await asyncio.wait_for(entered.wait(), timeout=20)
            async with admin.begin() as conn:
                await conn.execute(
                    text("UPDATE media_previews SET dispatch_fence=dispatch_fence+1 WHERE id=:id"),
                    {"id": preview.id},
                )
            assert await service.render(claim.id, claim.fence + 1) == "completed"
        finally:
            release.set()
        assert await first == "skipped"
        async with admin.connect() as conn:
            winner_key = await conn.scalar(
                text("SELECT object_key FROM media_previews WHERE id=:id"), {"id": preview.id}
            )
        assert f"/attempt-{claim.fence + 1}/" in winner_key
        assert list(objects) == [winner_key]
    finally:
        await worker.close()
        await owner.close()


@pytest.mark.parametrize("terminal", ["failed_dispatch", "stale_worker"])
async def test_dispatch_retries_are_fenced_and_bounded(admin, seeded, settings, terminal):
    tenant, business, actor, _, proposal, _ = await _accepted_case(admin, seeded)
    owner_db = Database(settings)
    worker = Database(settings, correlator=True)
    try:
        preview = await MediaPreviewService(settings, owner_db).request(
            tenant, business, actor, PreviewRequest(operation_id=uuid4(), proposal_id=proposal)
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
        assert (await MediaPreviewService(settings, owner_db).list(tenant, business, actor))[0].state == "failed"
    finally:
        await owner_db.close()
        await worker.close()


@pytest.mark.parametrize("cause", ["expired", "source_deleted", "proposal_deleted"])
async def test_retention_hides_and_erases_private_output(admin, seeded, settings, cause):
    tenant, business, actor, _, proposal, document = await _accepted_case(admin, seeded)
    if cause == "source_deleted":
        asset = await _attach_source(admin, tenant, business, proposal, document, b"image")
    owner_db = Database(settings)
    worker = Database(settings, correlator=True)
    try:
        service = MediaPreviewService(settings, owner_db)
        preview = await service.request(
            tenant, business, actor, PreviewRequest(operation_id=uuid4(), proposal_id=proposal)
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


async def test_static_preview_owner_lifecycle_and_tenant_isolation(admin, api, database, seeded, settings, monkeypatch):
    business = await _business(admin, seeded)
    tenant, actor = seeded["t1"], seeded["a1"]
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    viewer = {"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"}
    fact = uuid4()
    saved = await api.put(
        base + "/editorial-context",
        headers=owner,
        json={
            "expected_version": 0,
            "operation_id": str(uuid4()),
            "facts": [
                {
                    "id": str(fact),
                    "kind": "product",
                    "statement": "Cachorro-quente artesanal",
                    "source_detail": "Informado pelo dono",
                }
            ],
            "preferences": {"goal": "sales", "avoided_topics": []},
        },
    )
    assert saved.status_code == 200, saved.text
    proposal_url = base + "/editorial-proposals"
    proposal = await api.post(proposal_url, headers=owner, json={"operation_id": str(uuid4())})
    assert proposal.status_code == 202, proposal.text
    previews_url = base + "/media-previews"
    request = {"operation_id": str(uuid4()), "proposal_id": proposal.json()["id"]}
    assert (await api.post(previews_url, headers=owner, json=request)).json()[
        "error_code"
    ] == "PREVIEW_SCRIPT_NOT_ACCEPTED"
    worker = Database(settings, correlator=True)
    try:
        proposal_claim = (await claim_proposals(worker, uuid4()))[0]
        assert await EditorialProposalService(settings, worker).run(proposal_claim.id) == "completed"
        ready = (await api.get(proposal_url, headers=owner)).json()[0]
        assert ready["document"]["format"] in {"photo", "story"}
        review = await api.post(
            proposal_url + f"/{ready['id']}/script-review",
            headers=owner,
            json={"operation_id": str(uuid4()), "decision": "accepted"},
        )
        assert review.status_code == 200, review.text
        assert (await api.post(previews_url, headers=viewer, json=request)).status_code == 403
        first = await api.post(previews_url, headers=owner, json=request)
        assert first.status_code == 202, first.text
        assert first.json()["state"] == "pending"
        owner_service = MediaPreviewService(settings, database)
        replay = await owner_service.request(
            tenant, business, actor, PreviewRequest(operation_id=request["operation_id"], proposal_id=ready["id"])
        )
        assert str(replay.id) == first.json()["id"]
        with pytest.raises(AuthError, match="PREVIEW_OPERATION_CONFLICT"):
            await owner_service.request(
                tenant, business, actor, PreviewRequest(operation_id=request["operation_id"], proposal_id=uuid4())
            )
        with pytest.raises(AuthError, match="PROPOSAL_NOT_FOUND"):
            await owner_service.request(
                tenant, business, actor, PreviewRequest(operation_id=uuid4(), proposal_id=uuid4())
            )
        with pytest.raises(AuthError, match="PREVIEW_NOT_READY"):
            await owner_service.file_key(tenant, business, actor, replay.id)
        assert len(await owner_service.list(tenant, business, actor)) == 1
        assert (await api.post(previews_url, headers=owner, json=request)).json() == first.json()
        duplicate = await api.post(
            previews_url, headers=owner, json={"operation_id": str(uuid4()), "proposal_id": ready["id"]}
        )
        assert duplicate.json()["id"] == first.json()["id"]
        direct_duplicate = await owner_service.request(
            tenant, business, actor, PreviewRequest(operation_id=uuid4(), proposal_id=ready["id"])
        )
        assert direct_duplicate.id == replay.id
        assert (await api.get(previews_url, headers=viewer)).status_code == 403
        assert (await api.get(previews_url, headers=owner)).json()[0]["state"] == "pending"
        async with database.transaction(seeded["t2"], seeded["a2"]) as session:
            assert await session.scalar(text("SELECT count(*) FROM media_previews")) == 0
        claim = (await claim_previews(worker, uuid4()))[0]
        store = AsyncMock()
        service = MediaPreviewService(settings, worker, store)
        assert await service.render(claim.id, claim.fence) == "completed"
        store.put.assert_awaited_once()
        uploaded = store.put.call_args.args[1]
        assert uploaded.mime_type == "image/jpeg"
        assert uploaded.data[:3] == b"\xff\xd8\xff"
        assert await service.render(claim.id, claim.fence) == "skipped"
        assert await service._fail(claim.id, claim.fence, "STALE", False) == "skipped"
        completed = (await api.get(previews_url, headers=owner)).json()[0]
        assert completed["state"] == "completed" and completed["width"] == 1080
        assert completed["template_version"] == TEMPLATE_VERSION
        assert (await owner_service.file_key(tenant, business, actor, claim.id)).endswith(".jpg")
        assert (await api.get(previews_url + f"/{claim.id}/download-link", headers=viewer)).status_code == 403
        monkeypatch.setattr(
            "app.api.v1.media_previews.MaterialStore.signed_url", AsyncMock(return_value="https://example.test/private")
        )
        link = await api.get(previews_url + f"/{claim.id}/download-link", headers=owner)
        assert link.status_code == 200 and link.json()["url"] == "https://example.test/private"
        assert (await api.get(previews_url + f"/{uuid4()}/download-link", headers=owner)).status_code == 404
        assert await reconcile_stale_previews(worker) == 0
        async with admin.begin() as conn:
            await conn.execute(
                text("""UPDATE business_profiles SET brand_color='#e65024'
                  WHERE tenant_id=:tenant AND business_id=:business"""),
                {"tenant": tenant, "business": business},
            )
        with pytest.raises(AuthError, match="PREVIEW_NOT_READY"):
            await owner_service.file_key(tenant, business, actor, claim.id)
        assert (await api.get(previews_url + f"/{claim.id}/download-link", headers=owner)).status_code == 404
    finally:
        await worker.close()


async def test_short_video_preview_is_private_fenced_and_expires_with_offer(admin, api, seeded, settings, monkeypatch):
    tenant, business, actor, fact, proposal, document = await _accepted_case(admin, seeded)
    photo = io.BytesIO()
    Image.new("RGB", (100, 100), "#ffbb33").save(photo, format="PNG")
    asset = await _attach_source(admin, tenant, business, proposal, document, photo.getvalue())
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
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    url = f"/api/v1/organizations/{tenant}/businesses/{business}/media-previews"
    requested = await api.post(url, headers=owner, json={"operation_id": str(uuid4()), "proposal_id": str(proposal)})
    assert requested.status_code == 202, requested.text
    pending = requested.json()
    assert pending["mime_type"] == "video/mp4" and pending["source_asset_id"] == str(asset)
    assert datetime.fromisoformat(pending["expires_at"]) <= datetime.now(UTC) + timedelta(days=1)

    worker = Database(settings, correlator=True)
    try:
        claim = (await claim_previews(worker, uuid4()))[0]
        store = AsyncMock()
        store.get_image.return_value = photo.getvalue()
        video = FetchedMedia(b"mp4-preview", "video/mp4", hashlib.sha256(b"mp4-preview").hexdigest())
        renderer = AsyncMock(return_value=video)
        monkeypatch.setattr("app.services.media_previews.render_video_preview", renderer)
        service = MediaPreviewService(settings, worker, store)
        assert await service.render(claim.id, claim.fence) == "completed"
        renderer.assert_awaited_once()
        assert renderer.call_args.kwargs["source_image"] == photo.getvalue()
        assert renderer.call_args.kwargs["intro_text"] == "Material do negócio"
        assert renderer.call_args.kwargs["cta_text"] == "Fale com o negócio"
        assert store.put.call_args.args[0].endswith(".mp4")
        assert store.put.call_args.args[1] == video
        assert (await api.get(url, headers=owner)).json()[0]["duration_ms"] == 8000
        signed = AsyncMock(return_value="https://example.test/video")
        monkeypatch.setattr("app.api.v1.media_previews.MaterialStore.signed_url", signed)
        link = await api.get(url + f"/{claim.id}/download-link", headers=owner)
        assert link.status_code == 200 and link.json()["url"].endswith("video")
        assert signed.call_args.args[1] == "video/mp4"
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE media_previews SET expires_at=now()-interval '1 second' WHERE id=:id"),
                {"id": claim.id},
            )
        assert (await api.get(url, headers=owner)).json() == []
        assert (await api.get(url + f"/{claim.id}/download-link", headers=owner)).status_code == 404
        assert await purge_expired_previews(worker, store, uuid4()) == 1
        assert store.delete.call_args.args[0].endswith(".mp4")
    finally:
        await worker.close()


async def test_short_video_uses_source_clip_without_its_audio(admin, api, seeded, settings, monkeypatch):
    tenant, business, actor, _, proposal, document = await _accepted_case(admin, seeded)
    document["format"] = "short_video"
    source_bytes = b"source-video-contents"
    await _attach_source(admin, tenant, business, proposal, document, source_bytes, kind="video")
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE editorial_proposals SET document=CAST(:doc AS jsonb) WHERE id=:id"),
            {"id": proposal, "doc": json.dumps(document)},
        )
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    url = f"/api/v1/organizations/{tenant}/businesses/{business}/media-previews"
    requested = await api.post(url, headers=owner, json={"operation_id": str(uuid4()), "proposal_id": str(proposal)})
    assert requested.status_code == 202, requested.text
    worker = Database(settings, correlator=True)
    try:
        claim = (await claim_previews(worker, uuid4()))[0]
        store = AsyncMock()
        store.get_video.return_value = source_bytes
        rendered = FetchedMedia(b"mp4-preview", "video/mp4", hashlib.sha256(b"mp4-preview").hexdigest())
        renderer = AsyncMock(return_value=rendered)
        monkeypatch.setattr("app.services.media_previews.render_video_preview", renderer)
        assert await MediaPreviewService(settings, worker, store).render(claim.id, claim.fence) == "completed"
        store.get_video.assert_awaited_once()
        store.get_image.assert_not_awaited()
        assert renderer.call_args.kwargs["source_video"] == source_bytes
        assert renderer.call_args.kwargs["source_image"] is None
        assert renderer.call_args.kwargs["intro_text"] == "Material do negócio"
        assert renderer.call_args.kwargs["cta_text"] == "Fale com o negócio"
        assert renderer.call_args.kwargs["emphasis"] == "balanced"
        adjusted = await api.post(
            url,
            headers=owner,
            json={
                "operation_id": str(uuid4()),
                "proposal_id": str(proposal),
                "parent_preview_id": requested.json()["id"],
                "emphasis": "photo",
            },
        )
        assert adjusted.status_code == 202, adjusted.text
        assert adjusted.json()["revision"] == 2 and adjusted.json()["mime_type"] == "video/mp4"
        claim = (await claim_previews(worker, uuid4()))[0]
        assert await MediaPreviewService(settings, worker, store).render(claim.id, claim.fence) == "completed"
        assert renderer.call_args.kwargs["emphasis"] == "photo"
    finally:
        await worker.close()


async def test_static_adjustments_are_private_versioned_and_idempotent(admin, api, seeded, settings, monkeypatch):
    tenant, business, actor, _, proposal, _ = await _accepted_case(admin, seeded)
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    url = f"/api/v1/organizations/{tenant}/businesses/{business}/media-previews"
    base = (
        await api.post(url, headers=owner, json={"operation_id": str(uuid4()), "proposal_id": str(proposal)})
    ).json()
    assert base["revision"] == 1 and base["emphasis"] == "balanced" and base["parent_preview_id"] is None
    with_parent = {"proposal_id": str(proposal), "parent_preview_id": base["id"], "emphasis": "photo"}
    assert (await api.post(url, headers=owner, json={**with_parent, "operation_id": str(uuid4())})).json()[
        "error_code"
    ] == "PREVIEW_ADJUSTMENT_UNAVAILABLE"
    assert (
        await api.post(
            url, headers=owner, json={"operation_id": str(uuid4()), "proposal_id": str(proposal), "emphasis": "text"}
        )
    ).status_code == 422
    worker = Database(settings, correlator=True)
    try:
        store = AsyncMock()
        service = MediaPreviewService(settings, worker, store)
        first_claim = (await claim_previews(worker, uuid4()))[0]
        assert await service.render(first_claim.id, first_claim.fence) == "completed"
        operation = str(uuid4())
        adjusted = await api.post(url, headers=owner, json={**with_parent, "operation_id": operation})
        assert adjusted.status_code == 202, adjusted.text
        result = adjusted.json()
        assert result["revision"] == 2 and result["parent_preview_id"] == base["id"]
        assert result["emphasis"] == "photo" and result["id"] != base["id"]
        assert (await api.post(url, headers=owner, json={**with_parent, "operation_id": operation})).json() == result
        conflict = await api.post(
            url, headers=owner, json={**with_parent, "operation_id": operation, "emphasis": "text"}
        )
        assert conflict.status_code == 409 and conflict.json()["error_code"] == "PREVIEW_OPERATION_CONFLICT"
        stale = await api.post(
            url, headers=owner, json={**with_parent, "operation_id": str(uuid4()), "emphasis": "text"}
        )
        assert stale.status_code == 409 and stale.json()["error_code"] == "PREVIEW_ADJUSTMENT_CONFLICT"
        second_claim = (await claim_previews(worker, uuid4()))[0]
        assert await service.render(second_claim.id, second_claim.fence) == "completed"
        assert store.put.call_args.args[0].endswith(".jpg")
        assert (await api.get(url, headers=owner)).json()[0]["id"] == result["id"]
        assert await service.file_key(tenant, business, actor, first_claim.id)
        assert await service.file_key(tenant, business, actor, second_claim.id)
        third = await api.post(
            url,
            headers=owner,
            json={
                "operation_id": str(uuid4()),
                "proposal_id": str(proposal),
                "parent_preview_id": result["id"],
                "emphasis": "text",
            },
        )
        assert third.status_code == 202 and third.json()["revision"] == 3
        assert third.json()["parent_preview_id"] == result["id"]
    finally:
        await worker.close()


async def test_static_adjustment_rejects_same_emphasis_and_video(admin, api, seeded, settings):
    tenant, business, actor, _, proposal, document = await _accepted_case(admin, seeded)
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    url = f"/api/v1/organizations/{tenant}/businesses/{business}/media-previews"
    base = (
        await api.post(url, headers=owner, json={"operation_id": str(uuid4()), "proposal_id": str(proposal)})
    ).json()
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE media_previews SET state='completed',object_key='private/test.jpg' WHERE id=:id"),
            {"id": base["id"]},
        )
    same = await api.post(
        url,
        headers=owner,
        json={
            "operation_id": str(uuid4()),
            "proposal_id": str(proposal),
            "parent_preview_id": base["id"],
            "emphasis": "balanced",
        },
    )
    assert same.status_code == 409 and same.json()["error_code"] == "PREVIEW_ADJUSTMENT_CONFLICT"
    document["format"] = "short_video"
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE editorial_proposals SET document=CAST(:doc AS jsonb) WHERE id=:id"),
            {"id": proposal, "doc": json.dumps(document)},
        )
    unavailable = await api.post(
        url,
        headers=owner,
        json={
            "operation_id": str(uuid4()),
            "proposal_id": str(proposal),
            "parent_preview_id": base["id"],
            "emphasis": "photo",
        },
    )
    assert unavailable.status_code == 409 and unavailable.json()["error_code"] == "PREVIEW_ADJUSTMENT_UNAVAILABLE"
    document["format"] = "photo"
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE editorial_proposals SET document=CAST(:doc AS jsonb) WHERE id=:id"),
            {"id": proposal, "doc": json.dumps(document)},
        )
        await conn.execute(
            text("UPDATE media_previews SET state='failed',object_key=NULL WHERE id=:id"), {"id": base["id"]}
        )
    wrong_retry = await api.post(
        url,
        headers=owner,
        json={
            "operation_id": str(uuid4()),
            "proposal_id": str(proposal),
            "parent_preview_id": base["id"],
            "emphasis": "photo",
        },
    )
    assert wrong_retry.status_code == 409 and wrong_retry.json()["error_code"] == "PREVIEW_ADJUSTMENT_CONFLICT"
    parent = base
    for emphasis in ("balanced", "photo", "text"):
        retried = await api.post(
            url,
            headers=owner,
            json={
                "operation_id": str(uuid4()),
                "proposal_id": str(proposal),
                "parent_preview_id": parent["id"],
                "emphasis": emphasis,
            },
        )
        assert retried.status_code == 202, retried.text
        parent = retried.json()
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE media_previews SET state='completed',object_key='private/test.jpg' WHERE id=:id"),
                {"id": parent["id"]},
            )
    assert parent["revision"] == 4
    limit = await api.post(
        url,
        headers=owner,
        json={
            "operation_id": str(uuid4()),
            "proposal_id": str(proposal),
            "parent_preview_id": parent["id"],
            "emphasis": "photo",
        },
    )
    assert limit.status_code == 409 and limit.json()["error_code"] == "PREVIEW_ADJUSTMENT_LIMIT"


@pytest.mark.parametrize("changed_version", ["script", "context"])
async def test_static_adjustment_rejects_a_parent_from_an_old_version(admin, api, seeded, settings, changed_version):
    tenant, business, actor, _, proposal, _ = await _accepted_case(admin, seeded)
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    url = f"/api/v1/organizations/{tenant}/businesses/{business}/media-previews"
    base = (
        await api.post(url, headers=owner, json={"operation_id": str(uuid4()), "proposal_id": str(proposal)})
    ).json()
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE media_previews SET state='completed',object_key='private/test.jpg' WHERE id=:id"),
            {"id": base["id"]},
        )
        if changed_version == "script":
            await conn.execute(
                text("UPDATE editorial_proposals SET script_version=script_version+1 WHERE id=:id"), {"id": proposal}
            )
        else:
            await conn.execute(
                text("UPDATE editorial_proposals SET context_version=context_version+1 WHERE id=:id"),
                {"id": proposal},
            )
    result = await api.post(
        url,
        headers=owner,
        json={
            "operation_id": str(uuid4()),
            "proposal_id": str(proposal),
            "parent_preview_id": base["id"],
            "emphasis": "photo",
        },
    )
    assert result.status_code == 409
    assert result.json()["error_code"] == "PREVIEW_INPUT_CHANGED"
