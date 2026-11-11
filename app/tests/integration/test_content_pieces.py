"""Exact private-version decisions, tenant isolation and no publication side effects."""

import asyncio
import hashlib
import json
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr, ValidationError
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.adapters.material_media import MaterialError
from app.api.v1 import content_pieces as routes
from app.schemas.content_pieces import PieceDecision, PieceFromPreview
from app.services.auth import AuthError
from app.services.content_pieces import ContentPieceService, PieceArtifact, write_version
from app.services.media_previews import MediaPreviewService
from app.tests.integration import test_content_delivery as candidates
from app.tests.integration.test_business_collection import Store, _business
from app.tests.unit.test_content_pieces_contract import confirmation
from app.tests.unit.test_core import access_token

pytestmark = pytest.mark.integration


class PreviewStore(Store):
    async def signed_url(self, key, mime):
        assert key in self.objects and mime == "image/jpeg"
        return "https://private.test/normalized-preview?expires=120"


def _artifact(*, mime="video/mp4", data=b"already-verified-private-object"):
    identifier = uuid4()
    return PieceArtifact(identifier, f"private/pieces/{identifier}", hashlib.sha256(data).hexdigest(), mime, len(data))


def _decision(piece, **change):
    version = next(v for v in piece.versions if v.id == piece.current_version_id)
    return PieceDecision.model_validate(
        {
            "operation_id": uuid4(),
            "version_id": version.id,
            "decision": "approve",
            "artifacts": [a.model_dump() for a in version.artifacts],
            "confirmations": [confirmation(a.sha256) for a in version.artifacts],
            **change,
        }
    )


@pytest.fixture
async def case(admin, seeded, settings, database):
    business = await _business(admin, seeded)
    key = Fernet.generate_key()
    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr(key.decode())})
    store = AsyncMock()
    store.signed_url.return_value = "https://private.test/temporary?expires=120"
    service = ContentPieceService(cfg, database, store)
    return SimpleNamespace(
        tenant=seeded["t1"],
        actor=seeded["a1"],
        business=business,
        key=key,
        cfg=cfg,
        store=store,
        service=service,
        database=database,
    )


async def _create(
    case,
    *,
    format="reel",
    artifacts=None,
    operation=None,
    piece=None,
    parent=None,
    select=True,
    preview=None,
    simulated=False,
):
    identifier = piece or uuid4()
    async with case.database.transaction(case.tenant, case.actor) as session:
        version = await write_version(
            session,
            case.tenant,
            case.business,
            case.actor,
            identifier,
            operation or uuid4(),
            format,
            artifacts or (_artifact(),),
            parent_id=parent,
            source_preview_id=preview,
            select_current=select,
            simulated=simulated,
        )
    return identifier, version


