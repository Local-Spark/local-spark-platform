"""A required service notice gates provider work without disabling baseline logic."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.schemas.editorial_proposals import ProposalRequest
from app.services.audio_transcription import AudioTranscriptionService
from app.services.auth import AuthError
from app.services.creative_catalog_resolution import CatalogInterpreterUnavailable
from app.services.editorial_briefings import EditorialBriefingService
from app.services.editorial_proposals import EditorialProposalService
from app.services.jev_interpreter import BudgetedJevInterpreter
from app.services.whatsapp_processing import MaterialProcessor
from app.services.whatsapp_replies import claim_ack, claim_reply
from app.workflows.content_activities import ContentCandidateActivities


def database_for(session):
    @asynccontextmanager
    async def opened(*_args):
        yield session

    session.begin = opened
    return Mock(transaction=opened, sessions=opened)


def result(row):
    value = Mock()
    value.mappings.return_value.one_or_none.return_value = row
    return value


async def test_material_without_agreement_stops_before_whatsapp_fetch(settings, monkeypatch):
    tenant, business, event = uuid4(), uuid4(), uuid4()
    session = AsyncMock()
    session.execute.return_value = result(
        {
            "tenant_id": tenant,
            "business_id": business,
            "state": "processing",
            "expires_at": datetime.now(UTC) + timedelta(hours=1),
        }
    )
    database = database_for(session)
    media = SimpleNamespace(fetch=AsyncMock())
    processor = MaterialProcessor(
        settings.model_copy(update={"service_agreement_required": True}), database, media, Mock()
    )
    processor._fail = AsyncMock(return_value="failed")
    allowed = AsyncMock(return_value=False)
    monkeypatch.setattr("app.services.service_agreement.service_agreement_allowed", allowed)
    assert await processor.process(event) == "failed"
    allowed.assert_awaited_once_with(session, processor.settings, tenant, business, worker=True)
    media.fetch.assert_not_awaited()


@pytest.mark.parametrize("ack", [False, True])
async def test_reply_without_agreement_is_deferred_before_budget_and_send(settings, monkeypatch, ack):
    import app.services.whatsapp_replies as module

    tenant, business, reply = uuid4(), uuid4(), uuid4()
    session = AsyncMock()
    session.execute.return_value = result(
        {"tenant_id": tenant, "business_id": business, "id": reply, "legacy_consented": True}
    )
    database = database_for(session)
    cfg = settings.model_copy(update={"service_agreement_required": True})
    allowed = AsyncMock(return_value=False)
    deferred = AsyncMock()
    budget = AsyncMock()
    monkeypatch.setattr("app.services.service_agreement.service_agreement_allowed", allowed)
    monkeypatch.setattr(module, "_defer_for_agreement", deferred)
    monkeypatch.setattr(module, "_within_daily_limit", budget)
    assert await (claim_ack(database, cfg) if ack else claim_reply(database, cfg)) is None
    allowed.assert_awaited_once_with(session, cfg, tenant, business, worker=True)
    deferred.assert_awaited_once_with(session, reply, ack=ack)
    budget.assert_not_awaited()


@pytest.mark.parametrize("ack", [False, True])
async def test_reply_with_agreement_continues_to_existing_budget_gate(settings, monkeypatch, ack):
    import app.services.whatsapp_replies as module

    tenant, business, reply = uuid4(), uuid4(), uuid4()
    session = AsyncMock()
    session.execute.return_value = result(
        {"tenant_id": tenant, "business_id": business, "id": reply, "legacy_consented": True}
    )
    database = database_for(session)
    cfg = settings.model_copy(update={"service_agreement_required": True})
    allowed = AsyncMock(return_value=True)
    defer_agreement, defer_budget, audit = AsyncMock(), AsyncMock(), AsyncMock()
    budget = AsyncMock(return_value=False)
    monkeypatch.setattr("app.services.service_agreement.service_agreement_allowed", allowed)
    monkeypatch.setattr(module, "_defer_for_agreement", defer_agreement)
    monkeypatch.setattr(module, "_defer_to_tomorrow", defer_budget)
    monkeypatch.setattr(module, "_within_daily_limit", budget)
    monkeypatch.setattr(module, "_audit_reply", audit)
    assert await (claim_ack(database, cfg) if ack else claim_reply(database, cfg)) is None
    allowed.assert_awaited_once_with(session, cfg, tenant, business, worker=True)
    budget.assert_awaited_once()
    defer_budget.assert_awaited_once_with(session, reply, ack=ack)
    defer_agreement.assert_not_awaited()


@pytest.mark.parametrize("ack", [False, True])
async def test_agreement_deferral_updates_the_corresponding_due_time(ack):
    from app.services.whatsapp_replies import _defer_for_agreement

    session = AsyncMock()
    reply = uuid4()
    await _defer_for_agreement(session, reply, ack=ack)
    sql = str(session.execute.await_args.args[0])
    assert ("ack_next_attempt_at" if ack else "next_attempt_at") in sql
    assert "interval '1 minute'" in sql
    assert session.execute.await_args.args[1] == {"id": reply}


async def test_editorial_worker_without_agreement_never_calls_provider(settings, monkeypatch):
    import app.services.editorial_proposals as module

    tenant, business, proposal = uuid4(), uuid4(), uuid4()
    session = AsyncMock()
    session.execute.return_value = result(
        {
            "state": "dispatching",
            "expires_at": datetime.now(UTC) + timedelta(hours=1),
            "tenant_id": tenant,
            "business_id": business,
        }
    )
    session.scalar.return_value = True
    database = database_for(session)
    cfg = settings.model_copy(update={"service_agreement_required": True, "editorial_ai_mode": "openai"})
    provider = SimpleNamespace(propose=AsyncMock())
    service = EditorialProposalService(cfg, database, provider)
    service._reject = AsyncMock(return_value="rejected")
    allowed = AsyncMock(return_value=False)
    monkeypatch.setattr(module, "service_agreement_allowed", allowed)
    assert await service.run(proposal) == "rejected"
    service._reject.assert_awaited_once_with(session, service._reject.await_args.args[1], "SERVICE_AGREEMENT_REQUIRED")
    allowed.assert_awaited_once_with(session, cfg, tenant, business, worker=True)
    provider.propose.assert_not_awaited()


async def test_editorial_request_without_agreement_cannot_enqueue_paid_work(settings, monkeypatch):
    import app.services.editorial_proposals as module

    tenant, business, actor = uuid4(), uuid4(), uuid4()
    session = AsyncMock()
    session.execute.return_value = result(None)
    session.scalar.side_effect = [0, True]
    database = database_for(session)
    cfg = settings.model_copy(update={"service_agreement_required": True, "editorial_ai_mode": "openai"})
    monkeypatch.setattr(module.WhatsAppMaterialsService, "_require_owner", AsyncMock())
    allowed = AsyncMock(return_value=False)
    monkeypatch.setattr(module, "service_agreement_allowed", allowed)
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_REQUIRED"):
        await EditorialProposalService(cfg, database).request(
            tenant, business, actor, ProposalRequest(operation_id=uuid4())
        )
    allowed.assert_awaited_once_with(session, cfg, tenant, business)
    assert not any("INSERT INTO editorial_proposals" in str(call.args[0]) for call in session.execute.await_args_list)


async def test_jev_requires_agreement_before_reserving_or_calling_provider(settings, monkeypatch):
    tenant, business, actor, source, operation = [uuid4() for _ in range(5)]
    session = AsyncMock()
    database = database_for(session)
    cfg = settings.model_copy(
        update={
            "service_agreement_required": True,
            "intent_ai_mode": "jev",
            "typesafe_api_key": SecretStr("synthetic"),
            "meta_encryption_key": SecretStr("synthetic"),
        }
    )
    provider = SimpleNamespace(interpret=AsyncMock())
    allowed = AsyncMock(return_value=False)
    monkeypatch.setattr("app.services.service_agreement.service_agreement_allowed", allowed)
    with pytest.raises(CatalogInterpreterUnavailable):
        await BudgetedJevInterpreter(cfg, database, tenant, business, actor, source, operation, provider).interpret(
            "ideia fictícia", []
        )
    allowed.assert_awaited_once_with(session, cfg, tenant, business)
    provider.interpret.assert_not_awaited()
    assert not any(
        "INSERT INTO editorial_intent_usage" in str(call.args[0]) for call in session.execute.await_args_list
    )


async def test_briefing_blocks_new_jev_interpretation_without_agreement(settings, monkeypatch):
    tenant, business, actor, source, operation = [uuid4() for _ in range(5)]
    session = AsyncMock()
    database = database_for(session)
    cfg = settings.model_copy(update={"service_agreement_required": True, "intent_ai_mode": "jev"})
    interpreter = SimpleNamespace(interpret=AsyncMock())
    allowed = AsyncMock(return_value=False)
    monkeypatch.setattr("app.services.service_agreement.service_agreement_allowed", allowed)
    service = EditorialBriefingService(cfg, database, interpreter)
    service._source = AsyncMock()
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_REQUIRED"):
        await service.prepare(tenant, business, actor, source, operation)
    service._source.assert_not_awaited()
    interpreter.interpret.assert_not_awaited()


async def test_audio_without_agreement_does_not_read_or_transcribe(settings, monkeypatch):
    tenant, business, event = uuid4(), uuid4(), uuid4()
    session = AsyncMock()
    database = database_for(session)
    cfg = settings.model_copy(update={"service_agreement_required": True, "audio_transcription_mode": "openai"})
    store = SimpleNamespace(get_audio=AsyncMock())
    processor = MaterialProcessor(cfg, database, Mock(), store)
    provider = SimpleNamespace(transcribe=AsyncMock())
    service = AudioTranscriptionService(processor, provider)
    service._row = AsyncMock(
        return_value={
            "tenant_id": tenant,
            "business_id": business,
            "kind": "audio",
            "transcription_state": None,
            "delete_requested_at": None,
            "expires_at": datetime.now(UTC) + timedelta(hours=1),
            "sender_hash": "synthetic",
            "created_at": datetime.now(UTC),
            "event_expires": datetime.now(UTC),
        }
    )
    monkeypatch.setattr("app.services.service_agreement.service_agreement_allowed", AsyncMock(return_value=False))
    assert await service.run(event) == "skipped"
    store.get_audio.assert_not_awaited()
    provider.transcribe.assert_not_awaited()


async def test_candidate_without_agreement_skips_before_interpretation(settings, monkeypatch):
    tenant, business, actor, event = [uuid4() for _ in range(4)]
    session = AsyncMock()
    session.execute.return_value = result(
        {"tenant_id": tenant, "business_id": business, "actor_id": actor, "legacy_consented": True}
    )
    database = database_for(session)
    cfg = settings.model_copy(update={"service_agreement_required": True, "intent_ai_mode": "jev"})
    allowed = AsyncMock(return_value=False)
    monkeypatch.setattr("app.services.service_agreement.service_agreement_allowed", allowed)
    assert await ContentCandidateActivities(cfg, database, database).request_candidate_proposal(str(event)) == "skipped"
    allowed.assert_awaited_once_with(session, cfg, tenant, business)


async def test_candidate_baseline_does_not_require_agreement(settings, monkeypatch):
    import app.workflows.content_activities as module

    tenant, business, actor, event, proposal = [uuid4() for _ in range(5)]
    session = AsyncMock()
    session.execute.return_value = result(
        {"tenant_id": tenant, "business_id": business, "actor_id": actor, "kind": "image", "legacy_consented": True}
    )
    session.scalar.return_value = None
    database = database_for(session)
    cfg = settings.model_copy(
        update={"service_agreement_required": True, "intent_ai_mode": "disabled", "editorial_ai_mode": "disabled"}
    )
    allowed = AsyncMock(return_value=False)
    monkeypatch.setattr("app.services.service_agreement.service_agreement_allowed", allowed)
    request = AsyncMock(return_value=SimpleNamespace(id=proposal))
    monkeypatch.setattr(module, "EditorialProposalService", lambda *_: SimpleNamespace(request=request))
    assert await ContentCandidateActivities(cfg, database, database).request_candidate_proposal(str(event)) == str(
        proposal
    )
    allowed.assert_not_awaited()
