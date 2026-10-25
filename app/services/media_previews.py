"""Durable owner requests and fenced rendering of private static previews."""

from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from sqlalchemy import text

from app.adapters.material_media import MaterialError, MaterialStore
from app.adapters.static_preview import TEMPLATE_VERSION, PreviewRenderError, render_static_preview
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


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()


class MediaPreviewService:
    def __init__(self, settings: Settings, database: Database, store: MaterialStore | None = None) -> None:
        self.settings, self.database = settings, database
        self.store = store or MaterialStore(settings)

    async def _inputs(self, session: Any, proposal: Any) -> RenderInputs:
        if proposal["state"] != "completed" or proposal["review_state"] != "accepted" or proposal["document"] is None:
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
        if draft.format not in {"photo", "story"}:
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
        statement = fact.statement.rstrip(". ") + "."
        if statement != facts[0].on_screen_text:
            raise AuthError("PREVIEW_FACT_CHANGED", 409)
        materials = [scene for scene in draft.script if scene.role == "material"]
        if len(materials) > 1:
            raise AuthError("PREVIEW_MATERIAL_INVALID", 409)
        source_id = materials[0].source_asset_id if materials else None
        source_key = None
        source_hash = None
        if source_id is not None:
            asset = (
                (
                    await session.execute(
                        text("""SELECT object_key,sha256 FROM whatsapp_material_assets
                          WHERE id=:id AND tenant_id=:tenant AND business_id=:business AND kind='image'
                            AND mime_type IN ('image/jpeg','image/png') AND delete_requested_at IS NULL
                            AND expires_at>now()"""),
                        {"id": source_id, "tenant": proposal["tenant_id"], "business": proposal["business_id"]},
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
        render_key = _digest(
            {
                "proposal": proposal["id"],
                "document": proposal["document"],
                "context_version": proposal["context_version"],
                "name": profile["name"],
                "brand_color": profile["brand_color"],
                "source_sha256": source_hash,
                "template": TEMPLATE_VERSION,
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
        )

    async def request(self, tenant: UUID, business: UUID, actor: UUID, payload: PreviewRequest) -> PreviewRead:
        request_hash = _digest({"proposal_id": payload.proposal_id})
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
                          AND tenant_id=:tenant AND business_id=:business"""),
                        {"proposal": payload.proposal_id, "tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if proposal is None:
                raise AuthError("PROPOSAL_NOT_FOUND", 404)
            inputs = await self._inputs(session, proposal)
            row = (
                (
                    await session.execute(
                        text("""INSERT INTO media_previews
                          (id,tenant_id,business_id,proposal_id,actor_id,operation_id,request_hash,
                           render_key,template_version,context_version,source_asset_id,fact_ids,expires_at)
                          VALUES(:id,:tenant,:business,:proposal,:actor,:operation,:hash,:key,:template,
                            :version,:source,CAST(:facts AS jsonb),:expires)
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
                            "template": TEMPLATE_VERSION,
                            "version": proposal["context_version"],
                            "source": inputs.source_id,
                            "facts": json.dumps([str(inputs.fact_id)]),
                            "expires": proposal["expires_at"],
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
                          AND EXISTS(SELECT 1 FROM editorial_proposals e WHERE e.id=p.proposal_id)
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
            key = await session.scalar(
                text("""SELECT p.object_key FROM media_previews p WHERE p.id=:id AND p.tenant_id=:tenant
                  AND p.business_id=:business AND p.state='completed' AND p.expires_at>now()
                  AND EXISTS(SELECT 1 FROM editorial_proposals e WHERE e.id=p.proposal_id)
                  AND (p.source_asset_id IS NULL OR EXISTS(SELECT 1 FROM whatsapp_material_assets a
                    WHERE a.id=p.source_asset_id AND a.delete_requested_at IS NULL AND a.expires_at>now()))"""),
                {"id": preview_id, "tenant": tenant, "business": business},
            )
            if not key:
                raise AuthError("PREVIEW_NOT_READY", 404)
            return str(key)

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
                inputs = await self._inputs(session, proposal)
                if inputs.render_key != row["render_key"]:
                    raise AuthError("PREVIEW_INPUT_CHANGED", 409)
            except AuthError as exc:
                invalid_code = exc.code
        if invalid_code is not None:
            return await self._fail(preview_id, fence, invalid_code, False)
        key = f"previews/{row['tenant_id']}/{row['business_id']}/{preview_id}/{row['render_key']}.jpg"
        try:
            source = await self.store.get_image(inputs.source_key) if inputs.source_key else None
            if source is not None and hashlib.sha256(source).hexdigest() != inputs.source_sha256:
                raise MaterialError("MEDIA_CHECKSUM_MISMATCH")
            media = await asyncio.to_thread(
                render_static_preview,
                business_name=inputs.business_name,
                statement=inputs.statement,
                brand_color=inputs.brand_color,
                format=inputs.format,
                source_image=source,
            )
            await self.store.put(key, media)
        except MaterialError as exc:
            return await self._fail(preview_id, fence, exc.code, exc.retryable)
        except PreviewRenderError as exc:
            return await self._fail(preview_id, fence, exc.code, False)
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
                if current is None or (await self._inputs(session, current)).render_key != row["render_key"]:
                    raise AuthError("PREVIEW_INPUT_CHANGED", 409)
                completed = (
                    (
                        await session.execute(
                            text("""UPDATE media_previews SET state='completed',object_key=:key,sha256=:sha,
                              width=1080,height=:height,dispatch_owner=NULL,dispatch_lease_until=NULL,updated_at=now()
                              WHERE id=:id AND state='rendering' AND dispatch_fence=:fence RETURNING *"""),
                            {
                                "id": preview_id,
                                "fence": fence,
                                "key": key,
                                "sha": media.sha256,
                                "height": 1920 if inputs.format == "story" else 1350,
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
