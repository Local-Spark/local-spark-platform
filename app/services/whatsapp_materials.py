"""Owner consent and private material receipts for a linked WhatsApp channel."""

from typing import Any
from uuid import UUID, uuid4

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import text

from app.core.config import Settings
from app.db.session import Database
from app.services.auth import AuthError
from app.services.service_agreement_scope import accepted_agreement_sql, service_agreement_accepted


class WhatsAppMaterialsService:
    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings, self.database = settings, database

    @staticmethod
    async def _require_owner(session: Any, tenant: UUID, business: UUID, actor: UUID) -> None:
        found = await session.scalar(
            text("""SELECT 1 FROM business_profiles p JOIN memberships m
              ON m.tenant_id=p.tenant_id AND m.actor_id=:actor AND m.active AND m.role='owner'
              WHERE p.tenant_id=:tenant AND p.business_id=:business"""),
            {"tenant": tenant, "business": business, "actor": actor},
        )
        if found is None:
            raise AuthError("BUSINESS_OWNER_REQUIRED", 403)

    async def consent_status(self, tenant: UUID, business: UUID, actor: UUID) -> dict[str, bool]:
        async with self.database.transaction(tenant, actor) as session:
            await self._require_owner(session, tenant, business, actor)
            accepted = await session.scalar(
                text(f"""SELECT {accepted_agreement_sql()} OR EXISTS(
                  SELECT 1 FROM whatsapp_processing_consents
                  WHERE tenant_id=:tenant AND business_id=:business AND revoked_at IS NULL)"""),
                {"tenant": tenant, "business": business},
            )
        return {"accepted": bool(accepted)}

    async def audio_consent_status(self, tenant: UUID, business: UUID, actor: UUID) -> dict[str, bool]:
        async with self.database.transaction(tenant, actor) as session:
            await self._require_owner(session, tenant, business, actor)
            accepted = await session.scalar(
                text(f"""SELECT {accepted_agreement_sql()} OR EXISTS(
                  SELECT 1 FROM whatsapp_processing_consents WHERE tenant_id=:tenant AND business_id=:business
                    AND revoked_at IS NULL AND audio_transcription_accepted_at IS NOT NULL)"""),
                {"tenant": tenant, "business": business},
            )
        return {"accepted": bool(accepted)}

    async def set_audio_consent(self, tenant: UUID, business: UUID, actor: UUID, accepted: bool) -> dict[str, bool]:
        from app.services.visual_consent_gate import VisualConsentGate

        async with self.database.transaction(tenant, actor) as session:
            await VisualConsentGate._lock(session, tenant, business, actor)
            if await service_agreement_accepted(session, tenant, business):
                raise AuthError("SERVICE_AGREEMENT_MANAGES_PROCESSING", 409)
            changed = await session.scalar(
                text("""UPDATE whatsapp_processing_consents SET
                  audio_transcription_accepted_at=CASE WHEN :accepted THEN now() ELSE NULL END
                  WHERE tenant_id=:tenant AND business_id=:business AND revoked_at IS NULL
                    AND (audio_transcription_accepted_at IS NOT NULL)<>:accepted
                  RETURNING business_id"""),
                {"tenant": tenant, "business": business, "accepted": accepted},
            )
            if changed is not None:
                await session.execute(
                    text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                      VALUES(:tenant,:actor,:operation,:action,:business)"""),
                    {
                        "tenant": tenant,
                        "actor": actor,
                        "operation": uuid4(),
                        "business": business,
                        "action": "whatsapp.audio_consent_accepted" if accepted else "whatsapp.audio_consent_revoked",
                    },
                )
            else:
                current = await session.scalar(
                    text("""SELECT audio_transcription_accepted_at IS NOT NULL
                      FROM whatsapp_processing_consents WHERE tenant_id=:tenant AND business_id=:business
                        AND revoked_at IS NULL"""),
                    {"tenant": tenant, "business": business},
                )
                if current is None:
                    raise AuthError("WHATSAPP_CONSENT_REQUIRED", 409)
        return {"accepted": accepted}

    async def accept_consent(self, tenant: UUID, business: UUID, actor: UUID) -> dict[str, bool]:
        from app.services.visual_consent_gate import VisualConsentGate

        async with self.database.transaction(tenant, actor) as session:
            await VisualConsentGate._lock(session, tenant, business, actor)
            if await service_agreement_accepted(session, tenant, business):
                raise AuthError("SERVICE_AGREEMENT_MANAGES_PROCESSING", 409)
            changed = await session.scalar(
                text("""INSERT INTO whatsapp_processing_consents(tenant_id,business_id,actor_id)
                  VALUES(:tenant,:business,:actor)
                  ON CONFLICT(tenant_id,business_id) DO UPDATE SET
                    actor_id=EXCLUDED.actor_id,accepted_at=now(),revoked_at=NULL
                  WHERE whatsapp_processing_consents.revoked_at IS NOT NULL
                  RETURNING business_id"""),
                {"tenant": tenant, "business": business, "actor": actor},
            )
            if changed is not None:
                await session.execute(
                    text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                      VALUES(:tenant,:actor,:operation,'whatsapp.consent_accepted',:business)"""),
                    {"tenant": tenant, "actor": actor, "operation": uuid4(), "business": business},
                )
        return {"accepted": True}

    async def revoke_consent(self, tenant: UUID, business: UUID, actor: UUID) -> dict[str, bool]:
        from app.services.visual_consent_gate import VisualConsentGate

        async with self.database.transaction(tenant, actor) as session:
            await VisualConsentGate._lock(session, tenant, business, actor)
            if await service_agreement_accepted(session, tenant, business):
                raise AuthError("SERVICE_AGREEMENT_MANAGES_PROCESSING", 409)
            changed = await session.scalar(
                text("""UPDATE whatsapp_processing_consents SET revoked_at=now(),audio_transcription_accepted_at=NULL
                  WHERE tenant_id=:tenant AND business_id=:business AND revoked_at IS NULL RETURNING business_id"""),
                {"tenant": tenant, "business": business},
            )
            if changed is not None:
                await session.execute(
                    text("""UPDATE whatsapp_channel_links SET active=false
                      WHERE tenant_id=:tenant AND business_id=:business AND active"""),
                    {"tenant": tenant, "business": business},
                )
                await session.execute(
                    text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                      VALUES(:tenant,:actor,:operation,'whatsapp.consent_revoked',:business)"""),
                    {"tenant": tenant, "actor": actor, "operation": uuid4(), "business": business},
                )
        return {"accepted": False}

    async def list_materials(self, tenant: UUID, business: UUID, actor: UUID, limit: int = 30) -> list[dict[str, Any]]:
        async with self.database.transaction(tenant, actor) as session:
            await self._require_owner(session, tenant, business, actor)
            rows = (
                (
                    await session.execute(
                        text("""SELECT coalesce(e.id,a.id) AS id,coalesce(e.kind,a.kind) AS kind,
                          coalesce(e.state,'processed') AS state,
                          coalesce(e.created_at,a.created_at) AS created_at,e.error_code,a.ciphertext,
                          a.object_key,a.mime_type,a.size_bytes,a.transcript_ciphertext,a.transcription_state,
                          coalesce(e.group_id,a.group_id,e.id,a.id) AS group_id
                          FROM whatsapp_material_assets a FULL OUTER JOIN whatsapp_material_events e ON e.id=a.id
                          WHERE coalesce(e.tenant_id,a.tenant_id)=:tenant
                            AND coalesce(e.business_id,a.business_id)=:business
                            AND (a.id IS NULL OR (a.delete_requested_at IS NULL
                              AND (a.expires_at IS NULL OR a.expires_at>now())))
                            AND (a.id IS NOT NULL OR e.state<>'processed')
                          ORDER BY created_at DESC,id DESC LIMIT :limit"""),
                        {"tenant": tenant, "business": business, "limit": limit},
                    )
                )
                .mappings()
                .all()
            )
        cipher = (
            Fernet(self.settings.meta_encryption_key.get_secret_value().encode())
            if self.settings.meta_encryption_key
            else None
        )
        return [self._present(row, cipher) for row in rows]

    @staticmethod
    def _present(row: Any, cipher: Fernet | None) -> dict[str, Any]:
        body = None
        transcript = None
        if row["ciphertext"] and cipher:
            try:
                body = cipher.decrypt(row["ciphertext"].encode()).decode()
            except (InvalidToken, UnicodeDecodeError):
                body = None
        if row["transcript_ciphertext"] and cipher:
            try:
                transcript = cipher.decrypt(row["transcript_ciphertext"].encode()).decode()
            except (InvalidToken, UnicodeDecodeError):
                transcript = None
        return {
            "id": row["id"],
            "group_id": row["group_id"],
            "kind": row["kind"],
            "state": row["state"],
            "created_at": row["created_at"],
            "error_code": row["error_code"],
            "text": body,
            "transcript": transcript,
            "transcription_state": row["transcription_state"],
            "has_file": bool(row["object_key"]),
            "mime_type": row["mime_type"],
            "size_bytes": row["size_bytes"],
        }

    async def file_key(self, tenant: UUID, business: UUID, actor: UUID, event: UUID) -> tuple[str, str]:
        async with self.database.transaction(tenant, actor) as session:
            await self._require_owner(session, tenant, business, actor)
            row = (
                await session.execute(
                    text("""SELECT object_key,mime_type FROM whatsapp_material_assets
                          WHERE tenant_id=:tenant AND business_id=:business AND id=:event
                            AND delete_requested_at IS NULL AND (expires_at IS NULL OR expires_at>now())"""),
                    {"tenant": tenant, "business": business, "event": event},
                )
            ).one_or_none()
        if row is None or not row[0] or not row[1]:
            raise AuthError("MATERIAL_NOT_FOUND", 404)
        return row[0], row[1]

    async def delete_material(self, tenant: UUID, business: UUID, actor: UUID, event: UUID) -> dict[str, str]:
        async with self.database.transaction(tenant, actor) as session:
            await self._require_owner(session, tenant, business, actor)
            found = await session.scalar(
                text("""SELECT 1 FROM whatsapp_material_assets
                  WHERE tenant_id=:tenant AND business_id=:business AND id=:event"""),
                {"tenant": tenant, "business": business, "event": event},
            )
            if found is None:
                raise AuthError("MATERIAL_NOT_FOUND", 404)
            raise AuthError("WHATSAPP_MATERIAL_DELETE_UNAVAILABLE", 409)
