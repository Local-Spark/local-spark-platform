"""Fail before submission when a prepared request cannot be retained securely."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.services.editorial_proposals import EditorialProposalService
from app.tests.unit.test_media_preview_races import _database


@pytest.mark.parametrize("key", [None, "   "])
async def test_trace_key_required_even_after_inputs_have_been_prepared(settings, monkeypatch, key):
    proposal, tenant, business = uuid4(), uuid4(), uuid4()
    row = {
        "id": proposal,
        "state": "dispatching",
        "tenant_id": tenant,
        "business_id": business,
        "consent_generation": 1,
        "expires_at": datetime.now(UTC) + timedelta(days=1),
    }
    database, session = _database([row, None, None])
    session.scalar.side_effect = [True, 1, 0]
    monkeypatch.setattr("app.services.editorial_proposals.service_agreement_allowed", AsyncMock(return_value=True))
    provider = SimpleNamespace(propose=AsyncMock())
    cfg = settings.model_copy(
        update={
            "editorial_ai_mode": "openai",
            "editorial_daily_token_limit": 100000,
            "meta_encryption_key": SecretStr(key) if key is not None else None,
        }
    )
    service = EditorialProposalService(cfg, database, provider)
    service._consented = AsyncMock(return_value=True)
    service._inputs = AsyncMock(
        return_value=(
            {
                "confirmed_facts": [{"id": str(uuid4())}],
                "editorial_skill": {"id": "instagram-feed-v1", "sha256": "a" * 64},
            },
            set(),
        )
    )
    service._reject = AsyncMock(return_value="rejected")
    builder = Mock()
    monkeypatch.setattr("app.adapters.editorial_ai.OpenAIEditorialProvider.build_request", builder)
    assert await service.run(proposal) == "rejected"
    service._reject.assert_awaited_once_with(session, row, "EDITORIAL_TRACE_KEY_REQUIRED")
    builder.assert_not_called()
    provider.propose.assert_not_awaited()
    assert all("INSERT" not in str(call.args[0]) for call in session.execute.await_args_list)


async def test_catalog_required_proposal_cannot_use_source_without_briefing(settings):
    service = EditorialProposalService(settings, Mock())
    session = Mock()
    row = {"source_asset_id": None, "context_version": 0, "briefing_required": True}
    assert await service._inputs(session, row) is None
    session.execute.assert_not_called()
