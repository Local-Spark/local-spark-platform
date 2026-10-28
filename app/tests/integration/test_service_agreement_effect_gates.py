"""The required service agreement is scoped to each business and checked by real DB roles."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.db.session import Database
from app.schemas.editorial_proposals import ProposalRequest
from app.services.auth import AuthError
from app.services.editorial_dispatch import claim_proposals
from app.services.editorial_proposals import EditorialProposalService
from app.services.service_agreement import SERVICE_AGREEMENT_HASH, SERVICE_AGREEMENT_VERSION
from app.services.whatsapp_processing import MaterialProcessor
from app.tests.integration.test_editorial_briefings import _enable
from app.tests.integration.test_editorial_proposals import _business, _fact

pytestmark = pytest.mark.integration


async def test_agreement_is_per_business_and_rechecked_before_paid_editorial_effect(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    other_business = uuid4()
    await _enable(admin, tenant, business, actor)
    await _fact(admin, tenant, business, actor)
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Other','UTC')"),
            {"id": other_business, "tenant": tenant},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles
              (tenant_id,business_id,category,city,description,phone,phone_verified,brand_color)
              VALUES(:tenant,:business,'Food','Rio','Other','+5511999999999',true,'#6557ed')"""),
            {"tenant": tenant, "business": other_business},
        )
        await connection.execute(
            text("UPDATE business_profiles SET phone_verified=true WHERE tenant_id=:tenant AND business_id=:business"),
            {"tenant": tenant, "business": business},
        )
    cfg = settings.model_copy(update={"service_agreement_required": True, "editorial_ai_mode": "openai"})
    request = ProposalRequest(operation_id=uuid4())
    owner = EditorialProposalService(cfg, database)
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_REQUIRED"):
        await owner.request(tenant, business, actor, request)
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO service_agreement_acceptances(tenant_id,business_id,actor_id,version,notice_hash)
              VALUES(:tenant,:business,:actor,:version,:hash)"""),
            {
                "tenant": tenant,
                "business": business,
                "actor": actor,
                "version": SERVICE_AGREEMENT_VERSION,
                "hash": SERVICE_AGREEMENT_HASH,
            },
        )
    proposal = await owner.request(tenant, business, actor, request)
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_REQUIRED"):
        await owner.request(tenant, other_business, actor, ProposalRequest(operation_id=uuid4()))

    worker = Database(cfg, correlator=True)
    provider = SimpleNamespace(propose=AsyncMock())
    try:
        # Real role checks the material gate, scoped to the accepted business.
        processor = MaterialProcessor(cfg, worker, Mock(), Mock())
        now = datetime.now(UTC)
        inbound = {
            "tenant_id": tenant,
            "business_id": business,
            "sender_hash": "b" * 64,
            "created_at": now,
            "expires_at": now + timedelta(hours=1),
        }
        async with worker.sessions() as session, session.begin():
            assert await processor._eligible(session, inbound)
            assert not await processor._eligible(session, {**inbound, "business_id": other_business})

        claims = await claim_proposals(worker, uuid4())
        assert any(claim.id == proposal.id for claim in claims)
        async with admin.begin() as connection:
            await connection.execute(
                text("DELETE FROM service_agreement_acceptances WHERE tenant_id=:tenant AND business_id=:business"),
                {"tenant": tenant, "business": business},
            )
        assert (
            await EditorialProposalService(cfg, worker, provider, owner_database=database).run(proposal.id)
            == "rejected"
        )
        provider.propose.assert_not_awaited()
        async with admin.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT error_code FROM editorial_proposals WHERE id=:id"), {"id": proposal.id}
                )
                == "SERVICE_AGREEMENT_REQUIRED"
            )
    finally:
        await worker.close()
