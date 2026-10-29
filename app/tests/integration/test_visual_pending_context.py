"""Context changes wait for admitted work and block old queued previews."""

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.schemas.editorial_context import ContextRestore, ContextUpdate
from app.services.auth import AuthError
from app.services.editorial_context import EditorialContextService
from app.services.visual_consent_gate import VisualConsentGate
from app.tests.integration.test_editorial_proposals import _business
from app.tests.integration.test_visual_attempts import preview as create_preview

pytestmark = pytest.mark.integration


async def test_context_change_waits_for_all_runs_and_cancels_older_queue(admin, database, seeded):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    context, gate = EditorialContextService(database), VisualConsentGate(database)
    await gate.enable(tenant, business, actor)
    first_preview = await create_preview(admin, tenant, business, actor)
    queued_preview = await create_preview(admin, tenant, business, actor)
    first, second = uuid4(), uuid4()
    assert await gate.admit(tenant, business, actor, first_preview, first, 1)
    assert await gate.admit(tenant, business, actor, uuid4(), second, 1)
    payload = ContextUpdate(operation_id=uuid4(), expected_version=0, preferences={"tone": "friendly"})
    result = await context.update(tenant, business, actor, payload)
    assert result.version == 0 and result.pending_change.operation_id == payload.operation_id
    assert (await context.update(tenant, business, actor, payload)) == result
    with pytest.raises(AuthError, match="VISUAL_CHANGE_ALREADY_PENDING"):
        await context.update(tenant, business, actor, payload.model_copy(update={"operation_id": uuid4()}))
    with pytest.raises(AuthError, match="VISUAL_CHANGE_PENDING"):
        await gate.admit(tenant, business, actor, uuid4(), uuid4(), 1)
    await gate.finish(tenant, business, actor, first, 1)
    assert (await context.read(tenant, business, actor)).pending_change is not None
    await gate.finish(tenant, business, actor, second, 1)
    after = await context.read(tenant, business, actor)
    assert after.version == 1 and after.preferences.tone == "friendly" and after.pending_change is None
    assert (await context.update(tenant, business, actor, payload)).version == 1
    with pytest.raises(AuthError, match="VISUAL_CHANGE_QUEUE_CANCELLED"):
        await gate.admit(tenant, business, actor, queued_preview, uuid4(), 1)
    async with database.transaction(seeded["t2"], seeded["a2"]) as session:
        assert await session.scalar(text("SELECT count(*) FROM business_visual_pending_changes")) == 0


async def test_competing_context_changes_are_not_silently_lost(admin, database, seeded):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    context, gate = EditorialContextService(database), VisualConsentGate(database)
    await gate.enable(tenant, business, actor)
    operation = uuid4()
    await gate.admit(tenant, business, actor, uuid4(), operation, 1)
    changes = [
        ContextUpdate(operation_id=uuid4(), expected_version=0, preferences={"tone": tone})
        for tone in ("friendly", "direct")
    ]
    results = await asyncio.gather(
        *(context.update(tenant, business, actor, change) for change in changes), return_exceptions=True
    )
    assert (
        sum(isinstance(result, AuthError) and result.code == "VISUAL_CHANGE_ALREADY_PENDING" for result in results) == 1
    )
    assert sum(not isinstance(result, Exception) for result in results) == 1
    await gate.finish(tenant, business, actor, operation, 1)
    assert (await context.read(tenant, business, actor)).version == 1


async def test_expected_failure_is_visible_and_can_be_replaced(admin, database, seeded, monkeypatch):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    context, gate = EditorialContextService(database), VisualConsentGate(database)
    await gate.enable(tenant, business, actor)
    run = uuid4()
    await gate.admit(tenant, business, actor, uuid4(), run, 1)
    payload = ContextUpdate(operation_id=uuid4(), expected_version=0, preferences={"tone": "friendly"})
    await context.update(tenant, business, actor, payload)
    original = EditorialContextService.apply_pending_in_session

    async def fail(*args):
        raise AuthError("CONTEXT_VERSION_CONFLICT", 409)

    monkeypatch.setattr(EditorialContextService, "apply_pending_in_session", fail)
    assert await gate.finish(tenant, business, actor, run, 1) == "active"
    status = (await context.read(tenant, business, actor)).pending_change
    assert status.status == "failed" and status.error_code == "CONTEXT_VERSION_CONFLICT"
    with pytest.raises(AuthError, match="VISUAL_CHANGE_PENDING"):
        await gate.admit(tenant, business, actor, uuid4(), uuid4(), 1)
    monkeypatch.setattr(EditorialContextService, "apply_pending_in_session", original)
    result = await context.update(tenant, business, actor, payload.model_copy(update={"operation_id": uuid4()}))
    assert result.version == 1 and result.pending_change is None


