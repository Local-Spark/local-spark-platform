"""Versioned video capabilities: declared layers, editorial development and safe cuts."""

import json
import math
from typing import Any

from app.schemas.motion_plan import MotionPlan, VideoDesign, VideoLayer
from app.services.auth import AuthError
from app.services.motion_speech import speech_timing, validate_speech_source

RULES = (
    "Video C: motion-video-reel-v2 + motion-video-edit-v3, video_layout.design.version=video-design-v1. "
    "O plano é allowlist: declare TODOS os grafismos/imagens em design.layers com element_id, box "
    "{x,y,width,height} normalizado, z_index 0..18, shape rectangle/ellipse e color hexadecimal do kit. "
    "Cada layer aponta para role graphic ou image e beats lineares com JSON {x,y,opacity} em px. "
    "Grafismos puros sem filhos; imagens usam somente assets autorizados. O runtime cria essas layers, "
    "aplica beats e visibilidade; não duplique seus nós no HTML. Vídeo único e logo/textos ficam no HTML. "
    "design.viewport define retângulo normalizado do vídeo: mode cover exige 0,0,1,1; mode pip "
    "revela camada de fundo declarada. Vídeo z-index 10; texto e logo acima (20 ou mais). "
    "Layers 11..18 podem passar à frente da gravação; 0..9 são planos de fundo. "
    "O runtime executa EDL/crop e viewport; a guarda confere mídia, texto, logo e overlays. "
    "Corte com função: design.transition_reason relaciona origem/destino; >=2 funções editoriais, "
    "mudança de composição >=800ms, graphic com deslocamento >=48px e presença >=800ms. "
    "Take contínuo + texto + crop mínimo falha, mesmo em briefing soft; capacidade não prova qualidade. "
    "EDL in/out livres dentro da fonte, sem speed ramp; duração final <= output.duration_ms (teto). "
    "Pode encurtar sem repetir material; "
    "remonte com áudio exige fronteiras com margem 120ms em silêncio medido ou intervalo ASR completo "
    "com confiança >=.8; lacunas de transcrição parcial não provam silêncio. "
    "Cortes visuais contínuos não cortam áudio. Unsafe: MOTION_VIDEO_SPEECH_CUT_UNSAFE. "
    "O servidor monta áudio original na mesma EDL, aplica música autorizada/cache local e duck; "
    "SFX apenas biblioteca licenciada. Não comprar/gerar música. Ausência real fica explícita. "
    "Texto puro, scrim local estável, logo kit, scene-visibility, limites 60s/50MiB permanecem. "
    "Sem Remotion/TTS/avatar. Qualidade das refs 41/Maestros depende de MP4 e revisão humana autorizados."
)
EDIT_CONTRACT_V3 = {
    "version": "motion-video-edit-v3",
    "rules": RULES,
    "music": {"status": "supported", "policy": "existing-library-duck-v1"},
}

RULES_V4 = (
    "Video qualidade: motion-video-reel-v3 + motion-video-edit-v4, design video-design-v2. "
    "O plano é allowlist: design.layers com shape rectangle|ellipse|rounded|bar e color #RRGGBB ou #RRGGBBAA do kit. "
    "Beats lineares JSON {x,y,opacity} ou {x,y,opacity,scale} (scale>0, default 1). "
    "transition cut|dissolve|fade com transition_reason; dissolve/fade suavizam opacidade nas bordas da cena. "
    "EDL: com áudio, duração do segmento = intervalo na fonte (1:1) + speech-safe; silent permite rate "
    "0.75–1.25 (source_span/scene_span). Padding final 1–34ms na última cena permanece. "
    "Desenvolvimento editorial: >=2 funções, >=2 assinaturas de composição, e ao menos um de "
    "PIP>=800ms, imagem auxiliar sustentada, ou graphic exposto (deslocamento>=24px ou barra/rounded "
    "visível >=800ms). Take+texto+crop mínimo continua rejeitado. "
    "Mix: biblioteca/cache + duck; sem compra/geração paga sem credencial. "
    "Logo kit, texto legível (spans ok), scene-visibility, 60s/50MiB, sem Remotion/TTS/avatar/inventar assets."
)
EDIT_CONTRACT_V4 = {
    "version": "motion-video-edit-v4",
    "rules": RULES_V4,
    "music": {"status": "supported", "policy": "existing-library-duck-v1"},
}

