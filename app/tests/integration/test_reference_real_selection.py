"""Private selection transactions cannot select unpublished real results."""

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.tests.integration.test_reference_discovery import create_business

pytestmark = pytest.mark.integration


async def _seed(admin, seeded):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    cycle = uuid4()
    async with admin.begin() as conn:
        await conn.execute(text("INSERT INTO business_context_heads VALUES(:t,:b,1)"), {"t": tenant, "b": business})
        await conn.execute(
            text("""INSERT INTO business_context_versions
              (tenant_id,business_id,version,operation_id,actor_id,request_hash,document)
              VALUES(:t,:b,1,:op,:actor,:hash,'{}'::jsonb)"""),
            {"t": tenant, "b": business, "op": uuid4(), "actor": actor, "hash": "a" * 64},
        )
        await conn.execute(
            text("INSERT INTO reference_real_cycles(tenant_id,business_id,id) VALUES(:t,:b,:cycle)"),
            {"t": tenant, "b": business, "cycle": cycle},
        )
        await conn.execute(
            text("INSERT INTO reference_real_heads(tenant_id,business_id,cycle_id) VALUES(:t,:b,:cycle)"),
            {"t": tenant, "b": business, "cycle": cycle},
        )
    return tenant, business, actor, cycle


async def _result(admin, tenant, business, actor, cycle, radius, *, published=True, state="completed", places=None):
    search, result = uuid4(), uuid4()
    places = places or [uuid4()]
    candidates = [uuid4() for _ in places]
    async with admin.begin() as conn:
        await conn.execute(
            text("""INSERT INTO reference_provider_searches
              (id,tenant_id,business_id,actor_id,operation_id,context_version,request_mac,state,cycle_id,radius_km,
               identity_key_version)
              VALUES(:id,:t,:b,:actor,:op,1,:mac,:state,:cycle,:radius,'synthetic-v1')"""),
            {
                "id": search,
                "t": tenant,
                "b": business,
                "actor": actor,
                "op": uuid4(),
                "mac": "b" * 64,
                "state": state,
                "cycle": cycle,
                "radius": radius,
            },
        )
        await conn.execute(
            text(
                "INSERT INTO reference_provider_results(tenant_id,business_id,id,search_id) VALUES(:t,:b,:id,:search)"
            ),
            {"t": tenant, "b": business, "id": result, "search": search},
        )
        for position, (place, candidate) in enumerate(zip(places, candidates, strict=True), start=1):
            await conn.execute(
                text("""INSERT INTO reference_provider_places(tenant_id,business_id,id,place_id)
                  VALUES(:t,:b,:id,:place) ON CONFLICT DO NOTHING"""),
                {"t": tenant, "b": business, "id": place, "place": "synthetic-" + str(place)},
            )
            await conn.execute(
                text("""INSERT INTO reference_provider_result_candidates
                  (tenant_id,business_id,result_id,id,place_id,position,reputation_score,reputation_formula_version)
                  VALUES(:t,:b,:result,:id,:place,:position,9.3,'synthetic-v1')"""),
                {"t": tenant, "b": business, "result": result, "id": candidate, "place": place, "position": position},
            )
        if published:
            # Only the privileged test administrator seeds this marker. There
            # is no runtime publication writer or selectable endpoint.
            await conn.execute(
                text("INSERT INTO reference_real_published_results VALUES(:t,:b,:result)"),
                {"t": tenant, "b": business, "result": result},
            )
    return result, candidates, places


async def _confirm(admin, tenant, business, actor, operation, results, candidates):
    async with admin.begin() as conn:
        await conn.execute(text("SELECT set_config('app.tenant_id',:value,true)"), {"value": str(tenant)})
        await conn.execute(text("SELECT set_config('app.actor_id',:value,true)"), {"value": str(actor)})
        return await conn.scalar(
            text("SELECT public.reference_confirm_real_selection(:business,:operation,:results,:candidates)"),
            {"business": business, "operation": operation, "results": results, "candidates": candidates},
        )


