"""Durable, owner-requested editorial proposals with one-shot paid execution."""

from __future__ import annotations

import builtins
import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5
from zoneinfo import ZoneInfo

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import text

from app.adapters.editorial_ai import EditorialProviderError, OpenAIEditorialProvider
from app.core.config import Settings
from app.core.editorial_creative import creative_experiment_enabled, experimental_copy_matches_fact
from app.db.session import Database
from app.schemas.brand_kits import BrandKitOverrides
from app.schemas.editorial_context import ContextContent
from app.schemas.editorial_proposals import (
    BriefingOffering,
    BriefingRead,
    ProposalDraft,
    ProposalRead,
    ProposalRequest,
    ScriptEdit,
    ScriptReview,
    ScriptScene,
    ScriptVersionRead,
)
from app.services.auth import AuthError
from app.services.brand_kits import kit_commercially_available
from app.services.plan_capabilities import INITIAL_PLAN_INTENT_FORMATS
from app.services.whatsapp_materials import WhatsAppMaterialsService


def _present(row: Any) -> ProposalRead:
    return ProposalRead.model_validate(row)


def _replay(row: Any, digest: str) -> ProposalRead:
    if row["request_hash"] != digest:
        raise AuthError("PROPOSAL_OPERATION_CONFLICT", 409)
    return _present(row)


def _access_sql() -> str:
    return """SELECT EXISTS(
      SELECT 1 FROM billing_sponsorships s WHERE s.tenant_id=:tenant
        AND s.revoked_at IS NULL AND s.starts_at<=now() AND s.ends_at>now()
      UNION ALL
      SELECT 1 FROM billing_accounts b WHERE b.tenant_id=:tenant AND b.livemode=:live
        AND b.status='active' AND NOT b.blocked AND b.paid_until>now())"""


def _script_digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()


_COMMERCIAL_CLAIM = re.compile(
    r"(?i)(?:r\$\s*\d+(?:[.,]\d+)?|\b\d+(?:[.,]\d+)?\s*(?:%|reais|horas?|dias?|h)\b|"
    r"\b(?:gr[aá]tis|gratuit[oa]s?|desconto|promo[cç][aã]o|garantid[oa]s?|hoje|amanh[aã])\b)"
)


def _catalog_fact(snapshot: dict[str, object]) -> dict[str, object] | None:
    """Use only the versioned name of an active item as an editorial fact.

    Prices, offers and temporal claims require separately validated evidence.
    The deterministic ID belongs to this catalog version, not business_context.
    """
    offering = snapshot.get("offering")
    if not isinstance(offering, dict):
        return None
    name, kind, item_id, version = (offering.get(k) for k in ("name", "kind", "id", "version"))
    if not isinstance(name, str) or not name.strip() or _COMMERCIAL_CLAIM.search(name):
        return None
    if kind not in {"product", "service"} or not isinstance(item_id, str) or type(version) is not int:
        return None
    try:
        item = UUID(item_id)
    except ValueError:
        return None
    return {
        "id": str(uuid5(NAMESPACE_URL, f"catalog-fact:{item}:{version}")),
        "kind": kind,
        "statement": name,
        "valid_until": None,
    }


def _has_unconfirmed_claim(body: ScriptEdit, confirmed_statement: str) -> bool:
    allowed = {match.group().casefold() for match in _COMMERCIAL_CLAIM.finditer(confirmed_statement)}
    copy = [body.title, body.angle]
    copy.extend(
        value for scene in body.script if scene.role != "fact" for value in (scene.on_screen_text, scene.voiceover)
    )
    return any(match.group().casefold() not in allowed for value in copy for match in _COMMERCIAL_CLAIM.finditer(value))


