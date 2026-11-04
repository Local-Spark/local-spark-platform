"""Private capture of synthetic Apify resources is fenced and never dispatches cleanup."""

import asyncio
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db.session import Database
from app.tests.integration.test_reference_feed_ledger import _claim, _effect, _fixture, _revoke

pytestmark = pytest.mark.integration

_RECORD = text("""SELECT public.reference_record_feed_resources(
  :business,:effect,:executor,:operation,:run,:dataset,:store,:queue,:build_id,:build)""")


def _values(parent, effect, token, *, operation=None):
    return {
        "business": parent.business,
        "effect": effect["effect"],
        "executor": UUID(token),
        "operation": operation or uuid4(),
        "run": "synthetic-run",
        "dataset": "synthetic-dataset",
        "store": "synthetic-store",
        "queue": "synthetic-queue",
        "build_id": "synthetic-build-id",
        "build": "1.2.3",
    }


async def _record(admin, parent, values, *, tenant=None, actor=None):
    async with admin.begin() as connection:
        await connection.execute(
            text("SELECT set_config('app.tenant_id',:tenant,true)"), {"tenant": str(tenant or parent.tenant)}
        )
        await connection.execute(
            text("SELECT set_config('app.actor_id',:actor,true)"), {"actor": str(actor or parent.actor)}
        )
        return await connection.scalar(_RECORD, values)


async def test_record_is_fenced_private_and_idempotent_under_concurrency(admin, api, seeded, settings):
    parent, window, _, tariff = await _fixture(admin, api, seeded, settings)
    effect = await _effect(admin, parent, window, tariff)
    worker = Database(settings, correlator=True)
    try:
        claim = await _claim(worker, parent, effect)
        values = _values(parent, effect, claim["executor_token"])
        one, two = await asyncio.gather(_record(admin, parent, values), _record(admin, parent, values))
        assert {one["created"], two["created"]} == {True, False}
        assert one["event_id"] == two["event_id"]
        async with admin.connect() as connection:
            row = (
                (
                    await connection.execute(
                        text("SELECT * FROM reference_feed_resources WHERE effect_id=:effect"), values
                    )
                )
                .mappings()
                .one()
            )
            for name, column in (
                ("run", "run_id"),
                ("dataset", "dataset_id"),
                ("store", "store_id"),
                ("queue", "queue_id"),
                ("build_id", "build_id"),
            ):
                assert row[column] == values[name]
            event = await connection.scalar(
                text("SELECT payload::text FROM outbox_events WHERE id=:id"), {"id": row["event_id"]}
            )
            assert all(values[name] not in event for name in ("run", "dataset", "store", "queue", "build_id"))
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM audit_events WHERE action='reference.feed_resources_recorded'")
                )
                == 1
            )
            assert (
                await connection.scalar(
                    text("SELECT state FROM reference_feed_effects WHERE id=:id"), {"id": effect["effect"]}
                )
                == "running"
            )
            assert (
                await connection.scalar(
                    text("SELECT state FROM reference_cost_reservations WHERE effect_id=:id"), {"id": effect["effect"]}
                )
                == "claimed"
            )
        for change in (
            {"operation": uuid4()},
            {"run": "other-run"},
            {"dataset": "other-dataset"},
            {"store": "other-store"},
            {"queue": "other-queue"},
            {"build_id": "other-build"},
        ):
            with pytest.raises(DBAPIError, match="REFERENCE_FEED_RESOURCE_CONFLICT"):
                await _record(admin, parent, {**values, **change})
    finally:
        await worker.close()
        await _revoke(admin)