async def test_first_confirmation_combines_radii_and_replay_preserves_six_month_deadline(admin, seeded):
    t, b, actor, cycle = await _seed(admin, seeded)
    r1, c1, _ = await _result(admin, t, b, actor, cycle, 5)
    r2, c2, _ = await _result(admin, t, b, actor, cycle, 20)
    op = uuid4()
    first, replay = await asyncio.gather(
        _confirm(admin, t, b, actor, op, [r1, r2], [c1[0], c2[0]]),
        _confirm(admin, t, b, actor, op, [r2, r1], [c2[0], c1[0]]),
    )
    assert first == replay and first["cycle_id"] == str(cycle)
    async with admin.connect() as conn:
        row = (
            (
                await conn.execute(
                    text("""SELECT confirmed_at,locked_until,
          locked_until=((confirmed_at AT TIME ZONE 'UTC')+interval '6 months') AT TIME ZONE 'UTC' AS exact
          FROM reference_real_cycles WHERE id=:cycle"""),
                    {"cycle": cycle},
                )
            )
            .mappings()
            .one()
        )
        assert row["exact"]
        assert await conn.scalar(text("SELECT count(*) FROM reference_real_selected")) == 2
        assert await conn.scalar(text("SELECT count(*) FROM reference_real_selection_operations")) == 1
        assert (
            await conn.scalar(
                text("SELECT count(*) FROM audit_events WHERE action='reference.real_selection_confirmed'")
            )
            == 1
        )
        assert (
            await conn.scalar(
                text("SELECT count(*) FROM outbox_events WHERE event_type='reference.real_selection_confirmed'")
            )
            == 1
        )
    changed = await _confirm(admin, t, b, actor, uuid4(), [r2], [c2[0]])
    assert changed["locked_until"] == first["locked_until"]
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM reference_real_selected")) == 1
        assert (
            await conn.scalar(text("SELECT confirmed_at FROM reference_real_cycles WHERE id=:cycle"), {"cycle": cycle})
            == row["confirmed_at"]
        )
    with pytest.raises(DBAPIError, match="REFERENCE_SELECTION_OPERATION_CONFLICT"):
        await _confirm(admin, t, b, actor, op, [r1], [c1[0]])


async def test_unpublished_or_incomplete_result_never_changes_selection_or_emits_events(admin, seeded):
    t, b, actor, cycle = await _seed(admin, seeded)
    r1, c1, _ = await _result(admin, t, b, actor, cycle, 5, published=False)
    with pytest.raises(DBAPIError, match="REFERENCE_SELECTION_INVALID_CANDIDATE"):
        await _confirm(admin, t, b, actor, uuid4(), [r1], [c1[0]])
    r2, c2, _ = await _result(admin, t, b, actor, cycle, 20, state="pending")
    with pytest.raises(DBAPIError, match="REFERENCE_SELECTION_INVALID_CANDIDATE"):
        await _confirm(admin, t, b, actor, uuid4(), [r2], [c2[0]])
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM reference_real_selected")) == 0
        assert await conn.scalar(text("SELECT count(*) FROM reference_real_selection_operations")) == 0
        assert (
            await conn.scalar(text("SELECT confirmed_at FROM reference_real_cycles WHERE id=:cycle"), {"cycle": cycle})
            is None
        )
        assert (
            await conn.scalar(
                text("SELECT count(*) FROM outbox_events WHERE event_type='reference.real_selection_confirmed'")
            )
            == 0
        )


async def test_previous_selection_can_be_kept_after_cycle_rotation_but_other_old_results_cannot(admin, seeded):
    t, b, actor, old = await _seed(admin, seeded)
    old_result, old_candidates, _ = await _result(admin, t, b, actor, old, 5, places=[uuid4(), uuid4()])
    await _confirm(admin, t, b, actor, uuid4(), [old_result], [old_candidates[0]])
    new = uuid4()
    async with admin.begin() as conn:
        await conn.execute(
            text("INSERT INTO reference_real_cycles(tenant_id,business_id,id) VALUES(:t,:b,:id)"),
            {"t": t, "b": b, "id": new},
        )
        await conn.execute(
            text("UPDATE reference_real_heads SET cycle_id=:id WHERE tenant_id=:t AND business_id=:b"),
            {"t": t, "b": b, "id": new},
        )
    new_result, new_candidates, _ = await _result(admin, t, b, actor, new, 5)
    with pytest.raises(DBAPIError, match="REFERENCE_SELECTION_INVALID_CANDIDATE"):
        await _confirm(admin, t, b, actor, uuid4(), [new_result, old_result], [new_candidates[0], old_candidates[1]])
    result = await _confirm(
        admin, t, b, actor, uuid4(), [new_result, old_result], [new_candidates[0], old_candidates[0]]
    )
    assert result["cycle_id"] == str(new) and len(result["selection"]) == 2


