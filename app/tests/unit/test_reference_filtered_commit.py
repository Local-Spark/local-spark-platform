"""Only a sanitized batch and fenced operation identity reach the DB call."""

import json
from contextlib import asynccontextmanager
from dataclasses import replace
from uuid import uuid4

import pytest

from app.schemas.reference_filtered_batch import FilteredBatch
from app.services.reference_filtered_commit import FilteredCommitContext, FilteredCommitError, commit_filtered_batch


def context():
    ids = [uuid4() for _ in range(11)]
    return FilteredCommitContext(*ids, source_batch_mac="a" * 64, context_version=1)


def batch():
    return FilteredBatch(
        candidates=(
            {
                "candidate_id": uuid4(),
                "place_id": "fixture-place",
                "reputation_score": "8.25",
                "reputation_formula_version": "penalized-3.4-v1",
            },
        )
    )


class FakeDatabase:
    def __init__(self, result):
        self.result, self.calls = result, []

    @asynccontextmanager
    async def transaction(self, tenant, actor):
        self.calls.append((tenant, actor))
        yield self

    async def scalar(self, statement, params):
        self.calls.append((str(statement), params))
        return self.result


async def test_commit_sends_only_allowlisted_batch_and_exact_fences():
    ctx, data = context(), batch()
    database = FakeDatabase(ctx.batch)
    assert await commit_filtered_batch(database, ctx, data) == ctx.batch
    assert database.calls[0] == (ctx.tenant, ctx.actor)
    statement, params = database.calls[1]
    assert "reference_filtered_commit" in statement
    assert params["google_token"] == ctx.google_token and params["jev_token"] == ctx.jev_token
    assert params["source"] == ctx.source_batch_mac and params["context"] == ctx.context_version
    rows = json.loads(params["candidates"])
    assert rows == [
        {
            "candidate_id": str(data.candidates[0].candidate_id),
            "place_id": "fixture-place",
            "reputation_score": "8.25",
            "reputation_formula_version": "penalized-3.4-v1",
        }
    ]
    assert "fixture-place" not in repr(ctx)


@pytest.mark.parametrize(
    "change",
    [
        {"tenant": "x"},
        {"google_effect": None},
        {"source_batch_mac": None},
        {"source_batch_mac": "not-a-mac"},
        {"context_version": 0},
        {"context_version": True},
        {"context_version": 2**63},
    ],
)
async def test_invalid_context_never_reaches_database(change):
    ctx, database = replace(context(), **change), FakeDatabase(None)
    with pytest.raises(FilteredCommitError, match="REFERENCE_FILTERED_INPUT_INVALID"):
        await commit_filtered_batch(database, ctx, batch())
    assert database.calls == []


async def test_invalid_batch_context_and_duplicated_effect_fail_closed():
    ctx, database = context(), FakeDatabase(None)
    for bad_context, bad_batch in ((None, batch()), (ctx, {}), (replace(ctx, jev_effect=ctx.google_effect), batch())):
        with pytest.raises(FilteredCommitError, match="REFERENCE_FILTERED_INPUT_INVALID"):
            await commit_filtered_batch(database, bad_context, bad_batch)
    assert not database.calls


async def test_unexpected_database_return_is_not_treated_as_commit():
    ctx = context()
    with pytest.raises(FilteredCommitError, match="REFERENCE_FILTERED_RESULT_INVALID"):
        await commit_filtered_batch(FakeDatabase(uuid4()), ctx, batch())
