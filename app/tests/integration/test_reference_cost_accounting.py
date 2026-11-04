"""Provider accounting is exercised exclusively with fictitious effects."""

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db.session import Database
from app.services.reference_cost_guard import ReferenceCostError, ReferenceCostGuard, _digest

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
async def clean_aggregate(admin):
    # The shared integration fixture enforces a dedicated _test database.
    async with admin.begin() as connection:
        await connection.execute(text("DELETE FROM reference_cost_monthly"))
    await _policy(admin)
    yield
    async with admin.begin() as connection:
        await connection.execute(text("DELETE FROM reference_cost_monthly"))


async def _discovery(admin, tenant, actor):
    business, discovery, operation = uuid4(), uuid4(), uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:b,:t,'Test','UTC')"),
            {"b": business, "t": tenant},
        )
        await connection.execute(
            text("""INSERT INTO reference_discoveries
          (id,tenant_id,business_id,actor_id,operation_id,context_version,category,preference,state)
          VALUES(:id,:t,:b,:a,:op,1,'test','{}','pending')"""),
            {"id": discovery, "t": tenant, "b": business, "a": actor, "op": operation},
        )
        await connection.execute(
            text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
              VALUES(:id,:t,'reference.search_requested',jsonb_build_object(
                'business_id',CAST(:b AS text),'actor_id',CAST(:a AS text),'operation_id',CAST(:op AS text)))"""),
            {"id": uuid4(), "t": tenant, "b": str(business), "a": str(actor), "op": str(operation)},
        )
    return business, discovery


async def _policy(admin, search=100, monthly=100, search_provider=100, monthly_provider=100, timezone="UTC"):
    policy = uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO reference_cost_policies(id,timezone,per_search,monthly_total)
          VALUES(:id,:zone,:search,:monthly)"""),
            {"id": policy, "zone": timezone, "search": search, "monthly": monthly},
        )
        for provider in ("google", "apify", "jev"):
            await connection.execute(
                text("""INSERT INTO reference_cost_policy_providers
              (policy_id,provider,per_search,monthly_total) VALUES(:id,:provider,:search,:monthly)"""),
                {"id": policy, "provider": provider, "search": search_provider, "monthly": monthly_provider},
            )
        await connection.execute(text("UPDATE reference_cost_policy_head SET policy_id=:id"), {"id": policy})
    return policy