async def test_http_review_private_download_and_no_publication(case, api, settings, monkeypatch, admin, seeded):
    piece, version = await _create(case)
    monkeypatch.setattr(routes, "service", lambda _request: case.service)
    path = f"/api/v1/organizations/{case.tenant}/businesses/{case.business}/content-pieces"
    owner = {"Authorization": f"Bearer {access_token(settings, case.actor)}"}
    assert (await api.get(path)).status_code == 401
    denied = await api.get(path, headers={"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"})
    assert denied.status_code == 403 and denied.headers["Cache-Control"] == "no-store"
    listed = await api.get(path, headers=owner)
    assert listed.status_code == 200, listed.text
    assert listed.headers["Cache-Control"] == "no-store"
    assert [p["id"] for p in listed.json()] == [str(piece)]
    got = await api.get(f"{path}/{piece}", headers=owner)
    assert got.status_code == 200 and got.headers["Cache-Control"] == "no-store"
    assert "object_key" not in got.text and "private/pieces" not in got.text
    assert got.json()["simulated"] is False
    current = await case.service.get(case.tenant, case.business, case.actor, piece)
    body = _decision(current)
    result = await api.post(f"{path}/{piece}/decisions", headers=owner, json=body.model_dump(mode="json"))
    assert result.status_code == 200, result.text
    assert result.headers["Cache-Control"] == "no-store"
    assert result.json()["version_id"] == str(version)
    replay = await api.post(f"{path}/{piece}/decisions", headers=owner, json=body.model_dump(mode="json"))
    assert replay.json() == result.json()
    current = await case.service.get(case.tenant, case.business, case.actor, piece)
    assert current.state == "approved" and current.approved_version_id == version
    artifact = current.versions[0].artifacts[0]
    url = await api.get(f"{path}/{piece}/versions/{version}/artifacts/{artifact.id}/download-link", headers=owner)
    assert url.status_code == 200 and url.json() == {"url": case.store.signed_url.return_value}
    assert url.headers["Cache-Control"] == "no-store"
    case.store.signed_url.assert_awaited_once()
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM content_deliveries")) == 0
        events = (await conn.execute(text("SELECT event_type,payload FROM outbox_events ORDER BY created_at"))).all()
        assert [r.event_type for r in events] == ["content.piece_ready", "content.piece_decided"]
        assert all(set(r.payload) == {"business_id", "actor_id", "operation_id"} for r in events)
        assert await conn.scalar(text("SELECT count(*) FROM content_piece_decisions")) == 1


async def test_changes_are_encrypted_and_do_not_disclose_content_in_events(case, admin):
    piece, _ = await _create(case, format="carousel_motion", artifacts=(_artifact(), _artifact()))
    current = await case.service.get(case.tenant, case.business, case.actor, piece)
    note = "Ajustar página 2: cliente privado e campanha reservada."
    body = _decision(current, decision="request_changes", confirmations=[], note=note, page_positions=[1])
    decision = await case.service.decide(case.tenant, case.business, case.actor, piece, body)
    assert decision.decision == "request_changes"
    assert (await case.service.get(case.tenant, case.business, case.actor, piece)).state == "changes_requested"
    async with admin.connect() as conn:
        row = (
            await conn.execute(text("SELECT note_ciphertext,page_positions,confirmation FROM content_piece_decisions"))
        ).one()
        assert row.note_ciphertext != note
        assert Fernet(case.key).decrypt(row.note_ciphertext.encode()).decode() == note
        assert row.page_positions == [1] and row.confirmation == []
        for table in ("outbox_events", "audit_events"):
            rows = (await conn.execute(text(f"SELECT row_to_json(t) FROM {table} t"))).scalars().all()
            assert note not in json.dumps(rows)
        assert await conn.scalar(text("SELECT count(*) FROM content_deliveries")) == 0


async def test_versions_preserve_original_allow_nonselected_variants_and_replay(case, admin):
    operation, original = uuid4(), _artifact()
    piece, v0 = await _create(case, operation=operation, artifacts=(original,))
    assert await _create(case, operation=operation, piece=piece, artifacts=(original,)) == (piece, v0)
    approval = _decision(await case.service.get(case.tenant, case.business, case.actor, piece))
    approved = await case.service.decide(
        case.tenant,
        case.business,
        case.actor,
        piece,
        approval,
    )
    _, alternate = await _create(case, piece=piece, parent=v0, select=False)
    current = await case.service.get(case.tenant, case.business, case.actor, piece)
    assert current.current_version_id == v0 and current.approved_version_id == v0 and current.state == "approved"
    _, selected = await _create(case, piece=piece, parent=v0)
    current = await case.service.get(case.tenant, case.business, case.actor, piece)
    assert [v.number for v in current.versions] == [1, 2, 3]
    assert [v.id for v in current.versions] == [v0, alternate, selected]
    assert (
        current.current_version_id == selected
        and current.approved_version_id == v0
        and current.state == "ready_for_review"
    )
    assert current.versions[0].artifacts[0].sha256 == original.sha256
    # A lost-response retry returns the durable old decision even after a new
    # version exists; it must not approve that new version or duplicate events.
    assert await case.service.decide(case.tenant, case.business, case.actor, piece, approval) == approved
    assert await case.service.get(case.tenant, case.business, case.actor, piece) == current
    with pytest.raises(AuthError, match="PIECE_OPERATION_CONFLICT"):
        await _create(case, operation=operation, piece=piece, artifacts=(_artifact(),))
    with pytest.raises(AuthError, match="PIECE_OPERATION_CONFLICT"):
        await _create(case, operation=operation, piece=piece, artifacts=(original,), simulated=True)
    with pytest.raises(AuthError, match="PIECE_SOURCE_CHANGED"):
        await _create(case, piece=piece, parent=v0, simulated=True)
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM content_piece_versions")) == 3
        assert await conn.scalar(text("SELECT count(*) FROM content_piece_decisions")) == 1
        assert (
            await conn.scalar(text("SELECT count(*) FROM outbox_events WHERE event_type='content.piece_decided'")) == 1
        )


