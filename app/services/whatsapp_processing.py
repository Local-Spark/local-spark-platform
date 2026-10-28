"""Durable WhatsApp material dispatch and tenant-checked processing."""

import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import text
from temporalio.client import Client
from temporalio.common import WorkflowIDReusePolicy
from temporalio.exceptions import ApplicationError, WorkflowAlreadyStartedError

from app.adapters.material_media import MaterialError, MaterialStore, MetaMediaClient
from app.core.config import Settings
from app.db.session import Database
from app.services.content_deliveries import apply_candidate_command
from app.services.editorial_conversation import record_inbound_text
from app.services.whatsapp_replies import apply_inbound_command

logger = logging.getLogger("meu_braco_direito.whatsapp_material")


@dataclass(frozen=True)
class MaterialClaim:
    id: UUID
    tenant_id: UUID
    business_id: UUID
    owner_id: UUID
    fencing_token: int


async def claim_materials(database: Database, owner: UUID, limit: int = 10) -> list[MaterialClaim]:
    async with database.sessions() as session, session.begin():
        rows = (
            (
                await session.execute(
                    text("""WITH candidates AS (
                      SELECT id FROM whatsapp_material_events
                      WHERE (state='pending' OR (state='processing' AND lease_until<now()))
                        AND attempts<5 AND (expires_at IS NULL OR expires_at>now())
                      ORDER BY created_at,id LIMIT :limit FOR UPDATE SKIP LOCKED)
                      UPDATE whatsapp_material_events e SET state='processing',owner_id=:owner,
                        lease_until=now()+interval '60 seconds',attempts=e.attempts+1,
                        fencing_token=e.fencing_token+1
                      FROM candidates c WHERE e.id=c.id
                      RETURNING e.id,e.tenant_id,e.business_id,e.fencing_token"""),
                    {"owner": owner, "limit": limit},
                )
            )
            .mappings()
            .all()
        )
        return [
            MaterialClaim(row["id"], row["tenant_id"], row["business_id"], owner, row["fencing_token"]) for row in rows
        ]