async def test_claim_replay_uncertainty_reconciliation_and_tenant_isolation(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business, discovery = await _discovery(admin, tenant, actor)
    db = Database(settings, correlator=True)
    guard = ReferenceCostGuard(db)
    effect = uuid4()

    async def claim(amount=70, op=effect):
        return await guard.claim(tenant, business, actor, discovery, op, "google", "a" * 64, amount)

    try:
        first, replay = await asyncio.gather(claim(), claim())
        assert sorted((first.created, replay.created)) == [False, True]
        assert first.id == replay.id
        assert not (await claim()).created
        with pytest.raises(ReferenceCostError, match="EFFECT_CONFLICT"):
            await claim(69)
        assert (await guard.finish(tenant, actor, first.id, actual_usd_micros=None)).state == "uncertain"
        assert (await guard.finish(tenant, actor, first.id, actual_usd_micros=None)).state == "uncertain"
        with pytest.raises(ReferenceCostError, match="INVALID_ACTUAL_COST"):
            await guard.finish(tenant, actor, first.id, actual_usd_micros=-1)
        with pytest.raises(ReferenceCostError, match="BUDGET_EXCEEDED"):
            await claim(31, uuid4())
        for amount in (0, 20):
            with pytest.raises(ReferenceCostError, match="EVIDENCE_REQUIRED"):
                await guard.finish(tenant, actor, first.id, actual_usd_micros=amount)
        assert (await claim(30, uuid4())).created
        async with db.transaction(seeded["t2"], seeded["a2"]) as session:
            assert await session.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 0
        with pytest.raises(ReferenceCostError, match="RESERVATION_NOT_FOUND"):
            await guard.finish(seeded["t2"], seeded["a2"], first.id, actual_usd_micros=None)
    finally:
        await db.close()


async def test_global_concurrency_caps_and_separate_provider_caps(admin, seeded, settings):
    one = await _discovery(admin, seeded["t1"], seeded["a1"])
    two = await _discovery(admin, seeded["t2"], seeded["a2"])
    db = Database(settings, correlator=True)
    await _policy(admin, search=100, monthly=100, search_provider=100, monthly_provider=100)
    guard = ReferenceCostGuard(db)

    async def attempt(i, business, discovery):
        return await guard.claim(seeded[f"t{i}"], business, seeded[f"a{i}"], discovery, uuid4(), "google", "a" * 64, 70)

    try:
        results = await asyncio.gather(attempt(1, *one), attempt(2, *two), return_exceptions=True)
        assert sum(not isinstance(result, Exception) for result in results) == 1
        assert any(
            isinstance(result, ReferenceCostError) and "MONTHLY_BUDGET_EXCEEDED" in str(result) for result in results
        )
    finally:
        await db.close()


async def test_old_month_cannot_be_reconciled_without_evidence(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business, discovery = await _discovery(admin, tenant, actor)
    db = Database(settings, correlator=True)
    await _policy(admin, search=300, monthly=100, search_provider=300, monthly_provider=100)
    guard = ReferenceCostGuard(db)
    try:
        old = await guard.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 80)
        async with admin.begin() as connection:
            await connection.execute(
                text("""UPDATE reference_cost_reservations
              SET month=(month - interval '1 month')::date WHERE id=:id"""),
                {"id": old.id},
            )
            await connection.execute(
                text("""UPDATE reference_cost_monthly
              SET month=(month - interval '1 month')::date""")
            )
        with pytest.raises(ReferenceCostError, match="EVIDENCE_REQUIRED"):
            await guard.finish(tenant, actor, old.id, actual_usd_micros=90)
        assert (await guard.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 20)).created
        async with admin.connect() as connection:
            rows = (
                (
                    await connection.execute(
                        text("""SELECT committed_usd_micros FROM reference_cost_monthly
              WHERE provider='all' ORDER BY month""")
                    )
                )
                .scalars()
                .all()
            )
        assert rows == [80, 20]
    finally:
        await db.close()


async def test_unsettled_prior_month_carries_into_current_budget(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business, discovery = await _discovery(admin, tenant, actor)
    db = Database(settings, correlator=True)
    await _policy(admin, search=300, monthly=100, search_provider=300, monthly_provider=100)
    guard = ReferenceCostGuard(db)
    try:
        old = await guard.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 80)
        await guard.finish(tenant, actor, old.id, actual_usd_micros=None)
        async with admin.begin() as connection:
            await connection.execute(
                text("""UPDATE reference_cost_reservations
                  SET month=(month - interval '1 month')::date WHERE id=:id"""),
                {"id": old.id},
            )
            await connection.execute(
                text("""UPDATE reference_cost_monthly
              SET month=(month - interval '1 month')::date""")
            )
        with pytest.raises(ReferenceCostError, match="MONTHLY_BUDGET_EXCEEDED"):
            await guard.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 21)
        assert (await guard.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 20)).created
    finally:
        await db.close()


async def test_unsettled_future_month_still_counts_if_clock_moves_back(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business, discovery = await _discovery(admin, tenant, actor)
    await _policy(admin, search=300, monthly=100, search_provider=300, monthly_provider=100)
    db = Database(settings, correlator=True)
    guard = ReferenceCostGuard(db)
    try:
        future = await guard.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 80)
        async with admin.begin() as connection:
            await connection.execute(
                text("""UPDATE reference_cost_reservations
              SET month=(month + interval '1 month')::date WHERE id=:id"""),
                {"id": future.id},
            )
            await connection.execute(
                text("""UPDATE reference_cost_monthly
              SET month=(month + interval '1 month')::date""")
            )
        with pytest.raises(ReferenceCostError, match="MONTHLY_BUDGET_EXCEEDED"):
            await guard.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 21)
        assert (await guard.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 20)).created
    finally:
        await db.close()


