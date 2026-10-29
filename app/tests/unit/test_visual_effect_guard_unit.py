"""The concrete two-role guard fails closed at each durable authorization boundary."""

import hashlib
from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.material_media import FetchedMedia
from app.services import visual_effect_guard as module
from app.services.auth import AuthError
from app.services.editorial_consent_scope import current_visual_run
from app.services.visual_attempts import FencedVisualReservation
from app.services.visual_cost_ledger import VisualReservation
from app.services.visual_provider_execution import VisualSubmissionClaims, VisualSubmissionIdentity
from app.services.visual_real_orchestrator import VisualRunScope


def _mapped(row):
    result = MagicMock()
    result.mappings.return_value.one_or_none.return_value = row
    return result


@pytest.fixture
def case(settings, monkeypatch):
    scope = VisualRunScope(*(uuid4() for _ in range(6)), 2, True, "a" * 64)
    admitted_at = datetime(2026, 10, 29, 12, tzinfo=UTC)
    proof = module.VisualAuthorizationProof(admitted_at, "photo", datetime.now(UTC) + timedelta(days=2))
    row = {
        "id": scope.preview,
        "tenant_id": scope.tenant,
        "business_id": scope.business,
        "actor_id": scope.actor,
        "proposal_id": scope.proposal,
        "operation_id": scope.operation,
        "candidate": scope.candidate,
        "visual_fingerprint": scope.fingerprint,
        "state": "rendering",
        "object_key": None,
        "sha256": None,
    }
    owner_session, worker_session = AsyncMock(spec=AsyncSession), AsyncMock(spec=AsyncSession)
    owner_session.scalar.return_value = admitted_at
    worker_session.scalar.return_value = True
    worker_session.execute.return_value = _mapped(row)
    events = []
    faults = SimpleNamespace(owner_commit=None, worker_commit=None)

    @asynccontextmanager
    async def owner_transaction(*_args):
        events.append("owner.begin")
        yield owner_session
        events.append("owner.commit")
        if faults.owner_commit is not None:
            raise faults.owner_commit

    @asynccontextmanager
    async def worker_transaction(*_args):
        events.append("worker.begin")
        yield worker_session
        events.append("worker.commit")
        if faults.worker_commit is not None:
            raise faults.worker_commit

    owner = SimpleNamespace(transaction=MagicMock(side_effect=owner_transaction))
    worker = SimpleNamespace(transaction=MagicMock(side_effect=worker_transaction))

    async def finished(*_args, **_kwargs):
        events.append("gate.finish")

    gate = SimpleNamespace(
        _lock=AsyncMock(), admit=AsyncMock(return_value=True), finish=AsyncMock(side_effect=finished)
    )
    checks = SimpleNamespace(lock_proposal=AsyncMock())
    capture = AsyncMock(
        return_value=SimpleNamespace(fingerprint=scope.fingerprint, format="photo", briefing_id=uuid4())
    )
    context = SimpleNamespace(capture_in_transaction=capture)
    continuation = AsyncMock(return_value=True)
    agreement = AsyncMock(return_value=True)
    commercial_lock = AsyncMock()
    attempt = FencedVisualReservation(VisualReservation(uuid4(), "submitted", 70, None, True), True)
    reserve = AsyncMock(return_value=attempt)
    audit = AsyncMock()
    monkeypatch.setattr(module, "VisualConsentGate", MagicMock(return_value=gate))
    monkeypatch.setattr(module, "VisualAdmissionChecks", MagicMock(return_value=checks))
    monkeypatch.setattr(module, "VisualContextService", MagicMock(return_value=context))
    monkeypatch.setattr(module, "VisualAttemptService", MagicMock(return_value=SimpleNamespace(reserve=reserve)))
    monkeypatch.setattr(module, "visual_continuation_allowed", continuation)
    monkeypatch.setattr(module, "service_agreement_allowed", agreement)
    monkeypatch.setattr(module, "lock_commercial_change", commercial_lock)
    monkeypatch.setattr(module, "_audit", audit)
    monkeypatch.setattr(
        module, "authorize_visual_copy", AsyncMock(return_value=SimpleNamespace(valid_until=proof.source_valid_until))
    )
    cfg = settings.model_copy(update={"environment": "testing", "visual_ai_mode": "fake"})
    guard = module.DatabaseVisualEffectGuard(cfg, owner, worker, reserved_usd_micros=70)
    prepared = SimpleNamespace(
        context=SimpleNamespace(
            tenant_id=scope.tenant,
            business_id=scope.business,
            proposal_id=scope.proposal,
            fingerprint=scope.fingerprint,
        ),
        request=SimpleNamespace(request_id=scope.operation, model="synthetic-model"),
        request_hash="b" * 64,
    )
    identity = VisualSubmissionIdentity(
        scope.tenant,
        scope.business,
        scope.actor,
        scope.preview,
        module.visual_operation(scope.preview),
        scope.fence,
        prepared.request_hash,
        "openai",
    )
    media = FetchedMedia(b"synthetic-jpeg", "image/jpeg", hashlib.sha256(b"synthetic-jpeg").hexdigest())
    key = f"previews/{scope.tenant}/{scope.business}/{scope.preview}/attempt-{scope.fence}/{media.sha256}.jpg"
    return SimpleNamespace(
        guard=guard,
        scope=scope,
        prepared=prepared,
        identity=identity,
        proof=proof,
        admitted_at=admitted_at,
        row=row,
        owner=owner,
        worker=worker,
        owner_session=owner_session,
        worker_session=worker_session,
        events=events,
        faults=faults,
        gate=gate,
        checks=checks,
        capture=capture,
        continuation=continuation,
        agreement=agreement,
        commercial_lock=commercial_lock,
        reserve=reserve,
        attempt=attempt,
        audit=audit,
        media=media,
        key=key,
    )


