"""Activity adapters for a candidate generated from linked WhatsApp material."""

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
                        text("""SELECT e.tenant_id,e.business_id,e.kind,a.ciphertext,l.actor_id
                          FROM whatsapp_material_events e
                          JOIN whatsapp_material_assets a ON a.id=e.id
                          JOIN whatsapp_channel_links l ON l.tenant_id=e.tenant_id
                            AND l.business_id=e.business_id AND l.sender_hash=e.sender_hash
                          JOIN whatsapp_processing_consents c ON c.tenant_id=e.tenant_id
                            AND c.business_id=e.business_id
                          WHERE e.id=:id AND e.state='processed' AND e.expires_at>now()
                            AND a.delete_requested_at IS NULL AND a.expires_at>now()
                            AND l.active AND l.linked_at<=e.created_at AND c.revoked_at IS NULL"""),
                        {"id": event},
                    )
                )
                .mappings()
                .one_or_none()
            )
        if row is None:
            return "skipped"
        if row["kind"] == "text":
            cipher = Fernet(self.settings.meta_encryption_key.get_secret_value().encode())  # type: ignore[union-attr]
            content = cipher.decrypt(row["ciphertext"].encode()).decode().strip().casefold()
            if content in {"aprovar", "pedir ajustes", "confirmar", "descartar"} or content.startswith(
                "pedir ajustes:"
            ):
                return "skipped"
        briefing_id = None
        if self.interpreter is not None:
            try:
                briefing = await EditorialBriefingService(self.settings, self.app_database, self.interpreter).prepare(
                    row["tenant_id"],
                    row["business_id"],
                    row["actor_id"],
                    event,
                    uuid5(NAMESPACE_URL, f"candidate-briefing:{event}"),
                )
            except AuthError:
                return "skipped"
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
        event, proposal = UUID(ids[0]), UUID(ids[1])
        async with self.worker_database.sessions() as session, session.begin():
            row = (
                (
                    await session.execute(
                        text("""SELECT tenant_id,business_id,actor_id FROM editorial_proposals
                          WHERE id=:id AND source_asset_id=:source AND state='completed'"""),
                        {"id": proposal, "source": event},
                    )
                )
                .mappings()
                .one_or_none()
            )
        if row is None:
            return "blocked"
        try:
            preview = await MediaPreviewService(self.settings, self.app_database).request_candidate(
                row["tenant_id"],
                row["business_id"],
                row["actor_id"],
                PreviewRequest(operation_id=uuid5(NAMESPACE_URL, f"candidate-preview:{event}"), proposal_id=proposal),
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
    async def deliver_candidate_preview(self, ids: list[str]) -> str:
        delivered = await ContentDeliveryService(self.settings, self.app_database, self.worker_database).record(
            UUID(ids[0]), UUID(ids[1])
        )
        return "candidate_delivered" if delivered else "delivery_blocked"

    @activity.defn
    async def publish_fake_content(self, ids: list[str | int]) -> str:
        return await publish_fake(
            self.settings, self.app_database, self.worker_database, UUID(str(ids[0])), int(ids[1])
        )
