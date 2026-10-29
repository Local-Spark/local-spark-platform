"""Fenced reservation primitives; not authorization to call an external provider.

Caller must independently serialize and revalidate all source, owner, plan and
consent changes before an effect. The concrete guard exercises this contract
with simulated providers; real application wiring remains separate.
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.session import Database
from app.services.visual_cost_ledger import VisualCostError, VisualCostLedger, VisualReservation


@dataclass(frozen=True)
class FencedVisualReservation:
    reservation: VisualReservation
    created: bool


class VisualAttemptService:
    """Atomically bind a valid preview fence to a reservation and submission intent."""

    def __init__(self, settings: Settings, database: Database) -> None:
        self.database = database
        self.ledger = VisualCostLedger(settings, database)

    async def reserve(
        self,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        preview: UUID,
        fence: int,
        operation: UUID,
        provider: str,
        model: str,
        request_hash: str,
        reserved_usd_micros: int,
    ) -> FencedVisualReservation:
        async with self.database.transaction(tenant, actor) as session:
            return await self.reserve_in_transaction(
                session,
                tenant,
                business,
                actor,
                preview,
                fence,
                operation,
                provider,
                model,
                request_hash,
                reserved_usd_micros,
            )

    async def reserve_in_transaction(
        self,
        session: AsyncSession,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        preview: UUID,
        fence: int,
        operation: UUID,
        provider: str,
        model: str,
        request_hash: str,
        reserved_usd_micros: int,
    ) -> FencedVisualReservation:
        """Add a fenced reservation to the existing transaction; never commits it.

        The caller must hold the appropriate permissions and source locks. A new
        reservation does not authorize an effect until commit and all gates pass.
        """
        params: dict[str, UUID | int] = {
            "tenant": tenant,
            "business": business,
            "actor": actor,
            "preview": preview,
            "fence": fence,
        }
        # Lock the preview before the ledger's tenant advisory lock. A dispatcher
        # cannot replace its fence until the attempt and reservation commit.
        row = (
            (
                await session.execute(
                    text("""SELECT id FROM media_previews WHERE id=:preview
                      AND tenant_id=:tenant AND business_id=:business AND actor_id=:actor
                      AND state='rendering' AND dispatch_fence=:fence
                      FOR UPDATE"""),
                    params,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise VisualCostError("VISUAL_PREVIEW_FENCE_INVALID")
        await self._require_live_deadlines(session, params)
        if not await session.scalar(
            text("""SELECT 1 FROM memberships WHERE tenant_id=:tenant AND actor_id=:actor
              AND role='owner' AND active"""),
            params,
        ):
            raise VisualCostError("VISUAL_OWNER_REQUIRED")
        previous = (
            (
                await session.execute(
                    text("""SELECT operation_id,actor_id,request_hash,reservation_id
                      FROM visual_ai_attempts WHERE tenant_id=:tenant AND preview_id=:preview"""),
                    params,
                )
            )
            .mappings()
            .one_or_none()
        )
        if previous is not None and (
            previous["operation_id"] != operation
            or previous["actor_id"] != actor
            or previous["request_hash"] != request_hash
        ):
            raise VisualCostError("VISUAL_ATTEMPT_CONFLICT")
        reservation = await self.ledger.reserve_in_transaction(
            session, tenant, business, actor, operation, provider, model, request_hash, reserved_usd_micros
        )
        # The ledger can wait for tenant/global budget locks after the preview
        # lock was acquired. Expiry during that wait rolls back its reservation.
        await self._require_live_deadlines(session, params)
        if previous is not None:
            if reservation.created or previous["reservation_id"] != reservation.id:
                raise VisualCostError("VISUAL_ATTEMPT_INCONSISTENT")
            return FencedVisualReservation(reservation, False)
        if not reservation.created:
            # A reservation without a matching attempt might already have caused
            # a paid effect. Never infer that it is safe to send again.
            raise VisualCostError("VISUAL_RESERVATION_UNBOUND")
        await session.execute(
            text("""INSERT INTO visual_ai_attempts
              (tenant_id,business_id,preview_id,operation_id,actor_id,request_hash,dispatch_fence,reservation_id)
              VALUES(:tenant,:business,:preview,:operation,:actor,:hash,:fence,:reservation)"""),
            {**params, "operation": operation, "hash": request_hash, "reservation": reservation.id},
        )
        return FencedVisualReservation(reservation, True)

    @staticmethod
    async def _require_live_deadlines(session: AsyncSession, params: dict[str, UUID | int]) -> None:
        # A WHERE predicate on SELECT FOR UPDATE can run before waiting for its
        # row lock. Read the wall clock in a separate statement after acquisition.
        if not await session.scalar(
            text("""SELECT 1 FROM media_previews WHERE id=:preview AND tenant_id=:tenant
              AND business_id=:business AND actor_id=:actor AND state='rendering' AND dispatch_fence=:fence
              AND dispatch_lease_until>clock_timestamp() AND expires_at>clock_timestamp()"""),
            params,
        ):
            raise VisualCostError("VISUAL_PREVIEW_FENCE_INVALID")
