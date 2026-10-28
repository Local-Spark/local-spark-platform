"""Agreement proof is visible only within the intended tenant and role."""

from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db.session import Database
from app.services.auth import AuthError
from app.services.service_agreement import SERVICE_AGREEMENT_HASH, SERVICE_AGREEMENT_VERSION, service_agreement_allowed
from app.tests.integration.test_editorial_proposals import _business

pytestmark = pytest.mark.integration


async def test_agreement_owner_and_worker_are_scoped_to_business_and_tenant(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    other_business = uuid4()
    async with admin.begin() as session:
        await session.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Other','UTC')"),
            {"id": other_business, "tenant": seeded["t2"]},
        )
        for t, b, a in ((tenant, business, actor), (seeded["t2"], other_business, seeded["a2"])):
            await session.execute(
                text("""INSERT INTO service_agreement_acceptances
              (tenant_id,business_id,actor_id,version,notice_hash) VALUES(:tenant,:business,:actor,:version,:hash)"""),
                {
                    "tenant": t,
                    "business": b,
                    "actor": a,
                    "version": SERVICE_AGREEMENT_VERSION,
                    "hash": SERVICE_AGREEMENT_HASH,
                },
            )
    cfg = settings.model_copy(update={"service_agreement_required": True})
    async with database.transaction(tenant, actor) as session:
        assert await service_agreement_allowed(session, cfg, tenant, business)
        assert not await service_agreement_allowed(session, cfg, seeded["t2"], other_business)
    async with database.transaction(tenant, seeded["viewer"]) as session:
        assert not await service_agreement_allowed(session, cfg, tenant, business)
    with pytest.raises(DBAPIError):
        async with database.transaction(tenant, actor) as session:
            await session.execute(
                text("""INSERT INTO service_agreement_acceptances
              (tenant_id,business_id,actor_id,version,notice_hash) VALUES(:tenant,:business,:actor,'new',:hash)"""),
                {"tenant": seeded["t2"], "business": other_business, "actor": actor, "hash": SERVICE_AGREEMENT_HASH},
            )
    worker = Database(cfg, correlator=True)
    try:
        async with worker.sessions() as session, session.begin():
            assert await session.scalar(text("SELECT count(*) FROM service_agreement_acceptances")) == 0
            assert await service_agreement_allowed(session, cfg, tenant, business, worker=True)
            assert not await service_agreement_allowed(session, cfg, tenant, other_business, worker=True)
            with pytest.raises(AuthError, match="SERVICE_AGREEMENT_TENANT_MISMATCH"):
                await service_agreement_allowed(session, cfg, seeded["t2"], other_business, worker=True)
        with pytest.raises(DBAPIError):
            async with worker.sessions() as session, session.begin():
                await session.execute(text("SELECT actor_id FROM service_agreement_acceptances"))
    finally:
        await worker.close()
