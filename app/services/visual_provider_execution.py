"""One-shot provider execution after an independently authorized transaction.

This primitive does not independently authorize paid use. Its guarded caller
must commit and verify all owner, source, consent, fence and
budget gates before calling it, and revalidate before exposing the output.
"""

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.visual_ai import VisualRequest, VisualResult
from app.db.session import Database
from app.services.auth import AuthError
from app.services.billing import lock_commercial_change
from app.services.reference_generation_context import generation_context_is_current, read_generation_snapshot
from app.services.visual_attempts import FencedVisualReservation
from app.services.visual_cost_ledger import VisualReservation, _event
from app.services.visual_requests import PreparedVisualRequest, visual_request_digest


class VisualProvider(Protocol):
    async def generate(self, request: VisualRequest) -> VisualResult: ...


class VisualLedger(Protocol):
    async def finish(
        self, tenant: UUID, actor: UUID, reservation: UUID, *, actual_usd_micros: int | None
    ) -> VisualReservation: ...


class VisualSubmissionError(Exception):
    """No provider effect is permitted for an invalid or replayed reservation."""


@dataclass(frozen=True)
class VisualSubmissionIdentity:
    tenant: UUID
    business: UUID
    actor: UUID
    preview: UUID
    operation: UUID
    fence: int
    request_hash: str
    provider: str


async def visual_continuation_allowed(session: AsyncSession, tenant: UUID, admitted_at: datetime) -> bool:
    """Financial expiry cannot revoke an admitted effect; explicit changes can."""
    return bool(
        await session.scalar(
            text("""SELECT NOT EXISTS(SELECT 1 FROM billing_accounts WHERE tenant_id=:tenant AND blocked)
              AND NOT EXISTS(SELECT 1 FROM billing_sponsorships WHERE tenant_id=:tenant
                AND revoked_at IS NOT NULL AND revoked_at>=:admitted_at)"""),
            {"tenant": tenant, "admitted_at": admitted_at},
        )
    )


class VisualSubmissionClaims:
    """Claim a fenced reservation exactly once before a provider effect.

    A claim is an internal idempotency guard, not authorization for a provider
    effect. The caller must independently establish all source/consent gates.
    """

    def __init__(self, database: Database) -> None:
        self.database = database

    async def claim(
        self,
        identity: VisualSubmissionIdentity,
        reservation: UUID,
        model: str,
        proposal: UUID,
        *,
        admitted_at: datetime | None = None,
        source_valid_until: datetime | None = None,
    ) -> bool:
        params = {
            "tenant": identity.tenant,
            "business": identity.business,
            "actor": identity.actor,
            "preview": identity.preview,
            "operation": identity.operation,
            "fence": identity.fence,
            "request_hash": identity.request_hash,
            "provider": identity.provider,
            "model": model,
            "reservation": reservation,
            "proposal": proposal,
            "source_valid_until": source_valid_until,
        }
        async with self.database.transaction(identity.tenant, identity.actor) as session:
            # Fence is checked while the row is locked: redispatch cannot race
            # between this check and the commit of the durable claim.
            row = await session.scalar(
                text("""SELECT 1 FROM media_previews p
                  WHERE p.id=:preview AND p.tenant_id=:tenant AND p.business_id=:business
                    AND p.actor_id=:actor AND p.proposal_id=:proposal
                    AND p.state='rendering' AND p.dispatch_fence=:fence FOR UPDATE OF p"""),
                params,
            )
            if row is None:
                return False
            if admitted_at is not None:
                await lock_commercial_change(session, identity.tenant)
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 31))"),
                {"key": str(identity.tenant)},
            )
            # Evaluate eligibility in a new statement after both locks. Neither
            # transaction time nor a predicate evaluated before a lock wait may
            # extend a lease or the preview's creation window.
            eligible = await session.scalar(
                text("""SELECT 1 FROM media_previews p
                  JOIN visual_ai_attempts a ON a.tenant_id=p.tenant_id AND a.preview_id=p.id
                  JOIN visual_cost_reservations r ON r.tenant_id=a.tenant_id AND r.id=a.reservation_id
                  WHERE p.id=:preview AND p.tenant_id=:tenant AND p.business_id=:business
                    AND p.actor_id=:actor AND p.proposal_id=:proposal
                    AND p.state='rendering' AND p.dispatch_fence=:fence
                    AND p.dispatch_lease_until>clock_timestamp() AND p.expires_at>clock_timestamp()
                    AND (CAST(:source_valid_until AS timestamptz) IS NULL
                      OR clock_timestamp()<CAST(:source_valid_until AS timestamptz))
                    AND a.actor_id=:actor AND a.business_id=:business AND a.operation_id=:operation
                    AND a.dispatch_fence=:fence AND a.request_hash=:request_hash
                    AND a.reservation_id=:reservation AND r.actor_id=:actor AND r.business_id=:business
                    AND r.operation_id=:operation AND r.state='submitted' AND r.provider=:provider
                    AND r.model=:model
                    AND EXISTS (SELECT 1 FROM memberships m WHERE m.tenant_id=:tenant
                      AND m.actor_id=:actor AND m.role='owner' AND m.active)
                    AND EXISTS (SELECT 1 FROM user_accounts u WHERE u.id=:actor AND u.active)"""),
                params,
            )
            if eligible is None:
                return False
            if admitted_at is not None and not await visual_continuation_allowed(session, identity.tenant, admitted_at):
                return False
            reference_value = await session.scalar(
                text("""SELECT reference_generation_snapshot FROM editorial_proposals
                  WHERE tenant_id=:tenant AND business_id=:business AND id=:proposal"""),
                params,
            )
            if reference_value is not None:
                try:
                    snapshot = read_generation_snapshot(reference_value)
                except AuthError:
                    return False
                # Selection and the one-shot financial claim share this commit.
                # No source lock is held while the provider performs network IO.
                if not await generation_context_is_current(session, identity.business, snapshot):
                    return False
            claimed = await session.scalar(
                text("""UPDATE visual_cost_reservations SET state='uncertain',updated_at=now()
                  WHERE tenant_id=:tenant AND id=:reservation AND state='submitted' RETURNING 1"""),
                params,
            )
            if claimed is None:
                return False
            await _event(session, identity.tenant, identity.actor, reservation, "uncertain")
            return True


