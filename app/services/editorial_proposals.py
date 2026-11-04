"""Durable, owner-requested editorial proposals with one-shot paid execution."""

from __future__ import annotations

import builtins
import hashlib
import hmac
import json
import re
from datetime import UTC, date, datetime
from typing import Any, Literal
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5
from zoneinfo import ZoneInfo

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import text

from app.adapters.editorial_ai import EditorialProviderError, OpenAIEditorialProvider
from app.core.config import Settings
from app.core.editorial_creative import experimental_copy_matches_fact
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
from app.services.editorial_copy_quality import public_copy_has_no_internal_artifacts
from app.services.editorial_cta import public_action_matches_destination
from app.services.plan_capabilities import INITIAL_PLAN_INTENT_FORMATS
from app.services.reference_generation_context import (
    capture_generation_context,
    generation_context_is_current,
    read_generation_snapshot,
)
from app.services.service_agreement import service_agreement_allowed
from app.services.service_agreement_scope import (
    accepted_agreement_sql,
    agreement_worker_scope,
    editorial_agreement_generation_sql,
    service_agreement_accepted,
)
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


def _encode_request_trace(key: str, request: dict[str, object]) -> tuple[str, str]:
    """Encrypt the exact request and authenticate it without exposing its contents."""
    body = json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    digest = hmac.new(key.encode(), body, hashlib.sha256).hexdigest()
    return digest, Fernet(key.encode()).encrypt(body).decode()


def _decode_request_trace(key: str, digest: str, ciphertext: str) -> dict[str, object]:
    try:
        body = Fernet(key.encode()).decrypt(ciphertext.encode())
        expected = hmac.new(key.encode(), body, hashlib.sha256).hexdigest()
        value = json.loads(body)
        if not hmac.compare_digest(digest, expected) or not isinstance(value, dict):
            raise ValueError("Trace integrity mismatch")
        return value
    except (InvalidToken, ValueError, TypeError, UnicodeDecodeError) as exc:
        raise AuthError("EDITORIAL_TRACE_UNAVAILABLE", 409) from exc