RULES_V5 = (
    "Video handoff: motion-video-reel-v4 + motion-video-edit-v5, design video-design-v2. "
    "O plano é allowlist: design.layers com shape rectangle|ellipse|rounded|bar e color #RRGGBB ou #RRGGBBAA do kit. "
    "Runtime cria cada graphic como SVG com forma preenchida (não DIV vazio); filhos SVG só sob o id declarado. "
    "Beats lineares JSON {x,y,opacity} ou {x,y,opacity,scale} (scale>0, default 1). "
    "transition cut|dissolve|fade com transition_reason. "
    "dissolve/fade = handoff editorial: VIDEO pode ceder opacidade só na borda <=500ms se um plano "
    "full-bleed declarado (layer box 0,0,1,1, z_index<10, opacity>=.95) cobre o quadro — nunca fade para preto. "
    "EDL: com áudio, duração do segmento = intervalo na fonte (1:1) + speech-safe; silent permite rate "
    "0.75–1.25 (source_span/scene_span). Padding final 1–34ms na última cena permanece. "
    "Desenvolvimento editorial: >=2 funções, >=2 assinaturas de composição, e ao menos um de "
    "PIP>=800ms, imagem auxiliar sustentada, ou graphic exposto (deslocamento>=24px ou barra/rounded "
    "visível >=800ms). Take+texto+crop mínimo continua rejeitado. "
    "Mix: elevenlabs-music-v1 (cache + geração com as mesmas gates da photo) + duck; "
    "sem compra pelo modelo; sem credencial fica cache/status explícito. "
    "Logo kit, texto legível (spans ok), scene-visibility, 60s/50MiB, sem Remotion/TTS/avatar/inventar assets."
)
EDIT_CONTRACT_V5 = {
    "version": "motion-video-edit-v5",
    "rules": RULES_V5,
    "music": {"status": "supported", "policy": "elevenlabs-music-v1"},
}


def enabled(context: dict[str, Any]) -> bool:
    edit = context.get("video_edit_contract")
    reel = context.get("video_reel_contract", {}).get("version")
    return (
        (edit == EDIT_CONTRACT_V3 and reel == "motion-video-reel-v2")
        or (edit == EDIT_CONTRACT_V4 and reel == "motion-video-reel-v3")
        or (edit == EDIT_CONTRACT_V5 and reel == "motion-video-reel-v4")
    )


def quality_unlocked(context: dict[str, Any]) -> bool:
    return context.get("video_edit_contract") in (EDIT_CONTRACT_V4, EDIT_CONTRACT_V5) and context.get(
        "video_reel_contract", {}
    ).get("version") in {"motion-video-reel-v3", "motion-video-reel-v4"}


def handoff_unlocked(context: dict[str, Any]) -> bool:
    return (
        context.get("video_edit_contract") == EDIT_CONTRACT_V5
        and context.get("video_reel_contract", {}).get("version") == "motion-video-reel-v4"
    )


DESIGN_SCHEMA_REELS = frozenset({"motion-video-reel-v2", "motion-video-reel-v3", "motion-video-reel-v4"})


def design_schema_enabled(context: dict[str, Any]) -> bool:
    """Structured output must expose design for every reel that validates layers."""
    return context.get("video_reel_contract", {}).get("version") in DESIGN_SCHEMA_REELS


def pinned_design_version(context: dict[str, Any]) -> str | None:
    """Pin the design version the wire schema may emit for this reel capture."""
    reel = context.get("video_reel_contract", {}).get("version")
    if reel in {"motion-video-reel-v3", "motion-video-reel-v4"}:
        return "video-design-v2"
    if reel == "motion-video-reel-v2":
        return "video-design-v1"
    return None