@pytest.mark.parametrize("change", ["token", "build", "actor", "tenant", "event", "reservation"])
async def test_missing_evidence_or_wrong_fence_never_records(admin, api, seeded, settings, change):
    parent, window, _, tariff = await _fixture(admin, api, seeded, settings)
    effect = await _effect(admin, parent, window, tariff)
    worker = Database(settings, correlator=True)
    try:
        claim = await _claim(worker, parent, effect)
        values = _values(parent, effect, claim["executor_token"])
        actor, tenant = parent.actor, parent.tenant
        if change == "token":
            values["executor"] = uuid4()
        elif change == "build":
            values["build"] = "1.2.4"
        elif change == "actor":
            actor = seeded["viewer"]
        elif change == "tenant":
            tenant = seeded["t2"]
        elif change == "event":
            async with admin.begin() as connection:
                await connection.execute(
                    text("UPDATE outbox_events SET payload='{}'::jsonb WHERE id=:id"), {"id": effect["event"]}
                )
        else:
            async with admin.begin() as connection:
                await connection.execute(
                    text("DELETE FROM reference_cost_reservations WHERE effect_id=:id"), {"id": effect["effect"]}
                )
        with pytest.raises(DBAPIError, match="REFERENCE_FEED_(FENCE|EVENT|RESERVATION)_INVALID"):
            await _record(admin, parent, values, tenant=tenant, actor=actor)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM reference_feed_resources")) == 0
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM outbox_events WHERE event_type='reference.feed_resources_recorded'")
                )
                == 0
            )
    finally:
        await worker.close()
        await _revoke(admin)


@pytest.mark.parametrize(
    "field,value",
    [
        ("run", "../run"),
        ("dataset", ""),
        ("store", "x" * 65),
        ("queue", None),
        ("build_id", "bad space"),
        ("build", "latest"),
    ],
)
async def test_invalid_provider_id_is_rejected_without_logging_or_side_effect(
    admin, api, seeded, settings, field, value
):
    parent, window, _, tariff = await _fixture(admin, api, seeded, settings)
    effect = await _effect(admin, parent, window, tariff)
    worker = Database(settings, correlator=True)
    try:
        claim = await _claim(worker, parent, effect)
        values = {**_values(parent, effect, claim["executor_token"]), field: value}
        with pytest.raises(DBAPIError, match="REFERENCE_FEED_RESOURCE_INVALID"):
            await _record(admin, parent, values)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM reference_feed_resources")) == 0
    finally:
        await worker.close()
        await _revoke(admin)


async def test_metadata_can_be_preserved_for_recovery_after_owner_revocation_or_uncertain_result(
    admin, api, seeded, settings
):
    parent, window, _, tariff = await _fixture(admin, api, seeded, settings)
    effect = await _effect(admin, parent, window, tariff)
    worker = Database(settings, correlator=True)
    try:
        claim = await _claim(worker, parent, effect)
        async with worker.transaction(parent.tenant, parent.actor) as session:
            await session.execute(
                text("SELECT reference_feed_uncertain(:effect,:token)"),
                {"effect": effect["effect"], "token": UUID(claim["executor_token"])},
            )
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"),
                {"tenant": parent.tenant, "actor": parent.actor},
            )
        result = await _record(admin, parent, _values(parent, effect, claim["executor_token"]))
        assert result["created"] is True
        async with admin.connect() as connection:
            assert (
                await connection.scalar(
                    text("SELECT state FROM reference_feed_effects WHERE id=:id"), {"id": effect["effect"]}
                )
                == "uncertain"
            )
            assert (
                await connection.scalar(
                    text("SELECT state FROM reference_cost_reservations WHERE effect_id=:id"), {"id": effect["effect"]}
                )
                == "uncertain"
            )
    finally:
        await worker.close()
        await _revoke(admin)


async def test_runtime_cannot_read_resources_and_only_worker_can_record_fenced_identity(
    admin, api, seeded, settings, database
):
    parent, window, _, tariff = await _fixture(admin, api, seeded, settings)
    effect = await _effect(admin, parent, window, tariff)
    worker = Database(settings, correlator=True)
    try:
        claim = await _claim(worker, parent, effect)
        values = _values(parent, effect, claim["executor_token"])
        await _record(admin, parent, values)
        for db in (database, worker):
            with pytest.raises(DBAPIError):
                async with db.transaction(parent.tenant, parent.actor) as session:
                    await session.execute(text("SELECT * FROM reference_feed_resources"))
        with pytest.raises(DBAPIError):
            async with database.transaction(parent.tenant, parent.actor) as session:
                await session.execute(_RECORD, values)
        async with worker.transaction(parent.tenant, parent.actor) as session:
            assert (await session.scalar(_RECORD, values))["created"] is False
    finally:
        await worker.close()
        await _revoke(admin)
