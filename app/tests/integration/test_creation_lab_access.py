"""Laboratory discovery uses the restricted runtime and preserves staff revocation."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import text

from app.services.auth import AuthError
from app.services.business import AccessDenied
from app.services.creation_lab_access import lab_businesses

pytestmark = pytest.mark.integration


async def test_lab_discovery_exclusive_operator_and_revocation(admin, database, seeded, settings):
    operator, other = seeded["a1"], seeded["a2"]
    settings.creation_lab_actor_id = operator
    ids = [uuid4(), uuid4()]
    async with admin.begin() as session:
        for actor in (operator, other):
            await session.execute(text("INSERT INTO platform_staff(actor_id) VALUES(:actor)"), {"actor": actor})
        for business, tenant in zip(ids, (seeded["t1"], seeded["t2"]), strict=True):
            await session.execute(
                text("""INSERT INTO businesses(id,tenant_id,name,timezone)
                  VALUES(:id,:tenant,'Lab discovery','America/Sao_Paulo')"""),
                {"id": business, "tenant": tenant},
            )
    async with database.transaction(UUID(int=0), operator) as session:
        page = await lab_businesses(session, settings, operator, "Lab discovery", 1, None)
        assert page["items"][0]["id"] == min(ids)
        second = await lab_businesses(session, settings, operator, "Lab discovery", 1, UUID(page["next_cursor"]))
        assert second["items"][0]["id"] == max(ids)
        assert second["next_cursor"] is None
    async with database.transaction(UUID(int=0), other) as session:
        with pytest.raises(AuthError, match="CREATION_LAB_ACCESS_DENIED"):
            await lab_businesses(session, settings, other, "", 20, None)
    async with database.transaction(UUID(int=0), seeded["viewer"]) as session:
        with pytest.raises(AuthError, match="CREATION_LAB_ACCESS_DENIED"):
            await lab_businesses(session, settings, seeded["viewer"], "", 20, None)
    async with admin.begin() as session:
        assert (
            await session.scalar(
                text("SELECT count(*) FROM platform_audit WHERE action='admin.creation_lab.businesses.read'")
            )
            == 2
        )
        await session.execute(text("UPDATE platform_staff SET active=false WHERE actor_id=:id"), {"id": operator})
    async with database.transaction(UUID(int=0), operator) as session:
        with pytest.raises(AccessDenied):
            await lab_businesses(session, settings, operator, "", 20, None)
