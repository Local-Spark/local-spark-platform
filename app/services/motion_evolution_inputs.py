"""Resolve a captured historical baseline outside SQL locks; never execute its code."""

import base64
import hashlib
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from app.adapters.material_media import MaterialStore
from app.adapters.motion_html_renderer import RenderAsset, RenderedFrame
from app.adapters.visual_ai import VisualResult
from app.schemas.motion_production import HTMLMotionComposition
from app.services.auth import AuthError
from app.services.motion_evolution import sha
from app.services.motion_illustrations import verified_preview
from app.services.motion_payloads import MotionPayloads
from app.services.motion_temporal import POLICY_V3, sample_times

if TYPE_CHECKING:
    from app.adapters.motion_inputs import PreparedMotionInput
    from app.services.motion_context import MotionContext


async def load_evolution(
    prepared: "PreparedMotionInput", captured: dict[str, Any], context: "MotionContext", store: MaterialStore
) -> "PreparedMotionInput":
    base = HTMLMotionComposition.model_validate(captured["composition"])
    if (
        sha(base.model_dump(mode="json")) != captured["composition_sha256"]
        or prepared.context["source"]["sha256"] != captured["source_sha256"]
        or prepared.context["kit"] != captured["kit"]
        or base.audio.model_dump(mode="json") != prepared.audio
    ):
        raise AuthError("MOTION_EVOLUTION_BASELINE_CHANGED", 409)
    evidence = await MotionPayloads(context, store).open(captured["row"], captured["evidence_ciphertext"])
    frames = []
    for raw in evidence.get("frames", []):
        data = base64.b64decode(raw["png"], validate=True)
        if (
            hashlib.sha256(data).hexdigest() != raw["sha256"]
            or not data.startswith(b"\x89PNG\r\n\x1a\n")
            or not 0 <= raw["ms"] < prepared.duration_ms
            or len(data) > 4 * 1024 * 1024
        ):
            raise AuthError("MOTION_EVOLUTION_EVIDENCE_INVALID", 409)
        frames.append(RenderedFrame(raw["ms"], data, raw["sha256"]))
    if not 2 <= len(frames) <= 20 or len({f.ms for f in frames}) != len(frames):
        raise AuthError("MOTION_EVOLUTION_EVIDENCE_REQUIRED", 409)
    if "video" in captured:
        from app.adapters.motion_inputs import baseline_video_frames

        video = captured["video"]
        data = await store.get_video(video["object_key"])
        if (
            len(data) != video["size_bytes"]
            or not 0 < len(data) <= 50 * 1024 * 1024
            or hashlib.sha256(data).hexdigest() != video["sha256"]
        ):
            raise AuthError("MOTION_EVOLUTION_VIDEO_CHANGED", 409)
        frames = list(
            await baseline_video_frames(data, sample_times(base, {"creative_contract": {"temporal_review": POLICY_V3}}))
        )
    if captured["version"] == "motion-evolution-v2" and not {
        ms for function in captured["selection"]["functions"] for ms in function["evidence_at_ms"]
    } <= {f.ms for f in frames}:
        raise AuthError("MOTION_QUALITY_FUNCTION_EVIDENCE_INVALID", 409)
    assets, previews = list(prepared.assets), list(prepared.asset_previews)
    materials = list(prepared.context.get("available_materials", []))
    for item in captured["materials"]:
        data = await store.get_image(item["object_key"])
        if len(data) != item["size_bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise AuthError("MOTION_EVOLUTION_MATERIAL_CHANGED", 409)
        asset_id = "assets/reused-" + item["sha256"][:16] + ".png"
        preview = verified_preview(VisualResult(data, "image/png", item["sha256"], 1024, 1024, None, None))
        assets.append(RenderAsset(asset_id, "image/png", data, item["sha256"]))
        previews.append((asset_id, preview))
        materials.append(
            {
                "asset_id": asset_id,
                "sha256": item["sha256"],
                "role": "reused_illustration",
                "baseline_asset_id": item["asset_id"],
                "identity_rule": "Arte conceitual reutilizada da base, não fotografia real do negócio.",
            }
        )
    public = {key: captured[key] for key in ("version", "selection", "composition", "composition_sha256", "rules")}
    return replace(
        prepared,
        assets=tuple(assets),
        asset_previews=tuple(previews),
        baseline_frames=tuple(frames),
        context={**prepared.context, "evolution": public, "available_materials": materials},
    )