async def test_missing_limits_provider_caps_and_actual_above_hold(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business, discovery = await _discovery(admin, tenant, actor)
    db = Database(settings, correlator=True)
    disabled = ReferenceCostGuard(db)
    await _policy(admin, search=1000, monthly=1000, search_provider=100, monthly_provider=100)
    guard = ReferenceCostGuard(db)
    try:
        async with admin.begin() as connection:
            active = await connection.scalar(text("SELECT policy_id FROM reference_cost_policy_head"))
            await connection.execute(text("UPDATE reference_cost_policy_head SET policy_id=NULL"))
        with pytest.raises(ReferenceCostError, match="BUDGET_DISABLED"):
            await disabled.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 1)
        async with admin.begin() as connection:
            await connection.execute(text("UPDATE reference_cost_policy_head SET policy_id=:id"), {"id": active})
        first = await guard.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 80)
        with pytest.raises(ReferenceCostError, match="SEARCH_PROVIDER_BUDGET_EXCEEDED"):
            await guard.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 21)
        assert (await guard.claim(tenant, business, actor, discovery, uuid4(), "apify", "b" * 64, 50)).created
        with pytest.raises(ReferenceCostError, match="EVIDENCE_REQUIRED"):
            await guard.finish(tenant, actor, first.id, actual_usd_micros=120)
        other_tenant, other_actor = seeded["t2"], seeded["a2"]
        other_business, other_discovery = await _discovery(admin, other_tenant, other_actor)
        with pytest.raises(ReferenceCostError, match="MONTHLY_PROVIDER_BUDGET_EXCEEDED"):
            await guard.claim(
                other_tenant, other_business, other_actor, other_discovery, uuid4(), "google", "a" * 64, 21
            )
        async with admin.connect() as connection:
            amounts = dict(
                (
                    await connection.execute(
                        text("""SELECT provider,committed_usd_micros
              FROM reference_cost_monthly""")
                    )
                ).all()
            )
        assert amounts == {"all": 130, "google": 80, "apify": 50}
    finally:
        await db.close()


async def test_invalid_discovery_and_rolled_back_claim_do_not_consume_limits(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business, discovery = await _discovery(admin, tenant, actor)
    db = Database(settings, correlator=True)
    guard = ReferenceCostGuard(db)
    try:
        with pytest.raises(ReferenceCostError, match="DISCOVERY_NOT_PENDING"):
            await guard.claim(tenant, business, actor, uuid4(), uuid4(), "google", "a" * 64, 1)
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE reference_discoveries SET state='simulated' WHERE id=:id"), {"id": discovery}
            )
        with pytest.raises(ReferenceCostError, match="DISCOVERY_NOT_PENDING"):
            await guard.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 1)
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE reference_discoveries SET state='pending' WHERE id=:id"), {"id": discovery}
            )
        with pytest.raises(ReferenceCostError, match="BUDGET_EXCEEDED"):
            await guard.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 101)
        assert (await guard.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 100)).created
    finally:
        await db.close()


async def test_claim_observes_concurrent_stale_discovery_and_requires_durable_event(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business, discovery = await _discovery(admin, tenant, actor)
    db = Database(settings, correlator=True)
    guard = ReferenceCostGuard(db)
    try:
        async with admin.begin() as connection:
            await connection.execute(
                text("SELECT set_config('app.tenant_id',:tenant,true),set_config('app.actor_id',:actor,true)"),
                {"tenant": str(tenant), "actor": str(actor)},
            )
            await connection.execute(
                text("UPDATE reference_discoveries SET state='stale' WHERE id=:id"), {"id": discovery}
            )
            task = asyncio.create_task(guard.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 1))
            await asyncio.sleep(0.05)
            assert not task.done()
        with pytest.raises(ReferenceCostError, match="DISCOVERY_NOT_PENDING"):
            await task
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE reference_discoveries SET state='pending' WHERE id=:id"), {"id": discovery}
            )
            await connection.execute(text("DELETE FROM outbox_events WHERE tenant_id=:tenant"), {"tenant": tenant})
        with pytest.raises(ReferenceCostError, match="DISCOVERY_NOT_PENDING"):
            await guard.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 1)
    finally:
        await db.close()


