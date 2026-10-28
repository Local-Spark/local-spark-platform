"""Offline checks for conflicts and authorization at editorial admission."""

import hashlib
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.schemas.editorial_proposals import ProposalRequest
from app.services.editorial_proposals import EditorialProposalService
from app.services.whatsapp_materials import WhatsAppMaterialsService


def mapped(row):
    result = MagicMock()
    result.mappings.return_value.one_or_none.return_value = row
    result.mappings.return_value.one.return_value = row
    return result


@asynccontextmanager
async def transaction(session):
    yield session


async def test_request_replays_winner_after_insert_conflict_with_original_epoch(settings, monkeypatch):
    tenant, business, actor, operation = [uuid4() for _ in range(4)]
    winner = {"request_hash": hashlib.sha256(b"None").hexdigest(), "id": uuid4()}
    selected = 0
    inserted = []

    async def execute(statement, params=None):
        nonlocal selected
        sql = str(statement)
        if "SELECT * FROM editorial_proposals" in sql:
            selected += 1
            return mapped(None if selected == 1 else winner)
        if "INSERT INTO editorial_proposals" in sql:
            inserted.append(params)
        return mapped(None)

    async def scalar(statement, params=None):
        sql = str(statement)
        if "ELSE coalesce((SELECT generation" in sql:
            return 3
        if "SELECT version FROM business_context_heads" in sql:
            return 0
        return True

    session = SimpleNamespace(execute=AsyncMock(side_effect=execute), scalar=AsyncMock(side_effect=scalar))
    database = SimpleNamespace(transaction=lambda *_: transaction(session))
    cfg = settings.model_copy(update={"editorial_ai_mode": "openai"})
    service = EditorialProposalService(cfg, database)
    result = object()
    monkeypatch.setattr(WhatsAppMaterialsService, "_require_owner", AsyncMock())
    monkeypatch.setattr(service, "_consented", AsyncMock(return_value=True))
    monkeypatch.setattr("app.services.editorial_proposals._present", lambda row: result)
    assert await service.request(tenant, business, actor, ProposalRequest(operation_id=operation)) is result
    assert selected == 2 and len(inserted) == 1 and inserted[0]["generation"] == 3


async def test_worker_rejects_matching_epoch_when_editorial_consent_is_absent(settings, monkeypatch):
    tenant, business, proposal = uuid4(), uuid4(), uuid4()
    row = {
        "tenant_id": tenant,
        "business_id": business,
        "state": "dispatching",
        "expires_at": datetime.now(UTC) + timedelta(hours=1),
        "consent_generation": 2,
    }

    async def scalar(statement, params=None):
        if "current_setting('app.tenant_id'" in str(statement):
            return str(tenant)
        return 2 if "ELSE coalesce((SELECT generation" in str(statement) else True

    session = SimpleNamespace(execute=AsyncMock(return_value=mapped(row)), scalar=AsyncMock(side_effect=scalar))
    session.begin = lambda: transaction(session)
    database = SimpleNamespace(sessions=lambda: transaction(session))
    cfg = settings.model_copy(update={"editorial_ai_mode": "openai"})
    service = EditorialProposalService(cfg, database)
    monkeypatch.setattr(service, "_consented", AsyncMock(return_value=False))
    reject = AsyncMock(return_value="rejected")
    monkeypatch.setattr(service, "_reject", reject)
    assert await service.run(proposal) == "rejected"
    reject.assert_awaited_once_with(session, row, "EDITORIAL_AI_CONSENT_REQUIRED")
