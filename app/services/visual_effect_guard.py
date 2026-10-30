"""Concrete two-role authorization for an explicitly identified visual mode.

The owner run durably freezes coordinated sources. The worker reservation and
one-shot claim use their existing restricted role, with a fresh owner proof and
financial/identity checks at the claim. These are separate commits, not a single
distributed transaction. Any ambiguous commit preserves the run and hold.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import text

from app.adapters.material_media import FetchedMedia
from app.core.config import Settings
from app.db.session import Database
from app.services.auth import AuthError
from app.services.billing import lock_commercial_change
from app.services.editorial_consent_scope import VisualRunScope as AdmittedScope
from app.services.editorial_consent_scope import admitted_visual_run
from app.services.editorial_proposals import _audit
from app.services.service_agreement import service_agreement_allowed
from app.services.visual_admission import VisualAdmissionChecks
from app.services.visual_attempts import FencedVisualReservation, VisualAttemptService
from app.services.visual_consent_gate import VisualConsentGate
from app.services.visual_context import VisualContextService
from app.services.visual_copy_authorization import authorize_visual_copy
from app.services.visual_execution import require_visual_execution
from app.services.visual_provider_execution import (
    VisualSubmissionClaims,
    VisualSubmissionIdentity,
    visual_continuation_allowed,
)
from app.services.visual_real_orchestrator import VisualRunScope
from app.services.visual_requests import PreparedVisualRequest


@dataclass(frozen=True)
class VisualAuthorizationProof:
    admitted_at: datetime
    format: str
    source_valid_until: datetime


def visual_operation(preview: UUID) -> UUID:
    return uuid5(NAMESPACE_URL, f"visual-preview:{preview}")


class DatabaseVisualEffectGuard:
    def __init__(
        self,
        settings: Settings,
        owner: Database,
        worker: Database,
        *,
        reserved_usd_micros: int,
        generation_mode: Literal["visual_fake", "visual_ai"] = "visual_fake",
    ) -> None:
        self.settings, self.owner, self.worker = settings, owner, worker
        self.reserved_usd_micros = reserved_usd_micros
        self.generation_mode = generation_mode
        self.gate = VisualConsentGate(owner, settings)
        self.claims = GuardedVisualSubmissionClaims(self)

    def _require_mode(self) -> None:
        if self.generation_mode == "visual_ai":
            require_visual_execution(self.settings)
            if self.reserved_usd_micros != self.settings.visual_ai_reservation_usd_micros:
                raise AuthError("VISUAL_RESERVATION_CONFIG_CHANGED", 409)
            return
        if self.settings.environment not in {"development", "testing"} or self.settings.visual_ai_mode != "fake":
            raise AuthError("VISUAL_GUARD_SIMULATION_REQUIRED", 409)

    def _params(self, scope: VisualRunScope) -> dict[str, Any]:
        return {
            "tenant": scope.tenant,
            "business": scope.business,
            "actor": scope.actor,
            "preview": scope.preview,
            "proposal": scope.proposal,
            "operation": scope.operation,
            "visual_operation": visual_operation(scope.preview),
            "fence": scope.fence,
            "fingerprint": scope.fingerprint,
            "candidate": scope.candidate,
            "generation_mode": self.generation_mode,
            "visual_recipe": scope.visual_recipe,
        }

    async def _preview(self, session: Any, scope: VisualRunScope, *, lock: bool = False) -> Any:
        result = await session.execute(
            text(
                """SELECT * FROM media_previews WHERE id=:preview AND tenant_id=:tenant AND business_id=:business
              AND actor_id=:actor AND proposal_id=:proposal AND operation_id=:operation
              AND dispatch_fence=:fence AND visual_fingerprint=:fingerprint AND candidate=:candidate
              AND generation_mode=:generation_mode AND visual_recipe=:visual_recipe"""
                + (" FOR UPDATE" if lock else "")
            ),
            self._params(scope),
        )
        return result.mappings().one_or_none()

    async def admit(self, scope: VisualRunScope) -> bool:
        self._require_mode()
        # Old previews stay readable, but never start a new paid legacy effect.
        if self.generation_mode == "visual_ai" and scope.visual_recipe != "full_piece_v1":
            return False
        async with self.worker.transaction(scope.tenant, scope.actor) as session:
            row = await self._preview(session, scope)
            if row is None or row["state"] != "rendering":
                return False
        return await self.gate.admit(
            scope.tenant,
            scope.business,
            scope.actor,
            scope.preview,
            visual_operation(scope.preview),
            scope.fence,
            admission=VisualAdmissionChecks(self.settings, scope.proposal, scope.fingerprint, scope.candidate),
        )

    async def _owner_proof(self, scope: VisualRunScope) -> VisualAuthorizationProof:
        self._require_mode()
        checks = VisualAdmissionChecks(self.settings, scope.proposal, scope.fingerprint, scope.candidate)
        async with self.owner.transaction(scope.tenant, scope.actor) as session:
            await checks.lock_proposal(session, scope.tenant, scope.business)
            await self.gate._lock(session, scope.tenant, scope.business, scope.actor)
            await lock_commercial_change(session, scope.tenant)
            admitted_at = await session.scalar(
                text("""SELECT created_at FROM visual_consent_runs WHERE tenant_id=:tenant AND business_id=:business
                  AND actor_id=:actor AND preview_id=:preview AND operation_id=:visual_operation
                  AND fence=:fence AND state='in_flight'"""),
                self._params(scope),
            )
            if admitted_at is None:
                raise AuthError("VISUAL_ADMISSION_NOT_FOUND", 409)
            if not await visual_continuation_allowed(session, scope.tenant, admitted_at):
                raise AuthError("PLAN_REQUIRED", 403)
            if self.settings.service_agreement_required and not await service_agreement_allowed(
                session, self.settings, scope.tenant, scope.business
            ):
                raise AuthError("SERVICE_AGREEMENT_REQUIRED", 409)
            with admitted_visual_run(
                AdmittedScope(
                    scope.tenant,
                    scope.business,
                    scope.actor,
                    visual_operation(scope.preview),
                    scope.fence,
                    visual_recipe=scope.visual_recipe,
                )
            ):
                current = await VisualContextService(self.settings, self.owner).capture_in_transaction(
                    session, scope.tenant, scope.business, scope.actor, scope.proposal, candidate=scope.candidate
                )
                copy = await authorize_visual_copy(
                    session,
                    self.settings,
                    self.owner,
                    scope.tenant,
                    scope.business,
                    scope.actor,
                    scope.proposal,
                    current.briefing_id,
                    require_generated=self.generation_mode == "visual_ai",
                    full_piece=scope.visual_recipe == "full_piece_v1",
                )
            if current.fingerprint != scope.fingerprint:
                raise AuthError("PREVIEW_INPUT_CHANGED", 409)
            return VisualAuthorizationProof(admitted_at, current.format, copy.valid_until)

    async def authorize(
        self, scope: VisualRunScope, prepared: PreparedVisualRequest, identity: VisualSubmissionIdentity
    ) -> FencedVisualReservation:
        if (
            (self.generation_mode == "visual_ai" and scope.visual_recipe != "full_piece_v1")
            or prepared.context.fingerprint != scope.fingerprint
            or prepared.context.tenant_id != scope.tenant
            or prepared.context.business_id != scope.business
            or prepared.context.proposal_id != scope.proposal
            or prepared.request.request_id != scope.operation
            or identity
            != VisualSubmissionIdentity(
                scope.tenant,
                scope.business,
                scope.actor,
                scope.preview,
                visual_operation(scope.preview),
                scope.fence,
                prepared.request_hash,
                "openai",
            )
        ):
            raise AuthError("VISUAL_AUTHORIZATION_SCOPE_INVALID", 409)
        await self._owner_proof(scope)
        trace_ciphertext = None
        if scope.visual_recipe == "full_piece_v1":
            from app.services.visual_request_trace import encrypt_visual_trace

            trace_ciphertext = encrypt_visual_trace(self.settings, prepared)
        attempts = VisualAttemptService(self.settings, self.worker)
        if trace_ciphertext is None:
            return await attempts.reserve(
                scope.tenant,
                scope.business,
                scope.actor,
                scope.preview,
                scope.fence,
                identity.operation,
                identity.provider,
                prepared.request.model,
                prepared.request_hash,
                self.reserved_usd_micros,
            )
        return await attempts.reserve(
            scope.tenant,
            scope.business,
            scope.actor,
            scope.preview,
            scope.fence,
            identity.operation,
            identity.provider,
            prepared.request.model,
            prepared.request_hash,
            self.reserved_usd_micros,
            trace_ciphertext=trace_ciphertext,
        )

    async def current(self, scope: VisualRunScope, prepared: PreparedVisualRequest) -> bool:
        if prepared.context.fingerprint != scope.fingerprint:
            return False
        try:
            await self._owner_proof(scope)
        except AuthError:
            return False
        async with self.worker.transaction(scope.tenant, scope.actor) as session:
            row = await self._preview(session, scope)
            return row is not None and row["state"] == "rendering"

    async def commit(self, scope: VisualRunScope, key: str, media: FetchedMedia, width: int, height: int) -> bool:
        expected = f"previews/{scope.tenant}/{scope.business}/{scope.preview}/attempt-{scope.fence}/{media.sha256}.jpg"
        if (
            key != expected
            or media.mime_type != "image/jpeg"
            or not media.data
            or len(media.data) > 15 * 1024 * 1024
            or hashlib.sha256(media.data).hexdigest() != media.sha256
            or (width, height) not in {(1024, 1280), (1152, 2048)}
        ):
            raise AuthError("VISUAL_COMMIT_INVALID", 409)
        proof = await self._owner_proof(scope)
        if (width, height) != {"photo": (1024, 1280), "story": (1152, 2048)}[proof.format]:
            raise AuthError("VISUAL_COMMIT_INVALID", 409)
        async with self.worker.transaction(scope.tenant, scope.actor) as session:
            row = await self._preview(session, scope, lock=True)
            if row is None or row["state"] != "rendering":
                return False
            await lock_commercial_change(session, scope.tenant)
            if not await self._worker_eligible(session, scope, proof):
                return False
            claimed = await session.scalar(
                text("""SELECT 1 FROM visual_ai_attempts a JOIN visual_cost_reservations r
                  ON r.tenant_id=a.tenant_id AND r.id=a.reservation_id
                  WHERE a.tenant_id=:tenant AND a.business_id=:business AND a.preview_id=:preview
                    AND a.actor_id=:actor AND a.operation_id=:visual_operation AND a.dispatch_fence=:fence
                    AND r.state IN ('uncertain','completed') AND EXISTS(SELECT 1 FROM visual_cost_events e
                      WHERE e.tenant_id=r.tenant_id AND e.reservation_id=r.id AND e.action='uncertain')"""),
                self._params(scope),
            )
            if not claimed:
                return False
            await session.execute(
                text("""UPDATE media_previews SET state='completed',object_key=:key,sha256=:sha,
                  width=:width,height=:height,dispatch_owner=NULL,dispatch_lease_until=NULL,updated_at=now()
                  WHERE id=:preview"""),
                {**self._params(scope), "key": key, "sha": media.sha256, "width": width, "height": height},
            )
            await _audit(session, row, "media.preview_completed")
        return True

    async def _worker_eligible(self, session: Any, scope: VisualRunScope, proof: VisualAuthorizationProof) -> bool:
        return bool(
            await session.scalar(
                text("""SELECT 1 FROM media_previews WHERE id=:preview AND dispatch_fence=:fence
              AND dispatch_lease_until>clock_timestamp() AND expires_at>clock_timestamp()
              AND clock_timestamp()<CAST(:source_valid_until AS timestamptz)
              AND EXISTS(SELECT 1 FROM memberships WHERE tenant_id=:tenant AND actor_id=:actor
                AND active AND role='owner')
              AND EXISTS(SELECT 1 FROM user_accounts WHERE id=:actor AND active)"""),
                {**self._params(scope), "source_valid_until": proof.source_valid_until},
            )
        ) and await visual_continuation_allowed(session, scope.tenant, proof.admitted_at)

    async def finish(self, scope: VisualRunScope, *, completed: bool, effect_resolved: bool = False) -> None:
        self._require_mode()
        async with self.worker.transaction(scope.tenant, scope.actor) as session:
            row = await self._preview(session, scope, lock=True)
            if row is None and effect_resolved and not completed:
                # A known late response may finish its original run after a
                # redispatch replaced the fence. Stop the replacement preview
                # before releasing sources; it cannot create another attempt.
                row = (
                    (
                        await session.execute(
                            text("""SELECT * FROM media_previews WHERE id=:preview AND tenant_id=:tenant
                      AND business_id=:business AND actor_id=:actor AND proposal_id=:proposal
                      AND operation_id=:operation AND visual_fingerprint=:fingerprint AND candidate=:candidate
                      AND generation_mode=:generation_mode AND dispatch_fence>:fence FOR UPDATE"""),
                            self._params(scope),
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
            if row is None:
                return
            if completed:
                if not effect_resolved or row["state"] != "completed" or not row["object_key"] or not row["sha256"]:
                    return
            else:
                if row["state"] == "completed" or row["object_key"] or row["sha256"]:
                    return
                await session.execute(
                    text("SELECT pg_advisory_xact_lock(hashtextextended(:key,31))"), {"key": str(scope.tenant)}
                )
                if not effect_resolved and await session.scalar(
                    text("""SELECT 1 WHERE EXISTS(SELECT 1 FROM visual_ai_attempts WHERE tenant_id=:tenant
                        AND (preview_id=:preview OR operation_id=:visual_operation))
                      OR EXISTS(SELECT 1 FROM visual_cost_reservations WHERE tenant_id=:tenant
                        AND operation_id=:visual_operation)"""),
                    self._params(scope),
                ):
                    return
                await session.execute(
                    text("""UPDATE media_previews SET state='failed',error_code='VISUAL_GENERATION_STOPPED',
                      dispatch_owner=NULL,dispatch_lease_until=NULL,updated_at=now() WHERE id=:preview"""),
                    self._params(scope),
                )
                await _audit(session, row, "visual.generation_stopped")
        await self.gate.finish(
            scope.tenant,
            scope.business,
            scope.actor,
            visual_operation(scope.preview),
            scope.fence,
            preview_completed=completed,
        )


class GuardedVisualSubmissionClaims(VisualSubmissionClaims):
    """Fresh owner proof followed by the worker's financial one-shot claim."""

    def __init__(self, guard: DatabaseVisualEffectGuard) -> None:
        super().__init__(guard.worker)
        self.guard = guard

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
        async with self.database.transaction(identity.tenant, identity.actor) as session:
            row = (
                (
                    await session.execute(
                        text(
                            "SELECT * FROM media_previews WHERE id=:preview "
                            "AND tenant_id=:tenant AND business_id=:business"
                        ),
                        {"preview": identity.preview, "tenant": identity.tenant, "business": identity.business},
                    )
                )
                .mappings()
                .one_or_none()
            )
        if (
            row is None
            or row["generation_mode"] != self.guard.generation_mode
            or identity.operation != visual_operation(identity.preview)
            or (self.guard.generation_mode == "visual_ai" and row.get("visual_recipe") != "full_piece_v1")
        ):
            return False
        scope = VisualRunScope(
            identity.tenant,
            identity.business,
            identity.actor,
            identity.preview,
            proposal,
            row["operation_id"],
            identity.fence,
            row["candidate"],
            row["visual_fingerprint"],
            row.get("visual_skill_id"),
            row.get("visual_skill_sha256"),
            row.get("visual_recipe", "legacy_overlay"),
        )
        try:
            proof = await self.guard._owner_proof(scope)
        except AuthError:
            return False
        return await super().claim(
            identity,
            reservation,
            model,
            proposal,
            admitted_at=proof.admitted_at,
            source_valid_until=proof.source_valid_until,
        )
