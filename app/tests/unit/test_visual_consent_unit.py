"""Visual consent is explicit, separately scoped, and revocable when disabled."""

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import SecretStr, ValidationError

from app.api.v1 import media_previews
from app.core.config import Settings
from app.schemas.media_previews import VisualAIConsent
from app.services.visual_consent import VisualConsentService


@pytest.mark.parametrize("state,enabled", [("revoked", False), ("active", True), ("revocation_pending", False)])
async def test_status_delegates_to_gate_and_reports_configuration(settings, monkeypatch, state, enabled):
    gate = SimpleNamespace(status=AsyncMock(return_value=state))
    database = object()
    monkeypatch.setattr("app.services.visual_consent.VisualConsentGate", lambda db: gate if db is database else None)
    cfg = settings.model_copy(update={"visual_ai_mode": "openai" if enabled else "disabled"})
    ids = [uuid4() for _ in range(3)]
    assert await VisualConsentService(cfg, database).status(*ids) == {
        "accepted": state == "active",
        "state": state,
        "provider_enabled": enabled,
    }
    gate.status.assert_awaited_once_with(*ids)


@pytest.mark.parametrize("accepted,state", [(True, "active"), (False, "revoked"), (False, "revocation_pending")])
async def test_set_delegates_to_correct_gate_action_and_returns_effective_state(settings, monkeypatch, accepted, state):
    gate = SimpleNamespace(enable=AsyncMock(return_value=state), request_withdrawal=AsyncMock(return_value=state))
    database = object()
    monkeypatch.setattr("app.services.visual_consent.VisualConsentGate", lambda db: gate if db is database else None)
    ids = [uuid4() for _ in range(3)]
    result = await VisualConsentService(settings, database).set(*ids, accepted)
    assert result == {"accepted": state == "active", "state": state, "provider_enabled": False}
    selected = gate.enable if accepted else gate.request_withdrawal
    other = gate.request_withdrawal if accepted else gate.enable
    selected.assert_awaited_once_with(*ids)
    other.assert_not_awaited()


async def test_routes_delegate_authenticated_owner_and_preserve_result(monkeypatch):
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    status = AsyncMock(return_value={"accepted": False, "state": "revoked", "provider_enabled": True})
    update = AsyncMock(return_value={"accepted": True, "state": "active", "provider_enabled": True})
    monkeypatch.setattr(media_previews, "VisualConsentService", lambda *_: SimpleNamespace(status=status, set=update))
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(settings=object(), database=object())))
    assert not (await media_previews.visual_consent_status(tenant, business, request, actor))["accepted"]
    assert (await media_previews.set_visual_consent(tenant, business, VisualAIConsent(accepted=True), request, actor))[
        "accepted"
    ]
    status.assert_awaited_once_with(tenant, business, actor)
    update.assert_awaited_once_with(tenant, business, actor, True)


@pytest.mark.parametrize("value", ["true", 1, None])
def test_consent_requires_explicit_json_boolean(value):
    with pytest.raises(ValidationError):
        VisualAIConsent(accepted=value)


def test_visual_mode_requires_dev_or_test_with_credential_and_budget(settings):
    values = settings.model_dump()
    values.update(visual_ai_mode="openai", openai_api_key=None, visual_ai_monthly_budget_usd_micros=0)
    with pytest.raises(ValidationError, match="requires explicit credentials"):
        Settings(_env_file=None, **values)
    values.update(openai_api_key=SecretStr("   "), visual_ai_monthly_budget_usd_micros=1)
    with pytest.raises(ValidationError, match="requires explicit credentials"):
        Settings(_env_file=None, **values)
    values.update(openai_api_key=SecretStr("synthetic"), visual_ai_monthly_budget_usd_micros=0)
    with pytest.raises(ValidationError, match="requires explicit credentials"):
        Settings(_env_file=None, **values)
    values.update(openai_api_key=SecretStr("synthetic"), visual_ai_monthly_budget_usd_micros=1)
    assert Settings(_env_file=None, **values).visual_ai_mode == "openai"
    values.update(
        environment="production",
        temporal_tls=True,
        public_web_url="https://example.test",
        jwt_secret=SecretStr("a" * 32),
        auth_database_url=values["database_url"],
        auth_encryption_key=SecretStr("private"),
        smtp_starttls=True,
        smtp_username="test",
        smtp_password=SecretStr("test"),
        material_storage_endpoint=None,
        material_storage_public_endpoint=None,
    )
    with pytest.raises(ValidationError, match="restricted to development"):
        Settings(_env_file=None, **values)
