"""Abort an unreserved simulation without retrying generation or crossing RLS roles.

The correlator first makes the preview terminal under its row lock. Only after
that commit is acknowledged may the original owner finish the admission. A lost
acknowledgement is recovered by repeating this protocol, never by resubmitting.
Existing attempts and even unbound reservations remain unresolved holds.
"""

from uuid import UUID

from sqlalchemy import text

from app.core.config import Settings
from app.db.session import Database
from app.services.editorial_proposals import _audit
from app.services.visual_consent_gate import VisualConsentGate


class VisualAdmissionRecovery:
    def __init__(self, settings: Settings, worker: Database, owner: Database) -> None:
        self.settings, self.worker, self.owner = settings, worker, owner

    async def recover(self, tenant: UUID, business: UUID, actor: UUID, preview: UUID, operation: UUID) -> bool:
        """Release only an obsolete/failed fake run with proof of no reservation.

        The caller is the existing Temporal activity using its existing pools.
        A live same-fence execution, financial uncertainty, or lost author access
        remains blocked. No locks span the two transactions or any object IO.
        """
        if self.settings.environment not in {"development", "testing"} or self.settings.visual_ai_mode != "fake":
            return False
        params = {"tenant": tenant, "business": business, "actor": actor, "preview": preview, "operation": operation}
        gate = VisualConsentGate(self.owner, self.settings)
        async with self.owner.transaction(tenant, actor) as session:
            await gate._lock(session, tenant, business, actor)
            fence = await session.scalar(
                text("""SELECT fence FROM visual_consent_runs WHERE tenant_id=:tenant AND business_id=:business
                  AND actor_id=:actor AND preview_id=:preview AND operation_id=:operation"""),
                params,
            )
        if fence is None:
            return False
        async with self.worker.transaction(tenant, actor) as session:
            row = (
                (
                    await session.execute(
                        text("""SELECT * FROM media_previews WHERE tenant_id=:tenant AND business_id=:business
                          AND actor_id=:actor AND id=:preview AND generation_mode='visual_fake' FOR UPDATE"""),
                        params,
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None or row["state"] not in {"rendering", "failed"} or row["object_key"] or row["sha256"]:
                return False
            eligible = await session.scalar(
                text("""SELECT 1 FROM media_previews WHERE id=:preview AND tenant_id=:tenant
                  AND dispatch_fence>=:fence AND (state='failed' OR dispatch_fence>:fence
                    OR dispatch_lease_until<=clock_timestamp())"""),
                {**params, "fence": fence},
            )
            if not eligible:
                return False
            # Serialize even an unbound ledger reservation with this proof. The
            # order matches reservation: preview -> tenant ledger -> aggregate.
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 31))"), {"key": str(tenant)}
            )
            reserved = await session.scalar(
                text("""SELECT 1 WHERE EXISTS(SELECT 1 FROM visual_ai_attempts WHERE tenant_id=:tenant
                    AND (preview_id=:preview OR operation_id=:operation))
                  OR EXISTS(SELECT 1 FROM visual_cost_reservations WHERE tenant_id=:tenant
                    AND operation_id=:operation)"""),
                params,
            )
            if reserved:
                return False
            if row["error_code"] != "VISUAL_ADMISSION_ABORTED":
                await session.execute(
                    text("""UPDATE media_previews SET state='failed',error_code='VISUAL_ADMISSION_ABORTED',
                      dispatch_owner=NULL,dispatch_lease_until=NULL,updated_at=now() WHERE id=:preview"""),
                    params,
                )
                await _audit(session, row, "visual.unreserved_admission_aborted")
        # The terminal preview now prevents both a late reservation and a late
        # completion. A crash here leaves a repeatable proof, not a new effect.
        await gate.finish(tenant, business, actor, operation, fence)
        return True
