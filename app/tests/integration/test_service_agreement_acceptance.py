"""Explicit agreement acceptance; no external provider is called."""

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.services.auth import AuthError
from app.services.jev_consent import JevConsentService
from app.services.service_agreement import SERVICE_AGREEMENT_HASH, SERVICE_AGREEMENT_VERSION, ServiceAgreementService
from app.services.visual_consent_gate import VisualConsentGate
from app.services.whatsapp_materials import WhatsAppMaterialsService
from app.tests.integration.test_editorial_proposals import _business
from app.tests.integration.test_visual_attempts import preview

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("operation", ["jev", "audio", "whatsapp_accept", "whatsapp_revoke"])
async def test_legacy_mutations_wait_for_business_agreement_transaction(
    admin, database, seeded, settings, monkeypatch, operation
):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    agreement = ServiceAgreementService(settings, database)
    entered, resume = asyncio.Event(), asyncio.Event()
    initialize = agreement._initialize_absent_consents

    async def paused_initialize(session, params, operation_id):
        entered.set()
        await resume.wait()
        await initialize(session, params, operation_id)

    monkeypatch.setattr(agreement, "_initialize_absent_consents", paused_initialize)
    acceptance = asyncio.create_task(
        agreement.accept(tenant, business, actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH)
    )
    mutation = None
    try:
        await asyncio.wait_for(entered.wait(), 5)
        whatsapp = WhatsAppMaterialsService(settings, database)
        if operation == "jev":
            call = JevConsentService(settings, database).set(tenant, business, actor, False)
        elif operation == "audio":
            call = whatsapp.set_audio_consent(tenant, business, actor, False)
        elif operation == "whatsapp_accept":
            call = whatsapp.accept_consent(tenant, business, actor)
        else:
            call = whatsapp.revoke_consent(tenant, business, actor)
        mutation = asyncio.create_task(call)
        done, _ = await asyncio.wait({mutation}, timeout=0.2)
        assert not done, "legacy mutation must not pass the in-progress business acceptance"
    finally:
        resume.set()
        await asyncio.wait_for(acceptance, 5)
        if mutation is not None:
            await asyncio.wait_for(mutation, 5)


async def test_acceptance_is_explicit_idempotent_scoped_and_preserves_later_withdrawal(
    admin, database, seeded, settings
):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    service = ServiceAgreementService(settings, database)
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_VERSION_CONFLICT"):
        await service.accept(tenant, business, actor, SERVICE_AGREEMENT_VERSION, "0" * 64)
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_VERSION_CONFLICT"):
        await service.accept(tenant, business, actor, "other-version", SERVICE_AGREEMENT_HASH)
    before = await service.status(tenant, business, actor)
    assert not before["accepted"] and before["access_active"]
    one, two = await asyncio.gather(
        *(service.accept(tenant, business, actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH) for _ in range(2))
    )
    assert one["accepted"] and two["accepted"] and not one["review_required"]
    assert one["accepted_at"] == two["accepted_at"]
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM service_agreement_acceptances")) == 1
        assert (
            await connection.scalar(
                text("""SELECT count(*) FROM audit_events WHERE tenant_id=:tenant
          AND resource_id=:business AND action LIKE 'service.agreement.accepted:%'"""),
                {"tenant": tenant, "business": business},
            )
            == 1
        )
        assert await connection.scalar(
            text("""SELECT action FROM audit_events WHERE tenant_id=:tenant
          AND resource_id=:business AND action LIKE 'service.agreement.accepted:%'"""),
            {"tenant": tenant, "business": business},
        ) == (f"service.agreement.accepted:{SERVICE_AGREEMENT_VERSION}:{SERVICE_AGREEMENT_HASH}")
    await JevConsentService(settings, database).set(tenant, business, actor, False)
    replay = await service.accept(tenant, business, actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH)
    assert replay["accepted"] and replay["review_required"]
    assert not (await JevConsentService(settings, database).status(tenant, business, actor))["accepted"]
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await service.status(tenant, business, seeded["viewer"])


async def test_preexisting_withdrawal_is_not_silently_reactivated(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    jev = JevConsentService(settings, database)
    await jev.set(tenant, business, actor, True)
    await jev.set(tenant, business, actor, False)
    result = await ServiceAgreementService(settings, database).accept(
        tenant, business, actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH
    )
    assert result["accepted"] and result["review_required"]
    assert not (await jev.status(tenant, business, actor))["accepted"]


async def test_pending_visual_withdrawal_prevents_acceptance(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    gate = VisualConsentGate(database)
    await gate.enable(tenant, business, actor)
    operation = uuid4()
    await gate.admit(tenant, business, actor, await preview(admin, tenant, business, actor), operation, 1)
    assert await gate.request_withdrawal(tenant, business, actor) == "revocation_pending"
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_CHANGE_PENDING"):
        await ServiceAgreementService(settings, database).accept(
            tenant, business, actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH
        )
    assert not (await ServiceAgreementService(settings, database).status(tenant, business, actor))["accepted"]


async def test_terms_may_be_accepted_without_a_plan_but_do_not_activate_access(admin, database, seeded, settings):
    tenant, actor, business = seeded["t1"], seeded["a1"], uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Test','UTC')"),
            {"id": business, "tenant": tenant},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles
          (tenant_id,business_id,category,city,description,phone,brand_color)
          VALUES(:tenant,:business,'Food','Rio','Test','+5511999999999','#6557ed')"""),
            {"tenant": tenant, "business": business},
        )
    status = await ServiceAgreementService(settings, database).accept(
        tenant, business, actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH
    )
    assert status["accepted"] and not status["access_active"]


async def test_each_account_must_accept_its_business_and_tampered_version_fails_closed(
    admin, database, seeded, settings
):
    tenant, actor = seeded["t1"], seeded["a1"]
    other_tenant, other_actor = seeded["t2"], seeded["a2"]
    first, second = await _business(admin, seeded), uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Other','UTC')"),
            {"id": second, "tenant": other_tenant},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles
          (tenant_id,business_id,category,city,description,phone,brand_color)
          VALUES(:tenant,:business,'Food','Rio','Test','+5511999999999','#6557ed')"""),
            {"tenant": other_tenant, "business": second},
        )
    service = ServiceAgreementService(settings, database)
    assert (await service.accept(tenant, first, actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH))["accepted"]
    assert not (await service.status(other_tenant, second, other_actor))["accepted"]
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO service_agreement_acceptances
          (tenant_id,business_id,actor_id,version,notice_hash) VALUES(:tenant,:business,:actor,:version,:hash)"""),
            {
                "tenant": other_tenant,
                "business": second,
                "actor": other_actor,
                "version": SERVICE_AGREEMENT_VERSION,
                "hash": "0" * 64,
            },
        )
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_VERSION_CONFLICT"):
        await service.status(other_tenant, second, other_actor)
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_VERSION_CONFLICT"):
        await service.accept(other_tenant, second, other_actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH)
