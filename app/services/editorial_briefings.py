"""Experimental durable, owner-scoped catalog context for an inbound material.

The worker can inject a synthetic interpreter or a budgeted Jev adapter in
development/testing. Paid providers require separate consent and a durable ledger.
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
from app.services.service_agreement_scope import accepted_agreement_sql
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

    async def _source(
        self,
        session: Any,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        source: UUID,
        *,
        jev: bool | None = None,
        review_preview: UUID | None = None,
    ) -> str | None:
        await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
        params = {"tenant": tenant, "business": business, "actor": actor, "source": source}
        if not await session.scalar(text(_access_sql()), {"tenant": tenant, "live": False}):
            raise AuthError("PLAN_REQUIRED", 403)
        if jev if jev is not None else self.settings.intent_ai_mode == "jev":
            consented = await session.scalar(
                text(f"""SELECT {accepted_agreement_sql()} OR EXISTS(SELECT 1 FROM intent_jev_consents
                  WHERE tenant_id=:tenant AND business_id=:business AND revoked_at IS NULL)"""),
                params,
            )
            if not consented:
                raise AuthError("JEV_CONSENT_REQUIRED", 409)
        elif not await EditorialProposalService._consented(session, tenant, business):
            raise AuthError("EDITORIAL_AI_CONSENT_REQUIRED", 409)
        row = (
            (
                await session.execute(
                    text(f"""SELECT a.kind,a.ciphertext,a.transcript_ciphertext
                      FROM whatsapp_material_assets a JOIN whatsapp_material_events e ON e.id=a.id
                      JOIN whatsapp_channel_links l ON l.tenant_id=e.tenant_id AND l.business_id=e.business_id
                        AND l.actor_id=:actor
                      LEFT JOIN whatsapp_processing_consents c ON c.tenant_id=e.tenant_id
                        AND c.business_id=e.business_id
                      WHERE a.id=:source AND a.tenant_id=:tenant AND a.business_id=:business
                        AND e.tenant_id=:tenant AND e.business_id=:business AND e.state='processed'
                        AND (e.expires_at IS NULL OR e.expires_at>now())
                        AND a.delete_requested_at IS NULL AND (a.expires_at IS NULL OR a.expires_at>now())
                        AND ({accepted_agreement_sql()} OR
                          (c.revoked_at IS NULL AND c.accepted_at<=e.created_at))"""),
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
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 44))"),
                {"key": f"candidate-source:{tenant}:{business}:{source}"},
            )
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 48))"),
                {"key": f"visual-consent:{tenant}:{business}"},
            )
            if self.settings.intent_ai_mode == "jev":
                from app.services.service_agreement import service_agreement_allowed

                if not await service_agreement_allowed(session, self.settings, tenant, business):
                    raise AuthError("SERVICE_AGREEMENT_REQUIRED", 409)
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
                            text("""SELECT id,state,request_hash,operation_id,source_digest FROM editorial_briefings
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
                if row["state"] == "budget_blocked":
                    if row["source_digest"] != self._source_digest(message):
                        changed = await session.scalar(
                            text("""UPDATE editorial_briefings SET state='needs_clarification',updated_at=now()
                              WHERE id=:id AND state='budget_blocked' RETURNING id"""),
                            {"id": row["id"]},
                        )
                        if changed is not None:
                            await session.execute(
                                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                                  VALUES(:tenant,:actor,:audit_operation,'editorial.briefing_source_changed',:business)"""),
                                {**params, "audit_operation": uuid4()},
                            )
                            return BriefingResult(row["id"], "needs_clarification")
                    else:
                        resumed = await session.scalar(
                            text("""UPDATE editorial_briefings SET state='submitted',updated_at=now()
                              WHERE id=:id AND state='budget_blocked' AND NOT EXISTS (
                                SELECT 1 FROM editorial_intent_usage u
                                WHERE u.tenant_id=:tenant AND u.operation_id=:operation)
                              RETURNING id"""),
                            {**params, "id": row["id"]},
                        )
                        if resumed is not None:
                            briefing_id = row["id"]
                            await session.execute(
                                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                                  VALUES(:tenant,:actor,:audit_operation,'editorial.briefing_budget_replayed',:business)"""),
                                {**params, "audit_operation": uuid4()},
                            )
                        else:
                            current = await session.scalar(
                                text("""SELECT state FROM editorial_briefings WHERE id=:id"""), {"id": row["id"]}
                            )
                            if current == "budget_blocked":
                                await session.execute(
                                    text("""UPDATE editorial_briefings SET state='uncertain',updated_at=now()
                                      WHERE id=:id AND state='budget_blocked' AND EXISTS (
                                        SELECT 1 FROM editorial_intent_usage u WHERE u.tenant_id=:tenant
                                          AND u.operation_id=:operation)"""),
                                    {**params, "id": row["id"]},
                                )
                                return BriefingResult(row["id"], "uncertain")
                            return BriefingResult(row["id"], current)
                    if row["source_digest"] != self._source_digest(message):
                        current = await session.scalar(
                            text("SELECT state FROM editorial_briefings WHERE id=:id"), {"id": row["id"]}
                        )
                        return BriefingResult(row["id"], current)
                elif row["state"] == "submitted":
                    stale = await session.scalar(
                        text("""UPDATE editorial_briefings SET state='uncertain',updated_at=now()
                        WHERE id=:id AND state='submitted' AND updated_at<now()-interval '5 minutes' RETURNING id"""),
                        {"id": row["id"]},
                    )
                    if stale is not None:
                        return BriefingResult(row["id"], "uncertain")
                    return BriefingResult(row["id"], row["state"])
                else:
                    return BriefingResult(row["id"], row["state"])
            else:
                briefing_id = row["id"]
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                  VALUES(:tenant,:actor,:operation,'editorial.briefing_submitted',:business) ON CONFLICT DO NOTHING"""),
                params,
            )
        # No transaction or lock is held while the interpreter runs.
        snapshot: dict[str, object] | None = None
        intent_kind = None
        suggested_format = None
        state = "needs_clarification"
        if message:
            try:
                result = await resolve_catalog_context(
                    self.database,
                    tenant,
                    business,
                    actor,
                    message,
                    self.interpreter,
                    interpret_unmatched=self.settings.intent_ai_mode == "jev",
                )
                intent_kind, suggested_format = result.intent, result.format
                # A price/availability update is not itself a request to create
                # content and never confirms the factual information it contains.
                if result.status == "resolved" and result.intent in {None, "content_request"}:
                    snapshot = result.snapshot
                    state = "prepared"
                elif result.status == "budget_blocked":
                    state = "budget_blocked"
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
                          intent_kind=:intent_kind,suggested_format=:suggested_format,
                          updated_at=now() WHERE id=:id AND tenant_id=:tenant AND business_id=:business
                            AND state='submitted' RETURNING id,state"""),
                        {
                            **params,
                            "id": briefing_id,
                            "state": state,
                            "snapshot": json.dumps(snapshot) if snapshot else None,
                            "intent_kind": intent_kind,
                            "suggested_format": suggested_format,
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
        self,
        session: Any,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        briefing_id: UUID,
    ) -> tuple[Literal["prepared", "needs_clarification", "context_changed", "unavailable"], dict[str, object] | None]:
        await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
        row = (
            (
                await session.execute(
                    text("""SELECT b.id,b.source_asset_id,b.source_digest,b.state,b.catalog_snapshot,
              EXISTS(SELECT 1 FROM editorial_intent_usage u WHERE u.tenant_id=b.tenant_id
                AND u.operation_id=b.operation_id AND u.provider='typesafe') AS used_jev FROM editorial_briefings b
            WHERE b.id=:id AND b.tenant_id=:tenant AND b.business_id=:business"""),
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
            source_message = await self._source(
                session, tenant, business, actor, row["source_asset_id"], jev=row["used_jev"]
            )
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