@pytest.mark.parametrize("environment,mode", [("production", "fake"), ("staging", "fake"), ("testing", "openai")])
async def test_real_mode_is_not_enabled_by_constructing_the_guard(case, environment, mode):
    c = case
    c.guard.settings = c.guard.settings.model_copy(update={"environment": environment, "visual_ai_mode": mode})
    with pytest.raises(AuthError, match="VISUAL_GUARD_SIMULATION_REQUIRED"):
        await c.guard.admit(c.scope)
    c.owner.transaction.assert_not_called()
    c.worker.transaction.assert_not_called()
    c.gate.admit.assert_not_awaited()


@pytest.mark.parametrize("row", [None, {"state": "pending"}])
async def test_admission_requires_the_exact_rendering_preview(case, row):
    c = case
    c.worker_session.execute.return_value = _mapped(row)
    assert not await c.guard.admit(c.scope)
    c.gate.admit.assert_not_awaited()


@pytest.mark.parametrize("new", [True, False])
async def test_admission_commits_worker_read_before_owner_authorization(case, new):
    c = case
    c.gate.admit.return_value = new
    assert await c.guard.admit(c.scope) is new
    assert c.events == ["worker.begin", "worker.commit"]
    c.gate.admit.assert_awaited_once()
    args = c.gate.admit.await_args.args
    assert args == (
        c.scope.tenant,
        c.scope.business,
        c.scope.actor,
        c.scope.preview,
        c.identity.operation,
        c.scope.fence,
    )
    params = c.worker_session.execute.await_args.args[1]
    assert params["operation"] == c.scope.operation and params["candidate"] is True


@pytest.mark.parametrize(
    "variant,error",
    [
        ("missing_run", "VISUAL_ADMISSION_NOT_FOUND"),
        ("blocked", "PLAN_REQUIRED"),
        ("agreement", "SERVICE_AGREEMENT_REQUIRED"),
        ("changed", "PREVIEW_INPUT_CHANGED"),
    ],
)
async def test_owner_proof_rejects_missing_or_stale_authority(case, variant, error):
    c = case
    if variant == "missing_run":
        c.owner_session.scalar.return_value = None
    elif variant == "blocked":
        c.continuation.return_value = False
    elif variant == "agreement":
        c.guard.settings = c.guard.settings.model_copy(update={"service_agreement_required": True})
        c.agreement.return_value = False
    else:
        c.capture.return_value = SimpleNamespace(fingerprint="c" * 64, briefing_id=uuid4())
    with pytest.raises(AuthError, match=error):
        await c.guard._owner_proof(c.scope)
    c.reserve.assert_not_awaited()
    c.gate.finish.assert_not_awaited()


