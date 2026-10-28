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
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.session import Database
from app.schemas.editorial_proposals import ProposalDraft
from app.services.auth import AuthError
from app.services.editorial_briefings import EditorialBriefingService
from app.services.service_agreement_scope import accepted_agreement_at_sql
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
        self,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        proposal_id: UUID,
        *,
        candidate: bool = False,
        completed_preview_id: UUID | None = None,
    ) -> VisualContextSnapshot:
        async with self.database.transaction(tenant, actor) as session:
            return await self.capture_in_transaction(
                session,
                tenant,
                business,
                actor,
                proposal_id,
                candidate=candidate,
                completed_preview_id=completed_preview_id,
            )

    async def capture_in_transaction(
        self,
        session: AsyncSession,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        proposal_id: UUID,
        *,
        candidate: bool = False,
        completed_preview_id: UUID | None = None,
    ) -> VisualContextSnapshot:
        """Capture with the caller's existing owner-scoped transaction, without committing."""
        if self.settings.environment not in {"development", "testing"} or self.settings.visual_ai_mode not in {
            "openai",
            "fake",
        }:
            raise AuthError("VISUAL_AI_DISABLED", 409)
        key = self.settings.meta_encryption_key
        if key is None or not key.get_secret_value().strip():
            raise AuthError("VISUAL_CONTEXT_KEY_REQUIRED", 409)
        params = {"tenant": tenant, "business": business, "id": proposal_id}
        await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
        # Existing completed proposals keep their original permission fingerprint.
        # Only proposals captured under the contract epoch use the new authority.
        contract_at = f"""(CASE WHEN EXISTS(SELECT 1 FROM editorial_proposals contract_proposal
          WHERE contract_proposal.id=:id AND contract_proposal.tenant_id=:tenant
            AND contract_proposal.business_id=:business AND contract_proposal.consent_generation<0)
          THEN {accepted_agreement_at_sql()} END)"""
        if completed_preview_id is None:
            visual_consent = await session.scalar(
                text(f"""SELECT coalesce((SELECT accepted_at FROM visual_ai_consents WHERE tenant_id=:tenant
                  AND business_id=:business AND revoked_at IS NULL), {contract_at})"""),
                params,
            )
        else:
            # Narrow exception for viewing an already-admitted simulation which
            # finished during withdrawal. It never authorizes a new generation.
            visual_consent = await session.scalar(
                text(f"""SELECT coalesce((SELECT CASE WHEN r.preview_id IS NULL THEN c.accepted_at
                  ELSE r.consent_accepted_at END
                  FROM visual_ai_consents c LEFT JOIN visual_consent_runs r
                    ON r.tenant_id=c.tenant_id AND r.business_id=c.business_id AND r.actor_id=:actor
                    AND r.preview_id=:preview AND r.state='finished' AND r.finished_during_withdrawal
                    AND EXISTS (SELECT 1 FROM media_previews p WHERE p.id=r.preview_id
                      AND p.tenant_id=:tenant AND p.business_id=:business AND p.actor_id=:actor
                      AND p.proposal_id=:id AND p.state='completed' AND p.generation_mode='visual_fake'
                      AND p.dispatch_fence=r.fence AND p.object_key IS NOT NULL
                      AND p.sha256=r.completed_sha256)
                  WHERE c.tenant_id=:tenant AND c.business_id=:business
                    AND (c.revoked_at IS NULL OR r.preview_id IS NOT NULL)), {contract_at})"""),
                {**params, "actor": actor, "preview": completed_preview_id},
            )
        if not visual_consent:
            raise AuthError("VISUAL_AI_CONSENT_REQUIRED", 409)
        # The active grant's identity is part of the fingerprint. A withdrawal
        # followed by a new grant must not validate an old in-flight result.
        whatsapp_consent = await session.scalar(
            text(f"""SELECT coalesce((SELECT accepted_at FROM whatsapp_processing_consents WHERE tenant_id=:tenant
              AND business_id=:business AND revoked_at IS NULL), {contract_at})"""),
            params,
        )
        jev_consent = await session.scalar(
            text(f"""SELECT coalesce((SELECT accepted_at FROM intent_jev_consents WHERE tenant_id=:tenant
              AND business_id=:business AND revoked_at IS NULL), {contract_at})"""),
            params,
        )
        editorial_consent = await session.scalar(
            text(f"""SELECT coalesce((SELECT accepted_at FROM editorial_ai_consents WHERE tenant_id=:tenant
              AND business_id=:business AND revoked_at IS NULL), {contract_at})"""),
            params,
        )
        channel_link = await session.scalar(
            text("""SELECT linked_at FROM whatsapp_channel_links WHERE tenant_id=:tenant
              AND business_id=:business AND actor_id=:actor AND active"""),
            {**params, "actor": actor},
        )
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
        if source_kind not in {"text", "audio", "image"}:
            raise AuthError("VISUAL_SOURCE_NOT_NORMALIZED", 409)
        source_image_hash = None
        if source_kind == "image":
            source_image_hash = await session.scalar(
                text("""SELECT sha256 FROM whatsapp_material_assets WHERE id=:source
                  AND tenant_id=:tenant AND business_id=:business AND kind='image'
                  AND object_key IS NOT NULL AND mime_type IN ('image/png','image/jpeg')
                  AND sha256 IS NOT NULL AND delete_requested_at IS NULL
                  AND (expires_at IS NULL OR expires_at>now())"""),
                {**params, "source": source},
            )
            if not source_image_hash:
                raise AuthError("VISUAL_SOURCE_NOT_READY", 409)
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
                "source_image_hash": source_image_hash,
                "script_version": proposal["script_version"],
                "context_version": context_version,
                "document": proposal["document"],
                "kit_version": kit["version"],
                "kit_document": kit["document"],
                "logo_hash": logo_hash,
                "catalog": catalog,
                "visual_consent": visual_consent,
                "whatsapp_consent": whatsapp_consent,
                "jev_consent": jev_consent,
                "editorial_consent": editorial_consent,
                "channel_link": channel_link,
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