@pytest.mark.parametrize(
    "change", [{"sha256": "b" * 64}, {"size_bytes": 999}, {"id": uuid4()}, {"mime_type": "image/png"}]
)
async def test_decision_rejects_changed_artifact_identity_and_metadata(case, change):
    piece, _ = await _create(case)
    current = await case.service.get(case.tenant, case.business, case.actor, piece)
    altered = current.versions[0].artifacts[0].model_copy(update=change)
    body = _decision(current, artifacts=[altered.model_dump()], confirmations=[confirmation(altered.sha256)])
    with pytest.raises(AuthError, match="PIECE_ARTIFACT_SET_CHANGED"):
        await case.service.decide(case.tenant, case.business, case.actor, piece, body)


async def test_decision_rejects_wrong_version_partial_or_reordered_carousel(case):
    piece, _ = await _create(
        case, format="carousel_motion", artifacts=(_artifact(data=b"first"), _artifact(data=b"second"))
    )
    current = await case.service.get(case.tenant, case.business, case.actor, piece)
    with pytest.raises(AuthError, match="PIECE_VERSION_CHANGED"):
        await case.service.decide(case.tenant, case.business, case.actor, piece, _decision(current, version_id=uuid4()))
    items = current.versions[0].artifacts
    for ordered in (
        [items[0]],
        [items[1].model_copy(update={"position": 0}), items[0].model_copy(update={"position": 1})],
    ):
        body = _decision(
            current,
            artifacts=[a.model_dump() for a in ordered],
            confirmations=[confirmation(a.sha256) for a in ordered],
        )
        with pytest.raises(AuthError, match="PIECE_ARTIFACT_SET_CHANGED"):
            await case.service.decide(case.tenant, case.business, case.actor, piece, body)


async def test_repeated_decision_with_different_payload_conflicts_and_missing_key_blocks(case):
    piece, _ = await _create(case)
    current = await case.service.get(case.tenant, case.business, case.actor, piece)
    body = _decision(current)
    await case.service.decide(case.tenant, case.business, case.actor, piece, body)
    with pytest.raises(AuthError, match="PIECE_OPERATION_CONFLICT"):
        await case.service.decide(
            case.tenant, case.business, case.actor, piece, body.model_copy(update={"note": "Different note"})
        )
    service = ContentPieceService(case.cfg.model_copy(update={"meta_encryption_key": None}), case.database)
    with pytest.raises(AuthError, match="PIECE_PRIVACY_KEY_REQUIRED"):
        await service.decide(case.tenant, case.business, case.actor, piece, body)


@pytest.mark.parametrize("format,mime", [("photo", "image/png"), ("story", "image/jpeg"), ("story_video", "video/mp4")])
async def test_supported_formats_keep_private_exact_metadata(case, format, mime):
    piece, _ = await _create(case, format=format, artifacts=(_artifact(mime=mime),))
    assert (await case.service.get(case.tenant, case.business, case.actor, piece)).format == format