async def _audit(session: Any, row: Any, action: str) -> None:
    await session.execute(
        text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(:tenant,:actor,:operation,:action,:resource)
          ON CONFLICT DO NOTHING"""),
        {
            "tenant": row["tenant_id"],
            "actor": row["actor_id"],
            "operation": row.get("id") or uuid4(),
            "action": action,
            "resource": row["business_id"],
        },
    )


class EditorialProposalService:
    def __init__(
        self,
        settings: Settings,
        database: Database,
        provider: OpenAIEditorialProvider | None = None,
        *,
        owner_database: Database | None = None,
    ) -> None:
        self.settings, self.database = settings, database
        self.owner_database = owner_database
        self.provider = provider or OpenAIEditorialProvider(settings)

    async def consent_status(self, tenant: UUID, business: UUID, actor: UUID) -> dict[str, bool]:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            accepted = await session.scalar(
                text("""SELECT revoked_at IS NULL FROM editorial_ai_consents
              WHERE tenant_id=:tenant AND business_id=:business"""),
                {"tenant": tenant, "business": business},
            )
            return {"accepted": bool(accepted), "provider_enabled": self.settings.editorial_ai_mode == "openai"}

    async def set_consent(self, tenant: UUID, business: UUID, actor: UUID, accepted: bool) -> dict[str, bool]:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            current = await session.scalar(
                text("""SELECT revoked_at IS NULL FROM editorial_ai_consents
              WHERE tenant_id=:tenant AND business_id=:business FOR UPDATE"""),
                {"tenant": tenant, "business": business},
            )
            if current is not None and bool(current) == accepted:
                return {"accepted": accepted, "provider_enabled": self.settings.editorial_ai_mode == "openai"}
            if current is None and not accepted:
                return {"accepted": False, "provider_enabled": self.settings.editorial_ai_mode == "openai"}
            await session.execute(
                text("""INSERT INTO editorial_ai_consents(tenant_id,business_id,actor_id)
              VALUES(:tenant,:business,:actor) ON CONFLICT(tenant_id,business_id) DO UPDATE SET
              actor_id=EXCLUDED.actor_id,accepted_at=now(),revoked_at=CASE WHEN :accepted THEN NULL ELSE now() END"""),
                {"tenant": tenant, "business": business, "actor": actor, "accepted": accepted},
            )
            await _audit(
                session,
                {"tenant_id": tenant, "business_id": business, "actor_id": actor},
                "editorial.ai_consent_accepted" if accepted else "editorial.ai_consent_revoked",
            )
            return {"accepted": accepted, "provider_enabled": self.settings.editorial_ai_mode == "openai"}

    async def request(
        self, tenant: UUID, business: UUID, actor: UUID, payload: ProposalRequest, *, briefing_id: UUID | None = None
    ) -> ProposalRead:
        identity = str(payload.source_asset_id) if briefing_id is None else f"{payload.source_asset_id}:{briefing_id}"
        digest = hashlib.sha256(identity.encode()).hexdigest()
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            if payload.source_asset_id is not None:
                await session.execute(
                    text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 44))"),
                    {"key": f"candidate-source:{tenant}:{business}:{payload.source_asset_id}"},
                )
                if briefing_id is None and payload.operation_id == uuid5(
                    NAMESPACE_URL, f"candidate-proposal:{payload.source_asset_id}"
                ):
                    already_requires = await session.scalar(
                        text("""SELECT 1 FROM editorial_briefings WHERE tenant_id=:tenant
                          AND business_id=:business AND source_asset_id=:source"""),
                        {"tenant": tenant, "business": business, "source": payload.source_asset_id},
                    )
                    if already_requires:
                        raise AuthError("BRIEFING_REQUIRED", 409)
            existing = (
                (
                    await session.execute(
                        text("""SELECT * FROM editorial_proposals
              WHERE tenant_id=:tenant AND business_id=:business AND operation_id=:operation"""),
                        {"tenant": tenant, "business": business, "operation": payload.operation_id},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if existing is not None:
                return _replay(existing, digest)
            if not await session.scalar(
                text(_access_sql()), {"tenant": tenant, "live": self.settings.environment == "production"}
            ):
                raise AuthError("PLAN_REQUIRED", 403)
            if self.settings.editorial_ai_mode == "openai" and not await self._consented(session, tenant, business):
                raise AuthError("EDITORIAL_AI_CONSENT_REQUIRED", 409)
            if payload.source_asset_id is not None:
                source = await session.scalar(
                    text("""SELECT 1 FROM whatsapp_material_assets
                  WHERE id=:source AND tenant_id=:tenant AND business_id=:business
                    AND delete_requested_at IS NULL AND expires_at>now()"""),
                    {"source": payload.source_asset_id, "tenant": tenant, "business": business},
                )
                if source is None:
                    raise AuthError("MATERIAL_NOT_FOUND", 404)
            if briefing_id is not None:
                from app.services.editorial_briefings import EditorialBriefingService

                status, snapshot = await EditorialBriefingService(self.settings, self.database).read_valid(
                    session, tenant, business, actor, briefing_id
                )
                matching_source = await session.scalar(
                    text(
                        "SELECT source_asset_id FROM editorial_briefings "
                        "WHERE id=:id AND tenant_id=:tenant AND business_id=:business"
                    ),
                    {"id": briefing_id, "tenant": tenant, "business": business},
                )
                if status != "prepared" or snapshot is None or matching_source != payload.source_asset_id:
                    raise AuthError("BRIEFING_NOT_READY", 409)
            version = (
                await session.scalar(
                    text("""SELECT version FROM business_context_heads
              WHERE tenant_id=:tenant AND business_id=:business"""),
                    {"tenant": tenant, "business": business},
                )
                or 0
            )
            kit = (
                (
                    await session.execute(
                        text("""SELECT v.version,v.document FROM business_brand_kit_heads h
                          JOIN business_brand_kit_versions v ON v.tenant_id=h.tenant_id
                            AND v.business_id=h.business_id AND v.version=h.confirmed_version
                          WHERE h.tenant_id=:tenant AND h.business_id=:business"""),
                        {"tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if kit is not None and self.settings.environment == "production" and not kit_commercially_available():
                raise AuthError("BRAND_KIT_NOT_APPROVED", 409)
            proposal = uuid4()
            row = (
                (
                    await session.execute(
                        text("""INSERT INTO editorial_proposals
              (id,tenant_id,business_id,actor_id,operation_id,request_hash,context_version,source_asset_id,
               brand_kit_version,brand_kit_document,briefing_id,briefing_required)
              VALUES(:id,:tenant,:business,:actor,:operation,:digest,:version,:source,:kit_version,
                     CAST(:kit_document AS jsonb),:briefing_id,:briefing_required)
              ON CONFLICT(tenant_id,business_id,operation_id) DO NOTHING RETURNING *"""),
                        {
                            "id": proposal,
                            "tenant": tenant,
                            "business": business,
                            "actor": actor,
                            "operation": payload.operation_id,
                            "digest": digest,
                            "version": version,
                            "source": payload.source_asset_id,
                            "briefing_id": briefing_id,
                            "briefing_required": briefing_id is not None,
                            "kit_version": kit["version"] if kit is not None else None,
                            "kit_document": (
                                json.dumps(kit["document"], ensure_ascii=False) if kit is not None else None
                            ),
                        },
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                row = (
                    (
                        await session.execute(
                            text("""SELECT * FROM editorial_proposals
                  WHERE tenant_id=:tenant AND business_id=:business AND operation_id=:operation"""),
                            {"tenant": tenant, "business": business, "operation": payload.operation_id},
                        )
                    )
                    .mappings()
                    .one()
                )
                return _replay(row, digest)
            await _audit(session, row, "editorial.proposal_requested")
            return _present(row)

    async def list(self, tenant: UUID, business: UUID, actor: UUID, limit: int = 30) -> list[ProposalRead]:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            rows = (
                (
                    await session.execute(
                        text("""SELECT * FROM editorial_proposals
              WHERE tenant_id=:tenant AND business_id=:business AND expires_at>now()
              ORDER BY created_at DESC,id DESC LIMIT :limit"""),
                        {"tenant": tenant, "business": business, "limit": limit},
                    )
                )
                .mappings()
                .all()
            )
            return [await self._present_with_briefing(session, row, tenant, business, actor) for row in rows]

    async def _present_with_briefing(
        self, session: Any, row: Any, tenant: UUID, business: UUID, actor: UUID
    ) -> ProposalRead:
        proposal = _present(row)
        briefing_id = row.get("briefing_id")
        if briefing_id is None:
            if row.get("briefing_required"):
                return proposal.model_copy(update={"briefing": BriefingRead(status="unavailable")})
            return proposal
        if self.settings.environment not in {"development", "testing"}:
            return proposal.model_copy(update={"briefing": BriefingRead(status="unavailable")})
        from app.services.editorial_briefings import EditorialBriefingService

        status, snapshot = await EditorialBriefingService(self.settings, self.database).read_valid(
            session, tenant, business, actor, briefing_id
        )
        if status != "prepared" or snapshot is None:
            return proposal.model_copy(update={"briefing": BriefingRead(status=status)})
        offering = snapshot["offering"]
        assert isinstance(offering, dict)
        kit = row.get("brand_kit_document") or {}
        brand_name = kit.get("overrides", {}).get("brand_name")
        return proposal.model_copy(
            update={
                "briefing": BriefingRead(
                    status="prepared",
                    offering=BriefingOffering.model_validate({"name": offering["name"], "kind": offering["kind"]}),
                    brand_name=brand_name,
                    has_item_photo=bool(snapshot.get("item_photo")),
                    has_space_photo=bool(snapshot.get("space_photo")),
                )
            }
        )

    async def edit_script(
        self, tenant: UUID, business: UUID, actor: UUID, proposal_id: UUID, body: ScriptEdit
    ) -> ScriptVersionRead:
        request_hash = _script_digest(body.model_dump(mode="json"))
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            row = (
                (
                    await session.execute(
                        text("""SELECT * FROM editorial_proposals WHERE id=:id
                          AND tenant_id=:tenant AND business_id=:business FOR UPDATE"""),
                        {"id": proposal_id, "tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise AuthError("PROPOSAL_NOT_FOUND", 404)
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"),
                {"key": f"{tenant}:{business}:{body.operation_id}"},
            )
            existing = (
                (
                    await session.execute(
                        text("""SELECT * FROM editorial_script_versions WHERE tenant_id=:tenant
                          AND business_id=:business AND operation_id=:operation"""),
                        {"tenant": tenant, "business": business, "operation": body.operation_id},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if existing is not None:
                if existing["request_hash"] != request_hash or existing["proposal_id"] != proposal_id:
                    raise AuthError("SCRIPT_OPERATION_CONFLICT", 409)
                return ScriptVersionRead.model_validate(existing)
            if row["script_version"] != body.expected_version:
                raise AuthError("SCRIPT_VERSION_CONFLICT", 409)
            if row["state"] != "completed" or row["document"] is None or row["expires_at"] <= datetime.now(UTC):
                raise AuthError("SCRIPT_NOT_READY", 409)
            original = ProposalDraft.model_validate(row["document"])
            if len(original.script) != len(body.script) or any(
                (before.role, before.visual, before.fact_ids, before.source_asset_id)
                != (after.role, after.visual, after.fact_ids, after.source_asset_id)
                for before, after in zip(original.script, body.script, strict=True)
            ):
                raise AuthError("SCRIPT_PROVENANCE_CHANGED", 409)
            head = await session.scalar(
                text("""SELECT version FROM business_context_heads
                  WHERE tenant_id=:tenant AND business_id=:business"""),
                {"tenant": tenant, "business": business},
            )
            if (head or 0) != row["context_version"]:
                raise AuthError("SCRIPT_CONTEXT_CHANGED", 409)
            context_doc = await session.scalar(
                text("""SELECT document FROM business_context_versions WHERE tenant_id=:tenant
                  AND business_id=:business AND version=:version"""),
                {"tenant": tenant, "business": business, "version": head},
            )
            timezone = await session.scalar(
                text("SELECT timezone FROM businesses WHERE tenant_id=:tenant AND id=:business"),
                {"tenant": tenant, "business": business},
            )
            if context_doc is None and head:
                raise AuthError("SCRIPT_CONTEXT_CHANGED", 409)
            context = ContextContent.model_validate(context_doc) if context_doc is not None else ContextContent()
            today = datetime.now(ZoneInfo(timezone)).date()
            fact_scene = next(scene for scene in body.script if scene.role == "fact")
            fact = next((item for item in context.facts if item.id in fact_scene.fact_ids), None)
            if (
                fact is None
                and row.get("briefing_id") is not None
                and self.settings.environment in {"development", "testing"}
            ):
                from app.services.editorial_briefings import EditorialBriefingService

                status, snapshot = await EditorialBriefingService(self.settings, self.database).read_valid(
                    session, tenant, business, actor, row["briefing_id"]
                )
                catalog_fact = _catalog_fact(snapshot) if status == "prepared" and snapshot is not None else None
                if catalog_fact is None or UUID(str(catalog_fact["id"])) not in fact_scene.fact_ids:
                    raise AuthError("SCRIPT_FACT_EXPIRED", 409)
                statement = str(catalog_fact["statement"]).rstrip(". ") + "."
            else:
                if fact is None or (fact.valid_until is not None and fact.valid_until < today):
                    raise AuthError("SCRIPT_FACT_EXPIRED", 409)
                statement = fact.statement.rstrip(". ") + "."
            if fact_scene.on_screen_text != statement or fact_scene.voiceover != statement:
                raise AuthError("SCRIPT_FACT_CHANGED", 409)
            if _has_unconfirmed_claim(body, statement):
                raise AuthError("SCRIPT_UNCONFIRMED_CLAIM", 409)
            document = original.model_copy(
                update={"title": body.title, "angle": body.angle, "script": body.script}
            ).model_dump(mode="json")
            original_hash = _script_digest(row["document"])
            document_hash = _script_digest(document)
            if document_hash == original_hash:
                raise AuthError("SCRIPT_UNCHANGED", 409)
            await session.execute(
                text("""INSERT INTO editorial_script_versions
                  (proposal_id,tenant_id,business_id,version,document,document_hash,
                   context_version,source_asset_id,actor_id,review_state,review_operation_id,review_hash)
                  VALUES(:proposal,:tenant,:business,:version,CAST(:document AS jsonb),:hash,
                   :context,:source,:actor,:review_state,:review_operation,:review_hash)
                  ON CONFLICT(proposal_id,version) DO NOTHING"""),
                {
                    "proposal": proposal_id,
                    "tenant": tenant,
                    "business": business,
                    "version": row["script_version"],
                    "document": json.dumps(row["document"], ensure_ascii=False),
                    "hash": original_hash,
                    "context": head or 0,
                    "source": row["source_asset_id"],
                    "actor": row["reviewed_by"] or row["actor_id"],
                    "review_state": row["review_state"],
                    "review_operation": row["review_operation_id"],
                    "review_hash": row["review_hash"],
                },
            )
            next_version = row["script_version"] + 1
            result = (
                (
                    await session.execute(
                        text("""INSERT INTO editorial_script_versions
                          (proposal_id,tenant_id,business_id,version,document,document_hash,
                           context_version,source_asset_id,actor_id,operation_id,request_hash)
                          VALUES(:proposal,:tenant,:business,:version,CAST(:document AS jsonb),:hash,
                           :context,:source,:actor,:operation,:request_hash) RETURNING *"""),
                        {
                            "proposal": proposal_id,
                            "tenant": tenant,
                            "business": business,
                            "version": next_version,
                            "document": json.dumps(document, ensure_ascii=False),
                            "hash": document_hash,
                            "context": head or 0,
                            "source": row["source_asset_id"],
                            "actor": actor,
                            "operation": body.operation_id,
                            "request_hash": request_hash,
                        },
                    )
                )
                .mappings()
                .one()
            )
            await session.execute(
                text("""UPDATE editorial_proposals SET document=CAST(:document AS jsonb),
                  script_version=:version,review_state=NULL,review_note=NULL,
                  review_operation_id=NULL,review_hash=NULL,reviewed_at=NULL,reviewed_by=NULL,
                  updated_at=now() WHERE id=:proposal"""),
                {
                    "document": json.dumps(document, ensure_ascii=False),
                    "version": next_version,
                    "proposal": proposal_id,
                },
            )
            await _audit(session, {**row, "actor_id": actor, "id": body.operation_id}, "editorial.script_edited")
            return ScriptVersionRead.model_validate(result)

    async def script_versions(
        self, tenant: UUID, business: UUID, actor: UUID, proposal_id: UUID
    ) -> builtins.list[ScriptVersionRead]:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            row = (
                (
                    await session.execute(
                        text("""SELECT * FROM editorial_proposals WHERE id=:id
                          AND tenant_id=:tenant AND business_id=:business"""),
                        {"id": proposal_id, "tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise AuthError("PROPOSAL_NOT_FOUND", 404)
            versions = (
                (
                    await session.execute(
                        text("""SELECT * FROM editorial_script_versions WHERE tenant_id=:tenant
                          AND business_id=:business AND proposal_id=:proposal ORDER BY version"""),
                        {"tenant": tenant, "business": business, "proposal": proposal_id},
                    )
                )
                .mappings()
                .all()
            )
            if versions:
                return [ScriptVersionRead.model_validate(item) for item in versions]
            if row["document"] is None:
                return []
            return [
                ScriptVersionRead.model_validate(
                    {
                        "proposal_id": proposal_id,
                        "version": row["script_version"],
                        "document": row["document"],
                        "document_hash": _script_digest(row["document"]),
                        "context_version": row["context_version"],
                        "source_asset_id": row["source_asset_id"],
                        "actor_id": row["reviewed_by"] or row["actor_id"],
                        "operation_id": None,
                        "review_state": row["review_state"],
                        "created_at": row["created_at"],
                    }
                )
            ]

    async def review_script(
        self, tenant: UUID, business: UUID, actor: UUID, proposal_id: UUID, body: ScriptReview
    ) -> ProposalRead:
        digest = hashlib.sha256(
            json.dumps({"decision": body.decision, "note": body.note}, sort_keys=True).encode()
        ).hexdigest()
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            row = (
                (
                    await session.execute(
                        text("""SELECT * FROM editorial_proposals WHERE id=:id
                  AND tenant_id=:tenant AND business_id=:business FOR UPDATE"""),
                        {"id": proposal_id, "tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise AuthError("PROPOSAL_NOT_FOUND", 404)
            if row["review_operation_id"] == body.operation_id:
                if row["review_hash"] != digest:
                    raise AuthError("PROPOSAL_OPERATION_CONFLICT", 409)
                return _present(row)
            if row["review_state"] is not None:
                raise AuthError("SCRIPT_ALREADY_REVIEWED", 409)
            if row["state"] != "completed" or not row["document"] or not row["document"].get("script"):
                raise AuthError("SCRIPT_NOT_READY", 409)
            if row.get("briefing_required"):
                if row.get("briefing_id") is None or self.settings.environment not in {"development", "testing"}:
                    raise AuthError("SCRIPT_CONTEXT_CHANGED", 409)
                from app.services.editorial_briefings import EditorialBriefingService

                status, _ = await EditorialBriefingService(self.settings, self.database).read_valid(
                    session, tenant, business, actor, row["briefing_id"]
                )
                if status != "prepared":
                    raise AuthError("SCRIPT_CONTEXT_CHANGED", 409)
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"),
                {"key": f"{tenant}:{business}:{body.operation_id}"},
            )
            used_operation = await session.scalar(
                text("""SELECT 1 FROM editorial_proposals WHERE tenant_id=:tenant
                  AND business_id=:business AND review_operation_id=:operation"""),
                {"tenant": tenant, "business": business, "operation": body.operation_id},
            )
            if used_operation:
                raise AuthError("PROPOSAL_OPERATION_CONFLICT", 409)
            historical_operation = await session.scalar(
                text("""SELECT 1 FROM editorial_script_versions WHERE tenant_id=:tenant
                  AND business_id=:business AND review_operation_id=:operation"""),
                {"tenant": tenant, "business": business, "operation": body.operation_id},
            )
            if historical_operation:
                raise AuthError("PROPOSAL_OPERATION_CONFLICT", 409)
            result = (
                (
                    await session.execute(
                        text("""UPDATE editorial_proposals SET review_state=:decision,
                  review_note=:note,review_operation_id=:operation,review_hash=:digest,
                  reviewed_at=now(),reviewed_by=:actor WHERE id=:id RETURNING *"""),
                        {
                            "id": proposal_id,
                            "decision": body.decision,
                            "note": body.note,
                            "operation": body.operation_id,
                            "digest": digest,
                            "actor": actor,
                        },
                    )
                )
                .mappings()
                .one()
            )
            await session.execute(
                text("""UPDATE editorial_script_versions SET review_state=:decision,
                  review_operation_id=:operation,review_hash=:digest
                  WHERE proposal_id=:proposal AND version=:version"""),
                {
                    "decision": body.decision,
                    "operation": body.operation_id,
                    "digest": digest,
                    "proposal": proposal_id,
                    "version": row["script_version"],
                },
            )
            await _audit(session, result, "editorial.script_reviewed")
            return _present(result)

    @staticmethod
    async def _consented(session: Any, tenant: UUID, business: UUID) -> bool:
        return bool(
            await session.scalar(
                text("""SELECT 1 FROM editorial_ai_consents
          WHERE tenant_id=:tenant AND business_id=:business AND revoked_at IS NULL"""),
                {"tenant": tenant, "business": business},
            )
        )

    async def _reject(self, session: Any, row: Any, code: str, state: str = "rejected") -> str:
        await session.execute(
            text("""UPDATE editorial_proposals SET state=:state,error_code=:code,
          updated_at=now() WHERE id=:id"""),
            {"id": row["id"], "state": state, "code": code},
        )
        await _audit(session, row, f"editorial.proposal_{state}")
        return state

    def _source(self, row: Any) -> str | None:
        ciphertext = row["transcript_ciphertext"] or row["ciphertext"]
        if not ciphertext or not self.settings.meta_encryption_key:
            return None
        try:
            return (
                Fernet(self.settings.meta_encryption_key.get_secret_value().encode())
                .decrypt(ciphertext.encode())
                .decode()[:4000]
            )
        except (InvalidToken, UnicodeDecodeError):
            return None

    async def _inputs(self, session: Any, row: Any) -> tuple[dict[str, object], set[UUID]] | None:
        if row["source_asset_id"] is not None:
            asset = (
                (
                    await session.execute(
                        text("""SELECT a.ciphertext,a.transcript_ciphertext,a.kind
              FROM whatsapp_material_assets a WHERE a.id=:source AND a.tenant_id=:tenant
                AND a.business_id=:business AND a.delete_requested_at IS NULL AND a.expires_at>now()"""),
                        {"source": row["source_asset_id"], "tenant": row["tenant_id"], "business": row["business_id"]},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if asset is None:
                return None
            source = self._source(asset)
            kind = asset["kind"]
        else:
            source, kind = None, None
        if row["context_version"]:
            context_row = await session.scalar(
                text("""SELECT document FROM business_context_versions
              WHERE tenant_id=:tenant AND business_id=:business AND version=:version"""),
                {"tenant": row["tenant_id"], "business": row["business_id"], "version": row["context_version"]},
            )
            if context_row is None:
                return None
            context = ContextContent.model_validate(context_row)
        else:
            context = ContextContent()
        facts = [
            fact for fact in context.facts if fact.valid_until is None or fact.valid_until >= datetime.now(UTC).date()
        ]
        if not source and not facts:
            return None
        data: dict[str, object] = {
            "confirmed_facts": [
                {
                    "id": str(fact.id),
                    "kind": fact.kind,
                    "statement": fact.statement,
                    "valid_until": str(fact.valid_until) if fact.valid_until else None,
                }
                for fact in facts
            ],
            "preferences": context.preferences.model_dump(mode="json"),
            "material": source,
            "material_kind": kind,
            "source_asset_id": str(row["source_asset_id"]) if row["source_asset_id"] else None,
            "context_version": row["context_version"],
        }
        valid_ids = {fact.id for fact in facts}
        briefing_id = row.get("briefing_id")
        if row.get("briefing_required") and briefing_id is None:
            return None
        if briefing_id is not None:
            if self.owner_database is None or self.settings.environment not in {"development", "testing"}:
                return None
            from app.services.editorial_briefings import EditorialBriefingService

            async with self.owner_database.transaction(row["tenant_id"], row["actor_id"]) as owner_session:
                status, snapshot = await EditorialBriefingService(self.settings, self.owner_database).read_valid(
                    owner_session, row["tenant_id"], row["business_id"], row["actor_id"], briefing_id
                )
                suggested_format = await owner_session.scalar(
                    text(
                        "SELECT suggested_format FROM editorial_briefings "
                        "WHERE id=:id AND tenant_id=:tenant AND business_id=:business"
                    ),
                    {"id": briefing_id, "tenant": row["tenant_id"], "business": row["business_id"]},
                )
            if status != "prepared" or snapshot is None:
                return None
            if suggested_format is not None and suggested_format not in INITIAL_PLAN_INTENT_FORMATS:
                return None
            data["requested_format"] = suggested_format
            data["eligible_formats"] = list(INITIAL_PLAN_INTENT_FORMATS)
            offering = snapshot["offering"]
            assert isinstance(offering, dict)
            price = offering["price"]
            assert isinstance(price, dict)
            data["catalog_context"] = {
                "name": offering["name"],
                "kind": offering["kind"],
                "price": price if price.get("status") == "valid" else None,
                "has_item_photo": bool(snapshot.get("item_photo")),
                "has_space_photo": bool(snapshot.get("space_photo")),
            }
            catalog_fact = _catalog_fact(snapshot)
            if catalog_fact is not None:
                catalog_id = UUID(str(catalog_fact["id"]))
                if catalog_id in valid_ids:
                    return None
                valid_ids.add(catalog_id)
                confirmed = data["confirmed_facts"]
                assert isinstance(confirmed, list)
                confirmed.insert(0, catalog_fact)
        kit_document = row.get("brand_kit_document")
        if kit_document is not None:
            if self.settings.environment == "production" and not kit_commercially_available():
                return None
            overrides = BrandKitOverrides.model_validate(kit_document["overrides"])
            data["brand_kit"] = {
                "kit_id": kit_document["kit_id"],
                "kit_version": kit_document["kit_version"],
                "applied_version": row["brand_kit_version"],
                "brand_name": overrides.brand_name,
                "tagline": overrides.tagline,
                "cta": overrides.cta,
                "logo_asset_id": str(overrides.logo_asset_id) if overrides.logo_asset_id else None,
                "palette": overrides.palette.model_dump(),
                "heading_font": overrides.heading_font,
                "body_font": overrides.body_font,
                "formats": overrides.formats.model_dump(),
            }
        return data, valid_ids

    @staticmethod
    def _baseline(data: dict[str, object]) -> ProposalDraft:
        facts = data["confirmed_facts"]
        assert isinstance(facts, list)
        fact = facts[0] if facts else None
        assert fact is None or isinstance(fact, dict)
        angle = (
            f"Apresente este ponto do negócio: {str(fact['statement']).rstrip('. ')}."
            if fact
            else "Mostre o material recebido e explique ao público o que ele representa para o negócio."
        )
        kind = data["material_kind"]
        fmt: Literal["short_video", "photo", "story"] = (
            "short_video" if kind in {"audio", "video"} else "photo" if kind == "image" else "story"
        )
        requested = data.get("requested_format")
        eligible = data.get("eligible_formats")
        if requested == "photo":
            fmt = "photo"
        elif requested == "story":
            fmt = "story"
        elif isinstance(eligible, list) and fmt not in eligible:
            fmt = "story"
        draft = ProposalDraft(
            title="Uma história do seu negócio",
            format=fmt,
            angle=angle,
            fact_ids=[UUID(str(fact["id"]))] if fact else [],
            hypotheses=[],
            questions=["Qual detalhe você gostaria de destacar?"],
            scene_plan=["material", "fact", "cta"] if kind in {"image", "video"} else ["fact", "cta"],
        )
        return draft.model_copy(update={"script": EditorialProposalService._script(draft, data)})

    @staticmethod
    def _script(
        draft: ProposalDraft, data: dict[str, object], *, experimental: bool = False
    ) -> builtins.list[ScriptScene]:
        facts = data["confirmed_facts"]
        assert isinstance(facts, list)
        if not facts:
            return []
        first = facts[0]
        if experimental:
            first = next((fact for fact in facts if draft.fact_ids and str(fact["id"]) == str(draft.fact_ids[0])), None)
            if first is None:
                raise ValueError("Experimental fact source unavailable")
        assert isinstance(first, dict)
        fact_id = UUID(str(first["id"]))
        statement = str(first["statement"]).rstrip(". ") + "."
        source_value = data.get("source_asset_id")
        source_id = UUID(str(source_value)) if source_value else None
        visual_available = source_id is not None and data.get("material_kind") in {"image", "video"}
        default_plan: list[Literal["material", "fact", "cta"]] = (
            ["material", "fact", "cta"] if visual_available else ["fact", "cta"]
        )
        requested = list(dict.fromkeys(draft.scene_plan or default_plan))
        roles: list[Literal["material", "fact", "cta"]] = [
            role for role in requested if role != "material" or visual_available
        ]
        if "fact" not in roles:
            roles.insert(0, "fact")
        if "cta" not in roles:
            roles.append("cta")
        scenes: list[ScriptScene] = []
        for role in roles:
            if role == "material":
                scenes.append(
                    ScriptScene(
                        role=role,
                        visual="source_material",
                        on_screen_text=draft.title if experimental else "Seu negócio em destaque",
                        voiceover=(draft.angle if len(draft.angle) <= 240 else draft.title)
                        if experimental
                        else "Veja este material do negócio.",
                        fact_ids=[],
                        source_asset_id=source_id,
                    )
                )
            elif role == "fact":
                scenes.append(
                    ScriptScene(
                        role=role,
                        visual="brand_card",
                        on_screen_text=statement,
                        voiceover=statement,
                        fact_ids=[fact_id],
                    )
                )
            else:
                scenes.append(
                    ScriptScene(
                        role=role,
                        visual="brand_card",
                        on_screen_text="Fale com o negócio",
                        voiceover="Entre em contato para saber mais.",
                        fact_ids=[],
                    )
                )
        return scenes

    @staticmethod
    def _safe(draft: ProposalDraft, data: dict[str, object], valid_ids: set[UUID]) -> bool:
        eligible = data.get("eligible_formats")
        if isinstance(eligible, list) and (
            draft.format not in eligible or (data.get("requested_format") and draft.format != data["requested_format"])
        ):
            return False
        if not draft.fact_ids or not set(draft.fact_ids) <= valid_ids:
            return False
        facts = data["confirmed_facts"]
        assert isinstance(facts, list)
        evidence = " ".join(str(fact["statement"]) for fact in facts if isinstance(fact, dict))
        if any(number not in evidence for number in re.findall(r"\d+", draft.title + " " + draft.angle)):
            return False
        preferences = data["preferences"]
        assert isinstance(preferences, dict)
        grounded = EditorialProposalService._ground(draft, data)
        visible_text = " ".join((draft.title, draft.angle, grounded.title, grounded.angle)).casefold()
        return not any(str(topic).casefold() in visible_text for topic in preferences.get("avoided_topics", []))

    @staticmethod
    def _safe_experimental(draft: ProposalDraft, data: dict[str, object], valid_ids: set[UUID]) -> bool:
        # Keep the existing guard, then require one source for both title and angle.
        if not EditorialProposalService._safe(draft, data, valid_ids):
            return False
        if len(draft.fact_ids) != 1 or draft.fact_ids[0] not in valid_ids:
            return False
        facts = data["confirmed_facts"]
        assert isinstance(facts, list)
        fact = next((item for item in facts if str(item["id"]) == str(draft.fact_ids[0])), None)
        if fact is None:
            return False
        statement = str(fact["statement"])
        copy = f"{draft.title} {draft.angle}"
        preferences = data["preferences"]
        assert isinstance(preferences, dict)
        visible = f"{copy} {statement}".casefold()
        return experimental_copy_matches_fact(copy, statement) and not any(
            str(topic).casefold() in visible for topic in preferences.get("avoided_topics", [])
        )

    @staticmethod
    def _ground(draft: ProposalDraft, data: dict[str, object], *, experimental: bool = False) -> ProposalDraft:
        """Keep factual scenes exact; only a bounded dev/test experiment preserves copy."""
        baseline = EditorialProposalService._baseline(data)
        return ProposalDraft(
            title=draft.title if experimental else baseline.title,
            format=draft.format,
            angle=draft.angle if experimental else baseline.angle,
            fact_ids=draft.fact_ids if experimental else baseline.fact_ids,
            hypotheses=draft.hypotheses,
            questions=draft.questions,
            scene_plan=draft.scene_plan,
            script=EditorialProposalService._script(draft, data, experimental=experimental),
        )

    async def run(self, proposal_id: UUID) -> str:
        async with self.database.sessions() as session, session.begin():
            row = (
                (
                    await session.execute(
                        text("SELECT * FROM editorial_proposals WHERE id=:id FOR UPDATE"), {"id": proposal_id}
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None or row["state"] != "dispatching":
                return "skipped"
            if row["expires_at"] <= datetime.now(UTC):
                return await self._reject(session, row, "PROPOSAL_EXPIRED")
            if not await session.scalar(
                text(_access_sql()), {"tenant": row["tenant_id"], "live": self.settings.environment == "production"}
            ):
                return await self._reject(session, row, "PLAN_INACTIVE")
            if self.settings.editorial_ai_mode == "openai" and not await self._consented(
                session, row["tenant_id"], row["business_id"]
            ):
                return await self._reject(session, row, "EDITORIAL_AI_CONSENT_REQUIRED")
            inputs = await self._inputs(session, row)
            if inputs is None:
                return await self._reject(session, row, "EDITORIAL_SOURCE_UNAVAILABLE")
            data, _ = inputs
            if not data["confirmed_facts"]:
                return await self._reject(session, row, "EDITORIAL_FACTS_REQUIRED")
            if self.settings.editorial_ai_mode == "disabled":
                baseline_draft = self._baseline(data)
                await session.execute(
                    text("""UPDATE editorial_proposals SET state='completed',
                  document=CAST(:doc AS jsonb),
                  model='baseline-v1',updated_at=now() WHERE id=:id"""),
                    {"doc": baseline_draft.model_dump_json(), "id": proposal_id},
                )
                await _audit(session, row, "editorial.proposal_completed")
                return "completed"
            reserved = len(json.dumps(data, ensure_ascii=False).encode()) + 3800
            if reserved > 30000:
                return await self._reject(session, row, "EDITORIAL_INPUT_TOO_LARGE")
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:tenant,1))"), {"tenant": str(row["tenant_id"])}
            )
            used = await session.scalar(
                text("""SELECT coalesce(sum(reserved_tokens),0) FROM editorial_ai_usage
              WHERE tenant_id=:tenant AND created_at>=date_trunc('day',now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'"""),
                {"tenant": row["tenant_id"]},
            )
            if used + reserved > self.settings.editorial_daily_token_limit:
                return await self._reject(session, row, "EDITORIAL_BUDGET_EXCEEDED", "budget_exceeded")
            await session.execute(
                text("""INSERT INTO editorial_ai_usage
              (proposal_id,tenant_id,business_id,reserved_tokens,state)
              VALUES(:id,:tenant,:business,:reserved,'submitted')"""),
                {"id": proposal_id, "tenant": row["tenant_id"], "business": row["business_id"], "reserved": reserved},
            )
            await session.execute(
                text("""UPDATE editorial_proposals SET state='submitted',reserved_tokens=:reserved,
              model=:model,updated_at=now() WHERE id=:id"""),
                {"id": proposal_id, "reserved": reserved, "model": self.settings.editorial_ai_model},
            )
            await _audit(session, row, "editorial.proposal_submitted")
        draft: ProposalDraft | None
        try:
            draft, input_tokens, output_tokens = await self.provider.propose(data, proposal_id)
        except EditorialProviderError:
            draft, input_tokens, output_tokens = None, None, None
        async with self.database.sessions() as session, session.begin():
            row = (
                (
                    await session.execute(
                        text("SELECT * FROM editorial_proposals WHERE id=:id FOR UPDATE"), {"id": proposal_id}
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None or row["state"] != "submitted":
                return "uncertain"
            consent = await self._consented(session, row["tenant_id"], row["business_id"])
            access = await session.scalar(
                text(_access_sql()),
                {"tenant": row["tenant_id"], "live": self.settings.environment == "production"},
            )
            fresh_inputs = await self._inputs(session, row) if consent and access else None
            experimental = creative_experiment_enabled(self.settings)
            safe = bool(
                draft is not None
                and fresh_inputs is not None
                and (
                    self._safe_experimental(draft, fresh_inputs[0], fresh_inputs[1])
                    if experimental
                    else self._safe(draft, fresh_inputs[0], fresh_inputs[1])
                )
            )
            if safe and draft is not None and fresh_inputs is not None:
                draft = self._ground(draft, fresh_inputs[0], experimental=experimental)
            state = "completed" if safe else "uncertain"
            await session.execute(
                text("""UPDATE editorial_proposals SET state=:state,
              document=CAST(:doc AS jsonb),error_code=:error,input_tokens=:input,
              output_tokens=:output,updated_at=now() WHERE id=:id"""),
                {
                    "id": proposal_id,
                    "state": state,
                    "doc": draft.model_dump_json() if safe and draft else None,
                    "error": None if safe else "EDITORIAL_RESULT_UNCERTAIN",
                    "input": input_tokens,
                    "output": output_tokens,
                },
            )
            await session.execute(
                text("""UPDATE editorial_ai_usage SET state=:state,
              input_tokens=:input,output_tokens=:output WHERE proposal_id=:id"""),
                {"id": proposal_id, "state": state, "input": input_tokens, "output": output_tokens},
            )
            await _audit(session, row, f"editorial.proposal_{state}")
            return state


async def reconcile_stale_proposals(database: Database, limit: int = 100) -> int:
    async with database.sessions() as session, session.begin():
        rows = (
            (
                await session.execute(
                    text("""WITH due AS (
          SELECT id FROM editorial_proposals WHERE
            (state='submitted' AND updated_at<now()-interval '5 minutes') OR
            (state='dispatching' AND dispatch_lease_until IS NULL
              AND updated_at<now()-interval '10 minutes')
          ORDER BY updated_at,id LIMIT :limit FOR UPDATE SKIP LOCKED)
          UPDATE editorial_proposals p SET state='uncertain',error_code='EDITORIAL_RESULT_UNCERTAIN',
            updated_at=now() FROM due WHERE p.id=due.id
          RETURNING p.id,p.tenant_id,p.business_id,p.actor_id"""),
                    {"limit": limit},
                )
            )
            .mappings()
            .all()
        )
        for row in rows:
            await session.execute(
                text("""UPDATE editorial_ai_usage SET state='uncertain'
              WHERE proposal_id=:id AND state='submitted'"""),
                {"id": row["id"]},
            )
            await _audit(session, row, "editorial.proposal_uncertain")
        await session.execute(text("DELETE FROM editorial_proposals WHERE expires_at<=now()"))
        return len(rows)
