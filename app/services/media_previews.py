"""Durable owner requests and fenced rendering of private image/video previews."""

from __future__ import annotations

import asyncio
import hashlib
import io
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from typing import Any, Literal
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import text

from app.adapters.material_media import FetchedMedia, MaterialError, MaterialStore
from app.adapters.static_preview import TEMPLATE_VERSION, PreviewRenderError, render_static_preview
from app.adapters.video_preview import VIDEO_DURATION_MS, VIDEO_TEMPLATE_VERSION, render_video_preview
from app.core.config import Settings
from app.db.session import Database
from app.schemas.editorial_context import ContextContent
from app.schemas.editorial_proposals import ProposalDraft
from app.schemas.media_previews import PreviewRead, PreviewRequest
from app.services.auth import AuthError
from app.services.editorial_proposals import _access_sql, _audit
from app.services.service_agreement_scope import accepted_agreement_sql, agreement_worker_scope
from app.services.whatsapp_materials import WhatsAppMaterialsService

logger = logging.getLogger("meu_braco_direito.media_previews")


@dataclass(frozen=True)
class RenderInputs:
    business_name: str
    brand_color: str
    format: str
    statement: str
    source_key: str | None
    source_sha256: str | None
    source_id: UUID | None
    fact_id: UUID
    render_key: str
    expires_at: datetime | None = None
    source_kind: str | None = None
    emphasis: Literal["balanced", "photo", "text"] = "balanced"
    intro_text: str = "Conheça nosso trabalho"
    cta_text: str = "Entre em contato para saber mais"


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()


def _visual_render_key(fingerprint: str, operation: UUID, candidate: bool) -> str:
    return _digest({"fingerprint": fingerprint, "operation": operation, "candidate": candidate, "mode": "visual_fake"})


