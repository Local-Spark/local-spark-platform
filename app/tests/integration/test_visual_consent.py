"""Visual consent is independently owned, audited, and isolated per tenant."""

import pytest
from sqlalchemy import text

from app.services.jev_consent import JevConsentService
from app.tests.integration.test_editorial_proposals import _business
from app.tests.unit.test_core import access_token

pytestmark = pytest.mark.integration


async def test_visual_consent_requires_owner_and_does_not_change_other_consents(admin, api, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    base = f"/api/v1/organizations/{tenant}/businesses/{business}/media-previews/visual-consent"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    viewer = {"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"}
    other = {"Authorization": f"Bearer {access_token(settings, seeded['a2'])}"}
    assert (await api.get(base, headers=owner)).json() == {"accepted": False, "provider_enabled": False}
    assert (await api.get(base, headers=viewer)).status_code == 403
    assert (await api.put(base, headers=viewer, json={"accepted": True})).status_code == 403
    assert (await api.get(base, headers=other)).status_code in {403, 404}
    assert (await api.put(base, headers=owner, json={"accepted": "true"})).status_code == 422
    # Giving or withdrawing visual consent never modifies the separately stored Jev permission.
    await JevConsentService(settings, database).set(tenant, business, actor, True)
    assert (await api.put(base, headers=owner, json={"accepted": False})).json()["accepted"] is False
    assert (await api.put(base, headers=owner, json={"accepted": True})).json()["accepted"] is True
    assert (await api.put(base, headers=owner, json={"accepted": True})).json()["accepted"] is True
    assert (await api.put(base, headers=owner, json={"accepted": False})).json()["accepted"] is False
    assert (await api.put(base, headers=owner, json={"accepted": False})).json()["accepted"] is False
    assert (await JevConsentService(settings, database).status(tenant, business, actor))["accepted"] is True
    async with admin.connect() as conn:
        events = (
            (
                await conn.execute(
                    text("""SELECT action FROM audit_events WHERE tenant_id=:tenant
          AND action IN ('visual.ai_accepted','visual.ai_revoked') ORDER BY created_at"""),
                    {"tenant": tenant},
                )
            )
            .scalars()
            .all()
        )
        assert events == ["visual.ai_accepted", "visual.ai_revoked"]
    async with database.transaction(seeded["t2"], seeded["a2"]) as session:
        assert await session.scalar(text("SELECT count(*) FROM visual_ai_consents")) == 0
