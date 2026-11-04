"""Recover an accepted run and account authenticated cost without a new POST."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4, uuid5

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.adapters.apify_place_contacts import ApifyPlaceContacts, SubmittedPlaceContacts
from app.services.reference_contacts_budget_guard import (
    ContactsGuardContext,
    ContactsGuardError,
    DatabaseContactsBudgetGuard,
)
from app.services.reference_contacts_runs import load_contacts_run, record_contacts_cost, record_contacts_run
from app.tests.integration.test_reference_contacts_guard import _call, _revoke, _setup

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("historical_filtered_writer")]


@pytest.fixture
async def started_contacts(admin, api, seeded, settings):
    google, worker, cycle, batch, candidate, p = await _setup(admin, api, seeded, settings)
    c = ContactsGuardContext(
        google.tenant,
        google.business,
        google.actor,
        cycle,
        batch["batch"],
        candidate,
        "fake-place",
        p["lookup"],
        p["effect"],
        p["event"],
        google.pilot,
        1,
        google.key,
        p["key"],
        p["tariff"],
        p["credential"],
        40,
        "1.2.3",
        "actor-id",
    )
    claimed = await _call(worker, google, p)
    token = UUID(claimed["executor_token"])
    run = SubmittedPlaceContacts(
        c.effect, c.place_id, "run-id", "dataset-id", "store-id", "queue-id", "build-id", c.build, c.provider_actor_id
    )
    try:
        yield worker, c, token, run
    finally:
        await worker.close()
        await _revoke(admin)


async def test_run_recovery_and_receipt_release_only_unused_cost(admin, started_contacts):
    worker, c, token, run = started_contacts
    assert await load_contacts_run(worker, c) is None
    for _ in range(2):
        await record_contacts_run(worker, c, token, run)
    assert await load_contacts_run(worker, c) == (run, token)
    for _ in range(2):
        await record_contacts_cost(worker, c, token, run, 7)
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 107
        assert (
            await conn.scalar(text("SELECT outstanding_usd_micros FROM reference_cost_monthly WHERE provider='apify'"))
            == 0
        )
        assert (
            await conn.scalar(text("SELECT committed_usd_micros FROM reference_cost_monthly WHERE provider='all'"))
            == 107
        )
        assert (
            await conn.scalar(text("SELECT count(*) FROM audit_events WHERE action='reference.contacts_cost_reported'"))
            == 1
        )
        assert (
            await conn.scalar(
                text("SELECT count(*) FROM outbox_events WHERE event_type='reference.contacts_run_recorded'")
            )
            == 1
        )
    with pytest.raises(DBAPIError, match="CONTACTS_RECEIPT_CONFLICT"):
        await record_contacts_cost(worker, c, token, run, 6)


async def test_fence_owner_and_run_binding_cannot_be_replaced(admin, seeded, started_contacts):
    worker, c, token, run = started_contacts
    with pytest.raises(DBAPIError, match="CONTACTS_EXECUTOR_FENCE_INVALID"):
        await record_contacts_run(worker, c, uuid4(), run)
    await record_contacts_run(worker, c, token, run)
    with pytest.raises(DBAPIError, match="CONTACTS_RUN_CONFLICT"):
        await record_contacts_run(worker, c, token, replace(run, dataset_id="other"))
    async with admin.begin() as conn:
        await conn.execute(
            text("INSERT INTO memberships(tenant_id,actor_id,role) VALUES(:t,:a,'owner')"),
            {"t": c.tenant, "a": seeded["a2"]},
        )
    other = replace(c, actor=seeded["a2"])
    assert await load_contacts_run(worker, other) is None
    with pytest.raises(DBAPIError, match="CONTACTS_EXECUTOR_FENCE_INVALID"):
        await record_contacts_cost(worker, other, token, run, 7)
    for change in (
        {"place_id": "other"},
        {"submission_id": uuid4()},
        {"build_number": "9.0.0"},
        {"provider_actor_id": "other"},
    ):
        with pytest.raises(ContactsGuardError, match="CONTACTS_RUN_BINDING_INVALID"):
            await record_contacts_run(worker, c, token, replace(run, **change))
    for value in (True, -1, 1_000_000_000_001):
        with pytest.raises(ContactsGuardError, match="CONTACTS_RECEIPT_INVALID"):
            await record_contacts_cost(worker, c, token, run, value)


async def test_inconsistent_monthly_ledger_rolls_back_entire_receipt(admin, started_contacts):
    worker, c, token, run = started_contacts
    await record_contacts_run(worker, c, token, run)
    async with admin.begin() as conn:
        await conn.execute(text("DELETE FROM reference_cost_monthly WHERE provider='apify'"))
    with pytest.raises(DBAPIError, match="REFERENCE_MONTHLY_INCONSISTENT"):
        await record_contacts_cost(worker, c, token, run, 7)
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 140
        assert await conn.scalar(text("SELECT reported_cost_usd_micros FROM reference_contacts_runs")) is None
        assert (
            await conn.scalar(text("SELECT committed_usd_micros FROM reference_cost_monthly WHERE provider='all'"))
            == 140
        )


async def test_recovered_run_polls_same_run_without_a_paid_post(admin, started_contacts, monkeypatch):
    worker, c, token, run = started_contacts
    await record_contacts_run(worker, c, token, run)
    requests = []
    finished = datetime(2026, 1, 1, tzinfo=UTC)

    class Clock(datetime):
        current = finished

        @classmethod
        def now(cls, tz=None):
            return cls.current

    monkeypatch.setattr("app.adapters.apify_run_metadata.datetime", Clock)

    def respond(request):
        requests.append(request.method)
        assert request.method == "GET"
        if "/actor-runs/" in request.url.path:
            return httpx.Response(
                200,
                json={
                    "data": {
                        "id": run.run_id,
                        "actId": run.provider_actor_id,
                        "buildNumber": run.build_number,
                        "buildId": run.build_id,
                        "defaultDatasetId": run.dataset_id,
                        "defaultKeyValueStoreId": run.key_value_store_id,
                        "defaultRequestQueueId": run.request_queue_id,
                        "status": "SUCCEEDED",
                        "finishedAt": finished.isoformat(),
                        "usageTotalUsd": 0.000007,
                    }
                },
            )
        return httpx.Response(200, json=[{"placeId": run.place_id, "instagrams": ["https://instagram.com/example"]}])

    guard = DatabaseContactsBudgetGuard(worker, c)
    with pytest.raises(ContactsGuardError, match="CONTACTS_EXECUTOR_FENCE_INVALID"):
        guard.execution_token()
    adapter = ApifyPlaceContacts(
        SecretStr("synthetic-key"),
        guard,
        enabled=True,
        transport=httpx.MockTransport(respond),
        actor_build=c.build,
        provider_actor_id=c.provider_actor_id,
        max_actor_usd_micros=40,
    )
    pending = await adapter.inspect(run, uuid5(c.effect, "contacts-inspection-v1"))
    assert pending.state == "pending" and pending.reported_cost_usd_micros is None
    async with admin.connect() as conn:
        reservation = (
            await conn.execute(
                text("""SELECT state,reserved_usd_micros,actual_usd_micros FROM reference_cost_reservations
                  WHERE effect_id=:effect"""),
                {"effect": c.effect},
            )
        ).one()
        assert tuple(reservation) == ("claimed", 40, None)
    Clock.current = finished + timedelta(seconds=30)
    for _ in range(2):
        result = await adapter.inspect(run, uuid5(c.effect, "contacts-inspection-v1"))
        assert result.reported_cost_usd_micros == 7 and guard.execution_token() == token
    assert requests == ["GET"] * 5
    await record_contacts_cost(worker, c, token, run, result.reported_cost_usd_micros)
    async with admin.connect() as conn:
        assert (
            await conn.execute(
                text("SELECT state,actual_usd_micros FROM reference_cost_reservations WHERE effect_id=:effect"),
                {"effect": c.effect},
            )
        ).one() == ("completed", 7)