def state(value: str) -> dict[str, float]:
    try:
        result = json.loads(value)
        if not isinstance(result, dict) or not {"x", "y", "opacity"} <= set(result) <= {"x", "y", "opacity", "scale"}:
            raise ValueError
        if any(type(result[k]) not in (int, float) or isinstance(result[k], bool) for k in result):
            raise ValueError
        parsed = {k: float(result[k]) for k in result}
        if any(not math.isfinite(v) for v in parsed.values()) or not 0 <= parsed["opacity"] <= 1:
            raise ValueError
        if "scale" in parsed and parsed["scale"] <= 0:
            raise ValueError
        return parsed
    except (ValueError, TypeError) as exc:
        raise AuthError("MOTION_VIDEO_LAYER_STATE_INVALID", 409) from exc


def _exposed(layer: VideoLayer, design: VideoDesign, point: dict[str, float]) -> bool:
    x, y = layer.box.x + point["x"] / 720, layer.box.y + point["y"] / 1280
    right, bottom = x + layer.box.width, y + layer.box.height
    v = design.viewport
    return (
        0 <= x < right <= 1
        and 0 <= y < bottom <= 1
        and (layer.z_index > 10 or right <= v.x or x >= v.x + v.width or bottom <= v.y or y >= v.y + v.height)
        and not any(
            other.z_index > layer.z_index
            and other.box.x < right
            and other.box.x + other.box.width > x
            and other.box.y < bottom
            and other.box.y + other.box.height > y
            for other in design.layers
        )
    )


def _motion(a: dict[str, float], z: dict[str, float]) -> float:
    return math.hypot(z["x"] - a["x"], z["y"] - a["y"]) + 40 * abs(z.get("scale", 1) - a.get("scale", 1))


