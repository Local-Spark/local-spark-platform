"""Owner learning reads are bounded, truthful and never dispatch provider work."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import DBAPIError

from app.api.v1.reference_learnings import read_learnings
from app.schemas.reference_learnings import ReferenceLearningsRead
from app.services.auth import AuthError
from app.services.reference_learnings import ReferenceLearningsService


def entry(status="partial"):
    analyzed = status in {"partial", "completed"}
    return {
        "reference_id": str(uuid4()),
        "association_version": 1,
        "source": "owner",
        "instagram_handle": "ficticio",
        "analysis_status": status,
        "update_status": "scheduled" if analyzed else "waiting",
        "last_analyzed_at": "2026-11-04T12:00:00Z" if analyzed else None,
        "next_analysis_at": "2027-05-04T12:00:00Z",
        "patterns": [{"dimension": "visual", "observation": "Composições simples"}] if analyzed else [],
    }


def database(value):
    session = SimpleNamespace(scalar=AsyncMock(return_value=value))
    scopes = []

    @asynccontextmanager
    async def transaction(tenant, actor):
        scopes.append((tenant, actor))
        yield session

    return SimpleNamespace(transaction=transaction), session, scopes


@pytest.fixture
def owner(monkeypatch):
    check = AsyncMock()
    monkeypatch.setattr("app.services.reference_learnings.WhatsAppMaterialsService._require_owner", check)
    return check


async def test_route_reads_only_server_state_with_owner_scope(owner):
    raw = {"references": [entry()]}
    db, session, scopes = database(raw)
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(database=db)))
    value = await read_learnings(tenant, business, request, actor)
    assert isinstance(value, ReferenceLearningsRead)
    assert value.references[0].analysis_status == "partial"
    assert value.references[0].patterns[0].observation == "Composições simples"
    assert scopes == [(tenant, actor)]
    owner.assert_awaited_once_with(session, tenant, business, actor)
    session.scalar.assert_awaited_once()
    statement, params = session.scalar.await_args.args
    assert str(statement) == "SELECT public.reference_read_learning_status(:business)"
    assert params == {"business": business}
    assert "Composições simples" not in repr(value)


async def test_unauthorized_owner_never_reads_learning(owner):
    db, session, _ = database({"references": []})
    owner.side_effect = AuthError("BUSINESS_OWNER_REQUIRED", 403)
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await ReferenceLearningsService(db).read(uuid4(), uuid4(), uuid4())
    session.scalar.assert_not_awaited()


@pytest.mark.parametrize(
    "code,status", [("REFERENCE_OWNER_INACTIVE", 403), ("REFERENCE_BUSINESS_NOT_FOUND", 404), ("unknown", None)]
)
async def test_database_authority_failures_remain_safe(owner, code, status):
    db, session, _ = database(None)
    original = DBAPIError("SELECT", {}, RuntimeError(code))
    session.scalar.side_effect = original
    if status is None:
        with pytest.raises(DBAPIError) as caught:
            await ReferenceLearningsService(db).read(uuid4(), uuid4(), uuid4())
        assert caught.value is original
    else:
        with pytest.raises(AuthError) as caught:
            await ReferenceLearningsService(db).read(uuid4(), uuid4(), uuid4())
        assert caught.value.status == status
        assert caught.value.__cause__ is None


@pytest.mark.parametrize("status", ["not_requested", "pending", "unavailable", "completed", "partial"])
def test_status_and_patterns_are_not_inferred(status):
    item = ReferenceLearningsRead.model_validate({"references": [entry(status)]}).references[0]
    assert item.analysis_status == status
    assert bool(item.patterns) == (status in {"completed", "partial"})
    assert ReferenceLearningsRead.model_validate({"references": []}).references == ()


@pytest.mark.parametrize(
    "variant", ["missing_patterns", "unexpected_patterns", "missing_version", "missing_time", "duplicate", "raw_post"]
)
async def test_invalid_persisted_data_is_not_exposed(owner, variant):
    item = entry()
    raw = {"references": [item]}
    if variant == "missing_patterns":
        item["patterns"] = []
    elif variant == "unexpected_patterns":
        item["analysis_status"] = "pending"
    elif variant == "missing_version":
        item["association_version"] = None
    elif variant == "missing_time":
        item["last_analyzed_at"] = None
    elif variant == "duplicate":
        raw["references"] *= 2
    else:
        item["patterns"][0]["caption"] = "Private source post"
    db, _, _ = database(raw)
    with pytest.raises(AuthError, match="REFERENCE_LEARNINGS_UNAVAILABLE") as caught:
        await ReferenceLearningsService(db).read(uuid4(), uuid4(), uuid4())
    assert caught.value.__cause__ is None and caught.value.__suppress_context__
