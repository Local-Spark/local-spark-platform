"""Private top-ten preparation is fenced and does not choose tie winners."""

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.tests.integration.reference_identity_fixture import prepare_review_fixture
from app.tests.integration.test_reference_filtered_batch_storage import _params
from app.tests.integration.test_reference_filtered_fence import _commit, _linked

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("historical_filtered_writer")]
_SQL = text("SELECT public.reference_prepare_shortlist(:business,:search,:batch,:operation,:candidates)")
_SIG = "public.reference_prepare_shortlist(uuid,uuid,uuid,uuid,uuid[])"


async def test_private_preparation_never_omits_higher_score_and_replays_once(admin, api, seeded, settings, database):
    google, jev, gg, jg, worker, candidate = await _linked(admin, api, seeded, settings)
    filtered = _params(google, jev, gg, jg, candidate)
    try:
        await _commit(worker, google, filtered)
        await prepare_review_fixture(admin, api, settings, google, filtered["batch"])
        extra = [uuid4() for _ in range(10)]
        async with admin.begin() as connection:
            for score, identifier in enumerate(extra):
                await connection.execute(
                    text("""INSERT INTO reference_filtered_batch_candidates
                  (tenant_id,business_id,actor_id,batch_id,candidate_id,position,place_id,reputation_score,
                   reputation_formula_version)
                  VALUES(:tenant,:business,:actor,:batch,:candidate,:position,:place,:score,'penalized-3.4-v1')"""),
                    {
                        "tenant": google.tenant,
                        "business": google.business,
                        "actor": google.actor,
                        "batch": filtered["batch"],
                        "candidate": identifier,
                        "position": score + 2,
                        "place": f"synthetic-{score}",
                        "score": score,
                    },
                )
        selected = [extra[9], candidate, *reversed(extra[1:9])]
        params = {
            "business": google.business,
            "search": google.search,
            "batch": filtered["batch"],
            "operation": uuid4(),
            "candidates": selected,
        }

        async def prepare(values):
            async with worker.transaction(google.tenant, google.actor) as session:
                return await session.scalar(_SQL, values)

        with pytest.raises(DBAPIError):
            async with database.transaction(google.tenant, google.actor) as session:
                await session.scalar(_SQL, params)
        async with admin.begin() as connection:
            await connection.execute(text(f"GRANT EXECUTE ON FUNCTION {_SIG} TO meu_braco_direito_correlator"))
            await connection.execute(
                text("""INSERT INTO business_context_versions
              (tenant_id,business_id,version,operation_id,actor_id,request_hash,document)
              SELECT tenant_id,business_id,2,:operation,actor_id,request_hash,document FROM business_context_versions
              WHERE tenant_id=:tenant AND business_id=:business AND version=1"""),
                {"operation": uuid4(), "tenant": google.tenant, "business": google.business},
            )
            await connection.execute(
                text("UPDATE business_context_heads SET version=2 WHERE tenant_id=:tenant AND business_id=:business"),
                {"tenant": google.tenant, "business": google.business},
            )
        with pytest.raises(DBAPIError, match="REFERENCE_(SHORTLIST_CONTEXT_STALE|BUSINESS_IDENTITY_STALE)"):
            await prepare(params)
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE business_context_heads SET version=1 WHERE tenant_id=:tenant AND business_id=:business"),
                {"tenant": google.tenant, "business": google.business},
            )
        for invalid in (
            selected[:-1],
            [*selected[:-1], extra[0]],
            list(reversed(selected)),
            [*selected[:-1], selected[0]],
            [*selected[:-1], uuid4()],
            [None],
        ):
            with pytest.raises(DBAPIError, match="REFERENCE_SHORTLIST_(INVALID|RANK_INVALID)"):
                await prepare({**params, "candidates": invalid})
        result = await asyncio.gather(prepare(params), prepare(params))
        assert sorted(item["created"] for item in result) == [False, True]
        assert result[0]["event_id"] == result[1]["event_id"]
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE business_context_heads SET version=2 WHERE tenant_id=:tenant AND business_id=:business"),
                {"tenant": google.tenant, "business": google.business},
            )
        with pytest.raises(DBAPIError, match="REFERENCE_BUSINESS_IDENTITY_STALE"):
            await prepare(params)
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE business_context_heads SET version=1 WHERE business_id=:b"), {"b": google.business}
            )
        assert (await prepare(params))["created"] is False
        with pytest.raises(DBAPIError, match="REFERENCE_SHORTLIST_REPLAY_CONFLICT"):
            await prepare({**params, "candidates": list(reversed(selected))})
        with pytest.raises(DBAPIError):
            async with worker.transaction(seeded["t2"], seeded["a2"]) as session:
                await session.scalar(_SQL, params)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM reference_private_shortlist")) == 10
            assert await connection.scalar(text("SELECT count(*) FROM reference_filtered_batch_candidates")) == 11
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM audit_events WHERE action='reference.shortlist_prepared'")
                )
                == 1
            )
    finally:
        await worker.close()
        async with admin.begin() as connection:
            await connection.execute(text(f"GRANT EXECUTE ON FUNCTION {_SIG} TO meu_braco_direito_correlator"))