@pytest.mark.parametrize("agreement_required", [False, True])
async def test_owner_proof_preserves_original_admission_time_and_scopes_financial_expiry(case, agreement_required):
    c = case
    c.guard.settings = c.guard.settings.model_copy(update={"service_agreement_required": agreement_required})
    before = current_visual_run()

    async def capture(*_args, **_kwargs):
        admitted = current_visual_run()
        assert admitted is not None
        assert (admitted.tenant, admitted.business, admitted.actor, admitted.operation, admitted.fence) == (
            c.scope.tenant,
            c.scope.business,
            c.scope.actor,
            c.identity.operation,
            c.scope.fence,
        )
        return SimpleNamespace(fingerprint=c.scope.fingerprint, format="photo", briefing_id=uuid4())

    c.capture.side_effect = capture
    assert await c.guard._owner_proof(c.scope) == c.proof
    assert current_visual_run() is before
    c.continuation.assert_awaited_once_with(c.owner_session, c.scope.tenant, c.admitted_at)
    assert c.agreement.await_count == int(agreement_required)
    assert c.events == ["owner.begin", "owner.commit"]


@pytest.mark.parametrize("field", ["fingerprint", "tenant_id", "business_id", "proposal_id", "request_id", "identity"])
async def test_authorize_rejects_payload_or_identity_mismatch_before_any_reservation(case, field):
    c = case
    proof = c.guard._owner_proof = AsyncMock(return_value=c.proof)
    if field == "request_id":
        c.prepared.request.request_id = uuid4()
    elif field == "identity":
        c.identity = replace(c.identity, provider="other")
    else:
        setattr(c.prepared.context, field, "c" * 64 if field == "fingerprint" else uuid4())
    with pytest.raises(AuthError, match="VISUAL_AUTHORIZATION_SCOPE_INVALID"):
        await c.guard.authorize(c.scope, c.prepared, c.identity)
    proof.assert_not_awaited()
    c.reserve.assert_not_awaited()


async def test_authorization_reserves_only_after_a_fresh_owner_proof(case):
    c = case
    assert await c.guard.authorize(c.scope, c.prepared, c.identity) is c.attempt
    assert c.events == ["owner.begin", "owner.commit"]
    c.reserve.assert_awaited_once_with(
        c.scope.tenant,
        c.scope.business,
        c.scope.actor,
        c.scope.preview,
        c.scope.fence,
        c.identity.operation,
        "openai",
        c.prepared.request.model,
        c.prepared.request_hash,
        70,
    )


@pytest.mark.parametrize("error", [AuthError("OWNER_LOST", 403), RuntimeError("owner acknowledgement lost")])
async def test_owner_proof_failure_never_reserves_or_releases_admission(case, error):
    c = case
    c.guard._owner_proof = AsyncMock(side_effect=error)
    with pytest.raises(type(error)):
        await c.guard.authorize(c.scope, c.prepared, c.identity)
    c.reserve.assert_not_awaited()
    c.gate.finish.assert_not_awaited()


@pytest.mark.parametrize("variant", ["fingerprint", "owner", "missing", "finished", "current"])
async def test_current_requires_both_owner_authority_and_the_same_rendering_preview(case, variant):
    c = case
    proof = c.guard._owner_proof = AsyncMock(return_value=c.proof)
    if variant == "fingerprint":
        c.prepared.context.fingerprint = "c" * 64
    elif variant == "owner":
        proof.side_effect = AuthError("OWNER_LOST", 403)
    elif variant == "missing":
        c.worker_session.execute.return_value = _mapped(None)
    elif variant == "finished":
        c.row["state"] = "completed"
    assert await c.guard.current(c.scope, c.prepared) is (variant == "current")
    if variant == "fingerprint":
        proof.assert_not_awaited()


@pytest.mark.parametrize("variant", ["key", "mime", "empty", "oversized", "checksum", "dimensions"])
async def test_commit_rejects_invalid_output_before_reading_owner_or_worker(case, variant):
    c = case
    proof = c.guard._owner_proof = AsyncMock(return_value=c.proof)
    key, media, width, height = c.key, c.media, 1024, 1280
    if variant == "key":
        key = "previews/another-owner/result.jpg"
    elif variant == "mime":
        media = replace(media, mime_type="image/png")
    elif variant == "empty":
        media = replace(media, data=b"")
    elif variant == "oversized":
        media = replace(media, data=b"x" * (15 * 1024 * 1024 + 1))
    elif variant == "checksum":
        media = replace(media, data=b"altered synthetic bytes")
    else:
        width, height = 8, 8
    with pytest.raises(AuthError, match="VISUAL_COMMIT_INVALID"):
        await c.guard.commit(c.scope, key, media, width, height)
    proof.assert_not_awaited()
    c.worker.transaction.assert_not_called()


