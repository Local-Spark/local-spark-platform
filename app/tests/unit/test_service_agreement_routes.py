"""Route delegation keeps business and actor scope intact."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.api.v1 import service_agreement, whatsapp_link
from app.services.auth import AuthError


async def test_agreement_status_passes_scope_and_returns_service_result(monkeypatch):
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    settings, database = object(), object()
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(settings=settings, database=database)))
    result = {"accepted": False, "acceptance_enabled": False}
    service = SimpleNamespace(status=AsyncMock(return_value=result))
    constructor = Mock(return_value=service)
    monkeypatch.setattr(service_agreement, "ServiceAgreementService", constructor)

    assert await service_agreement.agreement_status(tenant, business, request, actor) == result
    constructor.assert_called_once_with(settings, database)
    service.status.assert_awaited_once_with(tenant, business, actor)


async def test_disconnect_passes_scope_and_preserves_service_error(monkeypatch):
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    request = object()
    disconnect = AsyncMock(side_effect=AuthError("SERVICE_AGREEMENT_CHANGE_PENDING", 409))
    monkeypatch.setattr(whatsapp_link, "service", Mock(return_value=SimpleNamespace(disconnect=disconnect)))

    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_CHANGE_PENDING"):
        await whatsapp_link.link_disconnect(tenant, business, request, actor)
    disconnect.assert_awaited_once_with(tenant, business, actor)


async def test_agreement_acceptance_passes_only_validated_notice_and_owner_scope(monkeypatch):
    from app.schemas.service_agreement import ServiceAgreementAcceptance
    from app.services.service_agreement import SERVICE_AGREEMENT_HASH, SERVICE_AGREEMENT_VERSION

    tenant, business, actor = uuid4(), uuid4(), uuid4()
    settings, database = object(), object()
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(settings=settings, database=database)))
    result = {"accepted": True, "acceptance_enabled": True}
    service = SimpleNamespace(accept=AsyncMock(return_value=result))
    constructor = Mock(return_value=service)
    monkeypatch.setattr(service_agreement, "ServiceAgreementService", constructor)
    payload = ServiceAgreementAcceptance(
        version=SERVICE_AGREEMENT_VERSION, notice_hash=SERVICE_AGREEMENT_HASH, accept=True
    )
    assert await service_agreement.agreement_accept(tenant, business, payload, request, actor) == result
    constructor.assert_called_once_with(settings, database)
    service.accept.assert_awaited_once_with(tenant, business, actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH)


@pytest.mark.parametrize(
    "body",
    [
        {"version": "v", "notice_hash": "0" * 64, "accept": False},
        {"version": "v", "notice_hash": "invalid", "accept": True},
        {"version": "v", "notice_hash": "0" * 64},
        {"version": "v", "notice_hash": "0" * 64, "accept": True, "actor": "other"},
    ],
)
def test_acceptance_schema_requires_an_explicit_complete_decision(body):
    from pydantic import ValidationError

    from app.schemas.service_agreement import ServiceAgreementAcceptance

    with pytest.raises(ValidationError):
        ServiceAgreementAcceptance.model_validate(body)
