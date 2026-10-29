"""Restricted PostgreSQL proves the financial-expiry exception stays scoped."""

from uuid import uuid4

import pytest
from sqlalchemy import text

from app.services.billing import revoke_sponsorship
from app.services.editorial_consent_scope import VisualRunScope, admitted_visual_run
from app.services.visual_consent_gate import VisualConsentGate
from app.services.visual_continuity import admitted_or_preserved
from app.tests.integration.test_editorial_proposals import _business
from app.tests.integration.test_visual_attempts import preview as create_preview

pytestmark = pytest.mark.integration


async def _case(admin, database, seeded, generation_mode="visual_fake"):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    preview, source, operation = await create_preview(admin, tenant, business, actor), uuid4(), uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("""UPDATE media_previews SET source_asset_id=:source,generation_mode=:generation_mode,
              visual_fingerprint=:fingerprint,expires_at=now()-interval '1 day' WHERE id=:preview"""),
            {"source": source, "preview": preview, "fingerprint": "a" * 64, "generation_mode": generation_mode},
        )
        await connection.execute(
            text("""UPDATE billing_sponsorships SET starts_at=now()-interval '8 months',
              ends_at=now()-interval '2 months' WHERE tenant_id=:tenant"""),
            {"tenant": tenant},
        )
    gate = VisualConsentGate(database)
    await gate.enable(tenant, business, actor)
    assert await gate.admit(tenant, business, actor, preview, operation, 1)
    return tenant, business, actor, source, preview, operation


@pytest.mark.parametrize("change", ["expired", "blocked", "revoked", "wrong_fence", "local", "wrong_source"])
@pytest.mark.parametrize("generation_mode", ["visual_fake", "visual_ai"])
async def test_only_admitted_visual_creation_continues_after_financial_expiry(
    admin, database, seeded, change, generation_mode
):
    tenant, business, actor, source, preview, operation = await _case(admin, database, seeded, generation_mode)
    async with admin.begin() as connection:
        if change == "blocked":
            await connection.execute(
                text("INSERT INTO billing_accounts(tenant_id,livemode,blocked) VALUES(:tenant,false,true)"),
                {"tenant": tenant},
            )
        elif change == "revoked":
            await connection.execute(
                text("UPDATE billing_sponsorships SET revoked_at=clock_timestamp() WHERE tenant_id=:tenant"),
                {"tenant": tenant},
            )
        elif change == "local":
            await connection.execute(
                text("UPDATE media_previews SET generation_mode='local',visual_fingerprint=NULL WHERE id=:preview"),
                {"preview": preview},
            )
    scope = VisualRunScope(tenant, business, actor, operation, 2 if change == "wrong_fence" else 1)
    async with database.transaction(tenant, actor) as session:
        with admitted_visual_run(scope):
            assert await admitted_or_preserved(
                session, tenant, business, actor, uuid4() if change == "wrong_source" else source, None
            ) is (change == "expired")
        assert not await admitted_or_preserved(session, tenant, business, actor, source, None)


@pytest.mark.parametrize("change", ["expired", "in_flight", "rendering", "local", "wrong_source", "revoked_owner"])
@pytest.mark.parametrize("generation_mode", ["visual_fake", "visual_ai"])
async def test_historical_review_requires_a_completed_scoped_proof(admin, database, seeded, change, generation_mode):
    tenant, business, actor, source, preview, operation = await _case(admin, database, seeded, generation_mode)
    async with admin.begin() as connection:
        await connection.execute(
            text("""UPDATE media_previews SET state='completed',sha256=:sha,object_key='private/preserved'
              WHERE id=:preview"""),
            {"preview": preview, "sha": "b" * 64},
        )
        await connection.execute(
            text("UPDATE visual_consent_runs SET state='finished',finished_at=now() WHERE operation_id=:operation"),
            {"operation": operation},
        )
        if change == "in_flight":
            await connection.execute(
                text("UPDATE visual_consent_runs SET state='in_flight' WHERE operation_id=:operation"),
                {"operation": operation},
            )
        elif change == "rendering":
            await connection.execute(
                text("UPDATE media_previews SET state='rendering' WHERE id=:preview"), {"preview": preview}
            )
        elif change == "local":
            await connection.execute(
                text("UPDATE media_previews SET generation_mode='local',visual_fingerprint=NULL WHERE id=:preview"),
                {"preview": preview},
            )
        elif change == "revoked_owner":
            await connection.execute(
                text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"),
                {"tenant": tenant, "actor": actor},
            )
    async with database.transaction(tenant, actor) as session:
        assert await admitted_or_preserved(
            session, tenant, business, actor, uuid4() if change == "wrong_source" else source, preview
        ) is (change == "expired")
    async with database.transaction(seeded["t2"], seeded["a2"]) as session:
        assert not await admitted_or_preserved(session, tenant, business, actor, source, preview)


async def test_revocation_transaction_started_before_run_still_stops_continuation(admin, database, seeded):
    tenant, staff = seeded["t1"], seeded["a2"]
    async with admin.begin() as connection:
        await connection.execute(text("INSERT INTO platform_staff(actor_id) VALUES(:actor)"), {"actor": staff})
    async with database.transaction(tenant, staff) as session:
        before_run = await session.scalar(text("SELECT transaction_timestamp()"))
        tenant, business, actor, source, preview, operation = await _case(admin, database, seeded)
        async with admin.begin() as connection:
            created = await connection.scalar(
                text("SELECT created_at FROM visual_consent_runs WHERE operation_id=:operation"),
                {"operation": operation},
            )
        assert before_run < created
        await revoke_sponsorship(session, tenant, staff)
    async with admin.begin() as connection:
        revoked = await connection.scalar(
            text("SELECT revoked_at FROM billing_sponsorships WHERE tenant_id=:tenant"), {"tenant": tenant}
        )
    assert created < revoked
    async with database.transaction(tenant, actor) as session:
        with admitted_visual_run(VisualRunScope(tenant, business, actor, operation, 1)):
            assert not await admitted_or_preserved(session, tenant, business, actor, source, None)