@pytest.mark.parametrize("variant", ["missing", "finished", "owner_lost", "blocked", "not_claimed", "commit"])
async def test_commit_requires_live_identity_finances_and_a_claimed_attempt(case, variant):
    c = case
    c.guard._owner_proof = AsyncMock(return_value=c.proof)
    if variant == "missing":
        c.worker_session.execute.return_value = _mapped(None)
    elif variant == "finished":
        c.row["state"] = "failed"
    elif variant == "owner_lost":
        c.worker_session.scalar.return_value = None
    elif variant == "blocked":
        c.continuation.return_value = False
    elif variant == "not_claimed":
        c.worker_session.scalar.side_effect = [True, None]
    assert await c.guard.commit(c.scope, c.key, c.media, 1024, 1280) is (variant == "commit")
    if variant == "commit":
        c.audit.assert_awaited_once_with(c.worker_session, c.row, "media.preview_completed")
        assert c.events == ["worker.begin", "worker.commit"]
        assert c.worker_session.execute.await_args.args[1]["sha"] == c.media.sha256
    else:
        c.audit.assert_not_awaited()
    c.gate.finish.assert_not_awaited()


async def test_lost_private_commit_acknowledgement_is_not_reclassified_as_a_rejected_commit(case):
    c = case
    c.guard._owner_proof = AsyncMock(return_value=c.proof)
    c.faults.worker_commit = RuntimeError("worker commit acknowledgement lost")
    with pytest.raises(RuntimeError, match="acknowledgement lost"):
        await c.guard.commit(c.scope, c.key, c.media, 1024, 1280)
    c.audit.assert_awaited_once()
    c.gate.finish.assert_not_awaited()


@pytest.mark.parametrize("format", ["photo", "story"])
async def test_commit_dimensions_must_match_the_authorized_format(case, format):
    c = case
    c.guard._owner_proof = AsyncMock(
        return_value=module.VisualAuthorizationProof(c.admitted_at, format, c.proof.source_valid_until)
    )
    other_format = (1152, 2048) if format == "photo" else (1024, 1280)
    with pytest.raises(AuthError, match="VISUAL_COMMIT_INVALID"):
        await c.guard.commit(c.scope, c.key, c.media, *other_format)
    c.worker.transaction.assert_not_called()
    c.audit.assert_not_awaited()


@pytest.mark.parametrize(
    "completed,effect_resolved,changes",
    [
        (True, False, {}),
        (True, True, {"state": "rendering"}),
        (True, True, {"object_key": None}),
        (True, True, {"sha256": None}),
        (False, False, {"state": "completed"}),
        (False, False, {"object_key": "private/key"}),
        (False, False, {"sha256": "a" * 64}),
    ],
)
async def test_finish_does_not_claim_a_terminal_outcome_without_its_required_evidence(
    case, completed, effect_resolved, changes
):
    c = case
    if completed:
        c.row.update(state="completed", object_key=c.key, sha256=c.media.sha256)
    c.row.update(changes)
    await c.guard.finish(c.scope, completed=completed, effect_resolved=effect_resolved)
    c.gate.finish.assert_not_awaited()
    c.audit.assert_not_awaited()


async def test_missing_preview_cannot_finish_an_admission(case):
    c = case
    c.worker_session.execute.return_value = _mapped(None)
    await c.guard.finish(c.scope, completed=False)
    c.gate.finish.assert_not_awaited()


@pytest.mark.parametrize("completed", [False, True])
async def test_a_known_response_without_a_matching_original_or_replacement_preview_keeps_the_run(case, completed):
    c = case
    c.worker_session.execute.return_value = _mapped(None)
    await c.guard.finish(c.scope, completed=completed, effect_resolved=True)
    assert c.worker_session.execute.await_count == (1 if completed else 2)
    c.gate.finish.assert_not_awaited()


@pytest.mark.parametrize("has_output", [False, True])
async def test_known_late_response_stops_only_an_unfinished_replacement_before_finishing_original_run(case, has_output):
    c = case
    c.row["dispatch_fence"] = c.scope.fence + 1
    if has_output:
        c.row.update(state="completed", object_key=c.key, sha256=c.media.sha256)
    c.worker_session.execute.side_effect = [_mapped(None), _mapped(c.row), MagicMock(), MagicMock()]
    await c.guard.finish(c.scope, completed=False, effect_resolved=True)
    fallback = c.worker_session.execute.await_args_list[1]
    assert "dispatch_fence>:fence FOR UPDATE" in str(fallback.args[0])
    assert fallback.args[1]["fence"] == c.scope.fence
    assert fallback.args[1]["fingerprint"] == c.scope.fingerprint
    if has_output:
        c.gate.finish.assert_not_awaited()
        c.audit.assert_not_awaited()
    else:
        assert c.events == ["worker.begin", "worker.commit", "gate.finish"]
        c.gate.finish.assert_awaited_once_with(
            c.scope.tenant,
            c.scope.business,
            c.scope.actor,
            c.identity.operation,
            c.scope.fence,
            preview_completed=False,
        )
        c.audit.assert_awaited_once()


