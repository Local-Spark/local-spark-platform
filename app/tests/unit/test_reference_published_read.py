"""The internal projection distinguishes current lists and retained choices."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.auth import AuthError
from app.services.reference_published_read import read_published_references


def _database(rows):
    result = MagicMock()
    result.mappings.return_value.all.return_value = rows
    session = SimpleNamespace(execute=AsyncMock(return_value=result))

    @asynccontextmanager
    async def transaction(tenant, actor):
        yield session

    return SimpleNamespace(transaction=transaction), session


def _row(cycle, search, result, candidate, place, *, radius=5, selected=False):
    return {
        "current_cycle": cycle,
        "locked_until": datetime(2027, 5, 1, tzinfo=UTC),
        "search_id": search,
        "cycle_id": cycle,
        "radius_km": radius,
        "search_state": "completed",
        "published": True,
        "result_id": result,
        "candidate_id": candidate,
        "place_identity": place,
        "place_id": "synthetic-place-id",
        "position": 1,
        "reputation_score": Decimal("8.5"),
        "reputation_formula_version": "test-v1",
        "selected": selected,
    }


async def test_current_radii_and_selected_historical_occurrence_are_distinct():
    tenant, business, actor, cycle, old = [uuid4() for _ in range(5)]
    first, second, old_search, result1, result2, result3, c1, c2, c3, p1, p2 = [uuid4() for _ in range(11)]
    rows = [
        _row(cycle, first, result1, c1, p1),
        _row(cycle, second, result2, c2, p2, radius=20, selected=True),
        {**_row(cycle, old_search, result3, c3, p1, radius=50, selected=True), "cycle_id": old},
    ]
    database, session = _database(rows)
    value = await read_published_references(database, tenant, business, actor)
    assert value.cycle_id == cycle
    assert [search.radius_km for search in value.searches] == [5, 20]
    assert [item.candidate_id for item in value.selected] == [c2, c3]
    assert [item.cycle_id for item in value.selected] == [cycle, old]
    assert value.searches[0].candidates[0].place_identity == value.selected[1].place_identity
    assert value.searches[0].candidates[0].score == Decimal("8.5")
    sql = str(session.execute.await_args.args[0]).lower()
    assert "reference_real_published_results" in sql and "s.state='completed'" in sql
    assert all(field not in sql for field in ("rating", "rating_count", "displayname"))
    assert "instagram_handle" in sql and "po.is_primary desc,po.source_position" in sql


async def test_empty_cycle_is_explicit_and_denied_owner_receives_no_data():
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    database, session = _database([{"current_cycle": None, "locked_until": None, "search_id": None}])
    value = await read_published_references(database, tenant, business, actor)
    assert value.cycle_id is None and value.searches == () and value.selected == ()
    session.execute.return_value.mappings.return_value.all.return_value = []
    session.execute.reset_mock()
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await read_published_references(database, tenant, business, actor)
    session.execute.assert_awaited_once()


async def test_occupied_unpublished_and_published_empty_searches_remain_distinct():
    tenant, business, actor, cycle = [uuid4() for _ in range(4)]
    pending, empty = uuid4(), uuid4()
    rows = [
        {**_row(cycle, pending, None, None, None), "search_state": "pending", "published": False},
        {**_row(cycle, empty, uuid4(), None, None, radius=20), "published": True},
    ]
    database, _ = _database(rows)
    value = await read_published_references(database, tenant, business, actor)
    assert [(s.radius_km, s.state, s.published, s.candidates) for s in value.searches] == [
        (5, "pending", False, ()),
        (20, "completed", True, ()),
    ]


async def test_unselected_historical_occurrences_are_not_returned():
    tenant, business, actor, cycle, old = [uuid4() for _ in range(5)]
    row = {**_row(cycle, uuid4(), uuid4(), uuid4(), uuid4()), "cycle_id": old}
    database, _ = _database([row])
    value = await read_published_references(database, tenant, business, actor)
    assert value.searches == () and value.selected == ()
