"""Durable fake WhatsApp delivery, explicit approval and fake Instagram publication."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from cryptography.fernet import Fernet
from sqlalchemy import text

from app.core.config import Settings
from app.db.session import Database
from app.schemas.content_deliveries import ContentDecision, ContentDeliveryRead
from app.schemas.editorial_proposals import ProposalDraft
from app.services.auth import AuthError
from app.services.media_previews import MediaPreviewService
from app.services.phone_verification import e164
from app.services.service_agreement_scope import accepted_agreement_sql
from app.services.whatsapp_ingest import sender_hash
from app.services.whatsapp_materials import WhatsAppMaterialsService

logger = logging.getLogger("meu_braco_direito.content_deliveries")


def _delivery_id(event_id: UUID) -> UUID:
    return uuid5(NAMESPACE_URL, f"content-delivery:{event_id}")


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()


async def _audit(session: Any, row: Any, action: str, operation_id: UUID) -> None:
    await session.execute(
        text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(:tenant,:actor,:operation,:action,:business) ON CONFLICT DO NOTHING"""),
        {
            "tenant": row["tenant_id"],
            "actor": row["actor_id"],
            "operation": operation_id,
            "action": action,
            "business": row["business_id"],
        },
    )


class ContentDeliveryService:
    def __init__(self, settings: Settings, app_database: Database, worker_database: Database) -> None:
        self.settings, self.app_database, self.worker_database = settings, app_database, worker_database

    async def record(
        self, event_id: UUID, preview_id: UUID | None = None, *, clarification: str = "fact"
    ) -> UUID | None:
        """Persist a local WhatsApp message after rechecking the current owner and preview."""
        async with self.worker_database.sessions() as session, session.begin():
            event = (
                (
                    await session.execute(
                        text("""SELECT e.id,e.tenant_id,e.business_id,e.created_at,
                          l.actor_id FROM whatsapp_material_events e
                          JOIN whatsapp_channel_links l ON l.tenant_id=e.tenant_id
                            AND l.business_id=e.business_id
                          WHERE e.id=:id AND e.state='processed' AND (e.expires_at IS NULL OR e.expires_at>now())
                            AND l.active"""),
                        {"id": event_id},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if event is None:
                return None
            existing = await session.scalar(
                text("SELECT id FROM content_deliveries WHERE source_event_id=:event"), {"event": event_id}
            )
            if existing is not None:
                return cast(UUID, existing)
        preview = None
        if preview_id is not None:
            await MediaPreviewService(self.settings, self.app_database).file_key(
                event["tenant_id"], event["business_id"], event["actor_id"], preview_id
            )
            async with self.worker_database.sessions() as session, session.begin():
                preview = (
                    (
                        await session.execute(
                            text("""SELECT p.id,p.sha256,p.expires_at,e.document
                              FROM media_previews p JOIN editorial_proposals e ON e.id=p.proposal_id
                              WHERE p.id=:preview AND p.tenant_id=:tenant AND p.business_id=:business
                                AND p.candidate AND p.state='completed'"""),
                            {"preview": preview_id, "tenant": event["tenant_id"], "business": event["business_id"]},
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
            if preview is None or preview["sha256"] is None:
                return None
            draft = ProposalDraft.model_validate(preview["document"])
            caption = next(scene.on_screen_text for scene in draft.script if scene.role == "fact")
            body = f"Prévia de conteúdo pronta: {caption} Responda Aprovar ou Pedir ajustes nesta mensagem."
            expires_at = preview["expires_at"]
        else:
            caption = None
            body = (
                "Para preparar seu conteúdo, conte o que você quer divulgar e como imagina a publicação."
                if clarification == "briefing"
                else "Para preparar uma publicação, me conte o que deseja mostrar e confirme um fato atual do negócio."
            )
            expires_at = datetime.now(UTC) + timedelta(days=1)
        cipher = Fernet(self.settings.meta_encryption_key.get_secret_value().encode())  # type: ignore[union-attr]
        async with self.app_database.transaction(event["tenant_id"], event["actor_id"]) as owner_session:
            params = {"tenant": event["tenant_id"], "business": event["business_id"], "actor": event["actor_id"]}
            if not await owner_session.scalar(
                text(f"""SELECT {accepted_agreement_sql()} OR EXISTS(
                  SELECT 1 FROM whatsapp_processing_consents WHERE tenant_id=:tenant
                    AND business_id=:business AND revoked_at IS NULL)"""),
                params,
            ):
                return None
            # All phone updates lock the profile before changing the link.
            profile = (
                (
                    await owner_session.execute(
                        text("""SELECT phone,phone_verified FROM business_profiles
                      WHERE tenant_id=:tenant AND business_id=:business FOR UPDATE"""),
                        params,
                    )
                )
                .mappings()
                .one_or_none()
            )
            if profile is None or not profile["phone_verified"]:
                return None
            active = (
                (
                    await owner_session.execute(
                        text("""SELECT sender_hash FROM whatsapp_channel_links
                      WHERE tenant_id=:tenant AND business_id=:business
                        AND active AND actor_id=:actor FOR UPDATE"""),
                        params,
                    )
                )
                .mappings()
                .one_or_none()
            )
            if active is None:
                return None
            try:
                recipient = e164(profile["phone"])
            except AuthError:
                return None
            if sender_hash(self.settings, recipient) != active["sender_hash"]:
                return None
            delivery_id = _delivery_id(event_id)
            async with self.worker_database.sessions() as session, session.begin():
                row = (
                    (
                        await session.execute(
                            text("""INSERT INTO content_deliveries
                              (id,tenant_id,business_id,actor_id,source_event_id,preview_id,kind,
                               recipient_hash,recipient_ciphertext,message_body,provider_message_id,
                               decision_state,caption,expires_at)
                              VALUES(:id,:tenant,:business,:actor,:event,:preview,:kind,:sender,:recipient,
                                :body,:message,:decision,:caption,:expires)
                              ON CONFLICT(source_event_id) DO UPDATE SET id=content_deliveries.id
                              RETURNING *"""),
                            {
                                "id": delivery_id,
                                "tenant": event["tenant_id"],
                                "business": event["business_id"],
                                "actor": event["actor_id"],
                                "event": event_id,
                                "preview": preview_id,
                                "kind": "candidate" if preview_id else "clarification",
                                "sender": active["sender_hash"],
                                "recipient": cipher.encrypt(recipient.encode()).decode(),
                                "body": body,
                                "message": f"fake-whatsapp/{delivery_id}",
                                "decision": "pending" if preview_id else None,
                                "caption": caption,
                                "expires": expires_at,
                            },
                        )
                    )
                    .mappings()
                    .one()
                )
                action = "content.candidate_delivered" if preview_id else "content.fact_requested"
                await _audit(session, row, action, row["id"])
                return delivery_id

    async def list(self, tenant: UUID, business: UUID, actor: UUID) -> list[ContentDeliveryRead]:
        async with self.app_database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            rows = (
                (
                    await session.execute(
                        text("""SELECT * FROM content_deliveries WHERE tenant_id=:tenant AND business_id=:business
                          ORDER BY created_at DESC,id DESC LIMIT 30"""),
                        {"tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .all()
            )
            return [ContentDeliveryRead.model_validate(row) for row in rows]

    async def decide(
        self, tenant: UUID, business: UUID, actor: UUID, delivery_id: UUID, body: ContentDecision
    ) -> ContentDeliveryRead:
        async with self.app_database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            row = (
                (
                    await session.execute(
                        text("""SELECT * FROM content_deliveries WHERE id=:id AND tenant_id=:tenant
                          AND business_id=:business FOR UPDATE"""),
                        {"id": delivery_id, "tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None or row["kind"] != "candidate":
                raise AuthError("CANDIDATE_NOT_FOUND", 404)
            if row["actor_id"] != actor:
                raise AuthError("CANDIDATE_OWNER_MISMATCH", 403)
            expected = "approved" if body.decision == "approve" else "changes_requested"
            request_hash = _digest(body.model_dump(mode="json"))
            if row["decision_operation_id"] == body.operation_id:
                if row["decision_request_hash"] != request_hash:
                    raise AuthError("CANDIDATE_DECISION_CONFLICT", 409)
                return ContentDeliveryRead.model_validate(row)
            if row["decision_state"] != "pending" or row["delivery_state"] != "delivered":
                raise AuthError("CANDIDATE_DECISION_CONFLICT", 409)
            if row["expires_at"] <= datetime.now(UTC):
                raise AuthError("CANDIDATE_EXPIRED", 409)
            preview = (
                (
                    await session.execute(
                        text("""SELECT p.*,e.document,e.state AS proposal_state,e.review_state,
                          e.model,e.script_version AS current_script_version,e.expires_at AS proposal_expires_at,
                          e.source_asset_id AS proposal_source_asset_id
                          FROM media_previews p JOIN editorial_proposals e ON e.id=p.proposal_id
                          WHERE p.id=:preview AND p.tenant_id=:tenant AND p.business_id=:business"""),
                        {"preview": row["preview_id"], "tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if preview is None or preview["state"] != "completed" or not preview["candidate"]:
                raise AuthError("CANDIDATE_INVALID", 409)
            proposal = (
                (
                    await session.execute(
                        text("SELECT * FROM editorial_proposals WHERE id=:id"), {"id": preview["proposal_id"]}
                    )
                )
                .mappings()
                .one()
            )
            preview_service = MediaPreviewService(self.settings, self.app_database)
            if preview["generation_mode"] == "visual_fake":
                await preview_service._validate_visual(preview, actor)
                valid_inputs = True
            else:
                inputs = await preview_service._inputs(
                    session,
                    proposal,
                    emphasis=preview["emphasis"],
                    parent_preview_id=preview["parent_preview_id"],
                    candidate=True,
                )
                valid_inputs = inputs.render_key == preview["render_key"]
            if not valid_inputs or preview["sha256"] is None:
                raise AuthError("CANDIDATE_INVALID", 409)
            # Use the transaction clock for immediate publication. Application and
            # database clocks can differ enough to leave an approved item not due.
            when = body.scheduled_at or await session.scalar(text("SELECT now()"))
            if when > datetime.now(UTC) + timedelta(days=7) or when >= row["expires_at"]:
                raise AuthError("CANDIDATE_SCHEDULE_INVALID", 409)
            approval_digest = _digest(
                {
                    "preview": row["preview_id"],
                    "sha256": preview["sha256"],
                    "caption": row["caption"],
                    "destination": "instagram",
                    "scheduled_at": when,
                }
            )
            updated = (
                (
                    await session.execute(
                        text("""UPDATE content_deliveries SET decision_state=:state,
                          decision_operation_id=:operation,review_note=:note,
                          decision_request_hash=:request_hash,
                          approved_sha256=CASE WHEN :state='approved' THEN :sha ELSE NULL END,
                          approval_digest=CASE WHEN :state='approved' THEN :approval_digest ELSE NULL END,
                          scheduled_at=CASE WHEN :state='approved' THEN CAST(:scheduled AS timestamptz) ELSE NULL END,
                          publish_state=CASE WHEN :state='approved' THEN 'pending' ELSE NULL END,
                          updated_at=now() WHERE id=:id RETURNING *"""),
                        {
                            "id": delivery_id,
                            "state": expected,
                            "operation": body.operation_id,
                            "request_hash": request_hash,
                            "note": body.note,
                            "sha": preview["sha256"],
                            "approval_digest": approval_digest,
                            "scheduled": when,
                        },
                    )
                )
                .mappings()
                .one()
            )
            await _audit(session, updated, f"content.{expected}", body.operation_id)
            return ContentDeliveryRead.model_validate(updated)


async def apply_candidate_command(
    settings: Settings, app_database: Database, worker_database: Database, event: Any, message: dict[str, Any]
) -> bool:
    """Resolve a quoted candidate or the sole recent candidate for this sender."""
    raw = message.get("text", {}).get("body", "")
    command = raw.strip() if isinstance(raw, str) else ""
    lowered = command.casefold()
    approve = lowered == "aprovar"
    changes = lowered == "pedir ajustes" or lowered.startswith("pedir ajustes: ")
    if not approve and not changes:
        return False
    context = message.get("context")
    reference = context.get("id") if isinstance(context, dict) else None
    async with worker_database.sessions() as session, session.begin():
        if isinstance(reference, str) and reference:
            matches = (
                (
                    await session.execute(
                        text("""SELECT id,actor_id FROM content_deliveries
                          WHERE provider_message_id=:reference AND tenant_id=:tenant
                            AND business_id=:business AND recipient_hash=:sender
                            AND kind='candidate' AND delivery_state='delivered'
                            AND decision_state='pending' AND expires_at>now()"""),
                        {
                            "reference": reference,
                            "tenant": event["tenant_id"],
                            "business": event["business_id"],
                            "sender": event["sender_hash"],
                        },
                    )
                )
                .mappings()
                .all()
            )
        else:
            matches = (
                (
                    await session.execute(
                        text("""SELECT id,actor_id FROM content_deliveries
                          WHERE tenant_id=:tenant AND business_id=:business AND recipient_hash=:sender
                            AND kind='candidate' AND delivery_state='delivered'
                            AND decision_state='pending' AND expires_at>now()
                            AND created_at>now()-interval '30 minutes'
                          ORDER BY created_at DESC,id DESC LIMIT 2"""),
                        {
                            "tenant": event["tenant_id"],
                            "business": event["business_id"],
                            "sender": event["sender_hash"],
                        },
                    )
                )
                .mappings()
                .all()
            )
    if len(matches) != 1:
        logger.info("content.command_ambiguous", extra={"event_id": str(event["id"])})
        return True
    body = ContentDecision(
        operation_id=uuid5(NAMESPACE_URL, f"content-command:{event['id']}"),
        decision="approve" if approve else "request_changes",
        note=command.split(":", 1)[1].strip() if ":" in command else None,
    )
    try:
        await ContentDeliveryService(settings, app_database, worker_database).decide(
            event["tenant_id"], event["business_id"], matches[0]["actor_id"], matches[0]["id"], body
        )
    except AuthError as error:
        logger.info("content.command_rejected", extra={"event_id": str(event["id"]), "error_code": error.code})
    return True


async def claim_publications(database: Database, owner: UUID, limit: int = 10) -> list[tuple[UUID, int]]:
    async with database.sessions() as session, session.begin():
        rows = (
            (
                await session.execute(
                    text("""WITH due AS (
                      SELECT id FROM content_deliveries
                      WHERE publish_state='pending' AND decision_state='approved'
                        AND scheduled_at<=now() AND expires_at>now()
                      ORDER BY scheduled_at,id LIMIT :limit FOR UPDATE SKIP LOCKED)
                      UPDATE content_deliveries d SET publish_state='dispatching',publish_owner=:owner,
                        publish_lease_until=now()+interval '2 minutes',publish_fence=d.publish_fence+1,
                        updated_at=now() FROM due WHERE d.id=due.id
                      RETURNING d.id,d.publish_fence"""),
                    {"owner": owner, "limit": limit},
                )
            )
            .mappings()
            .all()
        )
        return [(row["id"], row["publish_fence"]) for row in rows]


async def finish_publication_dispatch(database: Database, delivery_id: UUID, fence: int, accepted: bool) -> None:
    if accepted:
        return
    async with database.sessions() as session, session.begin():
        await session.execute(
            text("""UPDATE content_deliveries SET publish_state='pending',publish_owner=NULL,
              publish_lease_until=NULL,updated_at=now() WHERE id=:id AND publish_state='dispatching'
              AND publish_fence=:fence"""),
            {"id": delivery_id, "fence": fence},
        )


async def reconcile_publications(database: Database) -> int:
    """A lost dispatch acknowledgement is uncertain; no blind second publication."""
    async with database.sessions() as session, session.begin():
        rows = (
            (
                await session.execute(
                    text("""UPDATE content_deliveries SET publish_state='unknown',publish_owner=NULL,
                      publish_lease_until=NULL,updated_at=now() WHERE publish_state='dispatching'
                      AND publish_lease_until<now() RETURNING *"""),
                )
            )
            .mappings()
            .all()
        )
        for row in rows:
            await _audit(
                session, row, "content.publication_unknown", uuid5(NAMESPACE_URL, f"publish-unknown:{row['id']}")
            )
        return len(rows)


async def publish_fake(
    settings: Settings, app_database: Database, worker_database: Database, delivery_id: UUID, fence: int
) -> str:
    """Never call a real provider; an uncertain handoff is not retried blindly."""
    if settings.environment == "production":
        raise RuntimeError("Fake publication is disabled in production")
    async with worker_database.sessions() as session, session.begin():
        row = (
            (
                await session.execute(
                    text("""SELECT * FROM content_deliveries WHERE id=:id AND publish_state='dispatching'
                      AND publish_fence=:fence"""),
                    {"id": delivery_id, "fence": fence},
                )
            )
            .mappings()
            .one_or_none()
        )
    if row is None:
        return "skipped"
    valid = row["decision_state"] == "approved" and row["expires_at"] > datetime.now(UTC)
    if valid:
        try:
            await MediaPreviewService(settings, app_database).file_key(
                row["tenant_id"], row["business_id"], row["actor_id"], row["preview_id"]
            )
            async with worker_database.sessions() as session, session.begin():
                sha = await session.scalar(
                    text("SELECT sha256 FROM media_previews WHERE id=:id"), {"id": row["preview_id"]}
                )
            valid = sha == row["approved_sha256"] and row["approval_digest"] == _digest(
                {
                    "preview": row["preview_id"],
                    "sha256": sha,
                    "caption": row["caption"],
                    "destination": "instagram",
                    "scheduled_at": row["scheduled_at"],
                }
            )
        except AuthError:
            valid = False
    async with worker_database.sessions() as session, session.begin():
        finished = (
            (
                await session.execute(
                    text("""UPDATE content_deliveries SET publish_state=:state,
                      publication_id=CASE WHEN :valid THEN :publication ELSE NULL END,
                      publish_owner=NULL,publish_lease_until=NULL,updated_at=now()
                      WHERE id=:id AND publish_state='dispatching' AND publish_fence=:fence
                        AND decision_state='approved' AND expires_at>now()
                      RETURNING *"""),
                    {
                        "id": delivery_id,
                        "fence": fence,
                        "valid": valid,
                        "state": "published" if valid else "failed",
                        "publication": f"fake-instagram/{delivery_id}",
                    },
                )
            )
            .mappings()
            .one_or_none()
        )
        if finished is None:
            return "skipped"
        await _audit(
            session,
            finished,
            "content.fake_published" if valid else "content.publication_blocked",
            uuid5(NAMESPACE_URL, f"content-publish:{delivery_id}:{fence}"),
        )
        return "published" if valid else "failed"