@pytest.mark.parametrize("target", ["membership", "account"])
async def test_claim_waits_for_revocation_and_finish_remains_available(admin, seeded, settings, target):
    tenant, actor = seeded["t1"], seeded["a1"]
    business, discovery = await _discovery(admin, tenant, actor)
    db = Database(settings, correlator=True)
    guard = ReferenceCostGuard(db)
    try:
        effect = uuid4()
        first = await guard.claim(tenant, business, actor, discovery, effect, "google", "a" * 64, 1)
        async with admin.begin() as connection:
            if target == "membership":
                await connection.execute(
                    text("UPDATE memberships SET active=false WHERE tenant_id=:t AND actor_id=:a"),
                    {"t": tenant, "a": actor},
                )
            else:
                await connection.execute(text("UPDATE user_accounts SET active=false WHERE id=:a"), {"a": actor})
            task = asyncio.create_task(guard.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 1))
            await asyncio.sleep(0.05)
            assert not task.done()
        with pytest.raises(ReferenceCostError, match="OWNER_INACTIVE"):
            await task
        assert not (await guard.claim(tenant, business, actor, discovery, effect, "google", "a" * 64, 1)).created
        assert (await guard.finish(tenant, actor, first.id, actual_usd_micros=None)).state == "uncertain"
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM reference_cost_reservations")) == 1
    finally:
        await db.close()


async def test_replay_waiting_behind_revocation_recognizes_admitted_claim(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business, discovery = await _discovery(admin, tenant, actor)
    effect = uuid4()
    db = Database(settings, correlator=True)
    guard = ReferenceCostGuard(db)
    revocation_locked, finish_revocation = asyncio.Event(), asyncio.Event()

    async def revoke():
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE memberships SET active=false WHERE tenant_id=:t AND actor_id=:a"),
                {"t": tenant, "a": actor},
            )
            revocation_locked.set()
            await finish_revocation.wait()

    revoke_task = replay_task = None
    try:
        async with db.transaction(tenant, actor) as session:
            claim = await session.scalar(
                text("SELECT public.reference_cost_claim(:business,:discovery,:effect,'google',:hash,70)"),
                {
                    "business": business,
                    "discovery": discovery,
                    "effect": effect,
                    "hash": _digest(business, actor, discovery, "google", "a" * 64, 70),
                },
            )
            assert claim["created"] is True
            revoke_task = asyncio.create_task(revoke())
            await asyncio.sleep(0.05)
            assert not revoke_task.done()
            replay_task = asyncio.create_task(
                guard.claim(tenant, business, actor, discovery, effect, "google", "a" * 64, 70)
            )
            await asyncio.sleep(0.05)
            assert not replay_task.done()
        await asyncio.wait_for(revocation_locked.wait(), timeout=2)
        finish_revocation.set()
        await asyncio.wait_for(revoke_task, timeout=2)
        replay = await asyncio.wait_for(replay_task, timeout=2)
        assert not replay.created and str(replay.id) == claim["id"]
        assert (await guard.finish(tenant, actor, replay.id, actual_usd_micros=None)).state == "uncertain"
        with pytest.raises(ReferenceCostError, match="OWNER_INACTIVE"):
            await guard.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 1)
    finally:
        finish_revocation.set()
        for task in (revoke_task, replay_task):
            if task is not None and not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
        await db.close()


