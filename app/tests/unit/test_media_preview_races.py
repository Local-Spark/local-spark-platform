"""Defensive request and render branches under concurrent database changes."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.schemas.media_previews import PreviewRequest
from app.services import media_retention
from app.services.auth import AuthError
from app.services.media_previews import MediaPreviewService, RenderInputs
from app.services.media_retention import PreviewPurgeClaim
from app.services.whatsapp_materials import WhatsAppMaterialsService


def _result(row):
    result = Mock()
    result.mappings.return_value.one_or_none.return_value = row
    result.mappings.return_value.one.return_value = row
    return result


def _database(rows):
    session = Mock()
    session.execute = AsyncMock(side_effect=[_result(row) for row in rows])
    session.scalar = AsyncMock()

    @asynccontextmanager
    async def opened(*_):
        yield session

    session.begin = opened
    return Mock(transaction=opened, sessions=opened), session


async def test_concurrent_operation_conflict_is_detected_after_insert_race(settings, monkeypatch):
    tenant, business, actor, proposal, operation = [uuid4() for _ in range(5)]
    row = {"operation_id": operation, "request_hash": "another-hash"}
    database, _ = _database(
        [
            None,
            {"context_version": 1, "script_version": 1, "expires_at": datetime.now(UTC) + timedelta(days=1)},
            None,
            row,
        ]
    )
    service = MediaPreviewService(settings, database)
    monkeypatch.setattr(WhatsAppMaterialsService, "_require_owner", AsyncMock())
    monkeypatch.setattr(
        service,
        "_inputs",
        AsyncMock(return_value=RenderInputs("Test", "#6557ed", "photo", "Fato.", None, None, None, uuid4(), "a" * 64)),
    )
    with pytest.raises(AuthError, match="PREVIEW_OPERATION_CONFLICT"):
        await service.request(tenant, business, actor, PreviewRequest(operation_id=operation, proposal_id=proposal))


@pytest.mark.parametrize(
    ("parent_change", "latest_is_parent", "emphasis", "code"),
    [
        ({"missing": True}, True, "photo", "PREVIEW_ADJUSTMENT_UNAVAILABLE"),
        ({"state": "pending"}, True, "photo", "PREVIEW_ADJUSTMENT_UNAVAILABLE"),
        ({"mime_type": "video/mp4"}, True, "photo", "PREVIEW_ADJUSTMENT_UNAVAILABLE"),
        ({}, False, "photo", "PREVIEW_ADJUSTMENT_CONFLICT"),
        ({}, True, "balanced", "PREVIEW_ADJUSTMENT_CONFLICT"),
        ({"state": "failed"}, True, "photo", "PREVIEW_ADJUSTMENT_CONFLICT"),
        ({"revision": 4}, True, "photo", "PREVIEW_ADJUSTMENT_LIMIT"),
        ({"script_version": 2}, True, "photo", "PREVIEW_INPUT_CHANGED"),
        ({"context_version": 2}, True, "photo", "PREVIEW_INPUT_CHANGED"),
    ],
)
async def test_adjustment_parent_guard_under_concurrent_changes(
    settings, monkeypatch, parent_change, latest_is_parent, emphasis, code
):
    tenant, business, actor, proposal, operation, parent_id = [uuid4() for _ in range(6)]
    parent = {
        "id": parent_id,
        "state": "completed",
        "mime_type": "image/jpeg",
        "emphasis": "balanced",
        "revision": 1,
        "script_version": 1,
        "context_version": 1,
    } | parent_change
    database, session = _database(
        [None, {"script_version": 1, "context_version": 1}, None if parent_change.get("missing") else parent]
    )
    session.scalar.return_value = parent_id if latest_is_parent else uuid4()
    service = MediaPreviewService(settings, database)
    monkeypatch.setattr(WhatsAppMaterialsService, "_require_owner", AsyncMock())
    with pytest.raises(AuthError, match=code):
        await service.request(
            tenant,
            business,
            actor,
            PreviewRequest(
                operation_id=operation, proposal_id=proposal, parent_preview_id=parent_id, emphasis=emphasis
            ),
        )


@pytest.mark.parametrize("format", ["photo", "short_video"])
async def test_adjustment_serializes_parent_and_starts_only_a_static_revision(settings, monkeypatch, format):
    tenant, business, actor, proposal, operation, parent_id = [uuid4() for _ in range(6)]
    parent = {
        "id": parent_id,
        "state": "completed",
        "mime_type": "image/jpeg",
        "emphasis": "balanced",
        "revision": 1,
        "script_version": 1,
        "context_version": 1,
    }
    inserted = {"id": uuid4(), "revision": 2}
    database, session = _database(
        [
            None,
            {"script_version": 1, "context_version": 1, "expires_at": datetime.now(UTC) + timedelta(days=1)},
            parent,
            inserted,
        ]
    )
    session.scalar.return_value = parent_id
    service = MediaPreviewService(settings, database)
    monkeypatch.setattr(WhatsAppMaterialsService, "_require_owner", AsyncMock())
    monkeypatch.setattr(
        service,
        "_inputs",
        AsyncMock(return_value=RenderInputs("Test", "#6557ed", format, "Fato.", None, None, None, uuid4(), "a" * 64)),
    )
    monkeypatch.setattr("app.services.media_previews._audit", AsyncMock())
    monkeypatch.setattr("app.services.media_previews.PreviewRead.model_validate", lambda row: row)
    payload = PreviewRequest(
        operation_id=operation, proposal_id=proposal, parent_preview_id=parent_id, emphasis="photo"
    )
    if format == "short_video":
        with pytest.raises(AuthError, match="PREVIEW_ADJUSTMENT_UNAVAILABLE"):
            await service.request(tenant, business, actor, payload)
        return
    assert await service.request(tenant, business, actor, payload) == inserted
    params = session.execute.await_args_list[-1].args[1]
    assert params["parent"] == parent_id and params["revision"] == 2 and params["emphasis"] == "photo"


async def test_proposal_removed_after_claim_fails_without_render(settings, monkeypatch):
    preview, proposal = uuid4(), uuid4()
    database, _ = _database([{"proposal_id": proposal}, None])
    service = MediaPreviewService(settings, database)
    failed = AsyncMock(return_value="skipped")
    monkeypatch.setattr(service, "_fail", failed)
    assert await service.render(preview, 3) == "skipped"
    failed.assert_awaited_once_with(preview, 3, "PROPOSAL_NOT_FOUND", False)


async def test_purge_does_not_count_superseded_claim(monkeypatch):
    claim = PreviewPurgeClaim(uuid4(), uuid4(), 2, "previews/key.jpg")
    monkeypatch.setattr(media_retention, "claim_expired_previews", AsyncMock(return_value=[claim]))
    monkeypatch.setattr(media_retention, "finish_preview_purge", AsyncMock(return_value=False))
    store = AsyncMock()
    assert await media_retention.purge_expired_previews(Mock(), store, claim.owner) == 0
    store.delete.assert_awaited_once_with(claim.object_key)
