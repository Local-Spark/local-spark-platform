"""Consent routes delegate owner identity and business without changing provider settings."""

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from app.api.v1 import editorial_proposals
from app.schemas.editorial_proposals import EditorialAIConsent


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
