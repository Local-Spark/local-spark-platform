"""Owner-scoped admission and graceful withdrawal for the simulated visual flow.

This gate serializes only visual-consent withdrawal and admitted operations.
It is not an authorization for real provider calls or a lock on other sources.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Literal, cast
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.session import Database
from app.services.auth import AuthError
from app.services.service_agreement_scope import (
    accepted_agreement_at_sql,
    accepted_agreement_sql,
    service_agreement_accepted,
)
from app.services.whatsapp_materials import WhatsAppMaterialsService

if TYPE_CHECKING:
    from app.services.visual_admission import VisualAdmissionChecks

GateState = Literal["active", "revocation_pending", "revoked"]


class VisualConsentGate:
    def __init__(self, database: Database, settings: Settings | None = None) -> None:
        self.database, self.settings = database, settings

    @staticmethod
    async def _lock(session: AsyncSession, tenant: UUID, business: UUID, actor: UUID) -> None:
        await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
        await session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 48))"),
            {"key": f"visual-consent:{tenant}:{business}"},
        )

    @staticmethod
    async def _audit(session: AsyncSession, tenant: UUID, business: UUID, actor: UUID, action: str) -> None:
        await session.execute(
            text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
              VALUES(:tenant,:actor,:operation,:action,:business)"""),
            {"tenant": tenant, "business": business, "actor": actor, "operation": uuid4(), "action": action},
        )

    async def _state(self, session: AsyncSession, tenant: UUID, business: UUID) -> GateState:
        params = {"tenant": tenant, "business": business}
        state = await session.scalar(
            text(f"""SELECT CASE WHEN state='revocation_pending' THEN state
              WHEN {accepted_agreement_sql()} THEN 'active' ELSE state END FROM visual_consent_gates
          WHERE tenant_id=:tenant AND business_id=:business"""),
            params,
        )
        accepted = await session.scalar(
            text(f"""SELECT {accepted_agreement_sql()} OR EXISTS(SELECT 1 FROM visual_ai_consents
          WHERE tenant_id=:tenant AND business_id=:business AND revoked_at IS NULL)"""),
            params,
        )
        if state == "revocation_pending" and accepted:
            return "revocation_pending"
        return "active" if accepted and state != "revoked" else "revoked"

    async def status(self, tenant: UUID, business: UUID, actor: UUID) -> GateState:
        async with self.database.transaction(tenant, actor) as session:
            await self._lock(session, tenant, business, actor)
            return await self._state(session, tenant, business)

    async def enable(self, tenant: UUID, business: UUID, actor: UUID) -> GateState:
        params = {"tenant": tenant, "business": business, "actor": actor}
        async with self.database.transaction(tenant, actor) as session:
            await self._lock(session, tenant, business, actor)
            if await service_agreement_accepted(session, tenant, business):
                raise AuthError("SERVICE_AGREEMENT_MANAGES_PROCESSING", 409)
            state = await self._state(session, tenant, business)
            if state == "revocation_pending":
                raise AuthError("VISUAL_WITHDRAWAL_PENDING", 409)
            await session.execute(
                text("""INSERT INTO visual_consent_gates(tenant_id,business_id,state)
              VALUES(:tenant,:business,'active') ON CONFLICT(tenant_id,business_id)
              DO UPDATE SET state='active',updated_at=now()"""),
                params,
            )
            changed = await session.scalar(
                text("""INSERT INTO visual_ai_consents(tenant_id,business_id,actor_id)
              VALUES(:tenant,:business,:actor) ON CONFLICT(tenant_id,business_id) DO UPDATE SET
                actor_id=:actor,accepted_at=now(),revoked_at=NULL
              WHERE visual_ai_consents.revoked_at IS NOT NULL RETURNING 1"""),
                params,
            )
            if changed:
                await self._audit(session, tenant, business, actor, "visual.ai_accepted")
            return "active"

    async def request_withdrawal(self, tenant: UUID, business: UUID, actor: UUID) -> GateState:
        params = {"tenant": tenant, "business": business, "actor": actor}
        async with self.database.transaction(tenant, actor) as session:
            await self._lock(session, tenant, business, actor)
            if await service_agreement_accepted(session, tenant, business):
                raise AuthError("SERVICE_AGREEMENT_MANAGES_PROCESSING", 409)
            state = await self._state(session, tenant, business)
            if state == "revoked":
                return "revoked"
            count = await session.scalar(
                text("""SELECT count(*) FROM creative_active_runs
              WHERE tenant_id=:tenant AND business_id=:business AND state='in_flight'"""),
                params,
            )
            next_state: GateState = "revocation_pending" if count else "revoked"
            await session.execute(
                text("""INSERT INTO visual_consent_gates(tenant_id,business_id,state)
              VALUES(:tenant,:business,:state) ON CONFLICT(tenant_id,business_id)
              DO UPDATE SET state=:state,updated_at=now()"""),
                {**params, "state": next_state},
            )
            if state != next_state:
                await self._audit(
                    session, tenant, business, actor, "visual.ai_withdrawal_requested" if count else "visual.ai_revoked"
                )
            if not count:
                await session.execute(
                    text("""UPDATE visual_ai_consents SET actor_id=:actor,revoked_at=now()
                  WHERE tenant_id=:tenant AND business_id=:business AND revoked_at IS NULL"""),
                    params,
                )
            return next_state

    async def admit(
        self,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        preview: UUID,
        operation: UUID,
        fence: int,
        *,
        admission: "VisualAdmissionChecks | None" = None,
    ) -> bool:
        if fence <= 0:
            raise AuthError("VISUAL_ADMISSION_INVALID", 409)
        params = {
            "tenant": tenant,
            "business": business,
            "actor": actor,
            "preview": preview,
            "operation": operation,
            "fence": fence,
        }
        async with self.database.transaction(tenant, actor) as session:
            if admission is not None:
                await admission.lock_proposal(session, tenant, business)
            await self._lock(session, tenant, business, actor)
            existing = (
                (
                    await session.execute(
                        text("""SELECT preview_id,operation_id,actor_id,business_id FROM visual_consent_runs
              WHERE tenant_id=:tenant AND (preview_id=:preview OR operation_id=:operation)"""),
                        params,
                    )
                )
                .mappings()
                .all()
            )
            if existing:
                if (
                    len(existing) != 1
                    or existing[0]["preview_id"] != preview
                    or existing[0]["operation_id"] != operation
                    or existing[0]["actor_id"] != actor
                    or existing[0]["business_id"] != business
                ):
                    raise AuthError("VISUAL_ADMISSION_CONFLICT", 409)
                return False
            if admission is not None:
                from app.services.visual_context import VisualContextService

                await admission.validate(
                    session, tenant, business, actor, VisualContextService(admission.settings, self.database)
                )
            if await self._state(session, tenant, business) != "active":
                raise AuthError("VISUAL_AI_CONSENT_REQUIRED", 409)
            from app.services.visual_pending_changes import VisualPendingChanges

            if await VisualPendingChanges.has_pending_in_session(session, tenant, business):
                raise AuthError("VISUAL_CHANGE_PENDING", 409)
            cancelled = await session.scalar(
                text("""SELECT 1 FROM media_previews p
              JOIN business_visual_pending_changes c ON c.tenant_id=p.tenant_id AND c.business_id=p.business_id
              WHERE p.tenant_id=:tenant AND p.business_id=:business AND p.id=:preview
                AND p.created_at<=c.requested_at LIMIT 1"""),
                params,
            )
            if cancelled:
                raise AuthError("VISUAL_CHANGE_QUEUE_CANCELLED", 409)
            accepted_at = await session.scalar(
                text(f"""SELECT coalesce((SELECT accepted_at FROM visual_ai_consents
                  WHERE tenant_id=:tenant AND business_id=:business
                  AND revoked_at IS NULL), {accepted_agreement_at_sql()})"""),
                params,
            )
            if accepted_at is None:
                raise AuthError("VISUAL_AI_CONSENT_REQUIRED", 409)
            await session.execute(
                text("""INSERT INTO visual_consent_runs
              (tenant_id,business_id,preview_id,operation_id,actor_id,fence,state,consent_accepted_at,created_at)
              VALUES(:tenant,:business,:preview,:operation,:actor,:fence,'in_flight',:accepted_at,clock_timestamp())"""),
                {**params, "accepted_at": accepted_at},
            )
            if admission is not None:
                await self._audit(session, tenant, business, actor, "visual.creation_admitted")
            return True

    async def finish(
        self,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        operation: UUID,
        fence: int,
        *,
        preview_completed: bool = False,
    ) -> GateState:
        params = {"tenant": tenant, "business": business, "actor": actor, "operation": operation, "fence": fence}
        async with self.database.transaction(tenant, actor) as session:
            await self._lock(session, tenant, business, actor)
            state = await self._state(session, tenant, business)
            eligible_sha = None
            if state == "revocation_pending" and preview_completed:
                eligible_sha = await session.scalar(
                    text("""SELECT p.sha256 FROM visual_consent_runs r JOIN media_previews p
                          ON p.id=r.preview_id AND p.tenant_id=r.tenant_id AND p.business_id=r.business_id
                          WHERE r.tenant_id=:tenant AND r.business_id=:business AND r.actor_id=:actor
                            AND r.operation_id=:operation AND r.fence=:fence AND r.state='in_flight'
                            AND p.actor_id=:actor AND p.dispatch_fence=:fence AND p.state='completed'
                            AND p.generation_mode IN ('visual_fake','visual_ai') AND p.sha256 IS NOT NULL
                            AND p.object_key IS NOT NULL"""),
                    params,
                )
            found = await session.scalar(
                text("""UPDATE visual_consent_runs SET state='finished',finished_at=now(),
                    finished_during_withdrawal=:eligible,completed_sha256=:sha
              WHERE tenant_id=:tenant AND business_id=:business AND actor_id=:actor AND operation_id=:operation
                  AND fence=:fence AND state='in_flight' RETURNING 1"""),
                {**params, "eligible": bool(eligible_sha), "sha": eligible_sha},
            )
            finished_now = bool(found)
            if not found:
                found = await session.scalar(
                    text("""SELECT 1 FROM visual_consent_runs WHERE tenant_id=:tenant
                      AND business_id=:business AND actor_id=:actor AND operation_id=:operation
                      AND fence=:fence AND state='finished'"""),
                    params,
                )
                if not found:
                    raise AuthError("VISUAL_ADMISSION_NOT_FOUND", 404)
            from app.services.visual_pending_changes import VisualPendingChanges

            if (
                finished_now
                and preview_completed
                and await VisualPendingChanges.has_pending_in_session(session, tenant, business)
            ):
                await session.execute(
                    text("""INSERT INTO visual_change_completed_previews
                  (tenant_id,business_id,actor_id,preview_id,operation_id,fence,sha256,visual_fingerprint,
                   consent_accepted_at)
                  SELECT r.tenant_id,r.business_id,r.actor_id,r.preview_id,r.operation_id,r.fence,p.sha256,
                    p.visual_fingerprint,r.consent_accepted_at
                  FROM visual_consent_runs r JOIN media_previews p ON p.tenant_id=r.tenant_id
                    AND p.business_id=r.business_id AND p.id=r.preview_id
                  WHERE r.tenant_id=:tenant AND r.business_id=:business AND r.actor_id=:actor
                    AND r.operation_id=:operation AND r.fence=:fence AND r.state='finished'
                    AND p.actor_id=r.actor_id AND p.dispatch_fence=r.fence AND p.state='completed'
                    AND p.generation_mode IN ('visual_fake','visual_ai') AND p.sha256 IS NOT NULL
                    AND p.visual_fingerprint IS NOT NULL AND p.object_key IS NOT NULL
                  ON CONFLICT DO NOTHING"""),
                    params,
                )
            state = await self.finish_withdrawal_if_idle(session, tenant, business, actor, state)
            await VisualPendingChanges.apply_pending_in_session(session, tenant, business)
        if self.settings is not None:
            from app.services.visual_pending_scripts import apply_pending_script_changes

            await apply_pending_script_changes(self.settings, self.database, tenant, business, actor)
        return state

    async def finish_withdrawal_if_idle(
        self, session: AsyncSession, tenant: UUID, business: UUID, actor: UUID, state: GateState
    ) -> GateState:
        """Shared completion under the business gate, including admitted motion."""
        params = {"tenant": tenant, "business": business, "actor": actor}
        if state == "revocation_pending":
            count = await session.scalar(
                text("""SELECT count(*) FROM creative_active_runs
              WHERE tenant_id=:tenant AND business_id=:business AND state='in_flight'"""),
                params,
            )
            if not count:
                await session.execute(
                    text("""UPDATE visual_consent_gates SET state='revoked',updated_at=now()
                  WHERE tenant_id=:tenant AND business_id=:business"""),
                    params,
                )
                await session.execute(
                    text("""UPDATE visual_ai_consents SET actor_id=:actor,revoked_at=now()
                  WHERE tenant_id=:tenant AND business_id=:business AND revoked_at IS NULL"""),
                    params,
                )
                await self._audit(session, tenant, business, actor, "visual.ai_revoked")
                state = "revoked"
        return state

    async def withdrawn_preview_consent(
        self, tenant: UUID, business: UUID, actor: UUID, preview: UUID
    ) -> datetime | None:
        """Identify the original grant for one eligible completed visual preview.

        This is only a read/review exception, never an admission or grant for
        a provider call. Other sources and permissions still require validation.
        """
        params = {"tenant": tenant, "business": business, "actor": actor, "preview": preview}
        async with self.database.transaction(tenant, actor) as session:
            await self._lock(session, tenant, business, actor)
            return cast(
                datetime | None,
                await session.scalar(
                    text("""SELECT r.consent_accepted_at FROM visual_consent_runs r JOIN media_previews p
                      ON p.id=r.preview_id AND p.tenant_id=r.tenant_id AND p.business_id=r.business_id
                      WHERE r.tenant_id=:tenant AND r.business_id=:business AND r.actor_id=:actor
                        AND r.preview_id=:preview AND r.state='finished' AND r.finished_during_withdrawal
                        AND p.actor_id=:actor AND p.dispatch_fence=r.fence AND p.state='completed'
                        AND p.generation_mode IN ('visual_fake','visual_ai') AND p.sha256=r.completed_sha256
                        AND p.object_key IS NOT NULL"""),
                    params,
                ),
            )

    async def visible_after_withdrawal(self, tenant: UUID, business: UUID, actor: UUID, preview: UUID) -> bool:
        return await self.withdrawn_preview_consent(tenant, business, actor, preview) is not None
