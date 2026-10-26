"""Durable owner requests and fenced rendering of private image/video previews."""

from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from typing import Any, Literal
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import text

from app.adapters.material_media import MaterialError, MaterialStore
from app.adapters.static_preview import TEMPLATE_VERSION, PreviewRenderError, render_static_preview
from app.adapters.video_preview import VIDEO_DURATION_MS, VIDEO_TEMPLATE_VERSION, render_video_preview
from app.core.config import Settings
from app.db.session import Database
from app.schemas.editorial_context import ContextContent
from app.schemas.editorial_proposals import ProposalDraft
from app.schemas.media_previews import PreviewRead, PreviewRequest
from app.services.auth import AuthError
from app.services.editorial_proposals import _access_sql, _audit
from app.services.whatsapp_materials import WhatsAppMaterialsService


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


class MediaPreviewService:
    def __init__(self, settings: Settings, database: Database, store: MaterialStore | None = None) -> None:
        self.settings, self.database = settings, database
        self.store = store or MaterialStore(settings)

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
        if (
            proposal["state"] != "completed"
            or proposal["document"] is None
            or (proposal["review_state"] is not None if candidate else proposal["review_state"] != "accepted")
        ):
            raise AuthError("PREVIEW_SCRIPT_NOT_ACCEPTED", 409)
        if proposal["expires_at"] <= datetime.now(proposal["expires_at"].tzinfo):
            raise AuthError("PREVIEW_SCRIPT_EXPIRED", 409)
        if proposal["model"] not in (None, "baseline-v1") and not await session.scalar(
            text("""SELECT 1 FROM editorial_ai_consents WHERE tenant_id=:tenant
              AND business_id=:business AND revoked_at IS NULL"""),
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
                            AND expires_at>now()"""),
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

    async def list(self, tenant: UUID, business: UUID, actor: UUID) -> list[PreviewRead]:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            rows = (
                (
                    await session.execute(
                        text("""SELECT p.* FROM media_previews p WHERE p.tenant_id=:tenant AND p.business_id=:business
                          AND p.expires_at>now() AND p.state<>'purging'
                          AND EXISTS(SELECT 1 FROM editorial_proposals e WHERE e.id=p.proposal_id
                            AND e.script_version=p.script_version
                            AND ((p.candidate AND e.review_state IS NULL)
                              OR (NOT p.candidate AND e.review_state='accepted')))
                          AND EXISTS(SELECT 1 FROM business_context_heads h WHERE h.tenant_id=p.tenant_id
                            AND h.business_id=p.business_id AND h.version=p.context_version)
                          AND (p.source_asset_id IS NULL OR EXISTS(SELECT 1 FROM whatsapp_material_assets a
                            WHERE a.id=p.source_asset_id AND a.delete_requested_at IS NULL AND a.expires_at>now()))
                          ORDER BY p.created_at DESC,p.id DESC LIMIT 30"""),
                        {"tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .all()
            )
            return [PreviewRead.model_validate(row) for row in rows]

    async def file_key(self, tenant: UUID, business: UUID, actor: UUID, preview_id: UUID) -> str:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            row = (
                (
                    await session.execute(
                        text("""SELECT p.* FROM media_previews p WHERE p.id=:id AND p.tenant_id=:tenant
                  AND p.business_id=:business AND p.state='completed' AND p.expires_at>now()
                  AND EXISTS(SELECT 1 FROM editorial_proposals e WHERE e.id=p.proposal_id)
                  AND (p.source_asset_id IS NULL OR EXISTS(SELECT 1 FROM whatsapp_material_assets a
                    WHERE a.id=p.source_asset_id AND a.delete_requested_at IS NULL AND a.expires_at>now()))"""),
                        {"id": preview_id, "tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None or not row["object_key"]:
                raise AuthError("PREVIEW_NOT_READY", 404)
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
        key = f"previews/{row['tenant_id']}/{row['business_id']}/{preview_id}/{row['render_key']}.{extension}"
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
