"""Final destination checks refuse simulated delivery after access or channel changes."""

from contextlib import asynccontextmanager

import pytest
from sqlalchemy import text

from app.services.content_deliveries import ContentDeliveryService
from app.tests.integration.test_content_delivery import _candidate_case

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("condition", ["no_authority", "unverified_phone", "invalid_phone", "mismatched_destination"])
async def test_delivery_requires_processing_authority_and_a_verified_valid_phone(admin, seeded, settings, condition):
    cfg, app_db, worker_db, tenant, business, _, _, event, _ = await _candidate_case(
        admin, seeded, settings, need_preview=False
    )
    try:
        async with admin.begin() as connection:
            if condition == "no_authority":
                await connection.execute(
                    text("""UPDATE whatsapp_processing_consents SET revoked_at=now()
                      WHERE tenant_id=:tenant AND business_id=:business"""),
                    {"tenant": tenant, "business": business},
                )
            elif condition == "unverified_phone":
                await connection.execute(
                    text("""UPDATE business_profiles SET phone_verified=false
                      WHERE tenant_id=:tenant AND business_id=:business"""),
                    {"tenant": tenant, "business": business},
                )
            elif condition == "invalid_phone":
                await connection.execute(
                    text("""UPDATE business_profiles SET phone='invalid',phone_verified=true
                      WHERE tenant_id=:tenant AND business_id=:business"""),
                    {"tenant": tenant, "business": business},
                )
            else:
                await connection.execute(
                    text("""UPDATE business_profiles SET phone='+5511888888888',phone_verified=true
                      WHERE tenant_id=:tenant AND business_id=:business"""),
                    {"tenant": tenant, "business": business},
                )
        assert await ContentDeliveryService(cfg, app_db, worker_db).record(event) is None
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM content_deliveries")) == 0
    finally:
        await worker_db.close()
        await app_db.close()


@pytest.mark.parametrize("condition", ["owner_revoked", "channel_disconnected", "channel_actor_changed"])
async def test_delivery_rechecks_profile_and_channel_after_reading_the_source(
    admin, seeded, settings, monkeypatch, condition
):
    cfg, app_db, worker_db, tenant, business, actor, _, event, _ = await _candidate_case(
        admin, seeded, settings, need_preview=False
    )
    original_transaction = app_db.transaction
    changed = False

    @asynccontextmanager
    async def transaction(*args):
        async with original_transaction(*args) as session:
            original_execute = session.execute

            async def execute(statement, params=None):
                nonlocal changed
                # The source event and processing authority have already been
                # read. Concurrent access/channel changes must still stop the
                # final destination check, even for a clarification message.
                if not changed and "SELECT phone,phone_verified FROM business_profiles" in str(statement):
                    changed = True
                    async with admin.begin() as connection:
                        if condition == "owner_revoked":
                            await connection.execute(
                                text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"),
                                {"tenant": tenant, "actor": actor},
                            )
                        elif condition == "channel_disconnected":
                            await connection.execute(
                                text("""UPDATE whatsapp_channel_links SET active=false
                                  WHERE tenant_id=:tenant AND business_id=:business"""),
                                {"tenant": tenant, "business": business},
                            )
                        else:
                            await connection.execute(
                                text("""UPDATE whatsapp_channel_links SET actor_id=:other
                                  WHERE tenant_id=:tenant AND business_id=:business"""),
                                {"tenant": tenant, "business": business, "other": seeded["viewer"]},
                            )
                return await original_execute(statement, params)

            monkeypatch.setattr(session, "execute", execute)
            yield session

    monkeypatch.setattr(app_db, "transaction", transaction)
    try:
        assert await ContentDeliveryService(cfg, app_db, worker_db).record(event) is None
        assert changed
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM content_deliveries")) == 0
    finally:
        await worker_db.close()
        await app_db.close()
