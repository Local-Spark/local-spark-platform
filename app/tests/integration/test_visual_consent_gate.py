"""Consent admission and withdrawal serialize across owner sessions."""

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.services.auth import AuthError
from app.services.visual_consent_gate import VisualConsentGate
from app.tests.integration.test_editorial_proposals import _business
from app.tests.integration.test_visual_attempts import preview as create_preview

pytestmark = pytest.mark.integration


async def test_withdrawal_waits_for_original_fences_and_blocks_new_jobs(admin, database, seeded):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    service = VisualConsentGate(database)
    first, second = uuid4(), uuid4()
    preview, other_preview = uuid4(), uuid4()
    assert await service.status(tenant, business, actor) == "revoked"
    assert await service.request_withdrawal(tenant, business, actor) == "revoked"
    assert await service.enable(tenant, business, actor) == "active"
    assert await service.enable(tenant, business, actor) == "active"
    with pytest.raises(AuthError, match="VISUAL_ADMISSION_INVALID"):
        await service.admit(tenant, business, actor, preview, first, 0)
    assert await service.admit(tenant, business, actor, preview, first, 1)
    assert not await service.admit(tenant, business, actor, preview, first, 2)
    assert await service.admit(tenant, business, actor, other_preview, second, 4)
    with pytest.raises(AuthError, match="VISUAL_ADMISSION_CONFLICT"):
        await service.admit(tenant, business, actor, preview, uuid4(), 1)
    with pytest.raises(AuthError, match="VISUAL_ADMISSION_CONFLICT"):
        await service.admit(tenant, business, actor, uuid4(), first, 1)
    assert await service.request_withdrawal(tenant, business, actor) == "revocation_pending"
    assert await service.request_withdrawal(tenant, business, actor) == "revocation_pending"
    with pytest.raises(AuthError, match="VISUAL_AI_CONSENT_REQUIRED"):
        await service.admit(tenant, business, actor, uuid4(), uuid4(), 1)
    with pytest.raises(AuthError, match="VISUAL_WITHDRAWAL_PENDING"):
        await service.enable(tenant, business, actor)
    with pytest.raises(AuthError, match="VISUAL_ADMISSION_NOT_FOUND"):
        await service.finish(tenant, business, actor, first, 2)
    assert await service.finish(tenant, business, actor, first, 1) == "revocation_pending"
    assert await service.finish(tenant, business, actor, first, 1) == "revocation_pending"
    assert await service.finish(tenant, business, actor, second, 4) == "revoked"
    assert await service.finish(tenant, business, actor, second, 4) == "revoked"
    assert await service.status(tenant, business, actor) == "revoked"
    async with admin.connect() as conn:
        assert await conn.scalar(
            text("SELECT revoked_at IS NOT NULL FROM visual_ai_consents WHERE tenant_id=:t"), {"t": tenant}
        )
    assert await service.enable(tenant, business, actor) == "active"
    assert await service.request_withdrawal(tenant, business, actor) == "revoked"


async def test_admission_and_withdrawal_cannot_both_win(admin, database, seeded):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    service = VisualConsentGate(database)
    await service.enable(tenant, business, actor)
    operation = uuid4()
    result, withdrawal = await asyncio.gather(
        service.admit(tenant, business, actor, uuid4(), operation, 1),
        service.request_withdrawal(tenant, business, actor),
        return_exceptions=True,
    )
    if result is True:
        assert withdrawal == "revocation_pending"
        assert await service.finish(tenant, business, actor, operation, 1) == "revoked"
    else:
        assert isinstance(result, AuthError) and result.code == "VISUAL_AI_CONSENT_REQUIRED"
        assert withdrawal == "revoked"
    assert await service.status(tenant, business, actor) == "revoked"
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await service.status(tenant, business, seeded["viewer"])
    async with database.transaction(seeded["t2"], seeded["a2"]) as session:
        assert await session.scalar(text("SELECT count(*) FROM visual_consent_gates")) == 0
        assert await session.scalar(text("SELECT count(*) FROM visual_consent_runs")) == 0


async def test_only_successful_admitted_preview_completed_during_withdrawal_remains_visible(admin, database, seeded):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    service = VisualConsentGate(database)
    await service.enable(tenant, business, actor)
    first = await create_preview(admin, tenant, business, actor)
    second = await create_preview(admin, tenant, business, actor)
    async with admin.begin() as conn:
        await conn.execute(
            text("""UPDATE media_previews SET generation_mode='visual_fake',
          visual_fingerprint=:fingerprint WHERE id IN (:first,:second)"""),
            {"first": first, "second": second, "fingerprint": "b" * 64},
        )
    first_operation, second_operation = uuid4(), uuid4()
    assert await service.admit(tenant, business, actor, first, first_operation, 1)
    assert await service.admit(tenant, business, actor, second, second_operation, 1)
    assert not await service.visible_after_withdrawal(tenant, business, actor, first)
    assert await service.request_withdrawal(tenant, business, actor) == "revocation_pending"
    async with admin.begin() as conn:
        await conn.execute(
            text("""UPDATE media_previews SET state='completed',sha256=:sha,object_key='previews/test.jpg',
          generation_mode='visual_fake',visual_fingerprint=:fingerprint WHERE id=:id"""),
            {"id": first, "sha": "a" * 64, "fingerprint": "b" * 64},
        )
    assert (
        await service.finish(tenant, business, actor, first_operation, 1, preview_completed=True)
        == "revocation_pending"
    )
    assert await service.finish(tenant, business, actor, second_operation, 1) == "revoked"
    assert await service.visible_after_withdrawal(tenant, business, actor, first)
    original_grant = await service.withdrawn_preview_consent(tenant, business, actor, first)
    assert original_grant is not None
    assert await service.enable(tenant, business, actor) == "active"
    assert await service.withdrawn_preview_consent(tenant, business, actor, first) == original_grant
    async with admin.begin() as conn:
        await conn.execute(text("UPDATE media_previews SET sha256=:sha WHERE id=:id"), {"id": first, "sha": "c" * 64})
    assert not await service.visible_after_withdrawal(tenant, business, actor, first)
    assert not await service.visible_after_withdrawal(tenant, business, actor, second)
    # A different owner, business or a later generation cannot reuse the evidence.
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await service.visible_after_withdrawal(tenant, business, seeded["viewer"], first)
    assert not await service.visible_after_withdrawal(tenant, business, actor, uuid4())


async def test_no_exception_for_completion_before_withdrawal_or_unverified_preview(admin, database, seeded):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    service = VisualConsentGate(database)
    await service.enable(tenant, business, actor)
    old, unverified = (
        await create_preview(admin, tenant, business, actor),
        await create_preview(admin, tenant, business, actor),
    )
    old_operation, unverified_operation = uuid4(), uuid4()
    await service.admit(tenant, business, actor, old, old_operation, 1)
    await service.finish(tenant, business, actor, old_operation, 1, preview_completed=True)
    await service.admit(tenant, business, actor, unverified, unverified_operation, 1)
    await service.request_withdrawal(tenant, business, actor)
    # Still rendering, despite the caller claiming completion: no exception.
    assert await service.finish(tenant, business, actor, unverified_operation, 1, preview_completed=True) == "revoked"
    assert not await service.visible_after_withdrawal(tenant, business, actor, old)
    assert not await service.visible_after_withdrawal(tenant, business, actor, unverified)
