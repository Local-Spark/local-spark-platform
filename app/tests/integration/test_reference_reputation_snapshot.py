"""Persist the fictional score and ranking at discovery time, not at read time."""

import asyncio
from contextlib import suppress
from dataclasses import replace
from decimal import ROUND_DOWN, Decimal, localcontext
from importlib import import_module
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.services import reference_discovery as discovery_service
from app.services.reference_simulated_candidates import simulated_candidates
from app.tests.integration.test_reference_cycle import search
from app.tests.integration.test_reference_discovery import create_business, local_scope, save_scope
from app.tests.unit.test_core import access_token
from app.workflows import reference_discovery_activities as discovery_activities

pytestmark = pytest.mark.integration


def _apply_migration(connection, direction):
    migration = import_module("migrations.versions.0073_reference_score_snapshot")
    with Operations.context(MigrationContext.configure(connection)):
        getattr(migration, direction)()


async def test_score_migration_refuses_existing_fixtures_without_losing_them(admin):
    async with admin.begin() as connection:
        # Shadow the table only in this transaction; the real schema is untouched.
        await connection.execute(text("CREATE TEMP TABLE reference_discovery_candidates(id integer) ON COMMIT DROP"))
        await connection.execute(text("INSERT INTO reference_discovery_candidates(id) VALUES (1),(2)"))
        with pytest.raises(DBAPIError, match="REFERENCE_CANDIDATES_REQUIRE_SCORE_RECONCILIATION"):
            async with connection.begin_nested():
                await connection.run_sync(lambda sync: _apply_migration(sync, "upgrade"))
        ids = (
            (await connection.execute(text("SELECT id FROM reference_discovery_candidates ORDER BY id")))
            .scalars()
            .all()
        )
        assert ids == [1, 2]


async def test_score_migration_requires_full_valid_snapshot_and_protects_history(admin):
    async with admin.begin() as connection:
        await connection.execute(text("CREATE TEMP TABLE reference_discovery_candidates(id integer) ON COMMIT DROP"))
        await connection.run_sync(lambda sync: _apply_migration(sync, "upgrade"))
        statement = text("""INSERT INTO reference_discovery_candidates
          (id,reputation_score_snapshot,reputation_formula_version,reputation_fixture_version)
          VALUES(:id,:score,:formula,:fixture)""")
        for score, formula, fixture in (
            (None, "formula-v1", "fixture-v1"),
            (Decimal("10.01"), "formula-v1", "fixture-v1"),
            (Decimal("5"), "", "fixture-v1"),
            (Decimal("5"), "formula-v1", None),
        ):
            with pytest.raises(DBAPIError):
                async with connection.begin_nested():
                    await connection.execute(
                        statement, {"id": 1, "score": score, "formula": formula, "fixture": fixture}
                    )
        await connection.execute(
            statement, {"id": 1, "score": Decimal("8.7654321"), "formula": "formula-v1", "fixture": "fixture-v1"}
        )
        with pytest.raises(DBAPIError, match="REFERENCE_SCORE_SNAPSHOTS_PREVENT_AUTOMATIC_DOWNGRADE"):
            async with connection.begin_nested():
                await connection.run_sync(lambda sync: _apply_migration(sync, "downgrade"))
        score = await connection.scalar(text("SELECT reputation_score_snapshot FROM reference_discovery_candidates"))
        assert score == Decimal("8.7654321")


@pytest.mark.parametrize(
    ("direction", "error"),
    [
        ("upgrade", "REFERENCE_CANDIDATES_REQUIRE_SCORE_RECONCILIATION"),
        ("downgrade", "REFERENCE_SCORE_SNAPSHOTS_PREVENT_AUTOMATIC_DOWNGRADE"),
    ],
)
async def test_score_migration_waits_for_concurrent_insert_and_preserves_it(admin, direction, error):
    # The schema is unique to this test in the dedicated _test database. Using
    # separate connections demonstrates a real conflicting PostgreSQL lock.
    schema = f"reference_snapshot_{uuid4().hex}"
    table = f'"{schema}".reference_discovery_candidates'
    async with admin.begin() as connection:
        await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        columns = (
            "id integer, reputation_score_snapshot numeric, reputation_formula_version text, "
            "reputation_fixture_version text"
            if direction == "downgrade"
            else "id integer"
        )
        await connection.execute(text(f"CREATE TABLE {table} ({columns})"))

    insertion = await admin.connect()
    insertion_tx = await insertion.begin()
    migration_task = None
    try:
        blocker_pid = await insertion.scalar(text("SELECT pg_backend_pid()"))
        if direction == "upgrade":
            await insertion.execute(text(f"INSERT INTO {table}(id) VALUES(1)"))
        else:
            await insertion.execute(
                text(f"""INSERT INTO {table}(id,reputation_score_snapshot,reputation_formula_version,
                  reputation_fixture_version) VALUES(1,8.975,'formula-v1','fixture-v1')""")
            )
        started = asyncio.get_running_loop().create_future()

        async def migrate():
            async with admin.begin() as connection:
                await connection.execute(text(f'SET LOCAL search_path TO "{schema}", pg_catalog'))
                started.set_result(await connection.scalar(text("SELECT pg_backend_pid()")))
                await connection.run_sync(lambda sync: _apply_migration(sync, direction))

        migration_task = asyncio.create_task(migrate())
        migration_pid = await asyncio.wait_for(started, 3)
        async with admin.connect() as observer:

            async def lock_observed():
                while True:
                    blocked = await observer.scalar(
                        text("SELECT CAST(:blocker AS integer) = ANY(pg_blocking_pids(:migration))"),
                        {"blocker": blocker_pid, "migration": migration_pid},
                    )
                    if blocked:
                        return
                    await asyncio.sleep(0.02)

            await asyncio.wait_for(lock_observed(), 3)
        await insertion_tx.commit()
        with pytest.raises(DBAPIError, match=error):
            await asyncio.wait_for(migration_task, 3)
        async with admin.connect() as connection:
            assert await connection.scalar(text(f"SELECT count(*) FROM {table}")) == 1
            if direction == "downgrade":
                assert await connection.scalar(text(f"SELECT reputation_score_snapshot FROM {table}")) == Decimal(
                    "8.975"
                )
    finally:
        if insertion_tx.is_active:
            await insertion_tx.rollback()
        await insertion.close()
        if migration_task is not None and not migration_task.done():
            migration_task.cancel()
            with suppress(asyncio.CancelledError):
                await migration_task
        async with admin.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))


