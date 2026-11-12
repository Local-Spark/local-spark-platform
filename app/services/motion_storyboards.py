"""Durable board review; only owner approval can enqueue the existing Temporal path."""

import base64
import hashlib
import html
from dataclasses import replace
from typing import Any
from uuid import UUID, uuid5

from sqlalchemy import text

from app.adapters.material_media import FetchedMedia, MaterialStore
from app.adapters.motion_html_renderer import RenderAsset, RenderBundle, RenderedMotion
from app.adapters.motion_inputs import PreparedMotionInput
from app.adapters.visual_ai import VisualResult
from app.schemas.motion_production import HTMLMotionComposition
from app.schemas.motion_storyboards import StoryboardDecision, StoryboardRead
from app.services.auth import AuthError
from app.services.content_pieces import _event
from app.services.motion_context import digest
from app.services.motion_effects import MotionEffects
from app.services.motion_elements import elements_hash
from app.services.motion_illustrations import verified_preview
from app.services.motion_movement import movement_hash
from app.services.motion_payloads import MotionPayloads
from app.services.motion_plan import validate_motion_plan
from app.services.motion_protocols import MotionRenderer
from app.services.motion_requests import MotionRequestService
from app.services.motion_storyboard_frames import StoryboardMoment, storyboard_moments, storyboard_upload_name
from app.services.motion_temporal import evidence_manifest
from app.services.visual_pending_changes import VisualPendingChanges
from app.services.visual_pending_scripts import apply_pending_script_changes
from app.services.whatsapp_materials import WhatsAppMaterialsService
from app.workflows.contracts import BusinessEvent


