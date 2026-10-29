"""Activity adapters for a candidate generated from linked WhatsApp material."""

from typing import Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from cryptography.fernet import Fernet
from sqlalchemy import text
from temporalio import activity

from app.core.config import Settings
from app.db.session import Database
from app.schemas.editorial_proposals import ProposalRequest
from app.schemas.media_previews import PreviewRequest
from app.services.auth import AuthError
from app.services.content_deliveries import ContentDeliveryService, publish_fake
from app.services.creative_catalog_resolution import CatalogInterpreter
from app.services.editorial_briefings import EditorialBriefingService
from app.services.editorial_proposals import EditorialProposalService
from app.services.media_previews import MediaPreviewService
from app.services.service_agreement_scope import accepted_agreement_sql, agreement_worker_scope


class ContentCandidateActivities:
    def __init__(
        self,
        settings: Settings,
        app_database: Database,
        worker_database: Database,
        *,
        interpreter: CatalogInterpreter | None = None,
    ) -> None:
        if interpreter is not None and settings.environment not in {"development", "testing"}:
            raise ValueError("Experimental briefing is restricted to development and testing")
        self.settings, self.app_database, self.worker_database = settings, app_database, worker_database
        self.interpreter = interpreter

    @activity.defn
    async def request_candidate_proposal(self, event_id: str) -> str:
        event = UUID(event_id)
        async with self.worker_database.sessions() as session, session.begin():
            row = (
                (
                    await session.execute(
                        text("""SELECT e.tenant_id,e.business_id,e.kind,a.ciphertext,l.actor_id,
                          (c.tenant_id IS NOT NULL AND c.revoked_at IS NULL) AS legacy_consented
                          FROM whatsapp_material_events e
                          JOIN whatsapp_material_assets a ON a.id=e.id
                          JOIN whatsapp_channel_links l ON l.tenant_id=e.tenant_id
                            AND l.business_id=e.business_id
                          LEFT JOIN whatsapp_processing_consents c ON c.tenant_id=e.tenant_id
                            AND c.business_id=e.business_id
                          WHERE e.id=:id AND e.state='processed' AND (e.expires_at IS NULL OR e.expires_at>now())
                            AND a.delete_requested_at IS NULL AND (a.expires_at IS NULL OR a.expires_at>now())
                            """),
                        {"id": event},
                    )
                )
                .mappings()
                .one_or_none()
            )
        if row is None:
            return "skipped"
        if not row["legacy_consented"]:
            async with self.app_database.transaction(row["tenant_id"], row["actor_id"]) as owner_session:
                if not await owner_session.scalar(
                    text(f"SELECT {accepted_agreement_sql()}"),
                    {"tenant": row["tenant_id"], "business": row["business_id"]},
                ):
                    return "skipped"
        if self.settings.intent_ai_mode == "jev" or self.settings.editorial_ai_mode == "openai":
            from app.services.service_agreement import service_agreement_allowed

            async with self.app_database.transaction(row["tenant_id"], row["actor_id"]) as owner_session:
                if not await service_agreement_allowed(
                    owner_session, self.settings, row["tenant_id"], row["business_id"]
                ):
                    return "skipped"
        if row["kind"] == "text":
            cipher = Fernet(self.settings.meta_encryption_key.get_secret_value().encode())  # type: ignore[union-attr]
            content = cipher.decrypt(row["ciphertext"].encode()).decode().strip().casefold()
            if content in {"aprovar", "pedir ajustes", "confirmar", "descartar"} or content.startswith(
                "pedir ajustes:"
            ):
                return "skipped"
        briefing_id = None
        if self.interpreter is None and self.settings.intent_ai_mode != "jev":
            # Never downgrade an event that entered the briefing flow when the
            # provider is disabled while its workflow is waiting.
            async with self.app_database.transaction(row["tenant_id"], row["actor_id"]) as owner_session:
                already_requires_briefing = await owner_session.scalar(
                    text("""SELECT state FROM editorial_briefings WHERE tenant_id=:tenant
                      AND business_id=:business AND source_asset_id=:source"""),
                    {"tenant": row["tenant_id"], "business": row["business_id"], "source": event},
                )
            if already_requires_briefing:
                return (
                    "briefing_budget_blocked"
                    if already_requires_briefing == "budget_blocked"
                    else "briefing_unavailable"
                )
        if self.interpreter is not None or self.settings.intent_ai_mode == "jev":
            interpreter = self.interpreter
            if interpreter is None:
                from app.services.jev_interpreter import BudgetedJevInterpreter

                interpreter = BudgetedJevInterpreter(
                    self.settings,
                    self.app_database,
                    row["tenant_id"],
                    row["business_id"],
                    row["actor_id"],
                    event,
                    uuid5(NAMESPACE_URL, f"candidate-briefing:{event}"),
                )
            try:
                briefing = await EditorialBriefingService(self.settings, self.app_database, interpreter).prepare(
                    row["tenant_id"],
                    row["business_id"],
                    row["actor_id"],
                    event,
                    uuid5(NAMESPACE_URL, f"candidate-briefing:{event}"),
                )
            except AuthError:
                return "skipped"
            if briefing.state == "submitted":
                return "briefing_pending"
            if briefing.state == "budget_blocked":
                return "briefing_budget_blocked"
            if briefing.state != "prepared":
                return (
                    "briefing_needs_clarification"
                    if briefing.state == "needs_clarification"
                    else "briefing_unavailable"
                )
            briefing_id = briefing.id
        try:
            proposal = await EditorialProposalService(self.settings, self.app_database).request(
                row["tenant_id"],
                row["business_id"],
                row["actor_id"],
                ProposalRequest(
                    operation_id=uuid5(NAMESPACE_URL, f"candidate-proposal:{event}"), source_asset_id=event
                ),
                briefing_id=briefing_id,
            )
        except AuthError:
            return "skipped"
        return str(proposal.id)

    @activity.defn
    async def candidate_proposal_state(self, proposal_id: str) -> str:
        async with self.worker_database.sessions() as session, session.begin():
            row = (
                (
                    await session.execute(
                        text("SELECT state,error_code FROM editorial_proposals WHERE id=:id"),
                        {"id": UUID(proposal_id)},
                    )
                )
                .mappings()
                .one_or_none()
            )
        if row is None:
            return "failed"
        if row["state"] == "completed":
            return "completed"
        if row["error_code"] == "EDITORIAL_FACTS_REQUIRED":
            return "needs_fact"
        if row["state"] in {"rejected", "uncertain", "budget_exceeded"}:
            return "failed"
        return "waiting"

    @activity.defn
    async def request_candidate_preview(self, ids: list[str]) -> str:
        # A configured isolated adapter is not opt-in to the product workflow.
        # Never substitute a local placeholder for a disabled real pipeline.
        if self.settings.visual_ai_mode == "openai" and not self.settings.visual_ai_execution_enabled:
            return "blocked"
        event, proposal = UUID(ids[0]), UUID(ids[1])
        async with self.worker_database.sessions() as session, session.begin():
            row = (
                (
                    await session.execute(
                        text("""SELECT tenant_id,business_id,actor_id,briefing_required FROM editorial_proposals
                          WHERE id=:id AND source_asset_id=:source AND state='completed'"""),
                        {"id": proposal, "source": event},
                    )
                )
                .mappings()
                .one_or_none()
            )
        if row is None:
            return "blocked"
        mode: Literal["local", "visual_fake", "visual_ai"] = "local"
        if self.settings.visual_ai_mode == "openai":
            # Missing prepared context must be refused by the visual service,
            # never silently rendered as a local placeholder.
            mode = "visual_ai"
        elif self.settings.visual_ai_mode == "fake" and row.get("briefing_required"):
            mode = "visual_fake"
        try:
            preview = await MediaPreviewService(self.settings, self.app_database).request_candidate(
                row["tenant_id"],
                row["business_id"],
                row["actor_id"],
                PreviewRequest(
                    operation_id=uuid5(NAMESPACE_URL, f"candidate-preview:{event}"),
                    proposal_id=proposal,
                    generation_mode=mode,
                ),
            )
        except AuthError:
            return "blocked"
        return str(preview.id)

    @activity.defn
    async def candidate_preview_state(self, preview_id: str) -> str:
        async with self.worker_database.sessions() as session, session.begin():
            state = await session.scalar(
                text("SELECT state FROM media_previews WHERE id=:id"), {"id": UUID(preview_id)}
            )
        return str(state) if state is not None else "failed"

    @activity.defn
    async def deliver_candidate_clarification(self, event_id: str) -> str:
        delivered = await ContentDeliveryService(self.settings, self.app_database, self.worker_database).record(
            UUID(event_id)
        )
        return "clarification_delivered" if delivered else "delivery_blocked"

    @activity.defn
    async def deliver_briefing_clarification(self, event_id: str) -> str:
        delivered = await ContentDeliveryService(self.settings, self.app_database, self.worker_database).record(
            UUID(event_id), clarification="briefing"
        )
        return "clarification_delivered" if delivered else "delivery_blocked"

    @activity.defn
    async def deliver_candidate_preview(self, ids: list[str]) -> str:
        delivered = await ContentDeliveryService(self.settings, self.app_database, self.worker_database).record(
            UUID(ids[0]), UUID(ids[1])
        )
        if delivered:
            return "candidate_delivered"
        async with self.worker_database.sessions() as session, session.begin():
            tenant = await session.scalar(
                text("SELECT tenant_id FROM whatsapp_material_events WHERE id=:id"), {"id": UUID(ids[0])}
            )
            if tenant is None:
                return "delivery_blocked"
            await agreement_worker_scope(session, tenant)
            state = (
                await session.execute(
                    text(f"""SELECT l.active FROM whatsapp_material_events e
                  JOIN whatsapp_channel_links l ON l.tenant_id=e.tenant_id AND l.business_id=e.business_id
                  LEFT JOIN whatsapp_processing_consents c ON c.tenant_id=e.tenant_id AND c.business_id=e.business_id
                  JOIN media_previews p ON p.tenant_id=e.tenant_id AND p.business_id=e.business_id
                  WHERE e.id=:event AND e.state='processed' AND (e.expires_at IS NULL OR e.expires_at>now())
                    AND ({accepted_agreement_sql("e.tenant_id", "e.business_id")}
                      OR (c.tenant_id IS NOT NULL AND c.revoked_at IS NULL))
                    AND p.id=:preview AND p.candidate
                    AND p.state='completed' AND p.expires_at>now()"""),
                    {"event": UUID(ids[0]), "preview": UUID(ids[1])},
                )
            ).scalar_one_or_none()
        if state is False:
            return "waiting_for_channel"
        return "delivery_blocked"

    @activity.defn
    async def publish_fake_content(self, ids: list[str | int]) -> str:
        return await publish_fake(
            self.settings, self.app_database, self.worker_database, UUID(str(ids[0])), int(ids[1])
        )