@pytest.mark.parametrize(
    "kind", ["empty", "many", "not_carousel", "duplicate", "empty_key", "wrong_mime", "too_big", "bad_hash"]
)
async def test_internal_writer_rejects_invalid_complete_set_before_insert(case, admin, kind):
    item = _artifact()
    items = {
        "empty": (),
        "many": tuple(_artifact() for _ in range(21)),
        "not_carousel": (item, _artifact()),
        "duplicate": (item, item),
        "empty_key": (replace(item, object_key=""),),
        "wrong_mime": (replace(item, mime_type="image/png"),),
        "too_big": (replace(item, size_bytes=50 * 1024 * 1024 + 1),),
        "bad_hash": (replace(item, sha256="invalid"),),
    }[kind]
    async with case.database.transaction(case.tenant, case.actor) as session:
        with pytest.raises((AuthError, ValidationError)):
            await write_version(
                session,
                case.tenant,
                case.business,
                case.actor,
                uuid4(),
                uuid4(),
                "carousel_motion" if kind == "duplicate" else "reel",
                items,
            )
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM content_pieces")) == 0


async def test_parent_format_source_and_missing_resource_guards(case):
    for parent, selected in ((uuid4(), True), (None, False)):
        with pytest.raises(AuthError, match="PIECE_PARENT_INVALID"):
            await _create(case, parent=parent, select=selected)
    piece, parent = await _create(case)
    for kwargs in ({}, {"parent": uuid4()}):
        with pytest.raises(AuthError, match="PIECE_PARENT_INVALID"):
            await _create(case, piece=piece, **kwargs)
    for kwargs in ({"format": "story_video"}, {"preview": uuid4()}):
        with pytest.raises(AuthError, match="PIECE_SOURCE_CHANGED"):
            await _create(case, piece=piece, parent=parent, **kwargs)
    with pytest.raises(AuthError, match="PIECE_NOT_FOUND"):
        await case.service.get(case.tenant, case.business, case.actor, uuid4())
    with pytest.raises(AuthError, match="PIECE_ARTIFACT_NOT_FOUND"):
        await case.service.download(case.tenant, case.business, case.actor, piece, parent, uuid4())


async def test_owner_viewer_revocation_cross_tenant_and_direct_rls(case, seeded, admin):
    piece, _ = await _create(case)
    current = await case.service.get(case.tenant, case.business, case.actor, piece)
    await case.service.decide(case.tenant, case.business, case.actor, piece, _decision(current))
    for tenant, actor in ((case.tenant, seeded["viewer"]), (seeded["t2"], seeded["a2"]), (case.tenant, seeded["a2"])):
        with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
            await case.service.get(tenant, case.business, actor, piece)
        async with case.database.transaction(tenant, actor) as session:
            for table in (
                "content_pieces",
                "content_piece_versions",
                "content_piece_artifacts",
                "content_piece_decisions",
            ):
                assert await session.scalar(text(f"SELECT count(*) FROM {table}")) == 0
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE memberships SET active=false WHERE tenant_id=:t AND actor_id=:a"),
            {"t": case.tenant, "a": case.actor},
        )
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await case.service.list(case.tenant, case.business, case.actor)
    async with case.database.transaction(case.tenant, case.actor) as session:
        assert await session.scalar(text("SELECT count(*) FROM content_pieces")) == 0


async def test_database_denies_rewriting_immutable_versions_and_cross_piece_references(case, admin):
    piece, version = await _create(case)
    other, other_version = await _create(case)
    for table, column, value in (
        ("content_piece_versions", "number", "99"),
        ("content_piece_artifacts", "object_key", "'changed'"),
    ):
        with pytest.raises(DBAPIError):
            async with case.database.transaction(case.tenant, case.actor) as session:
                await session.execute(text(f"UPDATE {table} SET {column}={value}"))
    with pytest.raises(IntegrityError):
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE content_pieces SET current_version_id=:v WHERE id=:p"), {"v": other_version, "p": piece}
            )
    with pytest.raises(IntegrityError):
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE content_piece_versions SET parent_id=:v WHERE piece_id=:p"), {"v": version, "p": other}
            )


