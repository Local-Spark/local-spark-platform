"""The future sanitized result store is isolated and read-only to runtime."""

from decimal import Decimal
from importlib import import_module
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db.session import Database
from app.tests.integration.test_reference_discovery import create_business, local_scope, save_scope
from app.tests.unit.test_core import access_token

pytestmark = pytest.mark.integration


async def _seed_result(admin, seeded):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    base = f"/api/v1/organizations/{tenant}/businesses/{business}"
    return tenant, actor, business, base


async def _insert_synthetic_result(admin, tenant, business, actor):
    search, result, place, candidate = (uuid4() for _ in range(4))
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO reference_provider_searches
              (id,tenant_id,business_id,actor_id,operation_id,context_version,request_mac,state)
              VALUES(:id,:tenant,:business,:actor,:op,1,:mac,'completed')"""),
            {"id": search, "tenant": tenant, "business": business, "actor": actor, "op": uuid4(), "mac": "a" * 64},
        )
        await connection.execute(
            text("""INSERT INTO reference_provider_results(tenant_id,business_id,id,search_id)
              VALUES(:tenant,:business,:id,:search)"""),
            {"tenant": tenant, "business": business, "id": result, "search": search},
        )
        await connection.execute(
            text("""INSERT INTO reference_provider_places(tenant_id,business_id,id,place_id)
              VALUES(:tenant,:business,:id,'synthetic-place-1')"""),
            {"tenant": tenant, "business": business, "id": place},
        )
        await connection.execute(
            text("""INSERT INTO reference_provider_result_candidates
              (tenant_id,business_id,result_id,id,place_id,position,reputation_score,
               reputation_formula_version,jev_recommendation_rank)
              VALUES(:tenant,:business,:result,:id,:place,1,:score,'test-v1',1)"""),
            {
                "tenant": tenant,
                "business": business,
                "result": result,
                "id": candidate,
                "place": place,
                "score": Decimal("9.123456789"),
            },
        )
        await connection.execute(
            text("""INSERT INTO reference_provider_profile_options
              (tenant_id,business_id,result_id,candidate_id,instagram_handle,source_position,source,association_status)
              VALUES(:tenant,:business,:result,:candidate,'synthetic_profile',1,'apify','unverified')"""),
            {"tenant": tenant, "business": business, "result": result, "candidate": candidate},
        )
        await connection.execute(
            text("""INSERT INTO reference_provider_profile_options
              (tenant_id,business_id,result_id,candidate_id,instagram_handle,source_position,is_primary,source,association_status)
              VALUES(:tenant,:business,:result,:candidate,'aaa_profile',2,true,'apify','unverified')"""),
            {"tenant": tenant, "business": business, "result": result, "candidate": candidate},
        )
    return search, result, place, candidate


async def _setup(admin, api, seeded, settings):
    tenant, actor, business, base = await _seed_result(admin, seeded)
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    response = await save_scope(api, base, owner, 0, local_scope(5))
    assert response.status_code == 200
    values = await _insert_synthetic_result(admin, tenant, business, actor)
    return tenant, actor, business, values


async def test_owner_can_read_but_runtime_cannot_write_and_other_tenants_are_isolated(
    admin, api, seeded, settings, database
):
    tenant, actor, business, (_, result, place, candidate) = await _setup(admin, api, seeded, settings)
    tables = (
        "reference_provider_places",
        "reference_provider_results",
        "reference_provider_result_candidates",
        "reference_provider_profile_options",
    )
    async with database.transaction(tenant, actor) as session:
        for table in tables:
            assert await session.scalar(text(f"SELECT count(*) FROM {table}")) == 0
    async with admin.begin() as conn:
        await conn.execute(
            text("INSERT INTO reference_real_published_results VALUES(:t,:b,:r)"),
            {"t": tenant, "b": business, "r": result},
        )
    async with database.transaction(tenant, actor) as session:
        for table in tables:
            expected = 2 if table.endswith("options") else 1
            assert await session.scalar(text(f"SELECT count(*) FROM {table}")) == expected
        ordered = (
            await session.execute(
                text(
                    "SELECT instagram_handle,is_primary FROM "
                    "reference_provider_profile_options ORDER BY source_position"
                )
            )
        ).all()
        assert ordered == [("synthetic_profile", False), ("aaa_profile", True)]
        assert await session.scalar(
            text("SELECT reputation_score FROM reference_provider_result_candidates")
        ) == Decimal("9.123456789")
    for other_tenant, other_actor in ((tenant, seeded["viewer"]), (seeded["t2"], seeded["a2"])):
        async with database.transaction(other_tenant, other_actor) as session:
            for table in tables:
                assert await session.scalar(text(f"SELECT count(*) FROM {table}")) == 0

    statements = (
        (
            "INSERT INTO reference_provider_places(tenant_id,business_id,id,place_id) "
            "VALUES(:tenant,:business,:id,'synthetic-other')",
            {"id": uuid4()},
        ),
        ("UPDATE reference_provider_results SET search_id=search_id WHERE id=:id", {"id": result}),
        ("UPDATE reference_provider_result_candidates SET reputation_score=0 WHERE id=:id", {"id": candidate}),
        ("DELETE FROM reference_provider_profile_options WHERE candidate_id=:id", {"id": candidate}),
    )
    for statement, params in statements:
        with pytest.raises(DBAPIError):
            async with database.transaction(tenant, actor) as session:
                await session.execute(text(statement), {"tenant": tenant, "business": business, **params})
    worker = Database(settings, correlator=True)
    try:
        with pytest.raises(DBAPIError):
            async with worker.transaction(tenant, actor) as session:
                await session.execute(text("SELECT * FROM reference_provider_results"))
    finally:
        await worker.close()


async def test_result_constraints_and_downgrade_protect_sanitized_history(admin, api, seeded, settings):
    tenant, actor, business, (search, result, place, candidate) = await _setup(admin, api, seeded, settings)
    other_business = await create_business(admin, seeded["t2"])
    async with admin.begin() as connection:
        params = {"tenant": tenant, "business": business, "result": result, "place": place, "candidate": candidate}
        other_place = uuid4()
        await connection.execute(
            text("""INSERT INTO reference_provider_places(tenant_id,business_id,id,place_id)
              VALUES(:tenant,:business,:id,'synthetic-place-2')"""),
            {"tenant": tenant, "business": business, "id": other_place},
        )
        invalid = (
            (
                """INSERT INTO reference_provider_results(tenant_id,business_id,id,search_id)
                 VALUES(:tenant,:business,gen_random_uuid(),:search)""",
                {"search": search},
            ),
            (
                """INSERT INTO reference_provider_result_candidates
                 (tenant_id,business_id,result_id,id,place_id,position,reputation_score,reputation_formula_version)
                 VALUES(:tenant,:business,:result,gen_random_uuid(),:place,11,1,'v1')""",
                {},
            ),
            (
                """INSERT INTO reference_provider_result_candidates
                 (tenant_id,business_id,result_id,id,place_id,position,reputation_score,reputation_formula_version)
                 VALUES(:tenant,:business,:result,gen_random_uuid(),:place,2,11,'v1')""",
                {},
            ),
            (
                """INSERT INTO reference_provider_result_candidates
                 (tenant_id,business_id,result_id,id,place_id,position,reputation_score,
                  reputation_formula_version,jev_recommendation_rank)
                 VALUES(:tenant,:business,:result,gen_random_uuid(),:other_place,2,9,'v1',4)""",
                {"other_place": other_place},
            ),
            (
                """INSERT INTO reference_provider_result_candidates
                 (tenant_id,business_id,result_id,id,place_id,position,reputation_score,
                  reputation_formula_version,jev_recommendation_rank)
                 VALUES(:tenant,:business,:result,gen_random_uuid(),:other_place,2,9,'v1',1)""",
                {"other_place": other_place},
            ),
            (
                """INSERT INTO reference_provider_results(tenant_id,business_id,id,search_id)
                 VALUES(:tenant,:other_business,gen_random_uuid(),:search)""",
                {"search": search, "other_business": other_business},
            ),
            (
                """INSERT INTO reference_provider_profile_options
                 (tenant_id,business_id,result_id,candidate_id,instagram_handle,source_position,source,association_status)
                 VALUES(:tenant,:business,:result,:candidate,'other',2,'apify','confirmed')""",
                {},
            ),
            (
                """INSERT INTO reference_provider_profile_options
                 (tenant_id,business_id,result_id,candidate_id,instagram_handle,source_position,source,association_status)
                 VALUES(:tenant,:business,:result,:candidate,'other',2,'google','unverified')""",
                {},
            ),
            (
                """INSERT INTO reference_provider_profile_options
                 (tenant_id,business_id,result_id,candidate_id,instagram_handle,source_position,source,association_status)
                 VALUES(:tenant,:business,:result,:candidate,'other',1,'apify','unverified')""",
                {},
            ),
            (
                """INSERT INTO reference_provider_profile_options
                 (tenant_id,business_id,result_id,candidate_id,instagram_handle,source_position,source,association_status)
                 VALUES(:tenant,:business,:result,:candidate,'other',0,'apify','unverified')""",
                {},
            ),
            (
                """INSERT INTO reference_provider_profile_options
                 (tenant_id,business_id,result_id,candidate_id,instagram_handle,source_position,is_primary,source,association_status)
                 VALUES(:tenant,:business,:result,:candidate,'other',3,true,'apify','unverified')""",
                {},
            ),
        )
        for statement, extra in invalid:
            with pytest.raises(DBAPIError):
                async with connection.begin_nested():
                    await connection.execute(text(statement), {**params, **extra})

        columns = (
            (
                await connection.execute(
                    text("""SELECT column_name FROM information_schema.columns
                  WHERE table_schema='public' AND table_name IN
                  ('reference_provider_places','reference_provider_results','reference_provider_result_candidates',
                   'reference_provider_profile_options')""")
                )
            )
            .scalars()
            .all()
        )
        assert not {"rating", "rating_count", "google_name", "latitude", "longitude", "website", "raw"} & set(columns)
        migration = import_module("migrations.versions.0075_reference_results_storage")
        with pytest.raises(DBAPIError, match="REFERENCE_PROVIDER_RESULTS_PREVENT_AUTOMATIC_DOWNGRADE"):
            async with connection.begin_nested():
                await connection.run_sync(lambda sync: _downgrade(migration, sync))
        assert await connection.scalar(text("SELECT count(*) FROM reference_provider_result_candidates")) == 1


def _downgrade(migration, connection):
    with Operations.context(MigrationContext.configure(connection)):
        migration.downgrade()