async def test_replay_rechecks_after_owner_lock_reports_revoked(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business, discovery = await _discovery(admin, tenant, actor)
    effect, reservation = uuid4(), uuid4()
    db = Database(settings, correlator=True)
    guard = ReferenceCostGuard(db)
    revoke_ready, revoke_commit = asyncio.Event(), asyncio.Event()

    async def revoke():
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE memberships SET active=false WHERE tenant_id=:t AND actor_id=:a"),
                {"t": tenant, "a": actor},
            )
            revoke_ready.set()
            await revoke_commit.wait()

    revoke_task = replay_task = None
    try:
        # Hold an uncommitted reservation representing the first claim, so the
        # replay's first SELECT cannot see it while revocation owns the row lock.
        async with admin.begin() as connection:
            await connection.execute(
                text("SELECT set_config('app.tenant_id',:t,true),set_config('app.actor_id',:a,true)"),
                {"t": str(tenant), "a": str(actor)},
            )
            await connection.execute(
                text("""INSERT INTO reference_cost_reservations
              (id,tenant_id,business_id,actor_id,discovery_id,effect_id,request_hash,provider,month,
               reserved_usd_micros,state,policy_id)
              VALUES(:id,:tenant,:business,:actor,:discovery,:effect,:hash,'google',
                date_trunc('month',clock_timestamp() AT TIME ZONE 'UTC')::date,70,'claimed',
                (SELECT policy_id FROM reference_cost_policy_head))"""),
                {
                    "id": reservation,
                    "tenant": tenant,
                    "business": business,
                    "actor": actor,
                    "discovery": discovery,
                    "effect": effect,
                    "hash": _digest(business, actor, discovery, "google", "a" * 64, 70),
                },
            )
            revoke_task = asyncio.create_task(revoke())
            await asyncio.wait_for(revoke_ready.wait(), timeout=2)
            replay_task = asyncio.create_task(
                guard.claim(tenant, business, actor, discovery, effect, "google", "a" * 64, 70)
            )
            await asyncio.sleep(0.05)
            assert not replay_task.done()
        revoke_commit.set()
        await asyncio.wait_for(revoke_task, timeout=2)
        replay = await asyncio.wait_for(replay_task, timeout=2)
        assert replay.id == reservation and not replay.created
        with pytest.raises(ReferenceCostError, match="OWNER_INACTIVE"):
            await guard.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 1)
    finally:
        revoke_commit.set()
        for task in (revoke_task, replay_task):
            if task is not None and not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
        await db.close()


