"""Visual consent is explicit, separately scoped, and revocable when disabled."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import SecretStr, ValidationError

from app.api.v1 import media_previews
from app.core.config import Settings
from app.schemas.media_previews import VisualAIConsent
from app.services.visual_consent import VisualConsentService


class Database:
    def __init__(self, session):
        self.session = session

    @asynccontextmanager
    async def transaction(self, *_):
        yield self.session


@pytest.mark.parametrize("accepted,enabled", [(None, False), (True, True), (False, False)])
async def test_status_preserves_existing_consent_and_reports_configuration(settings, monkeypatch, accepted, enabled):
    owner = AsyncMock()
    monkeypatch.setattr("app.services.visual_consent.WhatsAppMaterialsService._require_owner", owner)
    session = SimpleNamespace(scalar=AsyncMock(return_value=accepted))
    cfg = settings.model_copy(update={"visual_ai_mode": "openai" if enabled else "disabled"})
    ids = [uuid4() for _ in range(3)]
    assert await VisualConsentService(cfg, Database(session)).status(*ids) == {
        "accepted": bool(accepted),
        "provider_enabled": enabled,
    }
    owner.assert_awaited_once_with(session, *ids)


@pytest.mark.parametrize("accepted,changed", [(True, 1), (False, 1), (True, None), (False, None)])
async def test_changed_consent_is_audited_atomically_and_unchanged_state_is_not(
    settings, monkeypatch, accepted, changed
):
    monkeypatch.setattr("app.services.visual_consent.WhatsAppMaterialsService._require_owner", AsyncMock())
    session = SimpleNamespace(scalar=AsyncMock(return_value=changed), execute=AsyncMock())
    ids = [uuid4() for _ in range(3)]
    result = await VisualConsentService(settings, Database(session)).set(*ids, accepted)
    assert result == {"accepted": accepted, "provider_enabled": False}
    assert session.execute.await_count == int(changed is not None)
    if changed:
        assert session.execute.await_args.args[1]["action"] == (
            "visual.ai_accepted" if accepted else "visual.ai_revoked"
        )


async def test_routes_delegate_authenticated_owner_and_preserve_result(monkeypatch):
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    status = AsyncMock(return_value={"accepted": False, "provider_enabled": True})
    update = AsyncMock(return_value={"accepted": True, "provider_enabled": True})
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
