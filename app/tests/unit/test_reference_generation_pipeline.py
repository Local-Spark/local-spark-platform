"""Editorial and image generation consume one pinned context and retain fact gates."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.auth import AuthError
from app.services.editorial_consent_scope import admitted_visual_run
from app.services.editorial_proposals import EditorialProposalService
from app.services.reference_generation_context import REFERENCE_CREATIVE_RULE, read_generation_snapshot
from app.services.visual_provider_execution import VisualSubmissionClaims
from app.tests.unit.test_media_preview_races import _database
from app.tests.unit.test_reference_generation_context import context
from app.tests.unit.test_visual_brand_finish_unit import brand_case as brand_case
from app.tests.unit.test_visual_context_unit import setup_case as setup_case
from app.tests.unit.test_visual_provider_execution import _case
from app.tests.unit.visual_full_fixture import configure_full


async def test_editorial_uses_pinned_reference_context_instead_of_conflicting_legacy_indication(settings, monkeypatch):
    raw = context()
    row = {
        "source_asset_id": uuid4(),
        "tenant_id": uuid4(),
        "business_id": uuid4(),
        "context_version": 0,
        "reference_generation_snapshot": raw,
        "owner_reference_snapshot": [{"instagram_handle": "old.indication", "access_status": "not_checked"}],
    }
    service = EditorialProposalService(settings, None)
    monkeypatch.setattr(service, "_source", lambda _: "Faça um post")
    session = SimpleNamespace(
        execute=AsyncMock(
            return_value=SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: {"kind": "text"}))
        )
    )
    result = await service._inputs(session, row)
    assert result is not None
    payload, fact_ids = result
    assert payload["reference_context"] == read_generation_snapshot(raw).model_input()
    assert "owner_reference_indications" not in payload
    assert payload["confirmed_facts"] == [] and fact_ids == set()


async def test_visual_uses_same_pinned_context_without_feed_images(brand_case):
    c = brand_case
    raw = context()
    c.row["reference_generation_snapshot"] = raw
    c.row["owner_reference_snapshot"] = [{"instagram_handle": "old.indication"}]
    scope, _, _ = configure_full(c)
    with admitted_visual_run(scope):
        prepared = await c.service.prepare(*c.ids)
    prompt = prepared.request.request.prompt
    assert REFERENCE_CREATIVE_RULE in prompt
    assert "Tom acolhedor" in prompt and '"estado_analise": "partial"' in prompt
    assert "old.indication" not in prompt and "não foram acessados ou analisados" not in prompt
    assert raw["selected"][0]["reference_id"] not in prompt
    assert raw["learnings"][0]["analysis_id"] not in prompt
    assert {source.kind for source in prepared.request.sources} == {"item_photo", "kit_example"}


async def test_visual_fingerprint_binds_snapshot_and_legacy_null_is_identical(setup_case, monkeypatch):
    c = setup_case
    before = await c.service.capture(*c.ids[:4])
    c.session.proposal["reference_generation_snapshot"] = None
    assert await c.service.capture(*c.ids[:4]) == before
    raw = context()
    c.session.proposal["reference_generation_snapshot"] = raw
    check = AsyncMock(return_value=True)
    monkeypatch.setattr("app.services.visual_context.generation_context_is_current", check)
    pinned = await c.service.capture(*c.ids[:4])
    assert pinned.fingerprint != before.fingerprint
    check.assert_awaited_once_with(c.session, c.ids[1], read_generation_snapshot(raw))
    raw["learnings"][0]["patterns"][0]["observation"] = "Cores suaves"
    assert (await c.service.capture(*c.ids[:4])).fingerprint != pinned.fingerprint


async def test_changed_reference_blocks_new_visual_effect_but_not_completed_review(setup_case, monkeypatch):
    c = setup_case
    c.session.proposal["reference_generation_snapshot"] = context()
    check = AsyncMock(return_value=False)
    monkeypatch.setattr("app.services.visual_context.generation_context_is_current", check)
    with pytest.raises(AuthError, match="REFERENCE_GENERATION_CONTEXT_CHANGED"):
        await c.service.capture(*c.ids[:4])
    check.reset_mock()
    result = await c.service.capture(*c.ids[:4], completed_preview_id=uuid4())
    assert len(result.fingerprint) == 64
    check.assert_not_awaited()


async def test_obsolete_selection_rejected_before_editorial_reservation_or_provider(settings, monkeypatch):
    row = {
        "id": uuid4(),
        "state": "dispatching",
        "tenant_id": uuid4(),
        "business_id": uuid4(),
        "consent_generation": 1,
        "expires_at": datetime.now(UTC) + timedelta(days=1),
    }
    database, session = _database([row, None, None])
    session.scalar.side_effect = [True, 1]
    monkeypatch.setattr("app.services.editorial_proposals.service_agreement_allowed", AsyncMock(return_value=True))
    provider = SimpleNamespace(propose=AsyncMock())
    service = EditorialProposalService(settings.model_copy(update={"editorial_ai_mode": "openai"}), database, provider)
    service._consented = AsyncMock(return_value=True)
    service._references_current = AsyncMock(return_value=False)
    service._inputs = AsyncMock()
    service._reject = AsyncMock(return_value="rejected")
    assert await service.run(row["id"]) == "rejected"
    service._reject.assert_awaited_once_with(session, row, "REFERENCE_GENERATION_CONTEXT_CHANGED")
    service._inputs.assert_not_awaited()
    provider.propose.assert_not_awaited()
    assert all("INSERT" not in str(call.args[0]) for call in session.execute.await_args_list)


@pytest.mark.parametrize("variant", ["current", "removed", "corrupted"])
async def test_visual_selection_is_checked_inside_financial_claim(variant):
    identity, prepared, attempt = _case()
    raw = {} if variant == "corrupted" else context()
    database, session = _database([])
    session.execute = AsyncMock()
    values = [1, 1, raw]
    if variant != "corrupted":
        values.append(variant == "current")
    if variant == "current":
        values.append(1)
    session.scalar = AsyncMock(side_effect=values)
    claimed = await VisualSubmissionClaims(database).claim(
        identity, attempt.reservation.id, prepared.request.model, prepared.context.proposal_id
    )
    assert claimed is (variant == "current")
    calls = [str(call.args[0]) for call in session.scalar.await_args_list]
    assert ("reference_generation_context_is_current" in " ".join(calls)) is (variant != "corrupted")
    financial = [sql for sql in calls if "UPDATE visual_cost_reservations" in sql]
    assert bool(financial) is (variant == "current")