async def test_identity_lock_role_is_narrow_and_blocks_revocation_until_commit(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    db = Database(settings, correlator=True)
    try:
        async with admin.connect() as connection:
            owner = await connection.scalar(
                text("""SELECT pg_get_userbyid(proowner) FROM pg_proc
              WHERE oid='public.lock_reference_cost_owner()'::regprocedure""")
            )
            assert owner == "meu_braco_direito_reference_lock"
            assert not await connection.scalar(
                text("""SELECT rolcanlogin OR rolsuper OR rolbypassrls
              OR rolcreatedb OR rolcreaterole OR rolreplication FROM pg_roles WHERE rolname=:role"""),
                {"role": owner},
            )
            # The address API reuses the same identity-only lock. This grants
            # no cost mutation, provider dispatch, or foreign actor access.
            assert await connection.scalar(
                text("""SELECT has_function_privilege('meu_braco_direito_app',
              'public.lock_reference_cost_owner()', 'EXECUTE')""")
            )
            assert await connection.scalar(
                text("""SELECT has_function_privilege('meu_braco_direito_correlator',
              'public.lock_reference_cost_owner()', 'EXECUTE')""")
            )

        async def revoke():
            async with admin.begin() as connection:
                await connection.execute(
                    text("UPDATE memberships SET active=false WHERE tenant_id=:t AND actor_id=:a"),
                    {"t": tenant, "a": actor},
                )

        async with db.transaction(tenant, actor) as session:
            assert await session.scalar(text("SELECT public.lock_reference_cost_owner()")) is True
            task = asyncio.create_task(revoke())
            await asyncio.sleep(0.05)
            assert not task.done()
        await task
        async with db.transaction(tenant, actor) as session:
            assert await session.scalar(text("SELECT public.lock_reference_cost_owner()")) is False
    finally:
        await db.close()


async def test_blocked_identity_does_not_block_other_tenants_claim_or_finish(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    other_tenant, other_actor = seeded["t2"], seeded["a2"]
    business, discovery = await _discovery(admin, tenant, actor)
    other_business, other_discovery = await _discovery(admin, other_tenant, other_actor)
    db = Database(settings, correlator=True)
    guard = ReferenceCostGuard(db)
    try:
        first = await guard.claim(
            other_tenant, other_business, other_actor, other_discovery, uuid4(), "google", "a" * 64, 5
        )
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE memberships SET active=false WHERE tenant_id=:t AND actor_id=:a"),
                {"t": tenant, "a": actor},
            )
            blocked = asyncio.create_task(
                guard.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 5)
            )
            await asyncio.sleep(0.05)
            assert not blocked.done()
            second = await asyncio.wait_for(
                guard.claim(other_tenant, other_business, other_actor, other_discovery, uuid4(), "google", "b" * 64, 5),
                timeout=1,
            )
            assert second.created
            assert (
                await asyncio.wait_for(
                    guard.finish(other_tenant, other_actor, first.id, actual_usd_micros=None), timeout=1
                )
            ).state == "uncertain"
        with pytest.raises(ReferenceCostError, match="OWNER_INACTIVE"):
            await blocked
    finally:
        await db.close()


async def test_replay_after_concurrent_commit_and_discovery_becoming_stale(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business, discovery = await _discovery(admin, tenant, actor)
    effect, reservation = uuid4(), uuid4()
    db = Database(settings, correlator=True)
    guard = ReferenceCostGuard(db)
    try:
        async with admin.begin() as connection:
            await connection.execute(
                text("SELECT set_config('app.tenant_id',:tenant,true),set_config('app.actor_id',:actor,true)"),
                {"tenant": str(tenant), "actor": str(actor)},
            )
            await connection.execute(
                text("UPDATE reference_discoveries SET state='stale' WHERE id=:id"), {"id": discovery}
            )
            task = asyncio.create_task(guard.claim(tenant, business, actor, discovery, effect, "google", "a" * 64, 5))
            await asyncio.sleep(0.05)
            assert not task.done()
            await connection.execute(
                text("""INSERT INTO reference_cost_reservations
              (id,tenant_id,business_id,actor_id,discovery_id,effect_id,request_hash,provider,month,
               reserved_usd_micros,state,policy_id)
              VALUES(:id,:tenant,:business,:actor,:discovery,:effect,:hash,'google',
                date_trunc('month',clock_timestamp() AT TIME ZONE 'UTC')::date,5,'claimed',
                (SELECT policy_id FROM reference_cost_policy_head))"""),
                {
                    "id": reservation,
                    "tenant": tenant,
                    "business": business,
                    "actor": actor,
                    "discovery": discovery,
                    "effect": effect,
                    "hash": _digest(business, actor, discovery, "google", "a" * 64, 5),
                },
            )
        replay = await task
        assert replay.id == reservation and not replay.created
    finally:
        await db.close()


async def test_policy_is_shared_versioned_and_disabled_without_active_policy(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business, discovery = await _discovery(admin, tenant, actor)
    one_db, two_db = Database(settings, correlator=True), Database(settings, correlator=True)
    one, two = ReferenceCostGuard(one_db), ReferenceCostGuard(two_db)
    try:
        async with admin.begin() as connection:
            await connection.execute(text("UPDATE reference_cost_policy_head SET policy_id=NULL"))
        with pytest.raises(ReferenceCostError, match="BUDGET_DISABLED"):
            await one.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 1)
        first_policy = await _policy(admin, monthly=100)
        first_claim = await one.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 60)
        second_policy = await _policy(admin, monthly=70)
        assert first_policy != second_policy
        with pytest.raises(ReferenceCostError, match="MONTHLY_BUDGET_EXCEEDED"):
            await two.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 11)
        second_claim = await two.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 10)
        assert second_claim.created
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM reference_cost_policy_activations")) >= 2
            policies = dict(
                (
                    await connection.execute(
                        text("""SELECT id,policy_id FROM reference_cost_reservations
              WHERE id IN (:one,:two)"""),
                        {"one": first_claim.id, "two": second_claim.id},
                    )
                ).all()
            )
            assert policies == {first_claim.id: first_policy, second_claim.id: second_policy}
    finally:
        await one_db.close()
        await two_db.close()


