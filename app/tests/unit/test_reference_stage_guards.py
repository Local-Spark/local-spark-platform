from contextlib import asynccontextmanager
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services import reference_stage_guards as module
from app.tests.unit.test_reference_jev_request_mac import _values
from app.tests.unit.test_reference_recommendation_mac import arguments


def context():
    value = arguments()
    return module.StageContext(
        value["tenant"],
        value["business"],
        value["actor"],
        value["search"],
        value["effect"],
        uuid4(),
        value["pilot"],
        1,
        value["key"],
        value["key_version"],
        value["tariff_version"],
        value["credential_version"],
        100,
        value["source_batch_mac"],
        value["batch_id"],
        value["similarity_effect"],
        value["shortlist"],
    ), value["request"]


def database(result):
    session = SimpleNamespace(scalar=AsyncMock(return_value=result))

    @asynccontextmanager
    async def transaction(*_):
        yield session

    return SimpleNamespace(transaction=transaction), session


async def test_guard_commits_only_metadata_and_exact_request_mac_before_granting_execution(monkeypatch):
    c, request = context()
    token = uuid4()
    db, session = database({"created": True, "executor_token": str(token)})
    guard = module.JevStageGuard(db, c, "recommendation")
    assert not await guard.claim(uuid4(), request)
    assert await guard.claim(c.effect, request)
    assert guard.execution_token() == token
    persisted = session.scalar.call_args.args[1]["intent"]
    assert (
        "secret-provider-credential" not in persisted
        and "private-place" not in persisted
        and "private" not in persisted
    )
    assert not await guard.claim(c.effect, request)
    await guard.uncertain()
    assert session.scalar.call_args.args[1] == {"effect": c.effect, "token": token}


async def test_mapping_can_only_claim_once_and_without_a_reservation_cannot_mark_uncertain():
    c, _ = context()
    db, session = database({"created": False})
    guard = module.JevStageGuard(db, replace(c, batch=None, source_mac="a" * 64), "mapping")
    assert not await guard.claim(c.effect, _values()["request"])
    assert session.scalar.await_count == 1
    with pytest.raises(ValueError, match="REFERENCE_STAGE_NOT_CLAIMED"):
        guard.execution_token()
    with pytest.raises(ValueError, match="REFERENCE_STAGE_NOT_CLAIMED"):
        await guard.uncertain()


@pytest.mark.parametrize(
    "kind,missing",
    [
        ("mapping", "request"),
        ("recommendation", "request"),
        ("recommendation", "batch"),
        ("recommendation", "similarity"),
        ("recommendation", "shortlist"),
    ],
)
async def test_bad_stage_cannot_reserve(kind, missing):
    c, request = context()
    if missing == "request":
        request = object()
    elif missing == "batch":
        c = replace(c, batch=None)
    elif missing == "similarity":
        c = replace(c, similarity_effect=None)
    else:
        c = replace(c, shortlist=None)
    db, session = database(None)
    with pytest.raises(ValueError, match="REFERENCE_STAGE_INVALID"):
        await module.JevStageGuard(db, c, kind).claim(c.effect, request)
    session.scalar.assert_not_awaited()


async def test_places_wrapper_cannot_finish_without_original_execution(monkeypatch):
    c, _ = context()
    guard = module.IntentPlacesGuard(None, c)
    for action in (guard.complete_empty, guard.uncertain):
        with pytest.raises(ValueError, match="PLACES_EXECUTOR_NOT_CLAIMED"):
            await action()
    with pytest.raises(ValueError, match="PLACES_EXECUTOR_NOT_CLAIMED"):
        guard.execution_token()
    created = replace(c, event=uuid4())
    monkeypatch.setattr(module, "create_google_intent", AsyncMock(return_value=created))
    inner = SimpleNamespace(
        claim=AsyncMock(return_value=True),
        complete_empty=AsyncMock(),
        uncertain=AsyncMock(),
        execution_token=lambda: c.effect,
    )
    monkeypatch.setattr(module, "DatabasePlacesBudgetGuard", lambda *_: inner)
    assert await guard.claim(c.effect, object())
    assert guard.context == created
    await guard.complete_empty()
    await guard.uncertain()
    assert guard.execution_token() == c.effect


async def test_contacts_submission_has_one_claim_and_keeps_its_recovery_token(monkeypatch):
    c, _ = context()
    contact = module.ContactsGuardContext(
        c.tenant,
        c.business,
        c.actor,
        uuid4(),
        c.batch,
        uuid4(),
        "place",
        uuid4(),
        c.effect,
        c.event,
        c.pilot,
        1,
        c.key,
        c.key_version,
        c.tariff_version,
        c.credential_version,
        100,
        "1.2.3",
        "actor",
    )
    db, _ = database(None)
    guard = module.IntentContactsGuard(db, contact, c.search, c.source_mac)
    monkeypatch.setattr(guard, "_request_mac", lambda _: "a" * 64)
    token = uuid4()
    claimed = AsyncMock(return_value={"created": True, "executor_token": str(token)})
    monkeypatch.setattr(module, "stage_claim", claimed)
    assert not await guard.claim_submission(uuid4(), object())
    assert await guard.claim_submission(c.effect, object())
    assert guard.execution_token() == token
    assert not await guard.claim_submission(c.effect, object())
    declined = module.IntentContactsGuard(db, contact, c.search, c.source_mac)
    monkeypatch.setattr(declined, "_request_mac", lambda _: "a" * 64)
    claimed.return_value = {"created": False}
    assert not await declined.claim_submission(c.effect, object())