async def test_new_version_serializes_with_approval_of_old_version(case):
    piece, original = await _create(case)
    body = _decision(await case.service.get(case.tenant, case.business, case.actor, piece))
    async with case.database.transaction(case.tenant, case.actor) as session:
        newer = await write_version(
            session, case.tenant, case.business, case.actor, piece, uuid4(), "reel", (_artifact(),), parent_id=original
        )
        decision_task = asyncio.create_task(case.service.decide(case.tenant, case.business, case.actor, piece, body))
        await asyncio.sleep(0)
        assert not decision_task.done()
    with pytest.raises(AuthError, match="PIECE_VERSION_CHANGED"):
        await asyncio.wait_for(decision_task, 60)
    current = await case.service.get(case.tenant, case.business, case.actor, piece)
    assert current.current_version_id == newer and current.approved_version_id is None


async def test_same_operation_concurrent_initial_versions_different_pieces_conflicts(case, admin):
    op, a, b = uuid4(), uuid4(), uuid4()
    result = await asyncio.gather(
        _create(case, operation=op, piece=a), _create(case, operation=op, piece=b), return_exceptions=True
    )
    assert sum(isinstance(item, tuple) for item in result) == 1
    error = next(item for item in result if isinstance(item, Exception))
    assert isinstance(error, AuthError) and error.code == "PIECE_OPERATION_CONFLICT"
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM content_piece_versions")) == 1


async def test_image_import_from_real_preview_replay_download_and_hash_verification(
    admin, seeded, settings, database, api, monkeypatch
):
    store = PreviewStore()
    monkeypatch.setattr(candidates, "Store", lambda: store)
    cfg, app_db, worker_db, tenant, business, actor, _, _, preview, sha = await candidates._visual_candidate_case(
        admin, seeded, settings, database
    )
    try:
        service = ContentPieceService(cfg, app_db, store)
        monkeypatch.setattr(routes, "service", lambda _request: service)
        path = f"/api/v1/organizations/{tenant}/businesses/{business}/content-pieces"
        headers = {"Authorization": f"Bearer {access_token(settings, actor)}"}
        body = PieceFromPreview(operation_id=uuid4(), preview_id=preview)
        response = await api.post(f"{path}/from-preview", headers=headers, json=body.model_dump(mode="json"))
        assert response.status_code == 201, response.text
        assert response.headers["Cache-Control"] == "no-store"
        current = await service.from_preview(tenant, business, actor, body)
        assert str(current.id) == response.json()["id"]
        assert current.format == "photo" and len(current.versions) == 1
        assert current.simulated is True and response.json()["simulated"] is True
        file = current.versions[0].artifacts[0]
        async with admin.connect() as conn:
            object_key = await conn.scalar(text("SELECT object_key FROM media_previews WHERE id=:id"), {"id": preview})
        original = store.objects[object_key]
        # The real visual pipeline normalizes this fixture to JPEG; metadata
        # must describe the retained file instead of inferring PNG from its key.
        assert original.startswith(b"\xff\xd8\xff")
        assert file.sha256 == sha and file.mime_type == "image/jpeg"
        signed = await service.download(tenant, business, actor, current.id, current.current_version_id, file.id)
        assert signed.startswith("https://private.test/") and "expires=120" in signed
        decision = _decision(current)
        await service.decide(tenant, business, actor, current.id, decision)
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT count(*) FROM content_deliveries")) == 0
            assert (
                await conn.scalar(text("SELECT count(*) FROM outbox_events WHERE event_type LIKE '%publication%'")) == 0
            )
        store.objects[object_key] = b"corrupt"
        with pytest.raises(MaterialError, match="MEDIA_INVALID"):
            await service.from_preview(
                tenant, business, actor, PieceFromPreview(operation_id=uuid4(), preview_id=preview)
            )
        store.objects[object_key] = original
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE media_previews SET sha256=:sha WHERE id=:id"), {"sha": "f" * 64, "id": preview}
            )
        with pytest.raises(AuthError, match="PIECE_PREVIEW_UNAVAILABLE"):
            await service.from_preview(
                tenant, business, actor, PieceFromPreview(operation_id=uuid4(), preview_id=preview)
            )
        monkeypatch.setattr(MediaPreviewService, "file_key", AsyncMock(return_value="different-key"))
        with pytest.raises(AuthError, match="PIECE_ARTIFACT_NOT_FOUND"):
            await service.download(tenant, business, actor, current.id, current.current_version_id, file.id)
    finally:
        await worker_db.close()
        await app_db.close()


