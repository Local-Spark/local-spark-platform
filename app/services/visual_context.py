"""Capture owner-scoped visual inputs; this does not authorize or perform generation.

The capture is a point-in-time record, not a reservation. The caller must capture
again and compare it immediately before any external effect and verify object bytes.
"""

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import text

from app.core.config import Settings
from app.db.session import Database
from app.schemas.editorial_proposals import ProposalDraft
from app.services.auth import AuthError
from app.services.editorial_briefings import EditorialBriefingService
from app.services.whatsapp_materials import WhatsAppMaterialsService


def _fingerprint(key: str, value: object) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":")).encode()
    return hmac.new(key.encode(), payload, hashlib.sha256).hexdigest()


@dataclass(frozen=True)
class VisualContextSnapshot:
    tenant_id: UUID
    business_id: UUID
    proposal_id: UUID
    briefing_id: UUID
    source_asset_id: UUID
    format: str
    script_version: int
    context_version: int
    brand_kit_version: int
    fingerprint: str


class VisualContextService:
    """Capture only IDs and a keyed fingerprint, never media or raw customer text."""

    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings, self.database = settings, database

    async def capture(
        self, tenant: UUID, business: UUID, actor: UUID, proposal_id: UUID, *, candidate: bool = False
    ) -> VisualContextSnapshot:
        if self.settings.environment not in {"development", "testing"} or self.settings.visual_ai_mode != "openai":
            raise AuthError("VISUAL_AI_DISABLED", 409)
        key = self.settings.meta_encryption_key
        if key is None or not key.get_secret_value().strip():
            raise AuthError("VISUAL_CONTEXT_KEY_REQUIRED", 409)
        params = {"tenant": tenant, "business": business, "id": proposal_id}
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            if not await session.scalar(
                text("""SELECT 1 FROM visual_ai_consents WHERE tenant_id=:tenant
                  AND business_id=:business AND revoked_at IS NULL"""),
                params,
            ):
                raise AuthError("VISUAL_AI_CONSENT_REQUIRED", 409)
            proposal = (
                (
                    await session.execute(
                        text("""SELECT * FROM editorial_proposals WHERE id=:id
                  AND tenant_id=:tenant AND business_id=:business"""),
                        params,
                    )
                )
                .mappings()
                .one_or_none()
            )
            if proposal is None:
                raise AuthError("PROPOSAL_NOT_FOUND", 404)
            if (
                proposal["state"] != "completed"
                or proposal["document"] is None
                or (proposal["review_state"] is not None if candidate else proposal["review_state"] != "accepted")
            ):
                raise AuthError("PREVIEW_SCRIPT_NOT_ACCEPTED", 409)
            if proposal["expires_at"] <= datetime.now(UTC):
                raise AuthError("PREVIEW_SCRIPT_EXPIRED", 409)
            if not proposal["briefing_required"] or proposal["briefing_id"] is None:
                raise AuthError("VISUAL_BRIEFING_REQUIRED", 409)
            draft = ProposalDraft.model_validate(proposal["document"])
            if draft.format not in {"photo", "story"}:
                raise AuthError("VISUAL_FORMAT_UNSUPPORTED", 409)
            status, catalog = await EditorialBriefingService(self.settings, self.database).read_valid(
                session, tenant, business, actor, proposal["briefing_id"]
            )
            if status != "prepared" or catalog is None:
                raise AuthError("VISUAL_BRIEFING_CHANGED", 409)
            source = await session.scalar(
                text("""SELECT source_asset_id FROM editorial_briefings
              WHERE id=:briefing AND tenant_id=:tenant AND business_id=:business"""),
                {**params, "briefing": proposal["briefing_id"]},
            )
            if source is None or source != proposal["source_asset_id"]:
                raise AuthError("VISUAL_SOURCE_CHANGED", 409)
            source_kind = await session.scalar(
                text("""SELECT kind FROM whatsapp_material_assets WHERE id=:source
              AND tenant_id=:tenant AND business_id=:business"""),
                {**params, "source": source},
            )
            if source_kind not in {"text", "audio"}:
                raise AuthError("VISUAL_SOURCE_NOT_NORMALIZED", 409)
            kit = (
                (
                    await session.execute(
                        text("""SELECT v.version,v.document FROM business_brand_kit_heads h
                  JOIN business_brand_kit_versions v ON v.tenant_id=h.tenant_id AND v.business_id=h.business_id
                    AND v.version=h.confirmed_version
                  WHERE h.tenant_id=:tenant AND h.business_id=:business"""),
                        params,
                    )
                )
                .mappings()
                .one_or_none()
            )
            if (
                kit is None
                or kit["version"] != proposal["brand_kit_version"]
                or kit["document"] != proposal["brand_kit_document"]
            ):
                raise AuthError("VISUAL_KIT_CHANGED", 409)
            logo_id = kit["document"].get("overrides", {}).get("logo_asset_id")
            logo_hash = None
            if logo_id:
                logo_hash = await session.scalar(
                    text("""SELECT sha256 FROM business_brand_kit_logos
                  WHERE id=:logo AND tenant_id=:tenant AND business_id=:business AND state='ready'
                    AND rights_scope='business_brand_confirmed' AND mime_type='image/png'"""),
                    {**params, "logo": UUID(str(logo_id))},
                )
                if not logo_hash:
                    raise AuthError("VISUAL_LOGO_CHANGED", 409)
            context_version = (
                await session.scalar(
                    text("""SELECT version FROM business_context_heads
              WHERE tenant_id=:tenant AND business_id=:business"""),
                    params,
                )
                or 0
            )
            if context_version != proposal["context_version"]:
                raise AuthError("VISUAL_CONTEXT_CHANGED", 409)
            # These are server-side documents verified in the same owner-scoped transaction.
            # They are fingerprinted, not exported to logs or a provider.
            digest = _fingerprint(
                key.get_secret_value(),
                {
                    "tenant": tenant,
                    "business": business,
                    "proposal": proposal_id,
                    "briefing": proposal["briefing_id"],
                    "source": source,
                    "source_kind": source_kind,
                    "script_version": proposal["script_version"],
                    "context_version": context_version,
                    "document": proposal["document"],
                    "kit_version": kit["version"],
                    "kit_document": kit["document"],
                    "logo_hash": logo_hash,
                    "catalog": catalog,
                },
            )
            return VisualContextSnapshot(
                tenant,
                business,
                proposal_id,
                proposal["briefing_id"],
                source,
                draft.format,
                proposal["script_version"],
                context_version,
                kit["version"],
                digest,
            )
