"""Owner-scoped point-in-time visual context capture against real PostgreSQL roles."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text

from app.db.session import Database
from app.schemas.business_catalog import CatalogUpdate
from app.services.auth import AuthError
from app.services.business_catalog import BusinessCatalogService
from app.services.creative_catalog_resolution import CatalogIntent
from app.services.editorial_dispatch import claim_proposals, finish_proposal_dispatch
from app.services.editorial_proposals import EditorialProposalService
from app.services.visual_consent import VisualConsentService
from app.services.visual_context import VisualContextService
from app.tests.integration.test_brand_kits import _overrides
from app.tests.integration.test_business_catalog import _payload
from app.tests.integration.test_editorial_briefings import _enable
from app.tests.integration.test_editorial_proposals import _asset, _business
from app.workflows.content_activities import ContentCandidateActivities

pytestmark = pytest.mark.integration


async def test_real_capture_revalidates_owner_consent_and_kit(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr(key), "visual_ai_mode": "openai"})
    source = await _asset(admin, tenant, business, key, body="Crie uma imagem do croissant")
    catalog = _payload()
    await BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
    async with admin.begin() as conn:
        params = {"tenant": tenant, "business": business, "actor": actor, "operation": uuid4()}
        await conn.execute(
            text("""INSERT INTO business_brand_kit_heads(tenant_id,business_id,version,confirmed_version)
          VALUES(:tenant,:business,1,1)"""),
            params,
        )
        await conn.execute(
            text("""INSERT INTO business_brand_kit_versions
          (tenant_id,business_id,version,operation_id,actor_id,request_hash,state,document)
              VALUES(:tenant,:business,1,:operation,:actor,:hash,'confirmed',CAST(:document AS jsonb))"""),
            {
                **params,
                "hash": "a" * 64,
                "document": json.dumps({"kit_id": "cafe-pausas", "kit_version": 1, "overrides": _overrides()}),
            },
        )
    interpreter = SimpleNamespace(
        interpret=AsyncMock(
            return_value=CatalogIntent("selected", UUID(catalog["offerings"][0]["id"]), "content_request", "photo")
        )
    )
    worker = Database(cfg, correlator=True)
    try:
        activity = ContentCandidateActivities(cfg, database, worker, interpreter=interpreter)
        proposal_id = UUID(await activity.request_candidate_proposal(str(source)))
        claims = await claim_proposals(worker, uuid4())
        await finish_proposal_dispatch(worker, claims[0], True)
        assert await EditorialProposalService(cfg, worker, owner_database=database).run(proposal_id) == "completed"
        consent = VisualConsentService(cfg, database)
        capture = VisualContextService(cfg, database)
        with pytest.raises(AuthError, match="VISUAL_AI_CONSENT_REQUIRED"):
            await capture.capture(tenant, business, actor, proposal_id, candidate=True)
        await consent.set(tenant, business, actor, True)
        result = await capture.capture(tenant, business, actor, proposal_id, candidate=True)
        assert result.proposal_id == proposal_id and result.format == "photo"
        with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
            await capture.capture(tenant, business, seeded["viewer"], proposal_id, candidate=True)
        async with database.transaction(seeded["t2"], seeded["a2"]) as session:
            assert await session.scalar(text("SELECT count(*) FROM visual_ai_consents")) == 0
        await consent.set(tenant, business, actor, False)
        with pytest.raises(AuthError, match="VISUAL_AI_CONSENT_REQUIRED"):
            await capture.capture(tenant, business, actor, proposal_id, candidate=True)
        await consent.set(tenant, business, actor, True)
        async with admin.begin() as conn:
            await conn.execute(
                text("""UPDATE business_brand_kit_heads SET confirmed_version=NULL
              WHERE tenant_id=:tenant AND business_id=:business"""),
                {"tenant": tenant, "business": business},
            )
        with pytest.raises(AuthError, match="VISUAL_KIT_CHANGED"):
            await capture.capture(tenant, business, actor, proposal_id, candidate=True)
    finally:
        await worker.close()
