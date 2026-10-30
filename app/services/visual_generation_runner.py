"""Connect a persisted visual request to its one-shot, guarded effect."""

import asyncio
import logging
from uuid import UUID

import httpx
from sqlalchemy import text

from app.adapters.material_media import MaterialStore
from app.adapters.visual_ai import OpenAIVisualProvider
from app.core.config import Settings
from app.db.session import Database
from app.services.editorial_proposals import _audit
from app.services.visual_admission_recovery import VisualAdmissionRecovery
from app.services.visual_brand_finish import VisualBrandFinishService
from app.services.visual_cost_ledger import VisualCostLedger
from app.services.visual_effect_guard import DatabaseVisualEffectGuard, GuardedVisualSubmissionClaims, visual_operation
from app.services.visual_execution import require_visual_execution
from app.services.visual_provider_execution import VisualProvider
from app.services.visual_real_orchestrator import VisualRealOrchestrator, VisualRunScope

logger = logging.getLogger("meu_braco_direito.visual_generation")


class DatabaseVisualGenerationRunner:
    def __init__(
        self,
        settings: Settings,
        owner: Database,
        worker: Database,
        *,
        provider: VisualProvider | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        store: MaterialStore | None = None,
    ) -> None:
        require_visual_execution(settings)
        # Readiness proves both keys before constructing adapters. Construction
        # performs no IO; all effect authorization remains inside the guard.
        assert settings.openai_api_key is not None
        assert settings.meta_encryption_key is not None
        self.settings, self.owner, self.worker = settings, owner, worker
        self.store = store if store is not None else MaterialStore(settings)
        self.guard = DatabaseVisualEffectGuard(
            settings,
            owner,
            worker,
            reserved_usd_micros=settings.visual_ai_reservation_usd_micros,
            generation_mode="visual_ai",
        )
        self.orchestrator = VisualRealOrchestrator(
            guard=self.guard,
            brand=VisualBrandFinishService(settings, owner, self.store),
            provider=provider
            if provider is not None
            else OpenAIVisualProvider(settings.openai_api_key.get_secret_value(), transport=transport),
            ledger=VisualCostLedger(settings, worker),
            claims=GuardedVisualSubmissionClaims(self.guard),
            store=self.store,
            signing_key=settings.meta_encryption_key.get_secret_value(),
        )

    async def run_preview(self, preview_id: UUID, fence: int) -> str:
        require_visual_execution(self.settings)
        async with self.worker.sessions() as session:
            row = (
                (await session.execute(text("SELECT * FROM media_previews WHERE id=:id"), {"id": preview_id}))
                .mappings()
                .one_or_none()
            )
        if row is None or row["generation_mode"] != "visual_ai" or row["dispatch_fence"] != fence:
            return "stale"
        if row["state"] != "rendering":
            return str(row["state"])
        scope = VisualRunScope(
            row["tenant_id"],
            row["business_id"],
            row["actor_id"],
            row["id"],
            row["proposal_id"],
            row["operation_id"],
            fence,
            row["candidate"],
            row["visual_fingerprint"],
            row.get("visual_skill_id"),
            row.get("visual_skill_sha256"),
            row.get("visual_recipe", "legacy_overlay"),
        )
        try:
            outcome = await self.orchestrator.run(scope)
        except asyncio.CancelledError:
            await self._uncertain(scope)
            raise
        except Exception:
            # Failure text may contain private provider/storage content. The
            # durable projection is deliberately stable and never releases a run.
            logger.warning("visual.generation_uncertain", extra={"operation_id": visual_operation(preview_id)})
            await self._uncertain(scope)
            return "uncertain"
        if outcome == "uncertain":
            await self._uncertain(scope)
        elif outcome != "completed":
            # This can only release an obsolete admission after a terminal
            # preview and proof that no attempt/reservation exists. A live
            # duplicate and every unresolved financial hold remain untouched.
            await VisualAdmissionRecovery(self.settings, self.worker, self.owner, generation_mode="visual_ai").recover(
                scope.tenant, scope.business, scope.actor, scope.preview, visual_operation(scope.preview)
            )
        return outcome

    async def _uncertain(self, scope: VisualRunScope) -> None:
        async with self.worker.transaction(scope.tenant, scope.actor) as session:
            row = (
                (
                    await session.execute(
                        text("""UPDATE media_previews SET state='failed',error_code='VISUAL_OUTCOME_UNCERTAIN',
                          dispatch_owner=NULL,dispatch_lease_until=NULL,updated_at=now()
                          WHERE id=:preview AND tenant_id=:tenant AND generation_mode='visual_ai'
                            AND state='rendering' AND dispatch_fence=:fence RETURNING *"""),
                        {"preview": scope.preview, "tenant": scope.tenant, "fence": scope.fence},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is not None:
                await _audit(session, row, "media.preview_failed")
