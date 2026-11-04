"""Defensive request and render branches under concurrent database changes."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.schemas.media_previews import PreviewRequest
from app.services import media_retention
from app.services.auth import AuthError
from app.services.media_previews import MediaPreviewService
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


async def test_historical_operation_conflict_is_detected_before_new_work(settings, monkeypatch):
    tenant, business, actor, proposal, operation = [uuid4() for _ in range(5)]
    database, session = _database([{"operation_id": operation, "request_hash": "another-hash"}])
    service = MediaPreviewService(settings, database)
    monkeypatch.setattr(WhatsAppMaterialsService, "_require_owner", AsyncMock())
    inputs = AsyncMock()
    monkeypatch.setattr(service, "_inputs", inputs)
    with pytest.raises(AuthError, match="PREVIEW_OPERATION_CONFLICT"):
        await service.request(
            tenant,
            business,
            actor,
            PreviewRequest(operation_id=operation, proposal_id=proposal, generation_mode="local"),
        )
    inputs.assert_not_awaited()
    assert session.execute.await_count == 1


@pytest.mark.parametrize(
    ("parent_change", "latest_is_parent", "emphasis", "code"),
    [
        ({"missing": True}, True, "photo", "PREVIEW_ADJUSTMENT_UNAVAILABLE"),
        ({"state": "pending"}, True, "photo", "PREVIEW_ADJUSTMENT_UNAVAILABLE"),
        ({"mime_type": "application/pdf"}, True, "photo", "PREVIEW_ADJUSTMENT_UNAVAILABLE"),
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
        "mime_type": "video/mp4",
        "emphasis": "balanced",
        "revision": 1,
        "script_version": 1,
        "context_version": 1,
    } | parent_change
    database, session = _database(
        [
            None,
            {"script_version": 1, "context_version": 1, "document": {"format": "short_video"}},
            None if parent_change.get("missing") else parent,
        ]
    )
    session.scalar.return_value = parent_id if latest_is_parent else uuid4()
    service = MediaPreviewService(settings, database)
    monkeypatch.setattr(WhatsAppMaterialsService, "_require_owner", AsyncMock())
    monkeypatch.setattr(
        service,
        "_inputs",
        AsyncMock(side_effect=AssertionError("Parent guard must reject before preparing inputs")),
    )
    with pytest.raises(AuthError, match=code):
        await service.request(
            tenant,
            business,
            actor,
            PreviewRequest(
                operation_id=operation,
                proposal_id=proposal,
                parent_preview_id=parent_id,
                emphasis=emphasis,
                generation_mode="local",
            ),
        )


@pytest.mark.parametrize("validator_rejects", [True, False])
@pytest.mark.parametrize("has_parent", [True, False])
async def test_legacy_local_request_cannot_create_job_even_if_validator_relaxes(
    settings, monkeypatch, validator_rejects, has_parent
):
    tenant, business, actor, proposal, operation, parent_id = [uuid4() for _ in range(6)]
    parent_id = parent_id if has_parent else None
    parent = {
        "id": parent_id,
        "state": "completed",
        "mime_type": "video/mp4",
        "emphasis": "balanced",
        "revision": 1,
        "script_version": 1,
        "context_version": 1,
    }
    source = {"script_version": 1, "context_version": 1, "document": {"format": "short_video"}}
    database, session = _database([None, source, parent] if has_parent else [None, source])
    session.scalar.return_value = parent_id
    service = MediaPreviewService(settings, database)
    monkeypatch.setattr(WhatsAppMaterialsService, "_require_owner", AsyncMock())
    inputs = AsyncMock(side_effect=AuthError("PREVIEW_LEGACY_CREATION_DISABLED", 409) if validator_rejects else None)
    monkeypatch.setattr(service, "_inputs", inputs)
    payload = PreviewRequest(
        operation_id=operation,
        proposal_id=proposal,
        parent_preview_id=parent_id,
        emphasis="photo" if has_parent else "balanced",
        generation_mode="local",
    )
    with pytest.raises(AuthError, match="PREVIEW_LEGACY_CREATION_DISABLED"):
        await service.request(tenant, business, actor, payload)
    inputs.assert_awaited_once_with(
        session, source, emphasis=payload.emphasis, parent_preview_id=parent_id, candidate=False
    )
    assert all("INSERT" not in str(call.args[0]) for call in session.execute.await_args_list)
    assert session.execute.await_count == (3 if has_parent else 2)
    assert session.scalar.await_count == (1 if has_parent else 0)


async def test_proposal_removed_after_claim_fails_without_render(settings, monkeypatch):
    preview, proposal = uuid4(), uuid4()
    database, _ = _database([{"proposal_id": proposal, "mime_type": "video/mp4"}, None])
    service = MediaPreviewService(settings, database)
    failed = AsyncMock(return_value="skipped")
    monkeypatch.setattr(service, "_fail", failed)
    assert await service.render(preview, 3) == "skipped"
    failed.assert_awaited_once_with(preview, 3, "PROPOSAL_NOT_FOUND", False)


async def test_old_context_fact_cannot_start_render_but_existing_preview_can_be_checked(settings):
    fact, tenant, business = uuid4(), uuid4(), uuid4()
    draft = {
        "title": "Uma ideia",
        "format": "short_video",
        "angle": "Apresentar produto",
        "fact_ids": [str(fact)],
        "hypotheses": [],
        "questions": [],
        "script": [
            {
                "role": "fact",
                "visual": "brand_card",
                "on_screen_text": "Croissant.",
                "voiceover": "Croissant.",
                "fact_ids": [str(fact)],
            },
            {
                "role": "cta",
                "visual": "brand_card",
                "on_screen_text": "Entre em contato",
                "voiceover": "Entre em contato",
                "fact_ids": [],
            },
        ],
    }
    proposal = {
        "id": uuid4(),
        "tenant_id": tenant,
        "business_id": business,
        "state": "completed",
        "document": draft,
        "review_state": "accepted",
        "expires_at": datetime.now(UTC) + timedelta(days=1),
        "model": "baseline-v1",
        "context_version": 1,
        "script_version": 1,
    }
    profile = {"version": 1, "timezone": "UTC", "name": "Café", "brand_color": "#6557ed"}
    document = {"facts": [{"id": str(fact), "kind": "product", "statement": "Croissant", "source_detail": "Titular"}]}
    database, session = _database([profile, profile])
    session.scalar.side_effect = [None, True, document, None, True, document]
    service = MediaPreviewService(settings, database)
    with pytest.raises(AuthError, match="PREVIEW_LEGACY_CREATION_DISABLED"):
        await service._inputs(session, proposal)
    assert (await service._inputs(session, proposal, historical_access=True)).statement == "Croissant."


async def test_purge_does_not_count_superseded_claim(monkeypatch):
    claim = PreviewPurgeClaim(uuid4(), uuid4(), 2, "previews/key.jpg")
    monkeypatch.setattr(media_retention, "claim_expired_previews", AsyncMock(return_value=[claim]))
    monkeypatch.setattr(media_retention, "finish_preview_purge", AsyncMock(return_value=False))
    store = AsyncMock()
    assert await media_retention.purge_expired_previews(Mock(), store, claim.owner) == 0
    store.delete.assert_awaited_once_with(claim.object_key)


def test_local_preview_cannot_accept_an_ai_skill_in_public_schema():
    with pytest.raises(ValueError, match="VISUAL_SKILL_REQUIRES_AI"):
        PreviewRequest(
            operation_id=uuid4(), proposal_id=uuid4(), generation_mode="local", visual_skill_id="instagram-feed-v1"
        )


async def test_internal_local_request_also_rejects_ai_skill_before_database_access(settings):
    database = Mock()
    payload = PreviewRequest.model_construct(
        operation_id=uuid4(), proposal_id=uuid4(), generation_mode="local", visual_skill_id="instagram-feed-v1"
    )
    with pytest.raises(AuthError, match="VISUAL_SKILL_REQUIRES_AI"):
        await MediaPreviewService(settings, database).request(uuid4(), uuid4(), uuid4(), payload)
    database.transaction.assert_not_called()


async def test_removed_proposal_cannot_start_a_preview(settings, monkeypatch):
    database, session = _database([None, None])
    monkeypatch.setattr(WhatsAppMaterialsService, "_require_owner", AsyncMock())
    with pytest.raises(AuthError, match="PROPOSAL_NOT_FOUND"):
        await MediaPreviewService(settings, database).request(
            uuid4(),
            uuid4(),
            uuid4(),
            PreviewRequest(operation_id=uuid4(), proposal_id=uuid4(), generation_mode="local"),
        )
    assert session.execute.await_count == 2


@pytest.mark.parametrize("row,expected", [(None, "skipped"), ({"state": "pending"}, "pending")])
async def test_failed_attempt_never_audits_stale_or_still_retryable_work(settings, monkeypatch, row, expected):
    database, _ = _database([row])
    audit = AsyncMock()
    monkeypatch.setattr("app.services.media_previews._audit", audit)
    assert await MediaPreviewService(settings, database)._fail(uuid4(), 4, "MEDIA_TIMEOUT", True) == expected
    audit.assert_not_awaited()


async def test_replaced_fake_preview_fence_does_not_start_admission_or_write_output(settings):
    database, _ = _database([None])
    store = AsyncMock()
    service = MediaPreviewService(settings.model_copy(update={"visual_ai_mode": "fake"}), database, store)
    assert await service._render_visual_fake(uuid4(), 4) == "skipped"
    store.put.assert_not_awaited()


def test_emphasis_change_requires_an_explicit_parent_preview():
    with pytest.raises(ValueError, match="PREVIEW_PARENT_REQUIRED"):
        PreviewRequest(operation_id=uuid4(), proposal_id=uuid4(), generation_mode="local", emphasis="photo")


async def test_catalog_briefing_never_enters_legacy_renderer(settings):
    with pytest.raises(AuthError, match="BRIEFING_PREVIEW_NOT_READY"):
        await MediaPreviewService(settings, Mock())._inputs(Mock(), {"briefing_required": True})
