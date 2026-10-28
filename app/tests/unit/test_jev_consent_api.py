"""Consent routes delegate owner identity and business without changing provider settings."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.v1 import editorial_proposals
from app.schemas.editorial_proposals import EditorialAIConsent
from app.services.auth import AuthError
from app.services.jev_consent import JevConsentService


async def test_jev_consent_endpoints_delegate_tenant_business_and_actor(monkeypatch):
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    status = AsyncMock(return_value={"accepted": False, "provider_enabled": True})
    update = AsyncMock(return_value={"accepted": True, "provider_enabled": True})
    service = SimpleNamespace(status=status, set=update)
    monkeypatch.setattr(editorial_proposals, "JevConsentService", lambda *_: service)
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(settings=object(), database=object())))
    assert not (await editorial_proposals.jev_consent_status(tenant, business, request, actor))["accepted"]
    assert (
        await editorial_proposals.set_jev_consent(tenant, business, EditorialAIConsent(accepted=True), request, actor)
    )["accepted"]
    status.assert_awaited_once_with(tenant, business, actor)
    update.assert_awaited_once_with(tenant, business, actor, True)


async def test_single_service_contract_replaces_the_legacy_interpreter_permission(settings, monkeypatch):
    session = SimpleNamespace(execute=AsyncMock())

    @asynccontextmanager
    async def transaction(*_args):
        yield session

    monkeypatch.setattr("app.services.visual_consent_gate.VisualConsentGate._lock", AsyncMock())
    monkeypatch.setattr("app.services.jev_consent.service_agreement_accepted", AsyncMock(return_value=True))
    service = JevConsentService(settings, SimpleNamespace(transaction=transaction))
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_MANAGES_PROCESSING"):
        await service.set(uuid4(), uuid4(), uuid4(), False)
    session.execute.assert_not_awaited()
