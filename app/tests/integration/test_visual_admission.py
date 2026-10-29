"""Restricted PostgreSQL admission serializes source and commercial changes."""

import asyncio
import json
from dataclasses import replace
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
from app.services.billing import lock_commercial_change, revoke_sponsorship
from app.services.business_catalog import BusinessCatalogService
from app.services.creative_catalog_resolution import CatalogIntent
from app.services.editorial_dispatch import claim_proposals, finish_proposal_dispatch
from app.services.editorial_proposals import EditorialProposalService
from app.services.visual_admission import VisualAdmissionChecks
from app.services.visual_consent import VisualConsentService
from app.services.visual_consent_gate import VisualConsentGate
from app.services.visual_context import VisualContextService
from app.tests.integration.test_brand_kits import _overrides
from app.tests.integration.test_business_catalog import _payload
from app.tests.integration.test_editorial_briefings import _enable
from app.tests.integration.test_editorial_proposals import _asset, _business
from app.workflows.content_activities import ContentCandidateActivities

pytestmark = pytest.mark.integration


async def _ready(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr(key), "visual_ai_mode": "fake"})
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
        proposal = UUID(await activity.request_candidate_proposal(str(source)))
        claim = (await claim_proposals(worker, uuid4()))[0]
        await finish_proposal_dispatch(worker, claim, True)
        assert await EditorialProposalService(cfg, worker, owner_database=database).run(proposal) == "completed"
        await VisualConsentService(cfg, database).set(tenant, business, actor, True)
        context = await VisualContextService(cfg, database).capture(tenant, business, actor, proposal, candidate=True)
        return tenant, business, actor, catalog, VisualAdmissionChecks(cfg, proposal, context.fingerprint, True)
    finally:
        await worker.close()


async def test_admission_revalidates_sources_and_defers_concurrent_change(
    admin, database, seeded, settings, monkeypatch
):
    tenant, business, actor, catalog, admission = await _ready(admin, database, seeded, settings)
    gate = VisualConsentGate(database)
    preview, operation = uuid4(), uuid4()
    with pytest.raises(AuthError, match="PREVIEW_INPUT_CHANGED"):
        await gate.admit(
            tenant, business, actor, preview, operation, 1, admission=replace(admission, fingerprint="0" * 64)
        )
    entered, release = asyncio.Event(), asyncio.Event()
    original = VisualAdmissionChecks.validate

    async def pause(self, *args):
        await original(self, *args)
        entered.set()
        await release.wait()

    monkeypatch.setattr(VisualAdmissionChecks, "validate", pause)
    admission_task = asyncio.create_task(
        gate.admit(tenant, business, actor, preview, operation, 1, admission=admission)
    )
    change = None
    try:
        await asyncio.wait_for(entered.wait(), 5)
        catalog["expected_version"], catalog["operation_id"] = 1, str(uuid4())
        catalog["offerings"][0]["name"] = "Novo croissant"
        change = asyncio.create_task(
            BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
        )
        # The writer cannot apply while the admission is holding its gate.
        async with database.transaction(tenant, actor) as session:
            assert await session.scalar(text("SELECT count(*) FROM visual_consent_runs")) == 0
            before_insert = await session.scalar(text("SELECT clock_timestamp()"))
    finally:
        release.set()
    assert await asyncio.wait_for(admission_task, 5) is True
    assert change is not None
    pending = await asyncio.wait_for(change, 5)
    assert pending.version == 1 and pending.pending_change is not None
    assert not await gate.admit(tenant, business, actor, preview, operation, 2, admission=admission)
    with pytest.raises(AuthError, match="VISUAL_CHANGE_PENDING"):
        await gate.admit(tenant, business, actor, uuid4(), uuid4(), 1, admission=admission)
    async with database.transaction(tenant, actor) as session:
        assert await session.scalar(text("SELECT count(*) FROM visual_consent_runs WHERE state='in_flight'")) == 1
        assert await session.scalar(text("SELECT created_at FROM visual_consent_runs")) >= before_insert
        assert (
            await session.scalar(text("SELECT count(*) FROM audit_events WHERE action='visual.creation_admitted'")) == 1
        )
    async with database.transaction(seeded["t2"], seeded["a2"]) as session:
        assert await session.scalar(text("SELECT count(*) FROM visual_consent_runs")) == 0


async def test_commercial_change_before_admission_prevents_a_new_run(admin, database, seeded, settings, monkeypatch):
    tenant, business, actor, _, admission = await _ready(admin, database, seeded, settings)
    staff = seeded["a2"]
    async with admin.begin() as connection:
        await connection.execute(text("INSERT INTO platform_staff(actor_id) VALUES(:actor)"), {"actor": staff})
    entered = asyncio.Event()
    original = VisualAdmissionChecks.validate

    async def observe(self, *args):
        entered.set()
        await original(self, *args)

    monkeypatch.setattr(VisualAdmissionChecks, "validate", observe)
    task = None
    async with database.transaction(tenant, staff) as session:
        await lock_commercial_change(session, tenant)
        task = asyncio.create_task(
            VisualConsentGate(database).admit(tenant, business, actor, uuid4(), uuid4(), 1, admission=admission)
        )
        await asyncio.wait_for(entered.wait(), 5)
        assert not task.done()
        await revoke_sponsorship(session, tenant, staff)
    with pytest.raises(AuthError, match="PLAN_REQUIRED"):
        await asyncio.wait_for(task, 5)
    async with database.transaction(tenant, actor) as session:
        assert await session.scalar(text("SELECT count(*) FROM visual_consent_runs")) == 0


async def test_plan_expiring_while_admission_waits_for_commercial_lock_is_not_admitted(
    admin, database, seeded, settings, monkeypatch
):
    tenant, business, actor, _, admission = await _ready(admin, database, seeded, settings)
    staff = seeded["a2"]
    async with admin.begin() as connection:
        await connection.execute(text("INSERT INTO platform_staff(actor_id) VALUES(:actor)"), {"actor": staff})
    entered = asyncio.Event()
    original = VisualAdmissionChecks.validate
    frozen_at = None

    async def observe(self, session, *args):
        nonlocal frozen_at
        frozen_at = await session.scalar(text("SELECT transaction_timestamp()"))
        entered.set()
        await original(self, session, *args)

    monkeypatch.setattr(VisualAdmissionChecks, "validate", observe)
    task = None
    async with database.transaction(tenant, staff) as session:
        await lock_commercial_change(session, tenant)
        task = asyncio.create_task(
            VisualConsentGate(database).admit(tenant, business, actor, uuid4(), uuid4(), 1, admission=admission)
        )
        await asyncio.wait_for(entered.wait(), 5)
        assert not task.done()
        async with admin.begin() as connection:
            deadline = await connection.scalar(
                text("""UPDATE billing_sponsorships SET ends_at=clock_timestamp()+interval '0.2 second'
                  WHERE tenant_id=:tenant RETURNING ends_at"""),
                {"tenant": tenant},
            )
            assert frozen_at < deadline
        # Keep the commercial lock across the deadline. Transaction time on the
        # blocked admission still precedes expiry when it resumes.
        await asyncio.sleep(0.25)
        assert await session.scalar(text("SELECT clock_timestamp()>:deadline"), {"deadline": deadline})
    with pytest.raises(AuthError, match="PLAN_REQUIRED"):
        await asyncio.wait_for(task, 5)
    async with database.transaction(tenant, actor) as session:
        assert await session.scalar(text("SELECT count(*) FROM visual_consent_runs")) == 0
