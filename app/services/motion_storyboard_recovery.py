"""Explicit reconciliation of a fully received capture, never a provider/render retry."""

from typing import Any
from uuid import UUID, uuid5

from sqlalchemy import text

from app.adapters.motion_html_renderer import RenderedFrame, RenderedMotion
from app.schemas.motion_production import HTMLMotionComposition
from app.services.auth import AuthError
from app.services.content_pieces import _event
from app.services.motion_context import digest
from app.services.motion_generation import staged_generation_enabled
from app.services.motion_storyboard_frames import storyboard_moments, storyboard_upload_name
from app.services.motion_storyboards import MotionStoryboards


class MotionStoryboardRecovery:
    def __init__(self, boards: MotionStoryboards):
        self.boards, self.requests = boards, boards.requests

    async def snapshot(
        self, session: Any, tenant: UUID, business: UUID, actor: UUID, request: UUID
    ) -> tuple[dict[str, Any], dict[str, Any] | None, dict[UUID, dict[str, Any]]]:
        await self.requests.gate._lock(session, tenant, business, actor)
        row = dict(await self.requests.row(session, tenant, business, request))
        if row["actor_id"] != actor:
            raise AuthError("MOTION_OWNER_CHANGED", 409)
        board = (
            (
                await session.execute(
                    text("""SELECT * FROM motion_storyboards
                WHERE tenant_id=:tenant AND business_id=:business AND request_id=:id"""),
                    {"tenant": tenant, "business": business, "id": request},
                )
            )
            .mappings()
            .one_or_none()
        )
        if board is not None:
            return row, dict(board), {}
        if row["state"] != "failed" or row["failure_code"] != "MOTION_EXECUTION_FAILED" or row["piece_id"]:
            raise AuthError("MOTION_STORYBOARD_RECOVERY_INELIGIBLE", 409)
        await self.requests._admission(session, tenant, business)
        await self.requests.current(session, row)
        if await session.scalar(
            text("SELECT EXISTS(SELECT 1 FROM motion_render_versions WHERE request_id=:id AND tenant_id=:tenant)"),
            {"id": request, "tenant": tenant},
        ):
            raise AuthError("MOTION_STORYBOARD_RECOVERY_INELIGIBLE", 409)
        effects = (
            (
                await session.execute(
                    text("""SELECT operation_id,kind,state,request_hash,request_ciphertext,response_ciphertext,
                reserved_usd_micros,estimated_usd_micros FROM motion_effects
                WHERE tenant_id=:tenant AND business_id=:business AND request_id=:id ORDER BY operation_id"""),
                    {"tenant": tenant, "business": business, "id": request},
                )
            )
            .mappings()
            .all()
        )
        if (
            any(e["state"] != "received" or e["kind"] not in {"generate", "upload", "render"} for e in effects)
            or any(e["reserved_usd_micros"] and e["estimated_usd_micros"] is None for e in effects)
            or sum(max(e["reserved_usd_micros"], e["estimated_usd_micros"] or 0) for e in effects)
            > row["budget_usd_micros"]
        ):
            raise AuthError("MOTION_STORYBOARD_RECOVERY_INELIGIBLE", 409)
        return row, None, {e["operation_id"]: dict(e) for e in effects}

    async def evidence(
        self, row: dict[str, Any], effects: dict[UUID, dict[str, Any]], expected_sha: str
    ) -> tuple[dict[str, Any], str]:
        """Only backend-sealed, received receipts; all storage IO is outside SQL locks."""
        version = uuid5(row["operation_id"], "storyboard:0")
        generation = uuid5(row["operation_id"], "generate:0")
        if {k for k, e in effects.items() if e["kind"] == "render"} != {version}:
            raise AuthError("MOTION_STORYBOARD_RECOVERY_INELIGIBLE", 409)

        async def receipt(operation: UUID, kind: str, field: str = "response_ciphertext") -> dict[str, Any]:
            effect = effects.get(operation)
            if effect is None or effect["kind"] != kind or not effect[field]:
                raise AuthError("MOTION_STORYBOARD_RECOVERY_EVIDENCE_MISSING", 409)
            return await self.boards.payloads.open(row, effect[field])

        # Recovery is deliberately limited to captures whose large board payload
        # was durably uploaded. It never reconstructs missing/unreceived outputs.
        effect = effects.get(uuid5(version, "payload:board"))
        if effect is None or effect["kind"] != "upload" or not effect["response_ciphertext"]:
            raise AuthError("MOTION_STORYBOARD_RECOVERY_EVIDENCE_MISSING", 409)
        ciphertext = effect["response_ciphertext"]
        payload = await self.boards.payloads.open(row, ciphertext)
        if digest(payload) != expected_sha or payload["source_fingerprint"] != row["source_fingerprint"]:
            raise AuthError("MOTION_STORYBOARD_BYTES_CHANGED", 409)
        composition = HTMLMotionComposition.model_validate(payload["composition"])
        generations = {generation}
        if staged_generation_enabled(payload["context"]):
            planning = uuid5(row["operation_id"], "generate:plan:0")
            generations.add(planning)
            planned = await receipt(planning, "generate")
            actual = composition.model_dump(mode="json", exclude={"html", "scene_init"})
            actual.setdefault("illustrations", [])
            if planned.get("construction_plan") != actual:
                raise AuthError("MOTION_STORYBOARD_BYTES_CHANGED", 409)
        if {k for k, e in effects.items() if e["kind"] == "generate"} != generations:
            raise AuthError("MOTION_STORYBOARD_RECOVERY_INELIGIBLE", 409)
        if composition.illustrations or payload["illustrations"] or not payload["context"]["request"]["storyboard"]:
            raise AuthError("MOTION_STORYBOARD_RECOVERY_INELIGIBLE", 409)
        signed = await receipt(version, "render", "request_ciphertext")
        generated = await receipt(generation, "generate")
        rendered = await receipt(version, "render")
        moments = storyboard_moments(composition, payload["context"])
        if (
            signed.get("purpose") != "storyboard"
            or signed["composition"] != payload["composition"]
            or generated["composition"] != payload["composition"]
            or digest(signed["moments"]) != digest(moments)
            or len(payload["frames"]) != len(moments)
        ):
            raise AuthError("MOTION_STORYBOARD_BYTES_CHANGED", 409)
        frames = []
        for moment, manifest in zip(moments, payload["frames"], strict=True):
            upload_name = storyboard_upload_name(moment)
            upload = uuid5(version, upload_name)
            key = f"motion/{row['tenant_id']}/{row['business_id']}/{row['id']}/storyboard/{upload}.png"
            if (
                any(manifest[k] != v for k, v in moment.items())
                or manifest["object_key"] != key
                or await receipt(upload, "upload") != manifest
            ):
                raise AuthError("MOTION_STORYBOARD_BYTES_CHANGED", 409)
            data = await self.boards.read_png(manifest)
            frames.append(RenderedFrame(manifest["at_ms"], data, manifest["sha256"], moment["frame_index"]))
        if rendered["frames"] != [{"ms": f.ms, "sha256": f.sha256} for f in frames]:
            raise AuthError("MOTION_STORYBOARD_BYTES_CHANGED", 409)
        self.boards.validate_frames(RenderedMotion(b"", "", tuple(frames), rendered["diagnostics"]), moments)
        return payload, ciphertext

    async def reconcile(
        self, tenant: UUID, business: UUID, actor: UUID, request: UUID, expected_sha: str
    ) -> dict[str, Any]:
        async with self.requests.database.transaction(tenant, actor) as session:
            row, existing, effects = await self.snapshot(session, tenant, business, actor, request)
        if existing is not None:
            if existing["content_sha256"] != expected_sha:
                raise AuthError("MOTION_STORYBOARD_BYTES_CHANGED", 409)
            return {"state": existing["state"], "reconciled": False}
        _, ciphertext = await self.evidence(row, effects, expected_sha)
        version = uuid5(row["operation_id"], "storyboard:0")
        async with self.requests.database.transaction(tenant, actor) as session:
            current, existing, latest = await self.snapshot(session, tenant, business, actor, request)
            if existing is not None:
                if existing["content_sha256"] != expected_sha:
                    raise AuthError("MOTION_STORYBOARD_BYTES_CHANGED", 409)
                return {"state": existing["state"], "reconciled": False}
            if digest(row) != digest(current) or digest(list(effects.values())) != digest(list(latest.values())):
                raise AuthError("MOTION_EXECUTION_FENCED", 409)
            params = {"tenant": tenant, "business": business, "id": request}
            await session.execute(
                text("""UPDATE motion_requests SET state='running',failure_code=NULL,finished_at=NULL
                WHERE tenant_id=:tenant AND business_id=:business AND id=:id"""),
                params,
            )
            await session.execute(
                text("""INSERT INTO motion_storyboards
                (tenant_id,business_id,request_id,version_id,content_sha256,payload_ciphertext,state)
                VALUES(:tenant,:business,:id,:version,:sha,:payload,'awaiting_approval')"""),
                {**params, "version": version, "sha": expected_sha, "payload": ciphertext},
            )
            for action in ("motion.storyboard_reconciled", "motion.storyboard_ready"):
                await _event(session, tenant, business, actor, row["operation_id"], action)
        return {"state": "awaiting_approval", "reconciled": True}
