"""One-shot submission keeps holds and never treats usage as a provider invoice."""

import asyncio
import hashlib
from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.adapters.visual_ai import VisualReference, VisualRequest, VisualResult
from app.services.visual_attempts import FencedVisualReservation
from app.services.visual_context import VisualContextSnapshot
from app.services.visual_cost_ledger import VisualReservation
from app.services.visual_provider_execution import (
    VisualSubmissionClaims,
    VisualSubmissionError,
    VisualSubmissionIdentity,
    execute_visual_submission,
)
from app.services.visual_references import VisualReferenceSource
from app.services.visual_requests import PreparedVisualRequest, visual_request_digest
from app.tests.unit.test_media_preview_races import _database


def _case():
    identity = VisualSubmissionIdentity(
        tenant=uuid4(),
        business=uuid4(),
        actor=uuid4(),
        preview=uuid4(),
        operation=uuid4(),
        fence=3,
        request_hash="",
        provider="openai",
    )
    request = VisualRequest(
        prompt="synthetic",
        model="gpt-image-2.5-flare-2026-09-08",
        quality="medium",
        size="1024x1280",
        output_format="png",
        request_id=uuid4(),
        references=(VisualReference(b"fictitious-image", "image/png"),),
    )
    context = VisualContextSnapshot(
        identity.tenant, identity.business, uuid4(), uuid4(), uuid4(), "photo", 1, 0, 1, "a" * 64
    )
    sources = (
        VisualReferenceSource("item_photo", uuid4(), 1, "b" * 64, hashlib.sha256(b"fictitious-image").hexdigest()),
    )
    digest = visual_request_digest("synthetic-key", context, sources, request)
    prepared = PreparedVisualRequest(context, sources, digest, request)
    identity = replace(identity, request_hash=digest)
    reservation = VisualReservation(uuid4(), "submitted", 100_000, None, True)
    attempt = FencedVisualReservation(reservation, True)
    return identity, prepared, attempt


async def test_claim_checks_fence_and_commits_only_once():
    identity, prepared, attempt = _case()
    request = prepared.request
    database, session = _database([])
    claims = VisualSubmissionClaims(database)
    session.scalar = AsyncMock(side_effect=[None, 1, None, 1, 1])
    session.execute = AsyncMock()
    assert not await claims.claim(identity, attempt.reservation.id, request.model, prepared.context.proposal_id)
    assert not await claims.claim(identity, attempt.reservation.id, request.model, prepared.context.proposal_id)
    assert await claims.claim(identity, attempt.reservation.id, request.model, prepared.context.proposal_id)
    queries = [str(call.args[0]) for call in session.scalar.await_args_list]
    assert all("FOR UPDATE OF p" in queries[n] for n in (0, 1, 3))
    assert all("UPDATE visual_cost_reservations SET state='uncertain'" in queries[n] for n in (2, 4))
    executed = [str(call.args[0]) for call in session.execute.await_args_list]
    assert "pg_advisory_xact_lock" in executed[0] and "visual_cost_events" in executed[-1]


@pytest.mark.parametrize("variant", ["outer_replay", "inner_replay", "finished", "zero"])
async def test_unusable_reservation_never_claims_or_contacts_provider(variant):
    identity, prepared, attempt = _case()
    if variant == "outer_replay":
        attempt = replace(attempt, created=False)
    elif variant == "inner_replay":
        attempt = replace(attempt, reservation=replace(attempt.reservation, created=False))
    elif variant == "finished":
        attempt = replace(attempt, reservation=replace(attempt.reservation, state="uncertain"))
    else:
        attempt = replace(attempt, reservation=replace(attempt.reservation, reserved_usd_micros=0))
    claims, provider, ledger = MagicMock(), MagicMock(), MagicMock()
    claims.claim, provider.generate, ledger.finish = AsyncMock(), AsyncMock(), AsyncMock()
    with pytest.raises(VisualSubmissionError, match="VISUAL_SUBMISSION_NOT_NEW"):
        await execute_visual_submission(
            identity=identity,
            prepared=prepared,
            signing_key="synthetic-key",
            attempt=attempt,
            provider=provider,
            ledger=ledger,
            claims=claims,
        )
    claims.claim.assert_not_awaited()
    provider.generate.assert_not_awaited()
    ledger.finish.assert_not_awaited()


async def test_replayed_claim_never_calls_provider_or_releases_hold():
    identity, prepared, attempt = _case()
    claims, provider, ledger = MagicMock(), MagicMock(), MagicMock()
    claims.claim = AsyncMock(return_value=False)
    provider.generate, ledger.finish = AsyncMock(), AsyncMock()
    with pytest.raises(VisualSubmissionError, match="VISUAL_SUBMISSION_NOT_NEW"):
        await execute_visual_submission(
            identity=identity,
            prepared=prepared,
            signing_key="synthetic-key",
            attempt=attempt,
            provider=provider,
            ledger=ledger,
            claims=claims,
        )
    provider.generate.assert_not_awaited()
    ledger.finish.assert_not_awaited()


