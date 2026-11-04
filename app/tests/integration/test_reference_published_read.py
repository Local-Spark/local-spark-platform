"""Published reference projection stays tenant-bound and preserves choices."""

from uuid import uuid4

import pytest
from sqlalchemy import text

from app.services.auth import AuthError
from app.services.reference_published_read import read_published_references
from app.tests.integration.test_reference_real_selection import _confirm, _result, _seed

pytestmark = pytest.mark.integration


async def test_active_owners_share_current_radii_and_keep_only_selected_historical_occurrences(admin, database, seeded):
    tenant, business, first, old_cycle = await _seed(admin, seeded)
    shared_place, discarded_place = uuid4(), uuid4()
    old_result, old_candidates, _ = await _result(
        admin, tenant, business, first, old_cycle, 5, places=[shared_place, discarded_place]
    )
    await _confirm(admin, tenant, business, first, uuid4(), [old_result], [old_candidates[0]])
    cycle = uuid4()
    second = seeded["a2"]
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO memberships(tenant_id,actor_id,role) VALUES(:tenant,:actor,'owner')"),
            {"tenant": tenant, "actor": second},
        )
        await connection.execute(
            text("INSERT INTO reference_real_cycles(tenant_id,business_id,id) VALUES(:tenant,:business,:cycle)"),
            {"tenant": tenant, "business": business, "cycle": cycle},
        )
        await connection.execute(
            text("UPDATE reference_real_heads SET cycle_id=:cycle WHERE tenant_id=:tenant AND business_id=:business"),
            {"tenant": tenant, "business": business, "cycle": cycle},
        )
    r5, c5, _ = await _result(admin, tenant, business, first, cycle, 5, places=[shared_place, uuid4()])
    r20, c20, _ = await _result(admin, tenant, business, first, cycle, 20)
    _, private_candidates, _ = await _result(admin, tenant, business, first, cycle, 50, published=False)
    await _confirm(admin, tenant, business, second, uuid4(), [old_result, r20], [old_candidates[0], c20[0]])

    a = await read_published_references(database, tenant, business, first)
    b = await read_published_references(database, tenant, business, second)
    assert a == b and a.cycle_id == cycle and a.locked_until is not None
    assert {search.radius_km for search in a.searches} == {5, 20, 50}
    private = next(search for search in a.searches if search.radius_km == 50)
    assert private.state == "completed" and not private.published and private.candidates == ()
    assert {candidate.candidate_id for candidate in a.selected} == {old_candidates[0], c20[0]}
    assert {candidate.cycle_id for candidate in a.selected} == {old_cycle, cycle}
    assert {candidate.candidate_id for search in a.searches for candidate in search.candidates} == set(c5 + c20)
    assert all(item.candidate_id != old_candidates[1] for item in a.selected)
    assert all(item.candidate_id not in private_candidates for search in a.searches for item in search.candidates)
    assert all(item.result_id in {old_result, r5, r20} for item in a.selected)
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await read_published_references(database, tenant, business, seeded["viewer"])
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await read_published_references(database, seeded["t2"], business, second)
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"),
            {"tenant": tenant, "actor": second},
        )
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await read_published_references(database, tenant, business, second)
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE memberships SET active=true WHERE tenant_id=:tenant AND actor_id=:actor"),
            {"tenant": tenant, "actor": second},
        )
        await connection.execute(text("UPDATE user_accounts SET active=false WHERE id=:actor"), {"actor": second})
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await read_published_references(database, tenant, business, second)


async def test_empty_published_and_occupied_unpublished_searches_are_not_conflated(admin, database, seeded):
    tenant, business, actor, cycle = await _seed(admin, seeded)
    empty_result, _, _ = await _result(admin, tenant, business, actor, cycle, 5)
    await _result(admin, tenant, business, actor, cycle, 20, state="pending", published=False)
    async with admin.begin() as connection:
        await connection.execute(
            text("DELETE FROM reference_provider_result_candidates WHERE tenant_id=:tenant AND result_id=:result"),
            {"tenant": tenant, "result": empty_result},
        )
    value = await read_published_references(database, tenant, business, actor)
    by_radius = {search.radius_km: search for search in value.searches}
    assert by_radius[5].state == "completed" and by_radius[5].published and by_radius[5].candidates == ()
    assert by_radius[20].state == "pending" and not by_radius[20].published and by_radius[20].candidates == ()