async def test_list_empty_and_failed_decision_does_not_emit_events(case, admin):
    assert await case.service.list(case.tenant, case.business, case.actor) == []
    piece, _ = await _create(case)
    current = await case.service.get(case.tenant, case.business, case.actor, piece)
    with pytest.raises(AuthError, match="PIECE_NOT_FOUND"):
        await case.service.decide(case.tenant, case.business, case.actor, uuid4(), _decision(current))
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM content_piece_decisions")) == 0
        assert (
            await conn.scalar(text("SELECT count(*) FROM outbox_events WHERE event_type='content.piece_decided'")) == 0
        )


async def test_replay_still_requires_active_owner_and_cross_business_stays_private(case, admin, seeded):
    piece, _ = await _create(case)
    body = _decision(await case.service.get(case.tenant, case.business, case.actor, piece))
    await case.service.decide(case.tenant, case.business, case.actor, piece, body)
    other_business = await _business(admin, {**seeded, "t1": seeded["t2"]})
    with pytest.raises(AuthError, match="PIECE_NOT_FOUND"):
        await case.service.get(seeded["t2"], other_business, seeded["a2"], piece)
    async with admin.begin() as conn:
        await conn.execute(text("UPDATE user_accounts SET active=false WHERE id=:actor"), {"actor": case.actor})
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await case.service.decide(case.tenant, case.business, case.actor, piece, body)


async def test_immutable_decision_and_cross_tenant_artifact_fk(case, admin, seeded):
    piece, version = await _create(case)
    current = await case.service.get(case.tenant, case.business, case.actor, piece)
    await case.service.decide(case.tenant, case.business, case.actor, piece, _decision(current))
    with pytest.raises(DBAPIError):
        async with case.database.transaction(case.tenant, case.actor) as session:
            await session.execute(text("UPDATE content_piece_decisions SET note_ciphertext='changed'"))
    with pytest.raises(DBAPIError):
        async with case.database.transaction(case.tenant, case.actor) as session:
            await session.execute(text("DELETE FROM content_piece_versions"))
    with pytest.raises(IntegrityError):
        async with admin.begin() as conn:
            await conn.execute(
                text("""INSERT INTO content_piece_artifacts
              (tenant_id,business_id,piece_id,version_id,id,position,object_key,sha256,mime_type,size_bytes)
              VALUES(:tenant,:business,:piece,:version,:id,0,'private','aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','video/mp4',20)"""),
                {"tenant": seeded["t2"], "business": case.business, "piece": piece, "version": version, "id": uuid4()},
            )


async def test_database_requires_the_exact_nonnull_version_when_approved(case):
    piece, current = await _create(case)
    _, other = await _create(case, piece=piece, parent=current, select=False)
    for approved in (None, other):
        with pytest.raises(IntegrityError, match="piece_approval_requires_version"):
            async with case.database.transaction(case.tenant, case.actor) as session:
                await session.execute(
                    text("UPDATE content_pieces SET state='approved',approved_version_id=:version WHERE id=:piece"),
                    {"version": approved, "piece": piece},
                )
    actual = await case.service.get(case.tenant, case.business, case.actor, piece)
    assert actual.state == "ready_for_review" and actual.approved_version_id is None