async def test_claim_failure_never_submits_or_releases_reservation():
    identity, prepared, attempt = _case()
    claims, provider, ledger = MagicMock(), MagicMock(), MagicMock()
    claims.claim = AsyncMock(side_effect=RuntimeError("database unavailable"))
    provider.generate, ledger.finish = AsyncMock(), AsyncMock()
    with pytest.raises(RuntimeError, match="database unavailable"):
        await execute_visual_submission(
            identity=identity,
            prepared=prepared,
            signing_key="synthetic-key",
            attempt=attempt,
            provider=provider,
            ledger=ledger,
            claims=claims,
        )
    provider.generate.assert_not_awaited()
    ledger.finish.assert_not_awaited()


@pytest.mark.parametrize(
    "change", ["key", "tenant", "business", "count", "identity_hash", "prompt", "model", "bytes", "mime"]
)
async def test_tampered_request_is_rejected_before_claim_or_submission(change):
    identity, prepared, attempt = _case()
    key = "synthetic-key"
    if change == "key":
        key = ""
    elif change == "tenant":
        identity = replace(identity, tenant=uuid4())
    elif change == "business":
        identity = replace(identity, business=uuid4())
    elif change == "count":
        prepared = replace(prepared, request=replace(prepared.request, references=()))
    elif change == "identity_hash":
        identity = replace(identity, request_hash="b" * 64)
    elif change == "prompt":
        prepared = replace(prepared, request=replace(prepared.request, prompt="changed"))
    elif change == "model":
        prepared = replace(prepared, request=replace(prepared.request, model="changed"))
    elif change == "bytes":
        prepared = replace(
            prepared, request=replace(prepared.request, references=(VisualReference(b"changed", "image/png"),))
        )
    else:
        prepared = replace(
            prepared,
            request=replace(prepared.request, references=(VisualReference(b"fictitious-image", "image/jpeg"),)),
        )
    claims, provider, ledger = MagicMock(), MagicMock(), MagicMock()
    claims.claim, provider.generate, ledger.finish = AsyncMock(), AsyncMock(), AsyncMock()
    with pytest.raises(VisualSubmissionError, match="VISUAL_SUBMISSION_INVALID_PAYLOAD"):
        await execute_visual_submission(
            identity=identity,
            prepared=prepared,
            signing_key=key,
            attempt=attempt,
            provider=provider,
            ledger=ledger,
            claims=claims,
        )
    claims.claim.assert_not_awaited()
    provider.generate.assert_not_awaited()
    ledger.finish.assert_not_awaited()


@pytest.mark.parametrize("failure", [None, RuntimeError("network"), asyncio.CancelledError()])
async def test_success_failure_and_cancellation_keep_financial_hold_uncertain(failure):
    identity, prepared, attempt = _case()
    request = prepared.request
    claims, provider, ledger = MagicMock(), MagicMock(), MagicMock()
    claims.claim = AsyncMock(return_value=True)
    result = VisualResult(b"image", "image/png", "a" * 64, 1024, 1280, {"input_tokens": 1}, None)
    provider.generate = AsyncMock(return_value=result, side_effect=failure)
    ledger.finish = AsyncMock()
    kwargs = dict(
        identity=identity,
        prepared=prepared,
        signing_key="synthetic-key",
        attempt=attempt,
        provider=provider,
        ledger=ledger,
        claims=claims,
    )
    if failure is None:
        assert await execute_visual_submission(**kwargs) == result
    else:
        with pytest.raises(type(failure)):
            await execute_visual_submission(**kwargs)
    claims.claim.assert_awaited_once_with(identity, attempt.reservation.id, request.model, prepared.context.proposal_id)
    provider.generate.assert_awaited_once_with(request)
    ledger.finish.assert_awaited_once_with(
        identity.tenant, identity.actor, attempt.reservation.id, actual_usd_micros=None
    )


async def test_ledger_failure_never_repeats_provider_call():
    identity, prepared, attempt = _case()
    claims, provider, ledger = MagicMock(), MagicMock(), MagicMock()
    claims.claim = AsyncMock(return_value=True)
    provider.generate = AsyncMock(return_value=object())
    ledger.finish = AsyncMock(side_effect=RuntimeError("ledger unavailable"))
    with pytest.raises(RuntimeError, match="ledger unavailable"):
        await execute_visual_submission(
            identity=identity,
            prepared=prepared,
            signing_key="synthetic-key",
            attempt=attempt,
            provider=provider,
            ledger=ledger,
            claims=claims,
        )
    provider.generate.assert_awaited_once()