def _current_script_version(row: Any) -> ScriptVersionRead:
    return ScriptVersionRead.model_validate(
        {
            "proposal_id": row["id"],
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


def _catalog_price_fact(snapshot: dict[str, object]) -> dict[str, object] | None:
    """Create a price fact only from a previously revalidated catalog snapshot."""
    name_fact = _catalog_fact(snapshot)
    offering = snapshot.get("offering")
    if name_fact is None or not isinstance(offering, dict) or snapshot.get("promotions") != []:
        return None
    price = offering.get("price")
    if not isinstance(price, dict) or price.get("status") != "valid" or price.get("currency") != "BRL":
        return None
    amount, deadline = price.get("amount_minor"), price.get("valid_until")
    if type(amount) is not int or not 0 <= amount <= 1000000000 or not isinstance(deadline, str):
        return None
    try:
        if date.fromisoformat(deadline).isoformat() != deadline:
            return None
    except ValueError:
        return None
    identity = f"catalog-price:{offering['id']}:{offering['version']}:{amount}:{deadline}"
    return {
        "id": str(uuid5(NAMESPACE_URL, identity)),
        "kind": "price",
        "statement": f"{name_fact['statement']} por R$ {amount // 100},{amount % 100:02d}",
        "valid_until": deadline,
    }


def _has_unconfirmed_claim(body: ScriptEdit, confirmed_statement: str) -> bool:
    allowed = {match.group().casefold() for match in _COMMERCIAL_CLAIM.finditer(confirmed_statement)}
    copy = [body.title, body.angle]
    copy.extend(
        value for scene in body.script if scene.role != "fact" for value in (scene.on_screen_text, scene.voiceover)
    )
    return any(match.group().casefold() not in allowed for value in copy for match in _COMMERCIAL_CLAIM.finditer(value))


def generated_copy_matches_fact(draft: ProposalDraft, statement: str, avoided_topics: list[str]) -> bool:
    """Conservative lexical check, not proof of semantic truth; owner review remains necessary."""
    if len(draft.fact_ids) != 1 or not draft.art_text or not draft.caption or not draft.cta:
        return False
    copy = " ".join((draft.title, draft.angle, draft.art_text, draft.caption, draft.cta))
    visible = f"{copy} {statement}".casefold()
    return experimental_copy_matches_fact(copy, statement) and not any(
        topic.casefold() in visible for topic in avoided_topics
    )


def _fact_check_direction(direction: str, format: str) -> str:
    """Remove recognized design notation without granting it factual authority."""
    result = re.sub(r"#(?:[0-9a-f]{8}|[0-9a-f]{6}|[0-9a-f]{4}|[0-9a-f]{3})\b", " ", direction, flags=re.IGNORECASE)
    result = re.sub(
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
        " ",
        result,
        flags=re.IGNORECASE,
    )
    ratio = r"(?<!\d)9\s*:\s*16(?!\d)" if format == "story" else r"(?<!\d)4\s*:\s*5(?!\d)"
    result = re.sub(ratio, " ", result)
    result = re.sub(r"(?<!\w)\d+\)\s*", " ", result)
    return re.sub(r"\bmarge(?:m|ns)\s+(?:seguras?\s+)?de\s+\d+(?:[.,]\d+)?\s*%", "margem visual", result)


def natural_generated_copy_matches_fact(
    draft: ProposalDraft, statement: str, avoided_topics: list[str], *, destination: str | None = None
) -> bool:
    """Check citations, values and known commercial expressions, not semantic truth.

    This experimental precheck cannot validate arbitrary factual claims: a human
    must still review the proposed copy and finished visual before publication.
    """
    brief = draft.creative_brief
    if len(draft.fact_ids) != 1 or not draft.art_text or not draft.caption or not draft.cta or brief is None:
        return False
    if not public_copy_has_no_internal_artifacts(draft):
        return False
    values = [draft.title, draft.angle, draft.art_text, draft.caption, draft.cta]
    creative_direction = " ".join(
        (brief.objective, brief.concept, brief.visual_direction, brief.hierarchy, brief.photo_use)
    ).casefold()
    copy = " ".join(values).casefold() + " " + creative_direction
    evidence = statement.casefold()
    if any(topic.casefold() in copy for topic in avoided_topics):
        return False
    allowed_numbers = set(re.findall(r"\d+(?:[.,]\d+)*", evidence))
    # Technical notation is ignored only in the private direction, never in
    # public copy or the evidence; it cannot authorize a commercial value.
    public_copy = " ".join(values).casefold()
    if destination:
        # Permit the exact owner-configured contact, not its individual numbers.
        public_copy = public_copy.replace(destination.casefold(), " ")
    number_checked = public_copy + " " + _fact_check_direction(creative_direction, draft.format)
    if any(number not in allowed_numbers for number in re.findall(r"\d+(?:[.,]\d+)*", number_checked)):
        return False
    allowed_claims = {re.sub(r"\s+", "", match.group()) for match in _COMMERCIAL_CLAIM.finditer(evidence)}
    return all(re.sub(r"\s+", "", match.group()) in allowed_claims for match in _COMMERCIAL_CLAIM.finditer(copy))


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

    async def get_request_trace(
        self, tenant: UUID, business: UUID, actor: UUID, proposal_id: UUID
    ) -> dict[str, object]:
        """Return the encrypted exact provider request only to an authorized owner."""
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            row = (
                (
                    await session.execute(
                        text("""SELECT t.request_hash,t.ciphertext,t.created_at,
                          p.state AS proposal_state,p.error_code AS proposal_error_code
                          FROM editorial_request_traces t JOIN editorial_proposals p
                            ON p.id=t.proposal_id AND p.tenant_id=t.tenant_id AND p.business_id=t.business_id
                          WHERE t.tenant_id=:tenant AND t.business_id=:business AND t.proposal_id=:proposal"""),
                        {"tenant": tenant, "business": business, "proposal": proposal_id},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise AuthError("EDITORIAL_TRACE_NOT_FOUND", 404)
            key = self.settings.meta_encryption_key
            if key is None:
                raise AuthError("EDITORIAL_TRACE_UNAVAILABLE", 409)
            value = _decode_request_trace(key.get_secret_value(), row["request_hash"], row["ciphertext"])
            return {
                "proposal_id": str(proposal_id),
                "trace_status": "prepared",
                "proposal_state": row["proposal_state"],
                "proposal_error_code": row["proposal_error_code"],
                "request_hash": row["request_hash"],
                "request": value,
                "created_at": row["created_at"],
            }

    async def consent_status(self, tenant: UUID, business: UUID, actor: UUID) -> dict[str, bool]:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            accepted = await session.scalar(
                text(f"""SELECT {accepted_agreement_sql()} OR EXISTS(SELECT 1 FROM editorial_ai_consents
              WHERE tenant_id=:tenant AND business_id=:business AND revoked_at IS NULL)"""),
                {"tenant": tenant, "business": business},
            )
            return {"accepted": bool(accepted), "provider_enabled": self.settings.editorial_ai_mode == "openai"}

    async def set_consent(self, tenant: UUID, business: UUID, actor: UUID, accepted: bool) -> dict[str, bool]:
        from app.services.visual_consent_gate import VisualConsentGate

        async with self.database.transaction(tenant, actor) as session:
            await VisualConsentGate._lock(session, tenant, business, actor)
            if await service_agreement_accepted(session, tenant, business):
                raise AuthError("SERVICE_AGREEMENT_MANAGES_PROCESSING", 409)
            current = await session.scalar(
                text("""SELECT revoked_at IS NULL FROM editorial_ai_consents
              WHERE tenant_id=:tenant AND business_id=:business FOR UPDATE"""),
                {"tenant": tenant, "business": business},
            )
            if current is not None and bool(current) == accepted:
                return {
                    "accepted": accepted,
                    "provider_enabled": self.settings.editorial_ai_mode == "openai",
                }
            if current is None and not accepted:
                return {
                    "accepted": False,
                    "provider_enabled": self.settings.editorial_ai_mode == "openai",
                }
            await session.execute(
                text("""INSERT INTO editorial_ai_consents(tenant_id,business_id,actor_id)
              VALUES(:tenant,:business,:actor) ON CONFLICT(tenant_id,business_id) DO UPDATE SET
              actor_id=EXCLUDED.actor_id,accepted_at=CASE WHEN :accepted THEN now()
                ELSE editorial_ai_consents.accepted_at END,
              generation=editorial_ai_consents.generation+CASE WHEN :accepted THEN 0 ELSE 1 END,
              revoked_at=CASE WHEN :accepted THEN NULL ELSE now() END"""),
                {"tenant": tenant, "business": business, "actor": actor, "accepted": accepted},
            )
            await _audit(
                session,
                {"tenant_id": tenant, "business_id": business, "actor_id": actor},
                "editorial.ai_consent_accepted" if accepted else "editorial.ai_consent_revoked",
            )
            return {
                "accepted": accepted,
                "provider_enabled": self.settings.editorial_ai_mode == "openai",
            }

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
            # The epoch read and request insertion share the withdrawal lock.
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 48))"),
                {"key": f"visual-consent:{tenant}:{business}"},
            )
            generation = await session.scalar(
                text(editorial_agreement_generation_sql()),
                {"tenant": tenant, "business": business},
            )
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
                if (
                    self.settings.editorial_ai_mode == "openai"
                    and existing["state"] in {"pending", "dispatching"}
                    and existing["consent_generation"] != generation
                ):
                    raise AuthError("EDITORIAL_REQUEST_CANCELLED", 409)
                return _replay(existing, digest)
            if not await session.scalar(
                text(_access_sql()), {"tenant": tenant, "live": self.settings.environment == "production"}
            ):
                raise AuthError("PLAN_REQUIRED", 403)
            if self.settings.editorial_ai_mode == "openai" and not await service_agreement_allowed(
                session, self.settings, tenant, business
            ):
                raise AuthError("SERVICE_AGREEMENT_REQUIRED", 409)
            if self.settings.editorial_ai_mode == "openai" and not await self._consented(session, tenant, business):
                raise AuthError("EDITORIAL_AI_CONSENT_REQUIRED", 409)
            if payload.source_asset_id is not None:
                source = await session.scalar(
                    text("""SELECT 1 FROM whatsapp_material_assets
                  WHERE id=:source AND tenant_id=:tenant AND business_id=:business
                    AND delete_requested_at IS NULL AND (expires_at IS NULL OR expires_at>now())"""),
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
            references = await session.scalar(
                text("""SELECT coalesce(jsonb_agg(jsonb_build_object(
                  'id',id,'instagram_handle',instagram_handle,'note',note,
                  'source','owner','access_status','not_checked') ORDER BY created_at,id), '[]'::jsonb)
                  FROM owner_references WHERE tenant_id=:tenant AND business_id=:business AND removed_at IS NULL"""),
                {"tenant": tenant, "business": business},
            )
            reference_context = await capture_generation_context(session, business)
            proposal = uuid4()
            row = (
                (
                    await session.execute(
                        text("""INSERT INTO editorial_proposals
              (id,tenant_id,business_id,actor_id,operation_id,request_hash,context_version,source_asset_id,
               brand_kit_version,brand_kit_document,briefing_id,briefing_required,consent_generation,
               owner_reference_snapshot,reference_generation_snapshot)
              VALUES(:id,:tenant,:business,:actor,:operation,:digest,:version,:source,:kit_version,
                     CAST(:kit_document AS jsonb),:briefing_id,:briefing_required,:generation,
                     CAST(:references AS jsonb),CAST(:reference_context AS jsonb))
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
                            "references": json.dumps(references or [], ensure_ascii=False),
                            "reference_context": reference_context.model_dump_json(),
                            "generation": (
                                generation
                                if self.settings.editorial_ai_mode == "openai"
                                or (generation is not None and generation < 0)
                                else None
                            ),
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
        from app.services.visual_pending_scripts import apply_pending_script_changes

        await apply_pending_script_changes(self.settings, self.database, tenant, business, actor)
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            rows = (
                (
                    await session.execute(
                        text("""SELECT e.*,(SELECT jsonb_build_object('operation_id',c.operation_id,
                  'status',c.state,'error_code',c.error_code) FROM business_visual_pending_changes c
                  WHERE c.tenant_id=e.tenant_id AND c.business_id=e.business_id
                    AND c.resource_key='script:'||e.id::text AND c.state IN ('pending','failed')) AS pending_change
              FROM editorial_proposals e
              WHERE e.tenant_id=:tenant AND e.business_id=:business
                AND (e.expires_at>now() OR EXISTS(SELECT 1 FROM media_previews p
                  WHERE p.proposal_id=e.id AND p.state='completed'))
              ORDER BY e.created_at DESC,e.id DESC LIMIT :limit"""),
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
        async with self.database.transaction(tenant, actor) as session:
            return await self._edit_script_in_session(session, tenant, business, actor, proposal_id, body)

    async def _edit_script_in_session(
        self,
        session: Any,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        proposal_id: UUID,
        body: ScriptEdit,
        *,
        enqueue: bool = True,
    ) -> ScriptVersionRead:
        request_hash = _script_digest(body.model_dump(mode="json"))
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
        from app.services.visual_consent_gate import VisualConsentGate

        await VisualConsentGate._lock(session, tenant, business, actor)
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
        if original.art_text is not None or original.caption is not None or original.cta is not None:
            # The legacy editor cannot edit or validate the generated copy fields.
            raise AuthError("SCRIPT_GENERATED_COPY_EDIT_UNSUPPORTED", 409)
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
        # Historic JSON may omit optional fields added by newer schemas. Compare
        # the normalized views for no-op detection while retaining the original
        # raw hash for version provenance and pending-change fencing.
        if document == original.model_dump(mode="json"):
            raise AuthError("SCRIPT_UNCHANGED", 409)
        if enqueue:
            from app.services.visual_pending_changes import VisualPendingChanges
            from app.services.visual_pending_scripts import require_script_change_slot

            await require_script_change_slot(
                session, tenant, business, actor, proposal_id, body.operation_id, "script_edit", request_hash
            )
            deferred = await VisualPendingChanges.enqueue_in_session(
                session,
                tenant,
                business,
                actor,
                body.operation_id,
                "script_edit",
                f"script:{proposal_id}",
                request_hash,
                {"proposal_id": str(proposal_id), "body": body.model_dump(mode="json")},
            )
            if deferred:
                return ScriptVersionRead.model_validate(
                    {
                        **_current_script_version(row).model_dump(),
                        "pending_change": {"operation_id": body.operation_id, "status": "pending"},
                    }
                )
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
        from app.services.visual_pending_scripts import apply_pending_script_changes, script_change_status

        await apply_pending_script_changes(self.settings, self.database, tenant, business, actor)
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
            pending = await script_change_status(session, tenant, business, proposal_id)
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
                return [
                    ScriptVersionRead.model_validate(
                        {**item, "pending_change": pending if item["version"] == row["script_version"] else None}
                    )
                    for item in versions
                ]
            if row["document"] is None:
                return []
            return [
                ScriptVersionRead.model_validate(
                    {**_current_script_version(row).model_dump(), "pending_change": pending}
                )
            ]

    async def review_script(
        self, tenant: UUID, business: UUID, actor: UUID, proposal_id: UUID, body: ScriptReview
    ) -> ProposalRead:
        async with self.database.transaction(tenant, actor) as session:
            return await self._review_script_in_session(session, tenant, business, actor, proposal_id, body)

    async def _review_script_in_session(
        self,
        session: Any,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        proposal_id: UUID,
        body: ScriptReview,
        *,
        enqueue: bool = True,
    ) -> ProposalRead:
        digest = hashlib.sha256(
            json.dumps({"decision": body.decision, "note": body.note}, sort_keys=True).encode()
        ).hexdigest()
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
        from app.services.visual_consent_gate import VisualConsentGate

        await VisualConsentGate._lock(session, tenant, business, actor)
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
        if enqueue:
            from app.services.visual_pending_changes import VisualPendingChanges
            from app.services.visual_pending_scripts import require_script_change_slot

            await require_script_change_slot(
                session, tenant, business, actor, proposal_id, body.operation_id, "script_review", digest
            )
            deferred = await VisualPendingChanges.enqueue_in_session(
                session,
                tenant,
                business,
                actor,
                body.operation_id,
                "script_review",
                f"script:{proposal_id}",
                digest,
                {
                    "proposal_id": str(proposal_id),
                    "expected_version": row["script_version"],
                    "body": body.model_dump(mode="json"),
                },
            )
            if deferred:
                return ProposalRead.model_validate(
                    {**row, "pending_change": {"operation_id": body.operation_id, "status": "pending"}}
                )
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
                text(f"""SELECT {accepted_agreement_sql()} OR EXISTS(SELECT 1 FROM editorial_ai_consents
          WHERE tenant_id=:tenant AND business_id=:business AND revoked_at IS NULL)"""),
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
                AND a.business_id=:business AND a.delete_requested_at IS NULL
                AND (a.expires_at IS NULL OR a.expires_at>now())"""),
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
        data: dict[str, object] = {
            "confirmed_facts": [],
            "preferences": context.preferences.model_dump(mode="json", exclude={"reference_search"}),
            "material": source,
            "material_kind": kind,
            "source_asset_id": str(row["source_asset_id"]) if row["source_asset_id"] else None,
            "context_version": row["context_version"],
        }
        if row.get("reference_generation_snapshot") is not None:
            data["reference_context"] = read_generation_snapshot(row["reference_generation_snapshot"]).model_input()
        elif row.get("owner_reference_snapshot"):
            data["owner_reference_indications"] = row["owner_reference_snapshot"]
        valid_ids: set[UUID] = set()
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
            catalog_price = _catalog_price_fact(snapshot)
            for item in (catalog_fact, catalog_price):
                if item is None:
                    continue
                catalog_id = UUID(str(item["id"]))
                valid_ids.add(catalog_id)
                confirmed = data["confirmed_facts"]
                assert isinstance(confirmed, list)
                if item is catalog_fact:
                    confirmed.insert(0, item)
                else:
                    confirmed.append(item)
        if not source and not valid_ids:
            return None
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
        if briefing_id is not None:
            requested = data.get("requested_format")
            if requested is None:
                # The baseline is bounded by eligible_formats above, so every
                # admitted catalog briefing resolves to a feed or story skill.
                requested = self._baseline(data).format
                data["requested_format"] = requested
                data["format_inferred"] = True
            from app.services.visual_skills import resolve_editorial_skill

            try:
                skill_id, skill_hash, instructions = resolve_editorial_skill(str(requested))
            except AuthError:
                return None
            data["editorial_skill"] = {"id": skill_id, "sha256": skill_hash, "instructions": instructions}
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
    def _safe_generated(
        draft: ProposalDraft, data: dict[str, object], valid_ids: set[UUID], *, full_piece: bool = False
    ) -> bool:
        eligible = data.get("eligible_formats")
        if isinstance(eligible, list) and (
            draft.format not in eligible or (data.get("requested_format") and draft.format != data["requested_format"])
        ):
            return False
        if len(draft.fact_ids) != 1 or draft.fact_ids[0] not in valid_ids:
            return False
        facts = data["confirmed_facts"]
        assert isinstance(facts, list)
        fact = next((item for item in facts if str(item["id"]) == str(draft.fact_ids[0])), None)
        if fact is None:
            return False
        preferences = data["preferences"]
        assert isinstance(preferences, dict)
        topics = preferences.get("avoided_topics", [])
        assert isinstance(topics, list)
        if full_piece:
            if not public_action_matches_destination(draft, preferences):
                return False
            cta_destination = preferences.get("cta_destination")
            destination = cta_destination.get("value") if isinstance(cta_destination, dict) else None
            return natural_generated_copy_matches_fact(
                draft, str(fact["statement"]), topics, destination=destination if isinstance(destination, str) else None
            )
        return generated_copy_matches_fact(draft, str(fact["statement"]), topics)

    @staticmethod
    def _ground_generated(draft: ProposalDraft, data: dict[str, object]) -> ProposalDraft:
        script = EditorialProposalService._script(draft, data, experimental=True)
        assert draft.cta is not None
        script = [
            scene.model_copy(update={"on_screen_text": draft.cta, "voiceover": draft.cta})
            if scene.role == "cta"
            else scene
            for scene in script
        ]
        return draft.model_copy(update={"script": script})

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

    async def _references_current(self, session: Any, row: Any) -> bool:
        value = row.get("reference_generation_snapshot")
        if value is None:
            # Historical proposals retain their original indication-only contract.
            return True
        try:
            snapshot = read_generation_snapshot(value)
        except AuthError:
            return False
        # The row was locked and its durable execution state was checked by run.
        # Keep the reference lock through the same submission/result commit;
        # the provider is invoked only after that transaction ends.
        await session.execute(
            text("SELECT set_config('app.tenant_id', :tenant, true), set_config('app.actor_id', :actor, true)"),
            {"tenant": str(row["tenant_id"]), "actor": str(row["actor_id"])},
        )
        return await generation_context_is_current(session, row["business_id"], snapshot)

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
            # Serialize the durable submission against a pending withdrawal;
            # the provider is called only after this transaction commits.
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 48))"),
                {"key": f"visual-consent:{row['tenant_id']}:{row['business_id']}"},
            )
            if self.settings.editorial_ai_mode == "openai" and not await service_agreement_allowed(
                session, self.settings, row["tenant_id"], row["business_id"], worker=True
            ):
                return await self._reject(session, row, "SERVICE_AGREEMENT_REQUIRED")
            generation = await session.scalar(
                text(editorial_agreement_generation_sql()),
                {"tenant": row["tenant_id"], "business": row["business_id"]},
            )
            if self.settings.editorial_ai_mode == "openai" and row["consent_generation"] != generation:
                return await self._reject(session, row, "EDITORIAL_REQUEST_CANCELLED")
            if self.settings.editorial_ai_mode == "openai" and not await self._consented(
                session, row["tenant_id"], row["business_id"]
            ):
                return await self._reject(session, row, "EDITORIAL_AI_CONSENT_REQUIRED")
            if not await self._references_current(session, row):
                return await self._reject(session, row, "REFERENCE_GENERATION_CONTEXT_CHANGED")
            inputs = await self._inputs(session, row)
            if inputs is None:
                return await self._reject(session, row, "EDITORIAL_SOURCE_UNAVAILABLE")
            data, _ = inputs
            if not data["confirmed_facts"]:
                return await self._reject(session, row, "EDITORIAL_FACTS_REQUIRED")
            if self.settings.editorial_ai_mode == "disabled":
                return await self._reject(session, row, "EDITORIAL_PROVIDER_DISABLED")
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
            key = self.settings.meta_encryption_key
            if key is None or not key.get_secret_value().strip():
                return await self._reject(session, row, "EDITORIAL_TRACE_KEY_REQUIRED")
            try:
                prepared_request = OpenAIEditorialProvider(self.settings).build_request(data)
                trace: dict[str, object] = {
                    "endpoint": "https://api.openai.com/v1/responses",
                    "client_request_id": str(proposal_id),
                    "body": prepared_request,
                }
                trace_hash, ciphertext = _encode_request_trace(key.get_secret_value(), trace)
            except (EditorialProviderError, ValueError, TypeError):
                return await self._reject(session, row, "EDITORIAL_TRACE_UNAVAILABLE")
            await agreement_worker_scope(session, row["tenant_id"])
            await session.execute(
                text("""INSERT INTO editorial_request_traces
                  (tenant_id,business_id,proposal_id,actor_id,request_hash,ciphertext)
                  VALUES(:tenant,:business,:proposal,:actor,:hash,:ciphertext)"""),
                {
                    "tenant": row["tenant_id"],
                    "business": row["business_id"],
                    "proposal": proposal_id,
                    "actor": row["actor_id"],
                    "hash": trace_hash,
                    "ciphertext": ciphertext,
                },
            )
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
            draft, input_tokens, output_tokens = await self.provider.propose(
                data, proposal_id, prepared_request=prepared_request
            )
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
            await agreement_worker_scope(session, row["tenant_id"])
            consent = await self._consented(session, row["tenant_id"], row["business_id"])
            access = await session.scalar(
                text(_access_sql()),
                {"tenant": row["tenant_id"], "live": self.settings.environment == "production"},
            )
            references_current = await self._references_current(session, row) if consent and access else False
            fresh_inputs = await self._inputs(session, row) if references_current else None
            safe = bool(
                draft is not None
                and fresh_inputs is not None
                and data.get("editorial_skill") == fresh_inputs[0].get("editorial_skill")
                and self._safe_generated(draft, fresh_inputs[0], fresh_inputs[1], full_piece=True)
            )
            if safe and draft is not None and fresh_inputs is not None:
                draft = self._ground_generated(draft, fresh_inputs[0])
                skill = fresh_inputs[0]["editorial_skill"]
                assert isinstance(skill, dict)
                draft = draft.model_copy(
                    update={"editorial_skill_id": skill["id"], "editorial_skill_sha256": skill["sha256"]}
                )
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
                {
                    "id": proposal_id,
                    "state": state,
                    "input": input_tokens,
                    "output": output_tokens,
                },
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
        # A preview's source document, script history and kit snapshot remain its
        # provenance after the proposal's creation/approval window has elapsed.
        # Keep pending attempts too until their own recovery/cleanup completes.
        await session.execute(
            text("""DELETE FROM editorial_proposals e WHERE e.expires_at<=now()
              AND NOT EXISTS(SELECT 1 FROM media_previews p WHERE p.proposal_id=e.id)""")
        )
        return len(rows)