def validate_development(plan: MotionPlan | None, *, unlocked: bool = False) -> None:
    if plan is None or len(plan.scenes) < 2:
        raise AuthError("MOTION_VIDEO_EDITORIAL_DEVELOPMENT_REQUIRED", 409)
    signatures = set()
    moving_graphic = False
    developed = False
    travel = 24 if unlocked else 48
    for scene in plan.scenes:
        layout = scene.video_layout
        if layout is None or layout.design is None:
            raise AuthError("MOTION_VIDEO_DESIGN_REQUIRED", 409)
        design = layout.design
        if unlocked and design.version != "video-design-v2":
            raise AuthError("MOTION_VIDEO_DESIGN_REQUIRED", 409)
        elements = {e.id: e for e in scene.elements}
        ids = [layer.element_id for layer in design.layers]
        expected = {
            e.id
            for e in scene.elements
            if e.id not in {layout.video_element_id, layout.brand_element_id, *layout.text_element_ids}
        }
        if len(ids) != len(set(ids)) or set(ids) != expected:
            raise AuthError("MOTION_VIDEO_LAYER_ALLOWLIST_INVALID", 409)
        viewport = design.viewport.model_dump()
        full = dict(x=0, y=0, width=1, height=1)
        if (layout.mode == "cover") != (viewport == full):
            raise AuthError("MOTION_VIDEO_VIEWPORT_INVALID", 409)
        if layout.mode == "pip" and not any(layer.box.model_dump() == full for layer in design.layers):
            raise AuthError("MOTION_VIDEO_BACKGROUND_REQUIRED", 409)
        if layout.mode == "pip" and scene.end_ms - scene.start_ms >= 800:
            developed = True
            backgrounds = [layer for layer in design.layers if layer.box.model_dump() == full]

            def idle(point: dict[str, float]) -> bool:
                return point["x"] == 0 and point["y"] == 0 and point["opacity"] == 1 and point.get("scale", 1) == 1

            if not any(
                all(idle(state(b.start_state)) and idle(state(b.end_state)) for b in elements[layer.element_id].beats)
                for layer in backgrounds
            ):
                raise AuthError("MOTION_VIDEO_BACKGROUND_REQUIRED", 409)
        for layer in design.layers:
            e = elements[layer.element_id]
            if e.role not in {"graphic", "image"}:
                raise AuthError("MOTION_VIDEO_LAYER_ALLOWLIST_INVALID", 409)
            last, end = None, scene.start_ms
            for beat in e.beats:
                a, z = state(beat.start_state), state(beat.end_state)
                if beat.curve.kind != "linear" or beat.start_ms != end or (last is not None and a != last):
                    raise AuthError("MOTION_VIDEO_LAYER_STATE_INVALID", 409)
                last, end = z, beat.end_ms
                if (
                    e.role == "image"
                    and layer.z_index > 10
                    and layer.box.width >= 0.5
                    and layer.box.height >= 0.5
                    and min(a["opacity"], z["opacity"]) >= 0.8
                    and beat.end_ms - beat.start_ms >= 800
                ):
                    developed = True
                graphic_pulse = (
                    e.role == "graphic"
                    and min(a["opacity"], z["opacity"]) >= 0.75
                    and beat.end_ms - beat.start_ms >= 800
                    and layer.box.width >= 0.04
                    and layer.box.height >= 0.01
                    and (
                        _motion(a, z) >= travel
                        or (unlocked and layer.shape in {"bar", "rounded"} and min(a["opacity"], z["opacity"]) >= 0.8)
                    )
                )
                if graphic_pulse:
                    moving_graphic = moving_graphic or (_exposed(layer, design, a) and _exposed(layer, design, z))
            if end != scene.end_ms:
                raise AuthError("MOTION_VIDEO_LAYER_STATE_INVALID", 409)
        if scene.end_ms - scene.start_ms >= 800:
            signatures.add(
                (
                    layout.mode,
                    tuple(viewport.values()),
                    tuple(
                        (elements[layer.element_id].asset_id, layer.shape, tuple(layer.box.model_dump().values()))
                        for layer in design.layers
                    ),
                )
            )
    # Unlocked contract: >=2 signatures and at least one of PIP / sustained image / exposed graphic.
    # Locked C still requires composition change and an exposed moving graphic together.
    has_development = (developed or moving_graphic) if unlocked else (developed and moving_graphic)
    if not has_development or len(signatures) < 2:
        raise AuthError("MOTION_VIDEO_EDITORIAL_DEVELOPMENT_REQUIRED", 409)


def safe_boundary(at: int, context: dict[str, Any]) -> bool:
    source = context.get("source", {})
    if at in (0, source.get("duration_ms")):
        return True
    margin = 120
    timing = speech_timing(context)
    validate_speech_source(timing, source)
    # An ASR word near a cut wins over a low-energy candidate (quiet speech).
    if timing and any(c.start_ms - margin < at < c.end_ms + margin for c in timing.cues):
        return False
    for m in context.get("audio_assessment", {}).get("measurements", []):
        if (
            m.get("asset_id") == "assets/source.mp4"
            and m.get("sha256") == source.get("sha256")
            and m.get("omitted_active_intervals") == 0
            and m.get("activity_threshold_dbfs") is not None
            and m["activity_threshold_dbfs"] <= -45
            and m.get("decoded_duration_ms", 0) >= at + margin
            and at >= margin
            and not any(start - margin < at < end + margin for start, end in m["active_intervals_ms"])
        ):
            return True
    # Only complete automatic timing, never owner-selected passages or an empty transcript.
    if timing and timing.provenance == "local_asr_unreviewed":
        before = [c for c in timing.cues if c.end_ms + margin <= at]
        after = [c for c in timing.cues if c.start_ms - margin >= at]
        return bool(
            before and after and all(c.confidence is not None and c.confidence >= 0.8 for c in (before[-1], after[0]))
        )
    return False