async def test_same_place_cannot_be_selected_twice_even_across_radii(admin, seeded):
    t, b, actor, cycle = await _seed(admin, seeded)
    r1, c1, places = await _result(admin, t, b, actor, cycle, 5)
    r2, c2, _ = await _result(admin, t, b, actor, cycle, 20, places=places)
    with pytest.raises(DBAPIError, match="REFERENCE_SELECTION_DUPLICATE_ENTITY"):
        await _confirm(admin, t, b, actor, uuid4(), [r1, r2], [c1[0], c2[0]])
    with pytest.raises(DBAPIError, match="REFERENCE_SELECTION_DUPLICATE_ENTITY"):
        await _confirm(admin, t, b, actor, uuid4(), [r1, r1], [c1[0], c1[0]])


async def test_another_active_owner_can_select_published_result_with_original_audit(admin, seeded):
    t, b, actor, cycle = await _seed(admin, seeded)
    result, candidates, _ = await _result(admin, t, b, actor, cycle, 5)
    await _confirm(admin, t, b, actor, uuid4(), [result], candidates)
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE memberships SET role='owner' WHERE tenant_id=:t AND actor_id=:actor"),
            {"t": t, "actor": seeded["viewer"]},
        )
    await _confirm(admin, t, b, seeded["viewer"], uuid4(), [result], candidates)
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM reference_real_selected")) == 1
        assert await conn.scalar(text("SELECT count(*) FROM reference_real_selection_operations")) == 2
        actors = set((await conn.execute(text("SELECT actor_id FROM reference_real_selection_operations"))).scalars())
        assert actors == {actor, seeded["viewer"]}
        assert await conn.scalar(text("SELECT actor_id FROM reference_provider_searches")) == actor


@pytest.mark.parametrize(
    "results,candidates", [([], []), ([None], [None]), ([uuid4()], []), ([uuid4()] * 4, [uuid4()] * 4)]
)
async def test_invalid_cardinality_never_confirms_a_cycle(admin, seeded, results, candidates):
    t, b, actor, cycle = await _seed(admin, seeded)
    with pytest.raises(DBAPIError, match="REFERENCE_REAL_SELECTION_INVALID"):
        await _confirm(admin, t, b, actor, uuid4(), results, candidates)
    async with admin.connect() as conn:
        assert (
            await conn.scalar(text("SELECT confirmed_at FROM reference_real_cycles WHERE id=:cycle"), {"cycle": cycle})
            is None
        )


async def test_runtime_cannot_read_write_or_invoke_private_selection(admin, seeded, database, relay_database):
    t, b, actor, cycle = await _seed(admin, seeded)
    r, c, _ = await _result(admin, t, b, actor, cycle, 5)
    async with database.transaction(t, actor) as session:
        assert await session.scalar(text("SELECT count(*) FROM reference_real_published_results")) == 1
        assert await session.scalar(text("SELECT count(*) FROM reference_real_selected")) == 0
    with pytest.raises(DBAPIError):
        async with relay_database.transaction(t, actor) as session:
            await session.execute(text("SELECT * FROM reference_real_selected"))
    for db in (database, relay_database):
        with pytest.raises(DBAPIError):
            async with db.transaction(t, actor) as session:
                await session.execute(
                    text("INSERT INTO reference_real_published_results VALUES(:t,:b,:r)"), {"t": t, "b": b, "r": r}
                )
        with pytest.raises(DBAPIError):
            async with db.transaction(t, actor) as session:
                await session.execute(
                    text("SELECT reference_confirm_real_selection(:b,:op,:r,:c)"),
                    {"b": b, "op": uuid4(), "r": [r], "c": c},
                )
    with pytest.raises(DBAPIError, match="REFERENCE_OWNER_INACTIVE"):
        await _confirm(admin, t, b, seeded["viewer"], uuid4(), [r], c)
    with pytest.raises(DBAPIError, match="REFERENCE_SELECTION_NO_CYCLE"):
        await _confirm(admin, seeded["t2"], b, seeded["a2"], uuid4(), [r], c)