async def test_claim_waits_for_concurrent_policy_activation_and_uses_new_limit(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business, discovery = await _discovery(admin, tenant, actor)
    policy = uuid4()
    db = Database(settings, correlator=True)
    guard = ReferenceCostGuard(db)
    try:
        async with admin.begin() as connection:
            await connection.execute(
                text("""INSERT INTO reference_cost_policies(id,timezone,per_search,monthly_total)
              VALUES(:id,'UTC',100,50)"""),
                {"id": policy},
            )
            await connection.execute(
                text("""INSERT INTO reference_cost_policy_providers
              (policy_id,provider,per_search,monthly_total) VALUES(:id,'google',100,100)"""),
                {"id": policy},
            )
            await connection.execute(text("UPDATE reference_cost_policy_head SET policy_id=:id"), {"id": policy})
            task = asyncio.create_task(guard.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 60))
            await asyncio.sleep(0.05)
            assert not task.done()
        with pytest.raises(ReferenceCostError, match="MONTHLY_BUDGET_EXCEEDED"):
            await task
        assert (await guard.claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 50)).created
    finally:
        await db.close()


async def test_policy_timezone_and_versions_cannot_be_changed_after_history(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business, discovery = await _discovery(admin, tenant, actor)
    db = Database(settings, correlator=True)
    try:
        policy = await _policy(admin, timezone="UTC")
        claim = await ReferenceCostGuard(db).claim(tenant, business, actor, discovery, uuid4(), "google", "a" * 64, 1)
        async with admin.connect() as connection:
            assert await connection.scalar(
                text("""SELECT month=date_trunc('month',created_at AT TIME ZONE
              'UTC')::date FROM reference_cost_reservations WHERE id=:id"""),
                {"id": claim.id},
            )
        with pytest.raises(DBAPIError, match="REFERENCE_POLICY_IMMUTABLE"):
            async with admin.begin() as connection:
                await connection.execute(
                    text("UPDATE reference_cost_policies SET monthly_total=200 WHERE id=:id"), {"id": policy}
                )
        with pytest.raises(DBAPIError, match="REFERENCE_POLICY_IMMUTABLE"):
            async with admin.begin() as connection:
                await connection.execute(
                    text("""INSERT INTO reference_cost_policy_providers
                  (policy_id,provider,per_search,monthly_total) VALUES(:id,'jev',10,10)"""),
                    {"id": policy},
                )
        async with admin.begin() as connection:
            await connection.execute(text("UPDATE reference_cost_policy_head SET policy_id=NULL"))
        with pytest.raises(DBAPIError, match="REFERENCE_TIMEZONE_NOT_SUPPORTED"):
            await _policy(admin, timezone="America/Sao_Paulo")
    finally:
        await db.close()


async def test_unsupported_timezone_cannot_be_activated_without_history(admin):
    with pytest.raises(DBAPIError, match="REFERENCE_TIMEZONE_NOT_SUPPORTED"):
        await _policy(admin, timezone="America/Sao_Paulo")
    with pytest.raises(DBAPIError, match="REFERENCE_INVALID_TIMEZONE"):
        await _policy(admin, timezone="Invalid/Timezone")


async def test_worker_cannot_modify_policy_reservations_or_aggregates(admin, seeded, settings):
    async with admin.connect() as connection:
        checks = (
            await connection.execute(
                text("""SELECT
          has_table_privilege('meu_braco_direito_correlator','reference_cost_policies','INSERT'),
          has_table_privilege('meu_braco_direito_correlator','reference_cost_reservations','INSERT'),
          has_table_privilege('meu_braco_direito_correlator','reference_cost_monthly','SELECT'),
          has_table_privilege('meu_braco_direito_correlator','reference_cost_monthly','UPDATE'),
          has_function_privilege('meu_braco_direito_app',
            'public.reference_cost_claim(uuid,uuid,uuid,text,text,bigint)','EXECUTE'),
          has_function_privilege('meu_braco_direito_correlator',
            'public.reference_cost_claim(uuid,uuid,uuid,text,text,bigint)','EXECUTE')""")
            )
        ).one()
        assert tuple(checks) == (False, False, False, False, False, True)
        owner = await connection.scalar(
            text("""SELECT pg_get_userbyid(proowner) FROM pg_proc WHERE
          oid='public.reference_cost_claim(uuid,uuid,uuid,text,text,bigint)'::regprocedure""")
        )
        assert owner == "meu_braco_direito_reference_ledger"
        assert not await connection.scalar(
            text("""SELECT rolcanlogin OR rolsuper OR rolbypassrls
          OR rolcreatedb OR rolcreaterole OR rolreplication FROM pg_roles WHERE rolname=:role"""),
            {"role": owner},
        )
        assert not await connection.scalar(
            text("""SELECT has_column_privilege('meu_braco_direito_correlator',
          'reference_cost_reservations','state','UPDATE')""")
        )
        assert not await connection.scalar(
            text("""SELECT has_column_privilege('meu_braco_direito_correlator',
          'reference_cost_monthly','committed_usd_micros','UPDATE')""")
        )
    db = Database(settings, correlator=True)
    try:
        for statement in (
            "UPDATE reference_cost_reservations SET state='uncertain' WHERE false",
            "UPDATE reference_cost_monthly SET committed_usd_micros=0 WHERE false",
            "UPDATE reference_cost_policy_head SET policy_id=NULL WHERE false",
        ):
            with pytest.raises(DBAPIError):
                async with db.transaction(seeded["t1"], seeded["a1"]) as session:
                    await session.execute(text(statement))
    finally:
        await db.close()


async def test_direct_sql_replay_cannot_change_bound_effect_fields(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business, discovery = await _discovery(admin, tenant, actor)
    db = Database(settings, correlator=True)
    effect = uuid4()
    guard = ReferenceCostGuard(db)
    try:
        await guard.claim(tenant, business, actor, discovery, effect, "google", "a" * 64, 5)
        original = {
            "business": business,
            "discovery": discovery,
            "effect": effect,
            "provider": "google",
            "hash": _digest(business, actor, discovery, "google", "a" * 64, 5),
            "amount": 5,
        }
        for field, value in (("business", uuid4()), ("discovery", uuid4()), ("provider", "apify"), ("amount", 6)):
            with pytest.raises(DBAPIError, match="REFERENCE_EFFECT_CONFLICT"):
                async with db.transaction(tenant, actor) as session:
                    await session.scalar(
                        text("""SELECT public.reference_cost_claim(
                      :business,:discovery,:effect,:provider,:hash,:amount)"""),
                        original | {field: value},
                    )
        async with admin.connect() as connection:
            reservation = await connection.scalar(
                text("SELECT id FROM reference_cost_reservations WHERE effect_id=:effect"), {"effect": effect}
            )
        with pytest.raises(DBAPIError, match="REFERENCE_EVIDENCE_REQUIRED"):
            async with db.transaction(tenant, actor) as session:
                await session.scalar(text("SELECT public.reference_cost_finish(:id,0)"), {"id": reservation})
    finally:
        await db.close()
