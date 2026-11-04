import json
from contextlib import asynccontextmanager
from dataclasses import replace
from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.adapters.google_places import PlaceCandidate
from app.adapters.jev_reference_similarity_levels import LeveledSimilarityJudgment
from app.schemas.reference_filtered_batch import FilteredBatch
from app.services.reference_filtered_commit import (
    FilteredCommitContext,
    FilteredCommitError,
)
from app.services.reference_google_batch_mac import google_batch_mac
from app.services.reference_leveled_commit import commit_leveled_batch
from app.services.reference_leveled_observation_sanitizer import (
    sanitize_leveled_observations,
)
from app.services.reference_observation_sanitizer import CandidateObservation


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


def values():
    ids = [uuid4() for _ in range(12)]
    ctx = FilteredCommitContext(*ids[:11], source_batch_mac="a" * 64, context_version=1)
    key = SecretStr("synthetic-key-not-for-production-0123456789")
    observations = (
        CandidateObservation(
            uuid4(),
            PlaceCandidate("place-a", "private name", 1.0, 1.0, 4.5, 20, None, ("cafe",)),
        ),
        CandidateObservation(
            uuid4(),
            PlaceCandidate("place-b", "private other", 2.0, 2.0, 4.9, 40, None, ("shop",)),
        ),
    )
    judgments = (
        LeveledSimilarityJudgment(observations[0].candidate_id, "match", 0.1, (0.8, 0.1, 0.1), "high"),
        LeveledSimilarityJudgment(observations[1].candidate_id, "match", 0.9, (0.8, 0.1, 0.1), "unknown"),
    )
    mac = google_batch_mac(
        key,
        key_version="v1",
        tenant=ctx.tenant,
        business=ctx.business,
        actor=ctx.actor,
        search=ctx.search,
        google_effect=ctx.google_effect,
        pilot=ids[11],
        context_version=1,
        observations=observations,
    )
    ctx = replace(ctx, source_batch_mac=mac)
    filtered = sanitize_leveled_observations(observations, judgments)
    batch = FilteredBatch(
        candidates=tuple(
            {
                "candidate_id": i.candidate_id,
                "place_id": i.place_id,
                "reputation_score": i.reputation_score,
                "reputation_formula_version": i.reputation_formula_version,
            }
            for i in filtered
        )
    )
    return ctx, batch, observations, judgments, key, ids[11]


async def test_sends_only_sanitized_source_bound_evidence_and_fences():
    ctx, batch, observations, judgments, key, pilot = values()
    db = FakeDatabase(ctx.batch)
    assert (
        await commit_leveled_batch(
            db,
            ctx,
            batch,
            observations=observations,
            judgments=judgments,
            source_key=key,
            source_key_version="v1",
            pilot=pilot,
        )
        == ctx.batch
    )
    assert db.calls[0] == (ctx.tenant, ctx.actor)
    statement, params = db.calls[1]
    assert "reference_filtered_commit_with_similarity" in statement
    assert params["google_token"] == ctx.google_token and params["jev_token"] == ctx.jev_token
    assert params["source"] == ctx.source_batch_mac
    evidence = json.loads(params["judgments"])
    assert evidence == [
        {
            "candidate_id": str(j.candidate_id),
            "judgment": j.choice,
            "similarity_level": j.similarity_level,
        }
        for j in judgments
    ]
    candidates = json.loads(params["candidates"])
    assert len(candidates) == 1 and candidates[0]["place_id"] == "place-a"
    assert "private name" not in params["candidates"] + params["judgments"]
    assert "private other" not in params["candidates"] + params["judgments"]
    assert "confidence" not in params["judgments"] and "probabilities" not in params["judgments"]


@pytest.mark.parametrize(
    "change",
    [
        {"tenant": "bad"},
        {"google_effect": None},
        {"source_batch_mac": None},
        {"source_batch_mac": "bad"},
        {"context_version": True},
        {"context_version": 0},
        {"context_version": 2**63},
    ],
)
async def test_invalid_context_never_writes(change):
    ctx, batch, obs, judgments, key, pilot = values()
    db = FakeDatabase(None)
    with pytest.raises(FilteredCommitError, match="REFERENCE_LEVELED_INPUT_INVALID"):
        await commit_leveled_batch(
            db,
            replace(ctx, **change),
            batch,
            observations=obs,
            judgments=judgments,
            source_key=key,
            source_key_version="v1",
            pilot=pilot,
        )
    assert db.calls == []


async def test_rejects_malformed_mapping_tampering_and_unproved_source():
    ctx, batch, obs, judgments, key, pilot = values()
    db = FakeDatabase(None)
    cases = [
        (None, batch, obs, judgments, key, pilot),
        (ctx, {}, obs, judgments, key, pilot),
        (replace(ctx, jev_effect=ctx.google_effect), batch, obs, judgments, key, pilot),
        (ctx, batch, [], judgments, key, pilot),
        (ctx, batch, obs, [], key, pilot),
        (ctx, batch, obs, judgments[:1], key, pilot),
        (ctx, batch, ("bad",), judgments[:1], key, pilot),
        (ctx, batch, obs[:1], ("bad",), key, pilot),
        (ctx, batch, obs, tuple(reversed(judgments)), key, pilot),
        (ctx, batch, obs, judgments, SecretStr("short"), pilot),
        (ctx, batch, obs, judgments, key, uuid4()),
        (ctx, FilteredBatch(candidates=()), obs, judgments, key, pilot),
        (
            ctx,
            batch,
            obs,
            (replace(judgments[0], similarity_level="bad"), judgments[1]),
            key,
            pilot,
        ),
    ]
    for context, b, observations, answers, source_key, source_pilot in cases:
        with pytest.raises(FilteredCommitError, match="REFERENCE_LEVELED_INPUT_INVALID"):
            await commit_leveled_batch(
                db,
                context,
                b,
                observations=observations,
                judgments=answers,
                source_key=source_key,
                source_key_version="v1",
                pilot=source_pilot,
            )
    assert db.calls == []


async def test_unexpected_result_is_not_accepted():
    ctx, batch, obs, judgments, key, pilot = values()
    with pytest.raises(FilteredCommitError, match="REFERENCE_LEVELED_RESULT_INVALID"):
        await commit_leveled_batch(
            FakeDatabase(uuid4()),
            ctx,
            batch,
            observations=obs,
            judgments=judgments,
            source_key=key,
            source_key_version="v1",
            pilot=pilot,
        )


async def test_own_identity_conclusion_is_in_the_same_filtered_commit():
    from app.services.reference_own_business_match import OwnBusinessMatch

    ctx, batch, observations, judgments, key, pilot = values()
    db = FakeDatabase(ctx.batch)
    await commit_leveled_batch(
        db,
        ctx,
        batch,
        observations=observations,
        judgments=judgments,
        source_key=key,
        source_key_version="v1",
        pilot=pilot,
        own_match=OwnBusinessMatch("review", ("place-a",)),
    )
    statement, params = db.calls[1]
    assert "reference_filtered_commit_with_identity" in statement
    assert json.loads(params["own_match"]) == {"status": "review", "place_ids": ["place-a"]}
    assert len(db.calls) == 2