async def execute_visual_submission(
    *,
    identity: VisualSubmissionIdentity,
    prepared: PreparedVisualRequest,
    signing_key: str,
    attempt: FencedVisualReservation,
    provider: VisualProvider,
    ledger: VisualLedger,
    claims: VisualSubmissionClaims,
) -> VisualResult:
    """Submit once; retain a financial hold until a charge is reconciled.

    A response containing token usage is not an invoice, so both successful and
    unsuccessful submissions leave an uncertain cost. The ledger transition is
    attempted even on cancellation. If the process or ledger fails, the existing
    submitted reservation must remain a hold and never authorize another submit.
    The calling worker owns persistence, cleanup and privacy-safe observability.
    """
    reservation = attempt.reservation
    if (
        not attempt.created
        or not reservation.created
        or reservation.state != "submitted"
        or reservation.reserved_usd_micros <= 0
    ):
        raise VisualSubmissionError("VISUAL_SUBMISSION_NOT_NEW")
    request = prepared.request
    if (
        not signing_key.strip()
        or prepared.context.tenant_id != identity.tenant
        or prepared.context.business_id != identity.business
        or len(prepared.sources) != len(request.references)
        or not hmac.compare_digest(prepared.request_hash, identity.request_hash)
        or not hmac.compare_digest(
            prepared.request_hash, visual_request_digest(signing_key, prepared.context, prepared.sources, request)
        )
    ):
        raise VisualSubmissionError("VISUAL_SUBMISSION_INVALID_PAYLOAD")
    for source, reference in zip(prepared.sources, request.references, strict=True):
        if reference.mime_type != "image/png" or not hmac.compare_digest(
            hashlib.sha256(reference.content).hexdigest(), source.normalized_sha256
        ):
            raise VisualSubmissionError("VISUAL_SUBMISSION_INVALID_PAYLOAD")
    if not await claims.claim(identity, reservation.id, request.model, prepared.context.proposal_id):
        raise VisualSubmissionError("VISUAL_SUBMISSION_NOT_NEW")
    try:
        return await provider.generate(request)
    finally:
        # Unknown includes success: usage alone cannot prove the actual charge.
        await ledger.finish(identity.tenant, identity.actor, reservation.id, actual_usd_micros=None)
