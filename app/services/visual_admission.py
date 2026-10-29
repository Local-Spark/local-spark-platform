"""Owner-side admission checks for simulated visual work, before its durable run.

The reservation remains a separate restricted-worker transaction. A committed
run blocks re-admission if that second transaction or its acknowledgement fails;
these checks do not authorize a real external provider.
"""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.services.auth import AuthError
from app.services.billing import lock_commercial_change
from app.services.editorial_proposals import _access_sql
from app.services.service_agreement import service_agreement_allowed
from app.services.visual_context import VisualContextService


@dataclass(frozen=True)
class VisualAdmissionChecks:
    settings: Settings
    proposal: UUID
    fingerprint: str
    candidate: bool = False

    async def lock_proposal(self, session: AsyncSession, tenant: UUID, business: UUID) -> None:
        # Existing editorial execution locks the proposal before visual-consent.
        # Preserve that order; never acquire the proposal lock after the gate.
        found = await session.scalar(
            text("""SELECT id FROM editorial_proposals WHERE id=:proposal
              AND tenant_id=:tenant AND business_id=:business FOR UPDATE"""),
            {"proposal": self.proposal, "tenant": tenant, "business": business},
        )
        if found is None:
            raise AuthError("PROPOSAL_NOT_FOUND", 404)

    async def validate(
        self, session: AsyncSession, tenant: UUID, business: UUID, actor: UUID, context: VisualContextService
    ) -> None:
        # This lock also covers absence/insertion of billing rows. It follows the
        # visual gate, as in editorial execution. Only SQL occurs under locks.
        await lock_commercial_change(session, tenant)
        if not await session.scalar(text("SELECT 1 FROM user_accounts WHERE id=:actor AND active"), {"actor": actor}):
            raise AuthError("BUSINESS_OWNER_REQUIRED", 403)
        if not await session.scalar(
            # PostgreSQL now() predates any wait for the commercial lock. Check
            # the wall clock after acquiring it so that expiry cannot admit work.
            text(_access_sql().replace("now()", "clock_timestamp()")),
            {"tenant": tenant, "live": self.settings.environment == "production"},
        ):
            raise AuthError("PLAN_REQUIRED", 403)
        if self.settings.service_agreement_required or self.settings.environment == "production":
            if not await service_agreement_allowed(session, self.settings, tenant, business):
                raise AuthError("SERVICE_AGREEMENT_REQUIRED", 409)
        current = await context.capture_in_transaction(
            session, tenant, business, actor, self.proposal, candidate=self.candidate
        )
        if current.fingerprint != self.fingerprint:
            raise AuthError("PREVIEW_INPUT_CHANGED", 409)
