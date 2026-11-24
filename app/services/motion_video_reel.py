"""Versioned VR1–VR3 admission and deterministic DOM enforcement, without new effects."""

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan
from app.services.auth import AuthError

GUARD_PATH = Path(__file__).resolve().parents[1] / "assets/motion_video/video-reel-v1.js"
VIDEO_REEL_CONTRACT = {
    "version": "motion-video-reel-v1",
    "dom_guard_sha256": "1aa5fb4c6f33b768569510bc22c57c1239df5dadf8e0ffd842ecc836600dc6b9",
    "rules": (
        "VR1–VR3: gravação assets/source.mp4 full-bleed cover 9:16 do primeiro ao último frame; "
        "sem janela, cartaz, letterbox, moldura ou ocultação. Preserve uma gravação inteira e seu áudio, "
        "até 60s/50MiB. Sem EDL, música nova, TTS, avatar ou novo renderer. "
        "Cada cena declara video_layout={mode:cover,video_element_id,brand_element_id,text_element_ids,"
        "cta_element_id:null|id}. Marca é IMG assets/logo.png discreta sobre a ação, nunca nome fixo como hero. "
        "Sem logo autorizado, solicitar material; não fabricar logo nem substituir por label. "
        "Todos os textos são declarados em text_element_ids e relacionados ao vídeo via related_element_ids. "
        "Frases curtas conforme briefing, sem hard-sell inventado. Enter, transform e exit suaves, lineares; "
        "start_state/end_state são JSON exato {x:number,y:number,opacity:number}, em px, sem escala/rotação. "
        "Beats contíguos com estados contínuos, cobrindo a cena; enter parte de opacity=0 e termina em 1, "
        "exit termina em 0; transform desloca pelo menos 4px. Execute translate(xpx,ypx) e opacity "
        "no próprio nó de texto, com interpolação absoluta, inclusive após seeks reversos. "
        "Texto legível sobre ação: fonte >=28px no canvas 720, cor branca, scrim preto local opacidade .75–.8 "
        "no pai direto, padding <=16px, largura <90% e altura <25% do quadro. Sem sombra/blur/placa/rodapé. "
        "Limites do texto entre 12% e 78% da altura; marca <=25% largura e <=12% altura. "
        "Última cena declara CTA com hold estável opacity=1 de pelo menos 1500ms antes da saída. "
        "A guarda confere plano e execução, não qualidade perceptual; revisão humana continua necessária."
    ),
}


def video_reel_rules(context: dict[str, Any]) -> str:
    contract = context.get("video_reel_contract")
    if contract is None:
        return ""
    if contract != VIDEO_REEL_CONTRACT:
        raise AuthError("MOTION_VIDEO_CONTRACT_CHANGED", 409)
    return " " + str(VIDEO_REEL_CONTRACT["rules"])


def _state(value: str) -> dict[str, float]:
    try:
        data = json.loads(value)
        if (
            not isinstance(data, dict)
            or set(data) != {"x", "y", "opacity"}
            or any(type(v) not in (int, float) or not math.isfinite(v) for v in data.values())
            or not 0 <= data["opacity"] <= 1
        ):
            raise ValueError
        return data
    except (ValueError, TypeError) as exc:
        raise AuthError("MOTION_VIDEO_TEXT_STATE_INVALID", 409) from exc


def validate_video_reel(
    artifact: HTMLMotionComposition | MotionConstructionPlan, context: dict[str, Any], *, asset_ids: set[str]
) -> None:
    if not video_reel_rules(context):
        return
    plan = artifact.motion_plan
    if plan is None:
        raise AuthError("MOTION_VIDEO_PLAN_REQUIRED", 409)
    if not {"assets/source.mp4", "assets/logo.png"} <= asset_ids:
        raise AuthError("MOTION_VIDEO_KIT_SOURCE_REQUIRED", 409)
    for scene in plan.scenes:
        layout = scene.video_layout
        elements = {e.id: e for e in scene.elements}
        if (
            layout is None
            or layout.video_element_id not in elements
            or elements[layout.video_element_id].asset_id != "assets/source.mp4"
            or elements[layout.video_element_id].role != "video"
            or layout.brand_element_id not in elements
            or elements[layout.brand_element_id].asset_id != "assets/logo.png"
            or elements[layout.brand_element_id].role != "image"
            or len(set(layout.text_element_ids)) != len(layout.text_element_ids)
            or set(layout.text_element_ids) != {e.id for e in scene.elements if e.role == "text"}
            or any(e.role == "video" and e.id != layout.video_element_id for e in scene.elements)
        ):
            raise AuthError("MOTION_VIDEO_LAYOUT_REQUIRED", 409)
        for identifier in layout.text_element_ids:
            element = elements[identifier]
            beats = element.beats
            if (
                layout.video_element_id not in element.related_element_ids
                or not {"enter", "transform", "exit"} <= {b.phase for b in beats}
                or beats[0].phase != "enter"
                or beats[-1].phase != "exit"
                or beats[0].start_ms != scene.start_ms
                or beats[-1].end_ms != scene.end_ms
            ):
                raise AuthError("MOTION_VIDEO_KINETIC_TEXT_REQUIRED", 409)
            previous = None
            end = scene.start_ms
            for beat in beats:
                a, z = _state(beat.start_state), _state(beat.end_state)
                if (
                    beat.curve.kind != "linear"
                    or beat.start_ms != end
                    or (previous is not None and a != previous)
                    or (beat.phase == "enter" and (a["opacity"] != 0 or z["opacity"] != 1))
                    or (beat.phase == "exit" and z["opacity"] != 0)
                    or (beat.phase == "hold" and (a != z or a["opacity"] != 1))
                    or (beat.phase == "transform" and math.hypot(z["x"] - a["x"], z["y"] - a["y"]) < 4)
                ):
                    raise AuthError("MOTION_VIDEO_KINETIC_TEXT_REQUIRED", 409)
                previous, end = z, beat.end_ms
        if scene == plan.scenes[-1]:
            cta = elements.get(layout.cta_element_id or "")
            if (
                cta is None
                or cta.id not in layout.text_element_ids
                or not any(b.phase == "hold" and b.end_ms - b.start_ms >= 1500 for b in cta.beats)
            ):
                raise AuthError("MOTION_VIDEO_CTA_WINDOW_INVALID", 409)
        elif layout.cta_element_id is not None:
            raise AuthError("MOTION_VIDEO_CTA_WINDOW_INVALID", 409)


def guarded_video_scene_init(composition: HTMLMotionComposition, context: dict[str, Any], original: str) -> str:
    if not video_reel_rules(context):
        return original
    source = GUARD_PATH.read_bytes()
    if hashlib.sha256(source).hexdigest() != VIDEO_REEL_CONTRACT["dom_guard_sha256"]:
        raise AuthError("MOTION_VIDEO_GUARD_CHANGED", 409)
    validate_video_reel(composition, context, asset_ids={"assets/source.mp4", "assets/logo.png"})
    assert composition.motion_plan is not None
    payload = composition.motion_plan.model_dump(mode="json")
    return original + "\n;(" + source.decode() + ")(" + json.dumps(payload, ensure_ascii=True) + ");"