def _cover_opacity(plan_scene: Any, at_ms: int) -> bool:
    layout = plan_scene.video_layout
    design = layout.design
    elements = {e.id: e for e in plan_scene.elements}
    full = {"x": 0, "y": 0, "width": 1, "height": 1}
    for layer in design.layers:
        if layer.box.model_dump() != full or layer.z_index >= 10:
            continue
        for beat in elements[layer.element_id].beats:
            if beat.start_ms <= at_ms <= beat.end_ms:
                a, z = state(beat.start_state), state(beat.end_state)
                span = beat.end_ms - beat.start_ms or 1
                opacity = a["opacity"] + (z["opacity"] - a["opacity"]) * ((at_ms - beat.start_ms) / span)
                if opacity >= 0.95 - 1e-9:
                    return True
    return False


def validate_handoff_cover(plan: MotionPlan | None) -> None:
    if plan is None:
        raise AuthError("MOTION_VIDEO_HANDOFF_COVER_REQUIRED", 409)
    for scene in plan.scenes:
        edit = scene.video_layout.edit if scene.video_layout else None
        if edit is None or edit.transition not in {"dissolve", "fade"}:
            continue
        span = scene.end_ms - scene.start_ms
        edge = min(500, span / 4)
        samples = {scene.start_ms, scene.start_ms + int(edge / 2), scene.end_ms - int(edge / 2), scene.end_ms}
        if not all(_cover_opacity(scene, int(at)) for at in samples if scene.start_ms <= at <= scene.end_ms):
            raise AuthError("MOTION_VIDEO_HANDOFF_COVER_REQUIRED", 409)


def validate_edl(artifact: Any, context: dict[str, Any]) -> None:
    plan = artifact.motion_plan
    unlocked = quality_unlocked(context)
    validate_development(plan, unlocked=unlocked)
    if handoff_unlocked(context):
        validate_handoff_cover(plan)
    duration = context.get("source", {}).get("duration_ms")
    if type(duration) is not int:
        raise AuthError("MOTION_VIDEO_EDL_SOURCE_REQUIRED", 409)
    end = 0
    purposes = set()
    edits = []
    silent = artifact.audio.mode == "silent"
    for scene in plan.scenes:
        edit = scene.video_layout.edit
        if edit is None:
            raise AuthError("MOTION_VIDEO_EDL_REQUIRED", 409)
        scene_span = scene.end_ms - scene.start_ms
        source_span = edit.source_out_ms - edit.source_in_ms
        padding = scene_span - source_span
        rate = source_span / scene_span if scene_span else 0
        final_pad = scene == plan.scenes[-1] and edit.source_out_ms == duration and 1 <= padding <= 34
        speed_ok = unlocked and silent and 0.75 - 1e-9 <= rate <= 1.25 + 1e-9
        if (
            scene.start_ms != end
            or edit.source_in_ms >= edit.source_out_ms
            or edit.source_out_ms > duration
            or (padding != 0 and not final_pad and not speed_ok)
            or (not silent and padding != 0 and not final_pad)
        ):
            raise AuthError("MOTION_VIDEO_EDL_INVALID", 409)
        for crop in (edit.crop_from, edit.crop_to):
            if max(abs(crop.x), abs(crop.y)) > (crop.scale - 1) / 2 + 1e-9:
                raise AuthError("MOTION_VIDEO_CROP_UNSAFE", 409)
        end = scene.end_ms
        purposes.add(edit.purpose)
        edits.append(edit)
    if len(purposes) < 2:
        raise AuthError("MOTION_VIDEO_EDITORIAL_FUNCTION_REQUIRED", 409)
    if not silent:
        boundaries = [edits[0].source_in_ms, edits[-1].source_out_ms]
        for a, b in zip(edits, edits[1:], strict=False):
            if a.source_out_ms != b.source_in_ms:
                boundaries.extend((a.source_out_ms, b.source_in_ms))
        if not all(safe_boundary(at, context) for at in boundaries):
            raise AuthError("MOTION_VIDEO_SPEECH_CUT_UNSAFE", 409)