async def finish_dispatch(database: Database, item: MaterialClaim, *, accepted: bool) -> None:
    async with database.sessions() as session, session.begin():
        row = (
            (
                await session.execute(
                    text("""UPDATE whatsapp_material_events SET
              state=CASE WHEN :accepted THEN 'processing' WHEN attempts>=5 THEN 'failed' ELSE 'pending' END,
              lease_until=NULL,owner_id=NULL,
              error_code=CASE WHEN :accepted THEN NULL WHEN attempts>=5 THEN 'TEMPORAL_UNAVAILABLE' ELSE NULL END
              WHERE id=:id AND state='processing' AND owner_id=:owner AND fencing_token=:token
              RETURNING tenant_id,business_id,attempts"""),
                    {"id": item.id, "owner": item.owner_id, "token": item.fencing_token, "accepted": accepted},
                )
            )
            .mappings()
            .one_or_none()
        )
        if not accepted and row is not None and row["attempts"] >= 5:
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                  VALUES(:tenant,:actor,:id,'whatsapp.material_dispatch_failed',:business)"""),
                {"tenant": row["tenant_id"], "actor": UUID(int=0), "id": item.id, "business": row["business_id"]},
            )


async def dispatch_materials(database: Database, client: Client, settings: Settings, owner: UUID) -> int:
    claims = await claim_materials(database, owner)
    for item in claims:
        accepted = True
        try:
            await client.start_workflow(
                "WhatsAppMaterialWorkflow",
                str(item.id),
                id=f"whatsapp-material/{item.id}",
                task_queue=settings.temporal_task_queue,
                id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
                rpc_timeout=timedelta(seconds=5),
            )
        except WorkflowAlreadyStartedError:
            pass
        except Exception:
            accepted = False
            logger.warning("whatsapp.material_dispatch_retry", extra={"event_id": str(item.id)})
        await finish_dispatch(database, item, accepted=accepted)
    return len(claims)


class MaterialProcessor:
    def __init__(self, settings: Settings, database: Database, media: MetaMediaClient, store: MaterialStore) -> None:
        self.settings, self.database, self.media, self.store = settings, database, media, store

    async def _eligible(self, session, row) -> bool:  # type: ignore[no-untyped-def]
        from app.services.service_agreement import service_agreement_allowed
        from app.services.service_agreement_scope import accepted_agreement_sql

        if not await service_agreement_allowed(
            session, self.settings, row["tenant_id"], row["business_id"], worker=True
        ):
            return False
        return bool(
            await session.scalar(
                text(f"""SELECT EXISTS(
                  SELECT 1 FROM whatsapp_channel_links l
                  LEFT JOIN whatsapp_processing_consents c ON c.tenant_id=l.tenant_id AND c.business_id=l.business_id
                  JOIN business_profiles p ON p.tenant_id=l.tenant_id AND p.business_id=l.business_id
                  JOIN memberships m ON m.tenant_id=l.tenant_id AND m.actor_id=l.actor_id
                  JOIN user_accounts u ON u.id=l.actor_id
                  WHERE l.tenant_id=:tenant AND l.business_id=:business
                    AND (CAST(:expires AS timestamptz) IS NULL OR :expires>now())
                    AND ({accepted_agreement_sql("l.tenant_id", "l.business_id")}
                      OR (c.revoked_at IS NULL AND c.accepted_at<=:created))
                    AND m.role='owner' AND m.active AND u.active
                    AND (EXISTS(SELECT 1 FROM billing_sponsorships s
                      WHERE s.tenant_id=l.tenant_id AND s.revoked_at IS NULL
                        AND s.starts_at<=now() AND s.ends_at>now())
                    OR EXISTS(SELECT 1 FROM billing_accounts b
                      WHERE b.tenant_id=l.tenant_id AND b.livemode=:live
                        AND b.status='active' AND NOT b.blocked AND b.paid_until>now())))"""),
                {
                    "tenant": row["tenant_id"],
                    "business": row["business_id"],
                    "sender": row["sender_hash"],
                    "created": row["created_at"],
                    "expires": row["expires_at"],
                    "live": self.settings.environment == "production",
                },
            )
        )

    @staticmethod
    async def _mark_failed(session, row, event: UUID, code: str) -> str:  # type: ignore[no-untyped-def]
        await session.execute(
            text("""UPDATE whatsapp_material_events SET state='failed',error_code=:code,
              lease_until=NULL,owner_id=NULL WHERE id=:id"""),
            {"id": event, "code": code},
        )
        await session.execute(
            text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
              VALUES(:tenant,:actor,:id,'whatsapp.material_failed',:business)"""),
            {"tenant": row["tenant_id"], "actor": UUID(int=0), "id": event, "business": row["business_id"]},
        )
        return "failed"

    async def _fail(self, event: UUID, code: str) -> str:
        async with self.database.sessions() as session, session.begin():
            row = (
                (
                    await session.execute(
                        text(
                            "SELECT tenant_id,business_id,state FROM whatsapp_material_events WHERE id=:id FOR UPDATE"
                        ),
                        {"id": event},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None or row["state"] in {"processed", "failed"}:
                return "already_finished"
            return await self._mark_failed(session, row, event, code)

    async def _stage_upload(self, row, event: UUID) -> tuple[UUID, str]:  # type: ignore[no-untyped-def]
        intent = uuid4()
        key = f"tenants/{row['tenant_id']}/businesses/{row['business_id']}/whatsapp/{event}/attempts/{intent}"
        async with self.database.sessions() as session, session.begin():
            await session.execute(
                text("""INSERT INTO whatsapp_upload_intents(id,event_id,tenant_id,business_id,object_key)
                  VALUES(:id,:event,:tenant,:business,:key)"""),
                {"id": intent, "event": event, "tenant": row["tenant_id"], "business": row["business_id"], "key": key},
            )
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                  VALUES(:tenant,:actor,:id,'whatsapp.upload_staged',:business)"""),
                {"tenant": row["tenant_id"], "actor": UUID(int=0), "id": intent, "business": row["business_id"]},
            )
        return intent, key

    async def process(self, event: UUID) -> str:
        async with self.database.sessions() as session, session.begin():
            row = (
                (
                    await session.execute(
                        text("""SELECT id,tenant_id,business_id,kind,ciphertext,sender_hash,group_id,
                          state,created_at,expires_at FROM whatsapp_material_events WHERE id=:id"""),
                        {"id": event},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None or row["state"] in {"processed", "failed"}:
                return "already_finished"
            eligible = (
                await self._eligible(session, row)
                if (row["expires_at"] is None or row["expires_at"] > datetime.now(UTC))
                else False
            )
        if not eligible:
            return await self._fail(event, "ACCESS_OR_CONSENT_INACTIVE")
        try:
            cipher = Fernet(self.settings.meta_encryption_key.get_secret_value().encode())  # type: ignore[union-attr]
            message = json.loads(cipher.decrypt(row["ciphertext"].encode()))
            if not isinstance(message, dict) or message.get("type") != row["kind"]:
                raise MaterialError("MATERIAL_INVALID")
            content = message.get(row["kind"])
            if not isinstance(content, dict):
                raise MaterialError("MATERIAL_INVALID")
            text_body = content.get("body") if row["kind"] == "text" else content.get("caption", "")
            if not isinstance(text_body, str) or len(text_body) > 4096:
                raise MaterialError("MATERIAL_INVALID")
            is_command = False
            if row["kind"] == "text":
                owner_database = Database(self.settings)
                try:
                    is_command = await apply_candidate_command(
                        self.settings, owner_database, self.database, row, message
                    ) or await apply_inbound_command(self.settings, self.database, row, message)
                finally:
                    await owner_database.close()
            object_key = mime_type = checksum = None
            upload_intent = None
            size_bytes = None
            if row["kind"] != "text":
                media_id = content.get("id")
                if not isinstance(media_id, str):
                    raise MaterialError("MEDIA_ID_INVALID")
                media = await self.media.fetch(media_id, row["kind"])
                upload_intent, object_key = await self._stage_upload(row, event)
                await self.store.put(object_key, media)
                mime_type, checksum, size_bytes = media.mime_type, media.sha256, len(media.data)
        except (InvalidToken, ValueError, UnicodeDecodeError) as exc:
            raise ApplicationError("MATERIAL_INVALID", type="MaterialInvalid", non_retryable=True) from exc
        except MaterialError as exc:
            if exc.retryable:
                raise ApplicationError(exc.code, type="MaterialUnavailable") from exc
            return await self._fail(event, exc.code)
        async with self.database.sessions() as session, session.begin():
            current = (
                (
                    await session.execute(
                        text("""SELECT id,tenant_id,business_id,kind,sender_hash,group_id,state,created_at,expires_at
                          FROM whatsapp_material_events WHERE id=:id FOR UPDATE"""),
                        {"id": event},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if current is None or current["state"] in {"processed", "failed"}:
                return "already_finished"
            if not await self._eligible(session, current):
                # The staged attempt remains durable for the reconciler to delete.
                return await self._mark_failed(session, current, event, "ACCESS_OR_CONSENT_INACTIVE")
            if upload_intent is not None:
                stage = (
                    (
                        await session.execute(
                            text("""SELECT delete_owner FROM whatsapp_upload_intents
                              WHERE id=:id FOR UPDATE"""),
                            {"id": upload_intent},
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if stage is None or stage["delete_owner"] is not None:
                    return await self._mark_failed(session, current, event, "UPLOAD_RECONCILING")
            await session.execute(
                text("""INSERT INTO whatsapp_material_assets
                  (id,tenant_id,business_id,kind,ciphertext,object_key,mime_type,size_bytes,sha256,group_id)
                  VALUES(:id,:tenant,:business,:kind,:ciphertext,:object_key,:mime,:size,:checksum,:group)
                  ON CONFLICT(id) DO NOTHING"""),
                {
                    "id": event,
                    "tenant": current["tenant_id"],
                    "business": current["business_id"],
                    "kind": current["kind"],
                    "ciphertext": cipher.encrypt(text_body.encode()).decode(),
                    "object_key": object_key,
                    "mime": mime_type,
                    "size": size_bytes,
                    "checksum": checksum,
                    "group": current["group_id"],
                },
            )
            if current["kind"] == "text" and not is_command:
                await record_inbound_text(session, current, text_body, message["from"], cipher)
            await session.execute(
                text("""UPDATE whatsapp_material_events SET state='processed',processed_at=now(),
                  lease_until=NULL,owner_id=NULL,error_code=NULL WHERE id=:id"""),
                {"id": event},
            )
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                  VALUES(:tenant,:actor,:id,'whatsapp.material_processed',:business)"""),
                {"tenant": current["tenant_id"], "actor": UUID(int=0), "id": event, "business": current["business_id"]},
            )
            if upload_intent is not None:
                await session.execute(text("DELETE FROM whatsapp_upload_intents WHERE id=:id"), {"id": upload_intent})
        return "processed"

    async def fail(self, event: UUID) -> str:
        return await self._fail(event, "MATERIAL_PROCESSING_FAILED")