async def test_restore_waits_and_consent_withdrawal_finishes_in_same_transaction(admin, database, seeded):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    context, gate = EditorialContextService(database), VisualConsentGate(database)
    first = ContextUpdate(operation_id=uuid4(), expected_version=0, preferences={"tone": "friendly"})
    second = ContextUpdate(operation_id=uuid4(), expected_version=1, preferences={"tone": "direct"})
    await context.update(tenant, business, actor, first)
    await context.update(tenant, business, actor, second)
    await gate.enable(tenant, business, actor)
    run = uuid4()
    await gate.admit(tenant, business, actor, uuid4(), run, 1)
    restore = ContextRestore(operation_id=uuid4(), expected_version=2, target_version=1)
    pending = await context.restore(tenant, business, actor, restore)
    assert pending.version == 2 and pending.preferences.tone == "direct"
    assert pending.pending_change.operation_id == restore.operation_id
    assert await gate.request_withdrawal(tenant, business, actor) == "revocation_pending"
    assert await gate.finish(tenant, business, actor, run, 1) == "revoked"
    restored = await context.read(tenant, business, actor)
    assert restored.version == 3 and restored.preferences.tone == "friendly"
    assert restored.pending_change is None


async def test_change_by_other_owner_fails_closed_without_impersonation(admin, database, seeded):
    tenant, actor, other = seeded["t1"], seeded["a1"], seeded["viewer"]
    business = await _business(admin, seeded)
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE memberships SET role='owner' WHERE tenant_id=:tenant AND actor_id=:actor"),
            {"tenant": tenant, "actor": other},
        )
    context, gate = EditorialContextService(database), VisualConsentGate(database)
    await gate.enable(tenant, business, actor)
    run = uuid4()
    await gate.admit(tenant, business, actor, uuid4(), run, 1)
    payload = ContextUpdate(operation_id=uuid4(), expected_version=0, preferences={"tone": "friendly"})
    assert (await context.update(tenant, business, other, payload)).pending_change is not None
    assert await gate.finish(tenant, business, actor, run, 1) == "active"
    result = await context.read(tenant, business, actor)
    assert result.version == 0 and result.pending_change.status == "failed"
    assert result.pending_change.error_code == "BUSINESS_OWNER_REQUIRED"


async def test_orphaned_command_cannot_be_replaced_by_owner_or_mutated_by_staff(admin, database, seeded):
    tenant, actor, former_owner, staff = seeded["t1"], seeded["a1"], seeded["viewer"], seeded["a2"]
    business = await _business(admin, seeded)
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE memberships SET role='owner' WHERE tenant_id=:tenant AND actor_id=:actor"),
            {"tenant": tenant, "actor": former_owner},
        )
        await connection.execute(text("INSERT INTO platform_staff(actor_id) VALUES(:actor)"), {"actor": staff})
    context, gate = EditorialContextService(database), VisualConsentGate(database)
    await gate.enable(tenant, business, actor)
    run = uuid4()
    await gate.admit(tenant, business, actor, uuid4(), run, 1)
    command = ContextUpdate(operation_id=uuid4(), expected_version=0, preferences={"tone": "friendly"})
    await context.update(tenant, business, former_owner, command)
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"),
            {"tenant": tenant, "actor": former_owner},
        )
    await gate.finish(tenant, business, actor, run, 1)
    with pytest.raises(AuthError, match="VISUAL_CHANGE_STAFF_REQUIRED"):
        await context.update(tenant, business, actor, command.model_copy(update={"operation_id": uuid4()}))
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await context.update(tenant, business, former_owner, command.model_copy(update={"operation_id": uuid4()}))
    async with database.transaction(tenant, staff) as session:
        assert await session.scalar(text("SELECT public.is_platform_staff()"))
        assert await session.scalar(text("SELECT count(*) FROM business_visual_pending_changes")) == 0
        assert (
            await session.scalar(
                text("UPDATE business_visual_pending_changes SET state='cancelled' RETURNING operation_id")
            )
            is None
        )
    async with admin.begin() as connection:
        row = (
            await connection.execute(
                text("SELECT actor_id,state FROM business_visual_pending_changes WHERE operation_id=:operation"),
                {"operation": command.operation_id},
            )
        ).one()
        assert tuple(row) == (former_owner, "failed")
        assert (
            await connection.scalar(text("SELECT count(*) FROM audit_events WHERE action='visual.change_superseded'"))
            == 0
        )
