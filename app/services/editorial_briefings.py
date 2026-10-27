"""Experimental durable, owner-scoped catalog context for an inbound material.

No external interpreter is configured here. The caller must use a synthetic
interpreter in development/testing; paid providers require a separate ledger.
"""

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from sqlalchemy import text

from app.core.config import Settings
from app.db.session import Database
from app.services.auth import AuthError
from app.services.creative_catalog import validate_catalog_snapshot
from app.services.creative_catalog_resolution import CatalogInterpreter, resolve_catalog_context
from app.services.editorial_proposals import EditorialProposalService, _access_sql
from app.services.whatsapp_materials import WhatsAppMaterialsService


@dataclass(frozen=True)
class BriefingResult:
    id: UUID
    state: str


class EditorialBriefingService:
    def __init__(self, settings: Settings, database: Database, interpreter: CatalogInterpreter | None = None) -> None:
        if settings.environment not in {"development", "testing"}:
            raise ValueError("Experimental briefing is restricted to development and testing")
        self.settings, self.database, self.interpreter = settings, database, interpreter

    async def _source(self, session: Any, tenant: UUID, business: UUID, actor: UUID, source: UUID) -> str | None:
        await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
        params = {"tenant": tenant, "business": business, "actor": actor, "source": source}
        if not await session.scalar(text(_access_sql()), {"tenant": tenant, "live": False}):
            raise AuthError("PLAN_REQUIRED", 403)
        if not await EditorialProposalService._consented(session, tenant, business):
            raise AuthError("EDITORIAL_AI_CONSENT_REQUIRED", 409)
        row = (
            (
                await session.execute(
                    text("""SELECT a.kind,a.ciphertext,a.transcript_ciphertext
                      FROM whatsapp_material_assets a JOIN whatsapp_material_events e ON e.id=a.id
                      JOIN whatsapp_channel_links l ON l.tenant_id=e.tenant_id AND l.business_id=e.business_id
                        AND l.sender_hash=e.sender_hash AND l.actor_id=:actor
                      JOIN whatsapp_processing_consents c ON c.tenant_id=e.tenant_id AND c.business_id=e.business_id
                      WHERE a.id=:source AND a.tenant_id=:tenant AND a.business_id=:business
                        AND e.tenant_id=:tenant AND e.business_id=:business AND e.state='processed'
                        AND e.expires_at>now() AND a.delete_requested_at IS NULL AND a.expires_at>now()
                        AND l.active AND l.linked_at<=e.created_at AND c.revoked_at IS NULL
                        AND c.accepted_at<=e.created_at"""),
                    params,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise AuthError("MATERIAL_NOT_FOUND", 404)
        # Audio is usable only after transcription; no guessing from audio bytes.
        if row["kind"] == "audio" and not row["transcript_ciphertext"]:
            return None
        return EditorialProposalService(self.settings, self.database)._source(row)

    def _source_digest(self, message: str | None) -> str | None:
        if message is None or self.settings.meta_encryption_key is None:
            return None
        return hmac.new(
            self.settings.meta_encryption_key.get_secret_value().encode(), message.encode(), hashlib.sha256
        ).hexdigest()

    async def prepare(self, tenant: UUID, business: UUID, actor: UUID, source: UUID, operation: UUID) -> BriefingResult:
        if self.interpreter is None:
            raise AuthError("BRIEFING_INTERPRETER_DISABLED", 409)
        digest = hashlib.sha256(f"{tenant}:{business}:{actor}:{source}".encode()).hexdigest()
        params = {"tenant": tenant, "business": business, "actor": actor, "source": source, "operation": operation}
        async with self.database.transaction(tenant, actor) as session:
            message = await self._source(session, tenant, business, actor, source)
            row = (
                (
                    await session.execute(
                        text("""INSERT INTO editorial_briefings
                          (id,tenant_id,business_id,actor_id,source_asset_id,operation_id,request_hash,source_digest,state)
                          VALUES(:id,:tenant,:business,:actor,:source,:operation,:digest,:source_digest,'submitted')
                          ON CONFLICT DO NOTHING RETURNING id,state,request_hash,operation_id"""),
                        {**params, "id": uuid4(), "digest": digest, "source_digest": self._source_digest(message)},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                row = (
                    (
                        await session.execute(
                            text("""SELECT id,state,request_hash,operation_id FROM editorial_briefings
                              WHERE tenant_id=:tenant AND business_id=:business
                                AND (source_asset_id=:source OR operation_id=:operation)"""),
                            params,
                        )
                    )
                    .mappings()
                    .one()
                )
                if row["request_hash"] != digest or row["operation_id"] != operation:
                    raise AuthError("BRIEFING_OPERATION_CONFLICT", 409)
                if row["state"] == "submitted":
                    stale = await session.scalar(
                        text("""UPDATE editorial_briefings SET state='uncertain',updated_at=now()
                        WHERE id=:id AND state='submitted' AND updated_at<now()-interval '5 minutes' RETURNING id"""),
                        {"id": row["id"]},
                    )
                    if stale is not None:
                        return BriefingResult(row["id"], "uncertain")
                return BriefingResult(row["id"], row["state"])
            briefing_id = row["id"]
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                  VALUES(:tenant,:actor,:operation,'editorial.briefing_submitted',:business) ON CONFLICT DO NOTHING"""),
                params,
            )
        # No transaction or lock is held while the interpreter runs.
        snapshot: dict[str, object] | None = None
        state = "needs_clarification"
        if message:
            try:
                result = await resolve_catalog_context(
                    self.database, tenant, business, actor, message, self.interpreter
                )
                if result.status == "resolved":
                    snapshot = result.snapshot
                    state = "prepared"
                elif result.status in {"interpreter_unavailable", "invalid_decision"}:
                    state = "uncertain"
            except Exception:
                state = "uncertain"
        async with self.database.transaction(tenant, actor) as session:
            # Recheck source, consent, plan and owner after the interpreter returns.
            try:
                current_message = await self._source(session, tenant, business, actor, source)
                if current_message != message:
                    snapshot, state = None, "needs_clarification"
                if (
                    snapshot is not None
                    and await validate_catalog_snapshot(session, tenant, business, actor, snapshot, datetime.now(UTC))
                    != "valid"
                ):
                    snapshot, state = None, "needs_clarification"
            except AuthError:
                snapshot, state = None, "uncertain"
            row = (
                (
                    await session.execute(
                        text("""UPDATE editorial_briefings SET state=:state,catalog_snapshot=CAST(:snapshot AS jsonb),
                          updated_at=now() WHERE id=:id AND tenant_id=:tenant AND business_id=:business
                            AND state='submitted' RETURNING id,state"""),
                        {
                            **params,
                            "id": briefing_id,
                            "state": state,
                            "snapshot": json.dumps(snapshot) if snapshot else None,
                        },
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise AuthError("BRIEFING_UNAVAILABLE", 409)
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                  VALUES(:tenant,:actor,:operation,:action,:business) ON CONFLICT DO NOTHING"""),
                {**params, "operation": uuid4(), "action": f"editorial.briefing_{state}"},
            )
            return BriefingResult(row["id"], row["state"])

    async def read_valid(
        self, session: Any, tenant: UUID, business: UUID, actor: UUID, briefing_id: UUID
    ) -> tuple[Literal["prepared", "needs_clarification", "context_changed", "unavailable"], dict[str, object] | None]:
        await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
        row = (
            (
                await session.execute(
                    text("""SELECT id,source_asset_id,source_digest,state,catalog_snapshot FROM editorial_briefings
            WHERE id=:id AND tenant_id=:tenant AND business_id=:business"""),
                    {"id": briefing_id, "tenant": tenant, "business": business},
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return "unavailable", None
        if row["state"] != "prepared":
            return ("needs_clarification" if row["state"] == "needs_clarification" else "unavailable"), None
        try:
            source_message = await self._source(session, tenant, business, actor, row["source_asset_id"])
            if self._source_digest(source_message) != row["source_digest"]:
                return "context_changed", None
            if (
                await validate_catalog_snapshot(
                    session, tenant, business, actor, row["catalog_snapshot"], datetime.now(UTC)
                )
                != "valid"
            ):
                return "context_changed", None
        except AuthError:
            return "unavailable", None
        return "prepared", row["catalog_snapshot"]