async def test_unresolved_attempt_or_unbound_reservation_keeps_the_run_blocking(case):
    c = case
    c.worker_session.scalar.return_value = True
    await c.guard.finish(c.scope, completed=False, effect_resolved=False)
    c.gate.finish.assert_not_awaited()
    c.audit.assert_not_awaited()


@pytest.mark.parametrize("completed,resolved", [(True, True), (False, True), (False, False)])
async def test_finish_commits_terminal_proof_before_finishing_owner_run(case, completed, resolved):
    c = case
    if completed:
        c.row.update(state="completed", object_key=c.key, sha256=c.media.sha256)
    c.worker_session.scalar.return_value = None
    await c.guard.finish(c.scope, completed=completed, effect_resolved=resolved)
    assert c.events == ["worker.begin", "worker.commit", "gate.finish"]
    c.gate.finish.assert_awaited_once_with(
        c.scope.tenant,
        c.scope.business,
        c.scope.actor,
        c.identity.operation,
        c.scope.fence,
        preview_completed=completed,
    )
    assert c.audit.await_count == int(not completed)
    assert c.worker_session.scalar.await_count == int(not completed and not resolved)


async def test_lost_terminal_worker_commit_never_releases_owner_run(case):
    c = case
    c.worker_session.scalar.return_value = None
    c.faults.worker_commit = RuntimeError("terminal acknowledgement lost")
    with pytest.raises(RuntimeError, match="acknowledgement lost"):
        await c.guard.finish(c.scope, completed=False)
    c.gate.finish.assert_not_awaited()


@pytest.mark.parametrize("variant", ["missing", "operation", "owner", "claimed"])
async def test_submission_claim_gets_fresh_owner_proof_and_forwards_its_admission_time(case, monkeypatch, variant):
    c = case
    proof = c.guard._owner_proof = AsyncMock(return_value=c.proof)
    original = AsyncMock(return_value=True)
    monkeypatch.setattr(VisualSubmissionClaims, "claim", original)
    if variant == "missing":
        c.worker_session.execute.return_value = _mapped(None)
    elif variant == "operation":
        c.identity = replace(c.identity, operation=uuid4())
    elif variant == "owner":
        proof.side_effect = AuthError("OWNER_LOST", 403)
    reservation = uuid4()
    assert await c.guard.claims.claim(c.identity, reservation, "synthetic-model", c.scope.proposal) is (
        variant == "claimed"
    )
    if variant == "claimed":
        proof.assert_awaited_once_with(c.scope)
        original.assert_awaited_once_with(
            c.identity,
            reservation,
            "synthetic-model",
            c.scope.proposal,
            admitted_at=c.admitted_at,
            source_valid_until=c.proof.source_valid_until,
        )
    else:
        original.assert_not_awaited()


async def test_owner_commit_uncertainty_cannot_become_a_submission_claim(case, monkeypatch):
    c = case
    c.guard._owner_proof = AsyncMock(side_effect=RuntimeError("owner acknowledgement lost"))
    original = AsyncMock(return_value=True)
    monkeypatch.setattr(VisualSubmissionClaims, "claim", original)
    with pytest.raises(RuntimeError, match="acknowledgement lost"):
        await c.guard.claims.claim(c.identity, uuid4(), "synthetic-model", c.scope.proposal)
    original.assert_not_awaited()


async def test_claim_ignores_an_injected_old_admission_timestamp_and_uses_fresh_owner_proof(case, monkeypatch):
    c = case
    c.guard._owner_proof = AsyncMock(return_value=c.proof)
    original = AsyncMock(return_value=True)
    monkeypatch.setattr(VisualSubmissionClaims, "claim", original)
    reservation = uuid4()
    injected = datetime(2000, 1, 1, tzinfo=UTC)
    assert await c.guard.claims.claim(
        c.identity, reservation, "synthetic-model", c.scope.proposal, admitted_at=injected, source_valid_until=injected
    )
    original.assert_awaited_once_with(
        c.identity,
        reservation,
        "synthetic-model",
        c.scope.proposal,
        admitted_at=c.admitted_at,
        source_valid_until=c.proof.source_valid_until,
    )