class MediaPreviewService:
    def __init__(
        self,
        settings: Settings,
        database: Database,
        store: MaterialStore | None = None,
        owner_database: Database | None = None,
    ) -> None:
        self.settings, self.database = settings, database
        self.store = store or MaterialStore(settings)
        self.owner_database = owner_database or database

    async def _inputs(
        self,
        session: Any,
        proposal: Any,
        *,
        emphasis: Literal["balanced", "photo", "text"] = "balanced",
        parent_preview_id: UUID | None = None,
        template_version: int | None = None,
        candidate: bool = False,
    ) -> RenderInputs:
        # BL04.1 does not yet revalidate catalog/kit throughout preview and delivery.
        if proposal.get("briefing_required"):
            raise AuthError("BRIEFING_PREVIEW_NOT_READY", 409)
        if (
            proposal["state"] != "completed"
            or proposal["document"] is None
            or (proposal["review_state"] is not None if candidate else proposal["review_state"] != "accepted")
        ):
            raise AuthError("PREVIEW_SCRIPT_NOT_ACCEPTED", 409)
        if proposal["expires_at"] <= datetime.now(proposal["expires_at"].tzinfo):
            raise AuthError("PREVIEW_SCRIPT_EXPIRED", 409)
        if await session.scalar(
            text("""SELECT 1 FROM editorial_ai_consents WHERE tenant_id=:tenant AND business_id=:business
              AND withdrawal_requested_at IS NOT NULL"""),
            {"tenant": proposal["tenant_id"], "business": proposal["business_id"]},
        ):
            raise AuthError("EDITORIAL_WITHDRAWAL_PENDING", 409)
        if proposal["model"] not in (None, "baseline-v1") and not await session.scalar(
            text(f"""SELECT {accepted_agreement_sql()} OR EXISTS(SELECT 1 FROM editorial_ai_consents
              WHERE tenant_id=:tenant AND business_id=:business
                AND revoked_at IS NULL AND withdrawal_requested_at IS NULL)"""),
            {"tenant": proposal["tenant_id"], "business": proposal["business_id"]},
        ):
            raise AuthError("EDITORIAL_AI_CONSENT_REQUIRED", 409)
        if not await session.scalar(
            text(_access_sql()),
            {"tenant": proposal["tenant_id"], "live": self.settings.environment == "production"},
        ):
            raise AuthError("PLAN_REQUIRED", 403)
        draft = ProposalDraft.model_validate(proposal["document"])
        if draft.format not in {"photo", "story", "short_video"}:
            raise AuthError("PREVIEW_FORMAT_UNSUPPORTED", 409)
        facts = [scene for scene in draft.script if scene.role == "fact"]
        if len(facts) != 1 or len(facts[0].fact_ids) != 1:
            raise AuthError("PREVIEW_FACT_REQUIRED", 409)
        profile = (
            (
                await session.execute(
                    text("""SELECT b.name,b.timezone,p.brand_color,h.version
                      FROM businesses b JOIN business_profiles p ON p.tenant_id=b.tenant_id AND p.business_id=b.id
                      JOIN business_context_heads h ON h.tenant_id=b.tenant_id AND h.business_id=b.id
                      WHERE b.tenant_id=:tenant AND b.id=:business"""),
                    {"tenant": proposal["tenant_id"], "business": proposal["business_id"]},
                )
            )
            .mappings()
            .one_or_none()
        )
        if profile is None or profile["version"] != proposal["context_version"]:
            raise AuthError("PREVIEW_CONTEXT_CHANGED", 409)
        context_doc = await session.scalar(
            text("""SELECT document FROM business_context_versions WHERE tenant_id=:tenant
              AND business_id=:business AND version=:version"""),
            {
                "tenant": proposal["tenant_id"],
                "business": proposal["business_id"],
                "version": proposal["context_version"],
            },
        )
        if context_doc is None:
            raise AuthError("PREVIEW_CONTEXT_CHANGED", 409)
        context = ContextContent.model_validate(context_doc)
        today = datetime.now(ZoneInfo(profile["timezone"])).date()
        fact = next((item for item in context.facts if item.id == facts[0].fact_ids[0]), None)
        if fact is None or (fact.valid_until is not None and fact.valid_until < today):
            raise AuthError("PREVIEW_FACT_EXPIRED", 409)
        fact_expiry = (
            datetime.combine(fact.valid_until + timedelta(days=1), time.min, ZoneInfo(profile["timezone"])).astimezone(
                UTC
            )
            if fact.valid_until is not None
            else None
        )
        statement = fact.statement.rstrip(". ") + "."
        if statement != facts[0].on_screen_text:
            raise AuthError("PREVIEW_FACT_CHANGED", 409)
        materials = [scene for scene in draft.script if scene.role == "material"]
        if len(materials) > 1:
            raise AuthError("PREVIEW_MATERIAL_INVALID", 409)
        source_id = materials[0].source_asset_id if materials else None
        source_key = None
        source_hash = None
        source_kind = None
        if source_id is not None:
            asset = (
                (
                    await session.execute(
                        text("""SELECT object_key,sha256,kind FROM whatsapp_material_assets
                          WHERE id=:id AND tenant_id=:tenant AND business_id=:business
                            AND ((kind='image' AND mime_type IN ('image/jpeg','image/png'))
                              OR (:is_video AND kind='video' AND mime_type IN ('video/mp4','video/3gpp')))
                            AND delete_requested_at IS NULL
                            AND (expires_at IS NULL OR expires_at>now())"""),
                        {
                            "id": source_id,
                            "tenant": proposal["tenant_id"],
                            "business": proposal["business_id"],
                            "is_video": draft.format == "short_video",
                        },
                    )
                )
                .mappings()
                .one_or_none()
            )
            if (
                asset is None
                or not asset["object_key"]
                or not asset["sha256"]
                or source_id != proposal["source_asset_id"]
            ):
                raise AuthError("PREVIEW_MATERIAL_NOT_READY", 409)
            source_key, source_hash = asset["object_key"], asset["sha256"]
            source_kind = asset["kind"]
        render_key = _digest(
            {
                "proposal": proposal["id"],
                "document": proposal["document"],
                "script_version": proposal["script_version"],
                "context_version": proposal["context_version"],
                "name": profile["name"],
                "brand_color": profile["brand_color"],
                "source_sha256": source_hash,
                "source_kind": source_kind,
                "template": template_version
                or (VIDEO_TEMPLATE_VERSION if draft.format == "short_video" else TEMPLATE_VERSION),
                "recipe": "silent-captioned-video" if draft.format == "short_video" else "static-image",
                **({"candidate": True} if candidate else {}),
                **({"emphasis": emphasis, "parent_preview_id": parent_preview_id} if parent_preview_id else {}),
            }
        )
        return RenderInputs(
            profile["name"],
            profile["brand_color"],
            draft.format,
            statement,
            source_key,
            source_hash,
            source_id,
            fact.id,
            render_key,
            min(proposal["expires_at"], fact_expiry) if fact_expiry is not None else proposal["expires_at"],
            source_kind,
            emphasis,
            next(
                (scene.on_screen_text for scene in draft.script if scene.role == "material"), "Conheça nosso trabalho"
            ),
            next(
                (scene.on_screen_text for scene in draft.script if scene.role == "cta"),
                "Entre em contato para saber mais",
            ),
        )

    async def request(self, tenant: UUID, business: UUID, actor: UUID, payload: PreviewRequest) -> PreviewRead:
        return await self._request(tenant, business, actor, payload, candidate=False)

    async def request_candidate(
        self, tenant: UUID, business: UUID, actor: UUID, payload: PreviewRequest
    ) -> PreviewRead:
        """Internal orchestration only; the public route always calls request()."""
        return await self._request(tenant, business, actor, payload, candidate=True)

    async def _request(
        self, tenant: UUID, business: UUID, actor: UUID, payload: PreviewRequest, *, candidate: bool
    ) -> PreviewRead:
        if payload.generation_mode == "visual_fake":
            return await self._request_visual_fake(tenant, business, actor, payload, candidate=candidate)
        request_hash = _digest(
            {"proposal_id": payload.proposal_id}
            | ({"candidate": True} if candidate else {})
            | (
                {"parent_preview_id": payload.parent_preview_id, "emphasis": payload.emphasis}
                if payload.parent_preview_id
                else {}
            )
        )
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            existing = (
                (
                    await session.execute(
                        text("""SELECT * FROM media_previews WHERE tenant_id=:tenant AND business_id=:business
                          AND operation_id=:operation"""),
                        {"tenant": tenant, "business": business, "operation": payload.operation_id},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if existing is not None:
                if existing["request_hash"] != request_hash:
                    raise AuthError("PREVIEW_OPERATION_CONFLICT", 409)
                return PreviewRead.model_validate(existing)
            proposal = (
                (
                    await session.execute(
                        text("""SELECT * FROM editorial_proposals WHERE id=:proposal
                          AND tenant_id=:tenant AND business_id=:business FOR UPDATE"""),
                        {"proposal": payload.proposal_id, "tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if proposal is None:
                raise AuthError("PROPOSAL_NOT_FOUND", 404)
            revision = 1
            parent_mime: str | None = None
            if payload.parent_preview_id is not None:
                parent = (
                    (
                        await session.execute(
                            text("""SELECT * FROM media_previews WHERE id=:id AND tenant_id=:tenant
                              AND business_id=:business AND proposal_id=:proposal"""),
                            {
                                "id": payload.parent_preview_id,
                                "tenant": tenant,
                                "business": business,
                                "proposal": payload.proposal_id,
                            },
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if (
                    parent is None
                    or parent["state"] not in {"completed", "failed"}
                    or parent["mime_type"] not in {"image/jpeg", "video/mp4"}
                ):
                    raise AuthError("PREVIEW_ADJUSTMENT_UNAVAILABLE", 409)
                parent_mime = parent["mime_type"]
                latest = await session.scalar(
                    text("""SELECT id FROM media_previews WHERE tenant_id=:tenant AND business_id=:business
                      AND proposal_id=:proposal ORDER BY created_at DESC,id DESC LIMIT 1"""),
                    {"tenant": tenant, "business": business, "proposal": payload.proposal_id},
                )
                if (
                    latest != parent["id"]
                    or (parent["state"] == "completed" and parent["emphasis"] == payload.emphasis)
                    or (parent["state"] == "failed" and parent["emphasis"] != payload.emphasis)
                ):
                    raise AuthError("PREVIEW_ADJUSTMENT_CONFLICT", 409)
                if parent["revision"] >= 4:
                    raise AuthError("PREVIEW_ADJUSTMENT_LIMIT", 409)
                if (
                    parent["script_version"] != proposal["script_version"]
                    or parent["context_version"] != proposal["context_version"]
                ):
                    raise AuthError("PREVIEW_INPUT_CHANGED", 409)
                revision = parent["revision"] + 1
            inputs = await self._inputs(
                session,
                proposal,
                emphasis=payload.emphasis,
                parent_preview_id=payload.parent_preview_id,
                candidate=candidate,
            )
            if payload.parent_preview_id is not None and parent_mime != (
                "video/mp4" if inputs.format == "short_video" else "image/jpeg"
            ):
                raise AuthError("PREVIEW_ADJUSTMENT_UNAVAILABLE", 409)
            row = (
                (
                    await session.execute(
                        text("""INSERT INTO media_previews
                          (id,tenant_id,business_id,proposal_id,actor_id,operation_id,request_hash,
                           render_key,template_version,context_version,script_version,
                           source_asset_id,fact_ids,expires_at,mime_type,
                           parent_preview_id,emphasis,revision,candidate)
                          VALUES(:id,:tenant,:business,:proposal,:actor,:operation,:hash,:key,:template,
                            :version,:script_version,:source,CAST(:facts AS jsonb),:expires,:mime,
                            :parent,:emphasis,:revision,:candidate)
                          ON CONFLICT DO NOTHING RETURNING *"""),
                        {
                            "id": uuid4(),
                            "tenant": tenant,
                            "business": business,
                            "proposal": payload.proposal_id,
                            "actor": actor,
                            "operation": payload.operation_id,
                            "hash": request_hash,
                            "key": inputs.render_key,
                            "template": VIDEO_TEMPLATE_VERSION if inputs.format == "short_video" else TEMPLATE_VERSION,
                            "version": proposal["context_version"],
                            "script_version": proposal["script_version"],
                            "source": inputs.source_id,
                            "facts": json.dumps([str(inputs.fact_id)]),
                            "expires": inputs.expires_at or proposal["expires_at"],
                            "mime": "video/mp4" if inputs.format == "short_video" else "image/jpeg",
                            "parent": payload.parent_preview_id,
                            "emphasis": payload.emphasis,
                            "revision": revision,
                            "candidate": candidate,
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
                            text("""SELECT * FROM media_previews WHERE tenant_id=:tenant AND business_id=:business
                              AND (operation_id=:operation OR render_key=:key) ORDER BY
                              CASE WHEN operation_id=:operation THEN 0 ELSE 1 END LIMIT 1"""),
                            {
                                "tenant": tenant,
                                "business": business,
                                "operation": payload.operation_id,
                                "key": inputs.render_key,
                            },
                        )
                    )
                    .mappings()
                    .one()
                )
                if row["operation_id"] == payload.operation_id and row["request_hash"] != request_hash:
                    raise AuthError("PREVIEW_OPERATION_CONFLICT", 409)
            else:
                await _audit(session, row, "media.preview_requested")
            return PreviewRead.model_validate(row)

    async def _request_visual_fake(
        self, tenant: UUID, business: UUID, actor: UUID, payload: PreviewRequest, *, candidate: bool
    ) -> PreviewRead:
        """Explicitly simulated preview: no external visual provider is called."""
        from app.services.visual_consent_gate import VisualConsentGate
        from app.services.visual_context import VisualContextService
        from app.services.visual_pending_changes import VisualPendingChanges

        if self.settings.environment not in {"development", "testing"} or self.settings.visual_ai_mode != "fake":
            raise AuthError("VISUAL_FAKE_DISABLED", 409)
        from app.services.service_agreement import service_agreement_allowed

        async with self.owner_database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            if not await session.scalar(text(_access_sql()), {"tenant": tenant, "live": False}):
                raise AuthError("PLAN_REQUIRED", 403)
            if self.settings.service_agreement_required or self.settings.environment == "production":
                if not await service_agreement_allowed(session, self.settings, tenant, business):
                    raise AuthError("SERVICE_AGREEMENT_REQUIRED", 409)
        if await VisualConsentGate(self.owner_database).status(tenant, business, actor) != "active":
            raise AuthError("VISUAL_AI_CONSENT_REQUIRED", 409)
        # Queueing validates only metadata; image bytes are read by the admitted
        # worker, so a queued item never begins consuming photos on its own.
        context = await VisualContextService(self.settings, self.owner_database).capture(
            tenant, business, actor, payload.proposal_id, candidate=candidate
        )
        render_key = _visual_render_key(context.fingerprint, payload.operation_id, candidate)
        request_hash = _digest({"proposal": payload.proposal_id, "mode": "visual_fake", "candidate": candidate})
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            # Keep explicit authorization and serialize acceptance with withdrawal.
            gate = VisualConsentGate(self.owner_database)
            await gate._lock(session, tenant, business, actor)
            if await gate._state(session, tenant, business) != "active":
                raise AuthError("VISUAL_AI_CONSENT_REQUIRED", 409)
            if await VisualPendingChanges.has_pending_in_session(session, tenant, business):
                raise AuthError("VISUAL_CHANGE_PENDING", 409)
            current = await VisualContextService(self.settings, self.owner_database).capture_in_transaction(
                session, tenant, business, actor, payload.proposal_id, candidate=candidate
            )
            if current.fingerprint != context.fingerprint:
                raise AuthError("PREVIEW_INPUT_CHANGED", 409)
            existing = (
                (
                    await session.execute(
                        text("""SELECT * FROM media_previews
              WHERE tenant_id=:tenant AND business_id=:business AND operation_id=:operation"""),
                        {"tenant": tenant, "business": business, "operation": payload.operation_id},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if existing is not None:
                if existing["request_hash"] != request_hash or existing["render_key"] != render_key:
                    raise AuthError("PREVIEW_OPERATION_CONFLICT", 409)
                return PreviewRead.model_validate(existing)
            proposal = (
                (
                    await session.execute(
                        text("""SELECT * FROM editorial_proposals WHERE id=:id
              AND tenant_id=:tenant AND business_id=:business"""),
                        {"tenant": tenant, "business": business, "id": payload.proposal_id},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if proposal is None:
                raise AuthError("PROPOSAL_NOT_FOUND", 404)
            row = (
                (
                    await session.execute(
                        text("""INSERT INTO media_previews
              (id,tenant_id,business_id,proposal_id,actor_id,operation_id,request_hash,render_key,
               template_version,context_version,script_version,source_asset_id,fact_ids,expires_at,mime_type,
               parent_preview_id,emphasis,revision,candidate,generation_mode,visual_fingerprint)
              VALUES(:id,:tenant,:business,:proposal,:actor,:operation,:hash,:key,1,:version,:script,
                :source,'[]'::jsonb,:expires,'image/jpeg',NULL,'balanced',1,:candidate,'visual_fake',:fingerprint)
              ON CONFLICT DO NOTHING RETURNING *"""),
                        {
                            "id": uuid4(),
                            "tenant": tenant,
                            "business": business,
                            "proposal": payload.proposal_id,
                            "actor": actor,
                            "operation": payload.operation_id,
                            "hash": request_hash,
                            "key": render_key,
                            "version": context.context_version,
                            "script": context.script_version,
                            "source": context.source_asset_id,
                            "expires": proposal["expires_at"],
                            "candidate": candidate,
                            "fingerprint": context.fingerprint,
                        },
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                # A concurrent request can have inserted this operation after our
                # first lookup. Return the same job only if its payload and all
                # visual inputs are identical; otherwise the operation conflicts.
                row = (
                    (
                        await session.execute(
                            text("""SELECT * FROM media_previews WHERE tenant_id=:tenant
                              AND business_id=:business AND operation_id=:operation"""),
                            {"tenant": tenant, "business": business, "operation": payload.operation_id},
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if row is None or row["request_hash"] != request_hash or row["render_key"] != render_key:
                    raise AuthError("PREVIEW_OPERATION_CONFLICT", 409)
                return PreviewRead.model_validate(row)
            await _audit(session, row, "media.preview_requested")
            return PreviewRead.model_validate(row)

    async def list(self, tenant: UUID, business: UUID, actor: UUID) -> list[PreviewRead]:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            rows = (
                (
                    await session.execute(
                        text("""SELECT p.* FROM media_previews p WHERE p.tenant_id=:tenant AND p.business_id=:business
                          AND (p.state='completed' OR p.expires_at>now()) AND p.state<>'purging'
                          AND EXISTS(SELECT 1 FROM editorial_proposals e WHERE e.id=p.proposal_id
                            AND (p.state='completed' OR (e.script_version=p.script_version
                            AND ((p.candidate AND e.review_state IS NULL)
                              OR (NOT p.candidate AND e.review_state='accepted')))))
                          AND (p.state='completed' OR p.generation_mode='visual_fake'
                            OR EXISTS(SELECT 1 FROM business_context_heads h
                            WHERE h.tenant_id=p.tenant_id AND h.business_id=p.business_id
                              AND h.version=p.context_version))
                          AND (p.generation_mode<>'visual_fake' OR p.state NOT IN ('pending','rendering')
                            OR NOT EXISTS(SELECT 1 FROM visual_consent_gates g WHERE g.tenant_id=p.tenant_id
                              AND g.business_id=p.business_id AND g.state<>'active')
                            OR EXISTS(SELECT 1 FROM visual_consent_runs r WHERE r.tenant_id=p.tenant_id
                              AND r.business_id=p.business_id AND r.preview_id=p.id AND r.actor_id=:actor
                              AND r.state='in_flight'))
                          AND (p.state='completed' OR p.source_asset_id IS NULL
                            OR EXISTS(SELECT 1 FROM whatsapp_material_assets a
                            WHERE a.id=p.source_asset_id AND a.delete_requested_at IS NULL
                              AND (a.expires_at IS NULL OR a.expires_at>now())))
                          ORDER BY p.created_at DESC,p.id DESC LIMIT 30"""),
                        {"tenant": tenant, "business": business, "actor": actor},
                    )
                )
                .mappings()
                .all()
            )
        visible = []
        for row in rows:
            created_before_change = False
            if row["generation_mode"] == "visual_fake":
                try:
                    created_before_change = await self._validate_visual(row, actor, view_only=True)
                except AuthError:
                    continue
            visible.append(PreviewRead.model_validate({**row, "created_before_change": created_before_change}))
        return visible

    async def _validate_visual(self, row: Any, actor: UUID, *, view_only: bool = False) -> bool:
        from app.services.visual_context import VisualContextService

        if row["generation_mode"] != "visual_fake" or self.settings.visual_ai_mode != "fake":
            raise AuthError("VISUAL_FAKE_DISABLED", 409)
        try:
            current = await VisualContextService(self.settings, self.owner_database).capture(
                row["tenant_id"],
                row["business_id"],
                actor,
                row["proposal_id"],
                candidate=row["candidate"],
                completed_preview_id=row["id"] if view_only else None,
            )
            if current.fingerprint == row["visual_fingerprint"]:
                if view_only:
                    async with self.owner_database.transaction(row["tenant_id"], actor) as session:
                        before_withdrawal = await session.scalar(
                            text("""SELECT 1 FROM visual_change_completed_previews v
                              JOIN editorial_ai_consents c ON c.tenant_id=v.tenant_id AND c.business_id=v.business_id
                              WHERE v.tenant_id=:tenant AND v.business_id=:business AND v.actor_id=:actor
                                AND v.preview_id=:preview AND v.editorial_consent_accepted_at=c.accepted_at
                                AND c.revoked_at IS NOT NULL"""),
                            {
                                "tenant": row["tenant_id"],
                                "business": row["business_id"],
                                "actor": actor,
                                "preview": row["id"],
                            },
                        )
                    return bool(before_withdrawal)
                return False
        except AuthError as exc:
            if not view_only or exc.code not in {
                "VISUAL_AI_CONSENT_REQUIRED",
                "VISUAL_BRIEFING_CHANGED",
                "VISUAL_KIT_CHANGED",
                "VISUAL_LOGO_CHANGED",
                "VISUAL_CONTEXT_CHANGED",
                "PREVIEW_SCRIPT_EXPIRED",
                "PREVIEW_SCRIPT_NOT_ACCEPTED",
            }:
                raise
        if not view_only or row["state"] != "completed" or not row["sha256"] or not row["object_key"]:
            raise AuthError("PREVIEW_INPUT_CHANGED", 409)
        async with self.owner_database.transaction(row["tenant_id"], actor) as session:
            await WhatsAppMaterialsService._require_owner(session, row["tenant_id"], row["business_id"], actor)
            proof = await session.scalar(
                text(f"""SELECT 1 FROM visual_change_completed_previews v
                  JOIN visual_consent_runs r ON r.tenant_id=v.tenant_id AND r.business_id=v.business_id
                    AND r.preview_id=v.preview_id AND r.operation_id=v.operation_id
                    AND r.actor_id=v.actor_id AND r.fence=v.fence AND r.state='finished'
                  LEFT JOIN visual_ai_consents c ON c.tenant_id=v.tenant_id AND c.business_id=v.business_id
                  WHERE v.tenant_id=:tenant AND v.business_id=:business AND v.actor_id=:actor
                    AND v.preview_id=:preview AND v.fence=:fence AND v.sha256=:sha
                    AND v.visual_fingerprint=:fingerprint
                    AND ({accepted_agreement_sql()} OR (c.revoked_at IS NULL AND c.accepted_at=v.consent_accepted_at)
                      OR (r.finished_during_withdrawal AND r.completed_sha256=v.sha256))"""),
                {
                    "tenant": row["tenant_id"],
                    "business": row["business_id"],
                    "actor": actor,
                    "preview": row["id"],
                    "fence": row["dispatch_fence"],
                    "sha": row["sha256"],
                    "fingerprint": row["visual_fingerprint"],
                },
            )
            created_before_change = bool(proof)
            if not proof:
                # A retained result is historical evidence. Its durable run,
                # fence and original contract authorize review, never a new effect.
                proof = await session.scalar(
                    text(f"""SELECT 1 FROM visual_consent_runs r
                      LEFT JOIN visual_ai_consents c ON c.tenant_id=r.tenant_id AND c.business_id=r.business_id
                      WHERE r.tenant_id=:tenant AND r.business_id=:business AND r.preview_id=:preview
                        AND r.actor_id=:original_actor AND r.fence=:fence AND r.state='finished'
                        AND NOT EXISTS(SELECT 1 FROM visual_change_completed_previews v
                          WHERE v.tenant_id=r.tenant_id AND v.business_id=r.business_id AND v.preview_id=r.preview_id)
                        AND ({accepted_agreement_sql()} OR
                          (c.revoked_at IS NULL AND c.accepted_at=r.consent_accepted_at))"""),
                    {
                        "tenant": row["tenant_id"],
                        "business": row["business_id"],
                        "preview": row["id"],
                        "original_actor": row["actor_id"],
                        "fence": row["dispatch_fence"],
                    },
                )
                if proof:
                    created_before_change = bool(
                        await session.scalar(
                            text("""SELECT EXISTS(SELECT 1 FROM business_visual_pending_changes c
                          JOIN media_previews p ON p.tenant_id=c.tenant_id AND p.business_id=c.business_id
                          WHERE p.id=:preview AND c.state='completed' AND c.requested_at>=p.created_at)"""),
                            {"preview": row["id"]},
                        )
                    )
            if proof:
                # Current identity and source permissions still apply. Plan
                # expiry and the historical script's deadline do not erase it.
                from app.services.editorial_briefings import EditorialBriefingService

                source = (
                    (
                        await session.execute(
                            text("""SELECT b.source_asset_id, EXISTS(
                      SELECT 1 FROM editorial_intent_usage u WHERE u.tenant_id=b.tenant_id
                        AND u.operation_id=b.operation_id AND u.provider='typesafe') AS used_jev
                      FROM editorial_proposals e JOIN editorial_briefings b
                        ON b.id=e.briefing_id AND b.tenant_id=e.tenant_id AND b.business_id=e.business_id
                      WHERE e.id=:proposal AND e.tenant_id=:tenant AND e.business_id=:business
                        AND e.state='completed'"""),
                            {
                                "proposal": row["proposal_id"],
                                "tenant": row["tenant_id"],
                                "business": row["business_id"],
                                "version": row["script_version"],
                                "candidate": row["candidate"],
                            },
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if source is None or source["source_asset_id"] != row["source_asset_id"]:
                    raise AuthError("PREVIEW_INPUT_CHANGED", 409)
                await EditorialBriefingService(self.settings, self.owner_database)._source(
                    session,
                    row["tenant_id"],
                    row["business_id"],
                    actor,
                    source["source_asset_id"],
                    jev=source["used_jev"],
                    review_preview=row["id"],
                )
        if not proof:
            raise AuthError("PREVIEW_INPUT_CHANGED", 409)
        return created_before_change

    async def file_key(
        self, tenant: UUID, business: UUID, actor: UUID, preview_id: UUID, *, review: bool = False
    ) -> str:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            row = (
                (
                    await session.execute(
                        text("""SELECT p.* FROM media_previews p WHERE p.id=:id AND p.tenant_id=:tenant
                  AND p.business_id=:business AND p.state='completed'
                  AND (:review OR p.expires_at>now())
                  AND EXISTS(SELECT 1 FROM editorial_proposals e WHERE e.id=p.proposal_id)
                  AND (:review OR p.source_asset_id IS NULL OR EXISTS(SELECT 1 FROM whatsapp_material_assets a
                    WHERE a.id=p.source_asset_id AND a.delete_requested_at IS NULL
                      AND (a.expires_at IS NULL OR a.expires_at>now())))"""),
                        {"id": preview_id, "tenant": tenant, "business": business, "review": review},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None or not row["object_key"]:
                raise AuthError("PREVIEW_NOT_READY", 404)
            if review and row["generation_mode"] == "local":
                return str(row["object_key"])
            if row["generation_mode"] == "visual_fake":
                try:
                    await self._validate_visual(row, actor, view_only=review)
                except AuthError as exc:
                    raise AuthError("PREVIEW_NOT_READY", 404) from exc
                return str(row["object_key"])
            proposal = (
                (
                    await session.execute(
                        text("SELECT * FROM editorial_proposals WHERE id=:id"), {"id": row["proposal_id"]}
                    )
                )
                .mappings()
                .one_or_none()
            )
            try:
                if (
                    proposal is None
                    or (
                        await self._inputs(
                            session,
                            proposal,
                            emphasis=row["emphasis"],
                            parent_preview_id=row["parent_preview_id"],
                            template_version=row["template_version"],
                            candidate=row["candidate"],
                        )
                    ).render_key
                    != row["render_key"]
                ):
                    raise AuthError("PREVIEW_NOT_READY", 404)
            except AuthError as exc:
                raise AuthError("PREVIEW_NOT_READY", 404) from exc
            return str(row["object_key"])

    async def _fail(self, preview_id: UUID, fence: int, code: str, retryable: bool) -> str:
        async with self.database.sessions() as session, session.begin():
            row = (
                (
                    await session.execute(
                        text("""UPDATE media_previews SET
                          state=CASE WHEN :retryable AND attempts<3 THEN 'pending' ELSE 'failed' END,
                          error_code=:code,dispatch_owner=NULL,dispatch_lease_until=NULL,updated_at=now()
                          WHERE id=:id AND state='rendering' AND dispatch_fence=:fence RETURNING *"""),
                        {"id": preview_id, "fence": fence, "code": code, "retryable": retryable},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                return "skipped"
            if row["state"] == "failed":
                await _audit(session, row, "media.preview_failed")
            return str(row["state"])

    async def render(self, preview_id: UUID, fence: int) -> str:
        async with self.database.sessions() as session, session.begin():
            mode = await session.scalar(
                text("""SELECT generation_mode FROM media_previews
              WHERE id=:id AND state='rendering' AND dispatch_fence=:fence"""),
                {"id": preview_id, "fence": fence},
            )
        if mode == "visual_fake":
            return await self._render_visual_fake(preview_id, fence)
        return await self._render_local(preview_id, fence)

    async def _render_visual_fake(self, preview_id: UUID, fence: int) -> str:
        """Exercise the visual lifecycle with a clearly simulated image, never an external call."""
        from app.adapters.brand_overlay import BrandOverlayError
        from app.services.editorial_consent_scope import VisualRunScope, admitted_visual_run
        from app.services.visual_admission import VisualAdmissionChecks
        from app.services.visual_attempts import VisualAttemptService
        from app.services.visual_brand_finish import VisualBrandFinishService
        from app.services.visual_consent_gate import VisualConsentGate
        from app.services.visual_context import VisualContextService
        from app.services.visual_cost_ledger import VisualCostError, VisualCostLedger

        if self.settings.environment not in {"development", "testing"} or self.settings.visual_ai_mode != "fake":
            return await self._fail(preview_id, fence, "VISUAL_FAKE_DISABLED", False)
        async with self.database.sessions() as session, session.begin():
            row = (
                (
                    await session.execute(
                        text("""SELECT * FROM media_previews WHERE id=:id AND state='rendering'
              AND dispatch_fence=:fence AND generation_mode='visual_fake'"""),
                        {"id": preview_id, "fence": fence},
                    )
                )
                .mappings()
                .one_or_none()
            )
        if row is None:
            return "skipped"
        brand_service = VisualBrandFinishService(self.settings, self.owner_database, self.store)
        operation = uuid5(NAMESPACE_URL, f"visual-preview:{preview_id}")
        gate = VisualConsentGate(self.owner_database)
        admitted = False
        terminal = False
        completed = False
        reservation = None
        upload_started = False
        consent_scope = None
        key = f"previews/{row['tenant_id']}/{row['business_id']}/{preview_id}/attempt-{fence}/{row['render_key']}.jpg"
        try:
            from app.services.service_agreement import service_agreement_allowed

            if self.settings.service_agreement_required or self.settings.environment == "production":
                async with self.owner_database.transaction(row["tenant_id"], row["actor_id"]) as session:
                    await WhatsAppMaterialsService._require_owner(
                        session, row["tenant_id"], row["business_id"], row["actor_id"]
                    )
                    if not await service_agreement_allowed(
                        session, self.settings, row["tenant_id"], row["business_id"]
                    ):
                        raise AuthError("SERVICE_AGREEMENT_REQUIRED", 409)
            admitted = await gate.admit(
                row["tenant_id"],
                row["business_id"],
                row["actor_id"],
                preview_id,
                operation,
                fence,
                admission=VisualAdmissionChecks(
                    self.settings, row["proposal_id"], row["visual_fingerprint"], row["candidate"]
                ),
            )
            if not admitted:
                return await self._fail(preview_id, fence, "VISUAL_OUTCOME_UNCERTAIN", False)
            consent_scope = admitted_visual_run(
                VisualRunScope(row["tenant_id"], row["business_id"], row["actor_id"], operation, fence)
            )
            consent_scope.__enter__()
            # A job left in the queue across withdrawal and re-grant must not
            # begin using images from the new consent generation.
            metadata = await VisualContextService(self.settings, self.owner_database).capture(
                row["tenant_id"],
                row["business_id"],
                row["actor_id"],
                row["proposal_id"],
                candidate=row["candidate"],
            )
            if metadata.fingerprint != row["visual_fingerprint"]:
                raise AuthError("PREVIEW_INPUT_CHANGED", 409)
            brand = await brand_service.prepare(
                row["tenant_id"],
                row["business_id"],
                row["actor_id"],
                row["proposal_id"],
                row["operation_id"],
                candidate=row["candidate"],
            )
            prepared = brand.request
            if (
                _visual_render_key(prepared.context.fingerprint, row["operation_id"], row["candidate"])
                != row["render_key"]
                or prepared.context.fingerprint != row["visual_fingerprint"]
            ):
                raise AuthError("PREVIEW_INPUT_CHANGED", 409)
            attempt = await VisualAttemptService(self.settings, self.database).reserve(
                row["tenant_id"],
                row["business_id"],
                row["actor_id"],
                preview_id,
                fence,
                operation,
                "fake",
                prepared.request.model,
                prepared.request_hash,
                1,
            )
            if not attempt.created:
                return await self._fail(preview_id, fence, "VISUAL_OUTCOME_UNCERTAIN", False)
            reservation = attempt.reservation.id
            width, height = (int(value) for value in prepared.request.size.split("x"))
            # No provider is invoked: this neutral scene makes it possible to
            # exercise the same validated brand finishing without implying that
            # the visual itself was generated by AI.
            scene_image = Image.new("RGB", (width, height), "#e8e6f8")
            scene_bytes = io.BytesIO()
            scene_image.save(scene_bytes, format="PNG")
            scene = scene_bytes.getvalue()
            finished_media = await brand_service.finish(
                row["actor_id"],
                brand,
                FetchedMedia(data=scene, mime_type="image/png", sha256=hashlib.sha256(scene).hexdigest()),
                candidate=row["candidate"],
            )
            with Image.open(io.BytesIO(finished_media.data)) as rendered:
                image = rendered.convert("RGB")
                draw = ImageDraw.Draw(image)
                band_height = max(50, height // 24)
                draw.rectangle((0, 0, width, band_height), fill="#272044")
                draw.text(
                    (width // 40, band_height // 5),
                    "SIMULACAO - NAO PUBLICAR",
                    fill="white",
                    font=ImageFont.load_default(size=max(18, width // 44)),
                )
                output = io.BytesIO()
                image.save(output, format="JPEG", quality=90)
            data = output.getvalue()
            media = FetchedMedia(data=data, mime_type="image/jpeg", sha256=hashlib.sha256(data).hexdigest())
            upload_started = True
            await self.store.put(key, media)
            current = await brand_service.prepare(
                row["tenant_id"],
                row["business_id"],
                row["actor_id"],
                row["proposal_id"],
                row["operation_id"],
                candidate=row["candidate"],
            )
            if current.request.request_hash != prepared.request_hash:
                raise AuthError("PREVIEW_INPUT_CHANGED", 409)
            async with self.database.sessions() as session, session.begin():
                finished = (
                    (
                        await session.execute(
                            text("""UPDATE media_previews SET state='completed',object_key=:key,
                  sha256=:sha,width=:width,height=:height,dispatch_owner=NULL,dispatch_lease_until=NULL,updated_at=now()
                  WHERE id=:id AND state='rendering' AND dispatch_fence=:fence RETURNING *"""),
                            {
                                "id": preview_id,
                                "fence": fence,
                                "key": key,
                                "sha": media.sha256,
                                "width": width,
                                "height": height,
                            },
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if finished is not None:
                    await _audit(session, finished, "media.preview_completed")
                    terminal = True
                    completed = True
                    return "completed"
            await self._discard_visual_object(key)
            terminal = True
            return "skipped"
        except (AuthError, BrandOverlayError, MaterialError, VisualCostError) as exc:
            if upload_started:
                await self._discard_visual_object(key)
            terminal = True
            return await self._fail(preview_id, fence, getattr(exc, "code", str(exc)), False)
        finally:
            if consent_scope is not None:
                consent_scope.__exit__(None, None, None)
            try:
                if reservation is not None:
                    await VisualCostLedger(self.settings, self.database).finish(
                        row["tenant_id"], row["actor_id"], reservation, actual_usd_micros=0
                    )
            finally:
                # This path uses only the fake renderer. Cancellation, crash or a
                # previous uncertain reservation leaves admission unresolved.
                if admitted and terminal:
                    await gate.finish(
                        row["tenant_id"],
                        row["business_id"],
                        row["actor_id"],
                        operation,
                        fence,
                        preview_completed=completed,
                    )

    async def _discard_visual_object(self, key: str) -> None:
        try:
            await self.store.delete(key)
        except Exception:
            # Cleanup failure must not turn a terminal, already reserved attempt into a retry.
            logger.warning("media.visual_cleanup_failed")

    async def _render_local(self, preview_id: UUID, fence: int) -> str:
        invalid_code: str | None = None
        async with self.database.sessions() as session, session.begin():
            row = (
                (
                    await session.execute(
                        text("""SELECT * FROM media_previews WHERE id=:id AND state='rendering'
                          AND dispatch_fence=:fence"""),
                        {"id": preview_id, "fence": fence},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                return "skipped"
            proposal = (
                (
                    await session.execute(
                        text("SELECT * FROM editorial_proposals WHERE id=:id"), {"id": row["proposal_id"]}
                    )
                )
                .mappings()
                .one_or_none()
            )
            try:
                if proposal is None:
                    raise AuthError("PROPOSAL_NOT_FOUND", 404)
                await agreement_worker_scope(session, row["tenant_id"])
                inputs = await self._inputs(
                    session,
                    proposal,
                    emphasis=row["emphasis"],
                    parent_preview_id=row["parent_preview_id"],
                    candidate=row["candidate"],
                )
                expected_template = VIDEO_TEMPLATE_VERSION if inputs.format == "short_video" else TEMPLATE_VERSION
                if row["template_version"] != expected_template or inputs.render_key != row["render_key"]:
                    raise AuthError("PREVIEW_INPUT_CHANGED", 409)
            except AuthError as exc:
                invalid_code = exc.code
        if invalid_code is not None:
            return await self._fail(preview_id, fence, invalid_code, False)
        is_video = inputs.format == "short_video"
        extension = "mp4" if is_video else "jpg"
        # Isolate each fenced attempt so a delayed worker can delete only its
        # own upload, never the object committed by a newer worker.
        key = (
            f"previews/{row['tenant_id']}/{row['business_id']}/{preview_id}/"
            f"attempt-{fence}/{row['render_key']}.{extension}"
        )
        try:
            source = None
            if inputs.source_key is not None:
                source = (
                    await self.store.get_video(inputs.source_key)
                    if inputs.source_kind == "video"
                    else await self.store.get_image(inputs.source_key)
                )
            if source is not None and hashlib.sha256(source).hexdigest() != inputs.source_sha256:
                raise MaterialError("MEDIA_CHECKSUM_MISMATCH")
            if is_video:
                media = await render_video_preview(
                    business_name=inputs.business_name,
                    statement=inputs.statement,
                    brand_color=inputs.brand_color,
                    source_image=source if inputs.source_kind != "video" else None,
                    source_video=source if inputs.source_kind == "video" else None,
                    intro_text=inputs.intro_text,
                    cta_text=inputs.cta_text,
                    emphasis=inputs.emphasis,
                )
            else:
                media = await asyncio.to_thread(
                    render_static_preview,
                    business_name=inputs.business_name,
                    statement=inputs.statement,
                    brand_color=inputs.brand_color,
                    format=inputs.format,
                    source_image=source,
                    emphasis=inputs.emphasis,
                )
            await self.store.put(key, media)
        except MaterialError as exc:
            return await self._fail(preview_id, fence, exc.code, exc.retryable)
        except PreviewRenderError as exc:
            return await self._fail(preview_id, fence, exc.code, exc.retryable)
        try:
            async with self.database.sessions() as session, session.begin():
                await agreement_worker_scope(session, row["tenant_id"])
                current = (
                    (
                        await session.execute(
                            text("SELECT * FROM editorial_proposals WHERE id=:id"), {"id": row["proposal_id"]}
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if (
                    current is None
                    or (
                        await self._inputs(
                            session,
                            current,
                            emphasis=row["emphasis"],
                            parent_preview_id=row["parent_preview_id"],
                            candidate=row["candidate"],
                        )
                    ).render_key
                    != row["render_key"]
                ):
                    raise AuthError("PREVIEW_INPUT_CHANGED", 409)
                completed = (
                    (
                        await session.execute(
                            text("""UPDATE media_previews SET state='completed',object_key=:key,sha256=:sha,
                              width=1080,height=:height,duration_ms=:duration,
                              dispatch_owner=NULL,dispatch_lease_until=NULL,updated_at=now()
                              WHERE id=:id AND state='rendering' AND dispatch_fence=:fence RETURNING *"""),
                            {
                                "id": preview_id,
                                "fence": fence,
                                "key": key,
                                "sha": media.sha256,
                                "height": 1920 if inputs.format in {"story", "short_video"} else 1350,
                                "duration": VIDEO_DURATION_MS if is_video else None,
                            },
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if completed is not None:
                    await _audit(session, completed, "media.preview_completed")
                    return "completed"
        except AuthError as exc:
            await self._fail(preview_id, fence, exc.code, False)
        await self.store.delete(key)
        return "skipped"
