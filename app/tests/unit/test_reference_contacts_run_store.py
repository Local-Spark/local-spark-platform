from contextlib import asynccontextmanager
from dataclasses import replace
from uuid import uuid4

import pytest

from app.adapters.apify_place_contacts import SubmittedPlaceContacts
from app.services.reference_contacts_budget_guard import ContactsGuardError
from app.services.reference_contacts_runs import (
    load_contacts_run,
    record_contacts_cost,
    record_contacts_run,
    run_metadata,
)
from app.tests.unit.test_reference_contacts_recovery_guard import context


class Database:
    def __init__(self, result=None):
        self.result, self.calls = result, []

    @asynccontextmanager
    async def transaction(self, tenant, actor):
        self.calls.append((tenant, actor))
        yield self

    async def scalar(self, sql, params):
        self.calls.append((str(sql), params))
        return self.result


def run(c):
    return SubmittedPlaceContacts(
        c.effect, c.place_id, "run", "dataset", "store", "queue", "build", c.build, c.provider_actor_id
    )


async def test_run_roundtrip_preserves_scope_and_durable_identity():
    c, token = context(), uuid4()
    submitted = run(c)
    db = Database()
    assert await load_contacts_run(db, c) is None
    await record_contacts_run(db, c, token, submitted)
    db.result = {"metadata": run_metadata(submitted), "executor_token": str(token)}
    assert await load_contacts_run(db, c) == (submitted, token)
    assert db.calls[0] == db.calls[2] == db.calls[4] == (c.tenant, c.actor)
    assert db.calls[3][1]["effect"] == c.effect and db.calls[3][1]["token"] == token


@pytest.mark.parametrize(
    "change",
    [{"submission_id": uuid4()}, {"place_id": "other"}, {"build_number": "2.0.0"}, {"provider_actor_id": "other"}],
)
async def test_unbound_runs_cannot_record_receipts(change):
    c, db = context(), Database()
    with pytest.raises(ContactsGuardError, match="BINDING_INVALID"):
        await record_contacts_cost(db, c, uuid4(), replace(run(c), **change), 1)
    assert db.calls == []


@pytest.mark.parametrize("value", [True, -1, 1_000_000_000_001, 0.1])
async def test_malformed_amounts_never_enter_ledger(value):
    c, db = context(), Database()
    with pytest.raises(ContactsGuardError, match="RECEIPT_INVALID"):
        await record_contacts_cost(db, c, uuid4(), run(c), value)
    assert db.calls == []


@pytest.mark.parametrize("value", [0, 51, 1_000_000_000_000])
async def test_an_authenticated_overrun_reaches_guarded_sql_without_authorizing_a_new_charge(value):
    c, db, token = context(), Database(), uuid4()
    await record_contacts_cost(db, c, token, run(c), value)
    assert db.calls[0] == (c.tenant, c.actor)
    assert db.calls[1][1] == {"business": c.business, "effect": c.effect, "token": token, "run": "run", "cost": value}
    assert "reference_contacts_record_cost" in db.calls[1][0]
