from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import uuid4, uuid5

import pytest
from pydantic import SecretStr

from app.services.reference_contacts_budget_guard import (
    ContactsGuardContext,
    ContactsGuardError,
    DatabaseContactsBudgetGuard,
)


class Database:
    def __init__(self):
        self.calls = []

    @asynccontextmanager
    async def transaction(self, tenant, actor):
        self.calls.append((tenant, actor))
        yield self

    async def scalar(self, statement, params):
        self.calls.append((str(statement), params))


def context():
    return ContactsGuardContext(
        uuid4(),
        uuid4(),
        uuid4(),
        uuid4(),
        uuid4(),
        uuid4(),
        "place-id",
        uuid4(),
        uuid4(),
        uuid4(),
        uuid4(),
        1,
        SecretStr("x" * 32),
        "key",
        "tariff",
        "credential",
        50,
        "1.2.3",
        "actor",
    )


@pytest.mark.parametrize("wrong", ["missing", "different"])
async def test_inspection_never_adopts_an_unrecorded_or_different_run(monkeypatch, wrong):
    c, db = context(), Database()
    run, other = object(), object()

    async def load(database, context):
        assert database is db and context == c
        return None if wrong == "missing" else (other, uuid4(), None)

    monkeypatch.setattr("app.services.reference_contacts_runs.load_contacts_run", load)
    guard = DatabaseContactsBudgetGuard(db, c)
    assert not await guard.claim_inspection(uuid5(c.effect, "contacts-inspection-v1"), SimpleNamespace(submission=run))
    with pytest.raises(ContactsGuardError, match="FENCE_INVALID"):
        guard.execution_token()
    assert db.calls == []


async def test_uncertain_get_marks_original_paid_effect_without_new_reservation(monkeypatch):
    c, db, run, token = context(), Database(), object(), uuid4()

    async def load(database, context):
        assert database is db and context == c
        return run, token, None

    monkeypatch.setattr("app.services.reference_contacts_runs.load_contacts_run", load)
    guard = DatabaseContactsBudgetGuard(db, c)
    await guard.inspection_uncertain(uuid5(c.effect, "contacts-inspection-v1"), SimpleNamespace(submission=run))
    assert guard.execution_token() == token
    assert db.calls[0] == (c.tenant, c.actor)
    assert "reference_provider_uncertain" in db.calls[1][0]
    assert db.calls[1][1] == {"effect": c.effect, "token": token}
    assert len(db.calls) == 2