class MotionStoryboards:
    def __init__(self, requests: MotionRequestService, store: MaterialStore):
        self.requests, self.store = requests, store
        self.payloads = MotionPayloads(requests.context, store)

    async def capture(
        self,
        row: dict[str, Any],
        token: UUID,
        prepared: PreparedMotionInput,
        composition: HTMLMotionComposition,
        renderer: MotionRenderer,
        effects: MotionEffects,
        *,
        capture_id: UUID | None = None,
    ) -> None:
        moments = storyboard_moments(composition, prepared.context)
        assert composition.motion_plan is not None
        validate_motion_plan(
            composition,
            prepared.context,
            duration_ms=prepared.duration_ms,
            asset_ids={asset.id for asset in prepared.assets},
        )
        if composition.audio.model_dump(mode="json") != prepared.audio:
            raise AuthError("MOTION_ORIGINAL_AUDIO_CHANGED", 409)
        operation = capture_id or uuid5(row["operation_id"], "storyboard:0")
        bundle = RenderBundle(
            composition.html,
            composition.scene_init,
            prepared.assets,
            prepared.audio,
            720,
            1280,
            30,
            prepared.duration_ms,
            sample_times_ms=tuple(int(m["requested_ms"]) for m in moments),
            movement_runtime_sha256=movement_hash(prepared.context),
            element_runtime_sha256=elements_hash(prepared.context),
            frames_only=True,
        )
        signed = {
            "purpose": "storyboard",
            "composition": composition.model_dump(mode="json"),
            "moments": moments,
            "assets": [{"id": a.id, "sha256": a.sha256} for a in prepared.assets],
            "movement_runtime_sha256": bundle.movement_runtime_sha256,
            "element_runtime_sha256": bundle.element_runtime_sha256,
        }
        await effects.claim(row, token, operation, "render", signed)
        rendered = await renderer.render(bundle, operation_id=operation)
        self.validate_frames(rendered, moments)
        await effects.received(
            row,
            token,
            operation,
            {
                "diagnostics": rendered.diagnostics,
                "frames": [{"ms": f.ms, "sha256": f.sha256} for f in rendered.evidence],
            },
        )
        if getattr(self.store, "single_attempt_put", False) is not True:
            raise AuthError("MOTION_STORAGE_SINGLE_ATTEMPT_REQUIRED", 409)
        frames = []
        for moment, frame in zip(moments, rendered.evidence, strict=True):
            upload_name = storyboard_upload_name(moment)
            upload = uuid5(operation, upload_name)
            key = f"motion/{row['tenant_id']}/{row['business_id']}/{row['id']}/storyboard/{upload}.png"
            manifest = {
                **moment,
                "at_ms": frame.ms,
                "sha256": frame.sha256,
                "object_key": key,
                "size_bytes": len(frame.png),
            }
            await effects.claim(row, token, upload, "upload", manifest)
            await self.store.put(key, FetchedMedia(frame.png, "image/png", frame.sha256))
            await self.read_png(manifest)
            await effects.received(row, token, upload, manifest)
            frames.append(manifest)
        illustrated = {item.asset_id for item in composition.illustrations}
        art = []
        for asset in prepared.assets:
            if asset.id in illustrated:
                art_operation = uuid5(row["operation_id"], "illustration:" + asset.id)
                art.append(
                    {
                        "asset_id": asset.id,
                        "sha256": asset.sha256,
                        "size_bytes": len(asset.data),
                        "object_key": (
                            f"motion/{row['tenant_id']}/{row['business_id']}/{row['id']}/"
                            f"illustrations/{art_operation}.png"
                        ),
                    }
                )
        payload = {
            "composition": composition.model_dump(mode="json"),
            "context": prepared.context,
            "frames": frames,
            "illustrations": art,
            "source_fingerprint": row["source_fingerprint"],
            **(
                {
                    "baseline_evidence": [
                        {"ms": f.ms, "sha256": f.sha256, "png": base64.b64encode(f.png).decode()}
                        for f in prepared.baseline_frames
                    ]
                }
                if prepared.baseline_frames
                else {}
            ),
            **(
                {
                    "asset_hashes": [{"id": a.id, "sha256": a.sha256} for a in prepared.assets],
                    "runtime_hashes": [bundle.movement_runtime_sha256, bundle.element_runtime_sha256],
                    "temporal_preview": evidence_manifest(
                        composition,
                        rendered.evidence,
                        "current",
                        prepared.context["creative_contract"]["temporal_review"],
                    ),
                    "omitted_scene_cards": [
                        scene.id
                        for scene in composition.motion_plan.scenes
                        if scene.keyframe_ms is not None
                        and scene.keyframe_ms * 30 // 1000 not in {moment["frame_index"] for moment in moments}
                    ],
                }
                if any("event_id" in moment for moment in moments)
                else {}
            ),
        }
        sha = digest(payload)
        ciphertext = await effects.persist_payload(row, token, operation, "board", payload)
        async with self.requests.database.transaction(row["tenant_id"], row["actor_id"]) as session:
            await self.requests.locked_running(session, row, token)
            await session.execute(
                text("""INSERT INTO motion_storyboards
              (tenant_id,business_id,request_id,version_id,content_sha256,payload_ciphertext,state)
              VALUES(:tenant,:business,:id,:version,:sha,:payload,'awaiting_approval')"""),
                {
                    "tenant": row["tenant_id"],
                    "business": row["business_id"],
                    "id": row["id"],
                    "version": operation,
                    "sha": sha,
                    "payload": ciphertext,
                },
            )
            await _event(
                session,
                row["tenant_id"],
                row["business_id"],
                row["actor_id"],
                row["operation_id"],
                "motion.storyboard_ready",
            )

    @staticmethod
    def validate_frames(rendered: RenderedMotion, moments: tuple[StoryboardMoment, ...]) -> None:
        if (
            rendered.mp4
            or rendered.diagnostics.get("evidence_source") != "browser_keyframes"
            or len(rendered.evidence) != len(moments)
        ):
            raise AuthError("MOTION_STORYBOARD_FRAMES_INVALID", 409)
        total = 0
        for frame, moment in zip(rendered.evidence, moments, strict=True):
            total += len(frame.png)
            if (
                frame.frame_index != moment["frame_index"]
                or frame.ms != round(frame.frame_index * 1000 / 30)
                or not frame.png.startswith(b"\x89PNG\r\n\x1a\n")
                or not 8 <= len(frame.png) <= 8 * 1024 * 1024
                or hashlib.sha256(frame.png).hexdigest() != frame.sha256
                or total > 32 * 1024 * 1024
            ):
                raise AuthError("MOTION_STORYBOARD_FRAMES_INVALID", 409)

    @staticmethod
    async def board(session: Any, tenant: UUID, business: UUID, request_id: UUID) -> Any:
        row = (
            (
                await session.execute(
                    text("""SELECT * FROM motion_storyboards
          WHERE tenant_id=:tenant AND business_id=:business AND request_id=:id FOR UPDATE"""),
                    {"tenant": tenant, "business": business, "id": request_id},
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise AuthError("MOTION_STORYBOARD_NOT_FOUND", 404)
        return row

    async def read_png(self, manifest: dict[str, Any]) -> bytes:
        data = await self.store.get_image(manifest["object_key"])
        if len(data) != manifest["size_bytes"] or hashlib.sha256(data).hexdigest() != manifest["sha256"]:
            raise AuthError("MOTION_STORYBOARD_BYTES_CHANGED", 409)
        return data

    async def load(
        self, tenant: UUID, business: UUID, actor: UUID, request_id: UUID
    ) -> tuple[Any, Any, dict[str, Any]]:
        async with self.requests.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            row = dict(await self.requests.row(session, tenant, business, request_id))
            board = dict(await self.board(session, tenant, business, request_id))
        payload = await self.payloads.open(row, board["payload_ciphertext"])
        if digest(payload) != board["content_sha256"]:
            raise AuthError("MOTION_STORYBOARD_BYTES_CHANGED", 409)
        return row, board, payload

    @staticmethod
    def present(board: Any, payload: dict[str, Any]) -> StoryboardRead:
        return StoryboardRead.model_validate(
            {
                "version_id": board["version_id"],
                "content_sha256": board["content_sha256"],
                "state": board["state"],
                "frames": [
                    {key: f[key] for key in ("scene_id", "message", "at_ms", "sha256")} for f in payload["frames"]
                ],
            }
        )

    async def gallery(self, tenant: UUID, business: UUID, actor: UUID, request_id: UUID) -> str:
        _, board, payload = await self.load(tenant, business, actor, request_id)
        labels = {
            "awaiting_approval": "Aguardando sua avaliação",
            "approved": "Composição aprovada",
            "rejected": "Composição não aprovada",
            "rendering": "Produção do vídeo iniciada",
        }
        cards: list[str] = []
        for frame in payload["frames"]:
            png = await self.read_png(frame)
            cards.append(
                '<figure><img alt="Quadro da cena" src="data:image/png;base64,' + base64.b64encode(png).decode() + '">'
                "<figcaption>"
                + html.escape(str(frame["message"]))
                + " · "
                + str(frame["at_ms"] / 1000)
                + " s"
                + (" · " + html.escape(str(frame["event_id"])) if "event_id" in frame else "")
                + "</figcaption></figure>"
            )
        preview = payload.get("temporal_preview")
        baseline_cards = []
        for frame in payload.get("baseline_evidence", []):
            png = base64.b64decode(frame["png"], validate=True)
            if hashlib.sha256(png).hexdigest() != frame["sha256"] or not png.startswith(b"\x89PNG\r\n\x1a\n"):
                raise AuthError("MOTION_EVOLUTION_EVIDENCE_INVALID", 409)
            baseline_cards.append(
                '<figure><img alt="Peça de referência" src="data:image/png;base64,'
                + base64.b64encode(png).decode()
                + '"><figcaption>Base · '
                + html.escape(str(frame["ms"] / 1000))
                + " s</figcaption></figure>"
            )
        comparison = (
            "<section><h2>Peça de referência</h2><p>Compare a mesma ação nas duas versões. "
            "Os instantes podem ser diferentes. Estes quadros não comprovam movimento ou som.</p><main>"
            + "".join(baseline_cards)
            + "</main></section><h2>Proposta atual</h2>"
            if baseline_cards
            else ""
        )
        coverage = (
            "<p>Prévia amostrada: "
            + str(preview["omitted_events"])
            + " eventos e "
            + str(preview["omitted_transitions"])
            + " passagens não selecionados; "
            + str(preview["incomplete_events"])
            + " sequências incompletas. "
            + str(len(payload.get("omitted_scene_cards", [])))
            + " quadros principais de cena omitidos. "
            + "Cenas sem janela: "
            + html.escape(", ".join(preview["uncovered_scene_ids"]) or "nenhuma")
            + ". "
            "Quadros não demonstram movimento contínuo nem áudio.</p>"
            if preview
            else ""
        )
        return (
            '<!doctype html><html lang="pt-BR"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width">'
            "<title>Composição das cenas</title><style>"
            "body{font:18px system-ui;background:#151515;color:#eee;margin:24px}"
            "main{display:flex;gap:24px;flex-wrap:wrap}figure{margin:0;width:min(360px,100%)}img{width:100%}"
            "figcaption{padding:12px 0}code{overflow-wrap:anywhere}</style><h1>Composição das cenas</h1>"
            "<p>Confira leitura, imagens, identidade e composição. Movimento e áudio serão avaliados no vídeo.</p>"
            + coverage
            + comparison
            + "<p>"
            + html.escape(labels[str(board["state"])])
            + '</p><main data-version="'
            + str(board["version_id"])
            + '" data-content-sha="'
            + str(board["content_sha256"])
            + '">'
            + "".join(cards)
            + "</main></html>"
        )

    async def decide(
        self, tenant: UUID, business: UUID, actor: UUID, request_id: UUID, body: StoryboardDecision
    ) -> dict[str, str]:
        fingerprint = digest(body.model_dump(mode="json"))
        async with self.requests.database.transaction(tenant, actor) as session:
            await self.requests.gate._lock(session, tenant, business, actor)
            row = await self.requests.row(session, tenant, business, request_id)
            board = await self.board(session, tenant, business, request_id)
            if row["actor_id"] != actor:
                raise AuthError("MOTION_OWNER_CHANGED", 409)
            if board["decision_operation_id"] == body.operation_id:
                if board["decision_hash"] != fingerprint:
                    raise AuthError("MOTION_OPERATION_CONFLICT", 409)
                return {"state": board["state"]}
            if (
                board["state"] != "awaiting_approval"
                or board["version_id"] != body.version_id
                or board["content_sha256"] != body.content_sha256
            ):
                raise AuthError("MOTION_STORYBOARD_VERSION_CONFLICT", 409)
            if row["state"] != "running":
                raise AuthError("MOTION_EXECUTION_FENCED", 409)
            if body.decision == "approve":
                await self.requests._admission(session, tenant, business)
                await self.requests.current(session, row)
            state = "approved" if body.decision == "approve" else "rejected"
            await session.execute(
                text("""UPDATE motion_storyboards SET state=:state,decision_operation_id=:operation,
              decision_hash=:hash,feedback_ciphertext=:feedback,decided_at=clock_timestamp()
              WHERE tenant_id=:tenant AND business_id=:business AND request_id=:id"""),
                {
                    "tenant": tenant,
                    "business": business,
                    "id": request_id,
                    "state": state,
                    "operation": body.operation_id,
                    "hash": fingerprint,
                    "feedback": self.requests.context.seal({"feedback": body.feedback}),
                },
            )
            await _event(session, tenant, business, actor, body.operation_id, "motion.storyboard_decided")
            if body.decision == "approve":
                await _event(session, tenant, business, actor, row["operation_id"], "motion.storyboard_approved")
            else:
                await session.execute(
                    text("""UPDATE motion_requests SET state='failed',
                  failure_code='MOTION_STORYBOARD_REJECTED',finished_at=clock_timestamp()
                  WHERE tenant_id=:tenant AND business_id=:business AND id=:id"""),
                    {"tenant": tenant, "business": business, "id": request_id},
                )
                await _event(session, tenant, business, actor, row["operation_id"], "motion.failed")
                gate = self.requests.gate
                await gate.finish_withdrawal_if_idle(
                    session, tenant, business, actor, await gate._state(session, tenant, business)
                )
                await VisualPendingChanges.apply_pending_in_session(session, tenant, business)
        if body.decision == "reject":
            await apply_pending_script_changes(self.requests.settings, self.requests.database, tenant, business, actor)
        return {"state": state}

    async def begin_resume(self, event: BusinessEvent) -> tuple[dict[str, Any], UUID, dict[str, Any]] | None:
        tenant, business, actor, operation = map(
            UUID, (event.tenant_id, event.business_id, event.actor_id, event.operation_id)
        )
        request_id = uuid5(operation, f"motion-request:{tenant}:{business}")
        async with self.requests.database.transaction(tenant, actor) as session:
            await self.requests.gate._lock(session, tenant, business, actor)
            row = dict(await self.requests.row(session, tenant, business, request_id))
            board = dict(await self.board(session, tenant, business, request_id))
            valid = await session.scalar(
                text("""SELECT 1 FROM outbox_events WHERE tenant_id=:tenant AND id=:event
              AND event_type='motion.storyboard_approved' AND payload->>'business_id'=:business
              AND payload->>'actor_id'=:actor AND payload->>'operation_id'=:operation"""),
                {
                    "tenant": tenant,
                    "event": UUID(event.event_id),
                    "business": str(business),
                    "actor": str(actor),
                    "operation": str(operation),
                },
            )
            if (
                UUID(event.event_id) != uuid5(operation, "motion.storyboard_approved")
                or not valid
                or row["actor_id"] != actor
            ):
                raise AuthError("MOTION_EVENT_MISMATCH", 409)
            if board["state"] != "approved" or row["state"] != "running":
                return None
            # Fence duplicate relay/activity deliveries before reading files or executing a render.
            await session.execute(
                text("""UPDATE motion_storyboards SET state='rendering'
              WHERE tenant_id=:tenant AND business_id=:business AND request_id=:id"""),
                {"tenant": tenant, "business": business, "id": request_id},
            )
        return row, row["execution_token"], board

    async def restore(
        self, row: dict[str, Any], board: dict[str, Any], prepared: PreparedMotionInput
    ) -> tuple[PreparedMotionInput, HTMLMotionComposition]:
        payload = await self.payloads.open(row, board["payload_ciphertext"])
        if digest(payload) != board["content_sha256"] or payload["source_fingerprint"] != row["source_fingerprint"]:
            raise AuthError("MOTION_STORYBOARD_BYTES_CHANGED", 409)
        if "asset_hashes" in payload:
            expected = payload["asset_hashes"]
            current = {asset.id: hashlib.sha256(asset.data).hexdigest() for asset in prepared.assets}
            for art in payload["illustrations"]:
                current.setdefault(art["asset_id"], art["sha256"])
            if (
                {item["id"]: item["sha256"] for item in expected} != current
                or payload["runtime_hashes"] != [movement_hash(prepared.context), elements_hash(prepared.context)]
                or payload["context"].get("request", {}).get("scene_direction")
                != prepared.context.get("request", {}).get("scene_direction")
            ):
                raise AuthError("MOTION_STORYBOARD_BYTES_CHANGED", 409)
        composition = HTMLMotionComposition.model_validate(payload["composition"])
        assets, previews = list(prepared.assets), list(prepared.asset_previews)
        for art in payload["illustrations"]:
            data = await self.read_png(art)
            preview = verified_preview(VisualResult(data, "image/png", art["sha256"], 1024, 1024, None, None))
            assets.append(RenderAsset(art["asset_id"], "image/png", data, art["sha256"]))
            previews.append((art["asset_id"], preview))
        return replace(
            prepared, context=payload["context"], assets=tuple(assets), asset_previews=tuple(previews)
        ), composition