async def test_fictional_scores_and_order_are_snapshots_of_each_discovery(
    admin, api, seeded, settings, database, relay_database, monkeypatch
):
    settings.reference_discovery_mode = "fake"
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    other = {"Authorization": f"Bearer {access_token(settings, seeded['a2'])}"}
    assert (await save_scope(api, base, owner, 0, local_scope(5))).status_code == 200
    first, first_fixtures, first_operation = await search(api, base, owner, database, relay_database)
    assert [item["fixture_number"] for item in first_fixtures] == [1, 2, 3]
    assert [item["reputation_score"] for item in first_fixtures] == ["9.42", "8.97", "8.62"]
    assert all(item["reputation_formula_version"] == "penalized-3.4-v1" for item in first_fixtures)

    # This simulates a future fixture/formula revision. Two scores intentionally
    # display the same value while their full precision requires reverse order.
    first_candidates = {candidate.number: candidate for candidate in simulated_candidates()}
    changed = (
        replace(first_candidates[2], reputation_score=Decimal("9.42"), ordering_score=Decimal("9.4249")),
        replace(first_candidates[1], reputation_score=Decimal("9.42"), ordering_score=Decimal("9.4241")),
        replace(first_candidates[3], reputation_score=Decimal("4.25"), ordering_score=Decimal("4.25")),
    )
    monkeypatch.setattr(discovery_activities, "simulated_candidates", lambda: changed)
    monkeypatch.setattr(discovery_service, "simulated_candidates", lambda: changed, raising=False)
    fixtures_url = base + "/reference-discoveries/" + first["id"] + "/fixtures"
    reread = await api.get(fixtures_url, headers=owner)
    assert reread.status_code == 200
    assert reread.json() == first_fixtures
    replay = await api.post(base + "/reference-discoveries", headers=owner, json={"operation_id": first_operation})
    assert replay.status_code == 200 and replay.json()["id"] == first["id"]
    assert (await api.get(fixtures_url, headers=owner)).json() == first_fixtures

    assert (await save_scope(api, base, owner, 1, local_scope(20))).status_code == 200
    second, second_fixtures, _ = await search(api, base, owner, database, relay_database)
    assert [item["fixture_number"] for item in second_fixtures] == [2, 1, 3]
    assert [item["reputation_score"] for item in second_fixtures] == ["9.42", "9.42", "4.25"]
    assert (await api.get(fixtures_url, headers=owner)).json() == first_fixtures
    assert (await api.get(fixtures_url, headers=other)).status_code == 403
    monkeypatch.setattr(discovery_service, "simulated_candidates", lambda: (), raising=False)
    assert (await api.get(fixtures_url, headers=owner)).json() == first_fixtures
    second_url = base + "/reference-discoveries/" + second["id"] + "/fixtures"
    assert (await api.get(second_url, headers=owner)).json() == second_fixtures

    async with admin.connect() as connection:
        rows = (
            (
                await connection.execute(
                    text("""SELECT fixture_number,reputation_score_snapshot,reputation_formula_version,
                      reputation_fixture_version FROM reference_discovery_candidates
                      WHERE discovery_id=:discovery ORDER BY fixture_number"""),
                    {"discovery": second["id"]},
                )
            )
            .mappings()
            .all()
        )
    assert [row["reputation_score_snapshot"] for row in rows] == [
        Decimal("9.4241"),
        Decimal("9.4249"),
        Decimal("4.25"),
    ]
    assert all(row["reputation_formula_version"] == "penalized-3.4-v1" for row in rows)
    assert all(row["reputation_fixture_version"] == "synthetic-v1" for row in rows)
    with pytest.raises(DBAPIError):
        async with database.transaction(tenant, actor) as session:
            await session.execute(
                text("""UPDATE reference_discovery_candidates SET reputation_score_snapshot=0
                  WHERE discovery_id=:discovery"""),
                {"discovery": second["id"]},
            )
    async with database.transaction(seeded["t2"], seeded["a2"]) as session:
        assert await session.scalar(text("SELECT count(*) FROM reference_discovery_candidates")) == 0


async def test_snapshot_display_uses_stable_rounding(
    admin, api, seeded, settings, database, relay_database, monkeypatch
):
    settings.reference_discovery_mode = "fake"
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    assert (await save_scope(api, base, owner, 0, local_scope(5))).status_code == 200
    original = simulated_candidates()[0]
    monkeypatch.setattr(
        discovery_activities,
        "simulated_candidates",
        lambda: (replace(original, reputation_score=Decimal("8.98"), ordering_score=Decimal("8.975")),),
    )
    found, _, _ = await search(api, base, owner, database, relay_database)
    url = base + "/reference-discoveries/" + found["id"] + "/fixtures"
    with localcontext() as context:
        context.rounding = ROUND_DOWN
        response = await api.get(url, headers=owner)
    assert response.status_code == 200
    assert response.json()[0]["reputation_score"] == "8.98"
