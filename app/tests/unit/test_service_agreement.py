"""Agreement lookups are business scoped and workers never switch tenants."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.auth import AuthError
from app.services.service_agreement import (
    SERVICE_AGREEMENT_HASH,
    SERVICE_AGREEMENT_VERSION,
    ServiceAgreementService,
    service_agreement_allowed,
)
from app.services.visual_consent_gate import VisualConsentGate
from app.services.visual_pending_changes import VisualPendingChanges
from app.services.whatsapp_materials import WhatsAppMaterialsService


async def test_transition_mode_never_bypasses_production(settings):
    session = AsyncMock()
    tenant, business = uuid4(), uuid4()
    assert await service_agreement_allowed(session, settings, tenant, business)
    assert not await service_agreement_allowed(
        session, settings.model_copy(update={"environment": "production"}), tenant, business
    )
    session.scalar.assert_not_awaited()


async def test_worker_sets_empty_tenant_context_and_checks_exact_version(settings):
    session = AsyncMock()
    session.scalar.side_effect = [None, 1]
    tenant, business = uuid4(), uuid4()
    enabled = settings.model_copy(update={"service_agreement_required": True})
    assert await service_agreement_allowed(session, enabled, tenant, business, worker=True)
    assert session.execute.await_args.args[1] == {"tenant": str(tenant)}
    assert session.scalar.await_args.args[1] == {
        "tenant": tenant,
        "business": business,
        "version": SERVICE_AGREEMENT_VERSION,
        "hash": SERVICE_AGREEMENT_HASH,
    }


async def test_worker_refuses_to_switch_tenant(settings):
    session = AsyncMock()
    session.scalar.return_value = str(uuid4())
    enabled = settings.model_copy(update={"service_agreement_required": True})
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_TENANT_MISMATCH"):
        await service_agreement_allowed(session, enabled, uuid4(), uuid4(), worker=True)
    session.execute.assert_not_awaited()


async def test_existing_tenant_context_is_not_reset(settings):
    session = AsyncMock()
    tenant = uuid4()
    session.scalar.side_effect = [str(tenant), None]
    enabled = settings.model_copy(update={"service_agreement_required": True})
    assert not await service_agreement_allowed(session, enabled, tenant, uuid4(), worker=True)
    session.execute.assert_not_awaited()


async def test_owner_lookup_does_not_set_worker_context(settings):
    session = AsyncMock()
    session.scalar.return_value = None
    enabled = settings.model_copy(update={"service_agreement_required": True})
    assert not await service_agreement_allowed(session, enabled, uuid4(), uuid4())
    session.execute.assert_not_awaited()


def test_production_requires_enforcement_even_if_testing_can_disable_it(settings):
    with pytest.raises(ValueError, match="requires service agreement"):
        settings.model_copy(update={"environment": "production"}).service_agreement_safety()
    assert settings.model_copy(
        update={"environment": "production", "service_agreement_required": True}
    ).service_agreement_safety()


@pytest.mark.parametrize("accepted", [False, True])
async def test_status_is_owner_scoped_and_offers_one_explicit_acceptance(settings, monkeypatch, accepted):
    agreement_result = MagicMock()
    agreement_result.mappings.return_value.one_or_none.return_value = (
        {"notice_hash": SERVICE_AGREEMENT_HASH, "accepted_at": datetime.now(UTC)} if accepted else None
    )
    session = SimpleNamespace(execute=AsyncMock(return_value=agreement_result), scalar=AsyncMock(return_value=1))

    @asynccontextmanager
    async def transaction(*_args):
        yield session

    owner = AsyncMock()
    monkeypatch.setattr(WhatsAppMaterialsService, "_require_owner", owner)
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    result = await ServiceAgreementService(settings, SimpleNamespace(transaction=transaction)).status(
        tenant, business, actor
    )
    owner.assert_awaited_once_with(session, tenant, business, actor)
    assert result["accepted"] is accepted
    assert result["review_required"] is False
    assert result["notice_hash"] == SERVICE_AGREEMENT_HASH
    assert result["acceptance_enabled"] is True
    assert "capabilities" not in result


async def test_status_rejects_a_changed_notice_with_the_same_version(settings, monkeypatch):
    result = MagicMock()
    result.mappings.return_value.one_or_none.return_value = {"notice_hash": "0" * 64}
    session = SimpleNamespace(execute=AsyncMock(return_value=result))

    @asynccontextmanager
    async def transaction(*_args):
        yield session

    monkeypatch.setattr(WhatsAppMaterialsService, "_require_owner", AsyncMock())
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_VERSION_CONFLICT"):
        await ServiceAgreementService(settings, SimpleNamespace(transaction=transaction)).status(
            uuid4(), uuid4(), uuid4()
        )


async def test_accept_rejects_existing_version_with_different_hash(settings, monkeypatch):
    session = SimpleNamespace(scalar=AsyncMock(return_value="0" * 64))

    @asynccontextmanager
    async def transaction(*_args):
        yield session

    monkeypatch.setattr(VisualConsentGate, "_lock", AsyncMock())
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_VERSION_CONFLICT"):
        await ServiceAgreementService(settings, SimpleNamespace(transaction=transaction)).accept(
            uuid4(), uuid4(), uuid4(), SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH
        )


@pytest.mark.parametrize(
    "version,notice_hash", [("other", SERVICE_AGREEMENT_HASH), (SERVICE_AGREEMENT_VERSION, "0" * 64)]
)
async def test_accept_rejects_unpresented_notice_before_opening_transaction(settings, version, notice_hash):
    database = MagicMock()
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_VERSION_CONFLICT"):
        await ServiceAgreementService(settings, database).accept(uuid4(), uuid4(), uuid4(), version, notice_hash)
    database.transaction.assert_not_called()


async def test_accept_rejects_pending_change_without_initializing_permissions(settings, monkeypatch):
    session = SimpleNamespace(scalar=AsyncMock(return_value=None), execute=AsyncMock())

    @asynccontextmanager
    async def transaction(*_args):
        yield session

    monkeypatch.setattr(VisualConsentGate, "_lock", AsyncMock())
    monkeypatch.setattr(VisualPendingChanges, "has_pending_in_session", AsyncMock(return_value=True))
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_CHANGE_PENDING"):
        await ServiceAgreementService(settings, SimpleNamespace(transaction=transaction)).accept(
            uuid4(), uuid4(), uuid4(), SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH
        )
    session.execute.assert_not_awaited()


async def test_accept_rejects_admitted_work_before_recording_agreement(settings, monkeypatch):
    session = SimpleNamespace(scalar=AsyncMock(side_effect=[None, True]), execute=AsyncMock())

    @asynccontextmanager
    async def transaction(*_args):
        yield session

    monkeypatch.setattr(VisualConsentGate, "_lock", AsyncMock())
    monkeypatch.setattr(VisualPendingChanges, "has_pending_in_session", AsyncMock(return_value=False))
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_CHANGE_PENDING"):
        await ServiceAgreementService(settings, SimpleNamespace(transaction=transaction)).accept(
            uuid4(), uuid4(), uuid4(), SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH
        )
    assert "creative_active_runs" in str(session.scalar.await_args.args[0])
    session.execute.assert_not_awaited()


@pytest.mark.parametrize("existing,writes", [(None, 2), (SERVICE_AGREEMENT_HASH, 0)])
async def test_accept_records_only_contract_and_audit_and_replay_does_not_rewrite_history(
    settings, monkeypatch, existing, writes
):
    from uuid import NAMESPACE_URL, uuid5

    session = SimpleNamespace(scalar=AsyncMock(side_effect=[existing, False]), execute=AsyncMock())

    @asynccontextmanager
    async def transaction(*_args):
        yield session

    monkeypatch.setattr(VisualConsentGate, "_lock", AsyncMock())
    monkeypatch.setattr(VisualPendingChanges, "has_pending_in_session", AsyncMock(return_value=False))
    service = ServiceAgreementService(settings, SimpleNamespace(transaction=transaction))
    service.status = AsyncMock(return_value={"accepted": True})
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    assert await service.accept(tenant, business, actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH) == {
        "accepted": True
    }
    assert session.execute.await_count == writes
    if writes:
        statements = [str(call.args[0]) for call in session.execute.await_args_list]
        assert "INSERT INTO service_agreement_acceptances" in statements[0]
        assert "INSERT INTO audit_events" in statements[1]
        audit = session.execute.await_args_list[1].args[1]
        assert audit["operation"] == uuid5(
            NAMESPACE_URL,
            f"service-agreement:{tenant}:{business}:{SERVICE_AGREEMENT_VERSION}:{SERVICE_AGREEMENT_HASH}",
        )
    service.status.assert_awaited_once_with(tenant, business, actor)


async def test_transition_worker_scope_is_checked_even_with_enforcement_disabled(settings):
    session = AsyncMock()
    tenant, business = uuid4(), uuid4()
    session.scalar.return_value = str(tenant)
    assert await service_agreement_allowed(session, settings, tenant, business, worker=True)
    assert session.scalar.await_count == 1
    session.execute.assert_not_awaited()


async def test_exact_acceptance_is_independent_of_enforcement_and_sql_helpers_share_document(settings):
    from app.services.service_agreement_scope import (
        accepted_agreement_at_sql,
        accepted_agreement_sql,
        editorial_agreement_generation_sql,
        service_agreement_accepted,
    )

    session = AsyncMock()
    session.scalar.side_effect = [None, 1]
    tenant, business = uuid4(), uuid4()
    assert await service_agreement_accepted(session, tenant, business, worker=True)
    for sql in (
        accepted_agreement_sql(),
        accepted_agreement_at_sql(),
        accepted_agreement_sql("p.tenant", "p.business"),
    ):
        assert SERVICE_AGREEMENT_VERSION in sql and SERVICE_AGREEMENT_HASH in sql
    assert "p.tenant" in accepted_agreement_sql("p.tenant", "p.business")
    assert "accepted_at" in accepted_agreement_at_sql()
    generation = -int(SERVICE_AGREEMENT_HASH[:15], 16)
    assert -(2**63) <= generation < 0
    assert str(generation) in editorial_agreement_generation_sql()
    assert accepted_agreement_sql() in editorial_agreement_generation_sql()
