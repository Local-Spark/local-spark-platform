"""Fatia B: pinned EDL admission and execution checks, additive to intact VR1–VR3."""

import hashlib
import json
from pathlib import Path
from typing import Any

from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan
from app.services.auth import AuthError
from app.services.motion_video_capabilities import (
    EDIT_CONTRACT_V3,
    EDIT_CONTRACT_V4,
    EDIT_CONTRACT_V5,
    enabled,
    validate_edl,
)

SOURCE = Path(__file__).resolve().parents[1] / "assets/motion_video/edit-v1.js"
RULES = (
    "Fatia B VR4–VR5: cada video_layout declara edit={source_in_ms,source_out_ms,purpose,transition,"
    "intent,crop_from,crop_to}. purpose: hook/detail/invitation; >=2 funções distintas. transition=cut. "
    "Cenas contíguas, sem sobreposição; duração de cada segmento igual ao intervalo na fonte, sem speed ramp. "
    "Tempos na fonte dentro da duração original; duração final preservada nesta versão. "
    "Com áudio, source_in_ms=scene.start_ms: manter fala e áudio inteiros; cortes são de reenquadramento. "
    "Sem áudio, remonte temporal permitido. Cada corte muda escala >=.06 ou x/y >=.04. "
    "crop_from/crop_to={scale:1..1.35,x,y}; x/y são frações do canvas. Em cada segmento, variar escala >=.03 "
    "ou x/y >=.02 com intenção, linearmente. Cobertura: abs(x),abs(y)<=(scale-1)/2. "
    "VIDEO absoluto 0,0, dimensões do canvas, object-fit:cover, object-position:50% 50%, "
    "transform-origin:50% 50%; transform translate(x*width px,y*height px) scale(scale). "
    "Seek da fonte = source_in_ms + ms - scene.start_ms; aguardar seeked; "
    "clamp a min(out,duração real)-1ms, tolerando só padding final de até 34ms. "
    "Um único VIDEO, renomeado para o ID da cena ativa. Não duplicar mídia. "
    "VR1–VR3, texto puro, scrim estável e scene-visibility permanecem obrigatórios. "
    "Grafismos e assets adicionais não são habilitados nesta versão. Sem inventar materiais. "
    "VR6 unavailable: edl_music_mix_not_qualified. Não adicionar música/SFX nem chamar provedor. "
    "Briefing soft: pausa aconchegante, frases curtas e kit, sem hard-sell."
)
CONTRACT = {
    "version": "motion-video-edit-v1",
    "sha256": "a6d462ce99d33c3279e92b8e041bbc39d6c11bc645d700a1b7ae19ed4fa006af",
    "rules": RULES,
    "music": {"status": "unavailable", "reason": "edl_music_mix_not_qualified"},
}


PADDING_RULE = (
    "Exceção final verificada: somente a última cena pode ter intervalo na fonte menor que sua duração "
    "por 1–34ms, quando source_out_ms é exatamente source.duration_ms medido pelo servidor. "
    "Esse restante é padding do último frame, não corte nem speed ramp. Nunca aplicar em cenas internas, "
    "com duração desconhecida ou fim inventado. Duração de saída e áudio autorizado permanecem intactos."
)
CONTRACT_V2 = {
    **CONTRACT,
    "version": "motion-video-edit-v2",
    "rules": RULES + " " + PADDING_RULE,
}


def edit_rules(context: dict[str, Any]) -> str:
    contract = context.get("video_edit_contract")
    if contract is None:
        return ""
    if contract not in (CONTRACT, CONTRACT_V2, EDIT_CONTRACT_V3, EDIT_CONTRACT_V4, EDIT_CONTRACT_V5):
        raise AuthError("MOTION_VIDEO_EDIT_CONTRACT_CHANGED", 409)
    return str(contract["rules"])


def capture_video_edit(*, video: bool, previous: dict[str, Any] | None) -> dict[str, Any]:
    if previous is not None:
        return {"video_edit_contract": previous["video_edit_contract"]} if "video_edit_contract" in previous else {}
    return {"video_edit_contract": dict(EDIT_CONTRACT_V5)} if video else {}


def _final_source_padding(scene: Any, plan: Any, context: dict[str, Any]) -> bool:
    if context.get("video_edit_contract") != CONTRACT_V2 or scene != plan.scenes[-1]:
        return False
    edit = scene.video_layout.edit
    source_duration = context.get("source", {}).get("duration_ms")
    return (
        type(source_duration) is int
        and edit.source_out_ms == source_duration
        and 1 <= scene.end_ms - scene.start_ms - (edit.source_out_ms - edit.source_in_ms) <= 34
    )


def validate_video_edit(artifact: HTMLMotionComposition | MotionConstructionPlan, context: dict[str, Any]) -> None:
    if not edit_rules(context):
        return
    if enabled(context):
        validate_edl(artifact, context)
        return
    plan = artifact.motion_plan
    if plan is None or len(plan.scenes) < 2:
        raise AuthError("MOTION_VIDEO_EDL_REQUIRED", 409)
    previous_end = 0
    previous_crop = None
    purposes = set()
    for scene in plan.scenes:
        edit = scene.video_layout.edit if scene.video_layout else None
        if (
            edit is None
            or scene.start_ms != previous_end
            or (
                edit.source_out_ms - edit.source_in_ms != scene.end_ms - scene.start_ms
                and not _final_source_padding(scene, plan, context)
            )
            or edit.source_out_ms > plan.duration_ms
            or (artifact.audio.mode != "silent" and edit.source_in_ms != scene.start_ms)
        ):
            raise AuthError("MOTION_VIDEO_EDL_INVALID", 409)
        purposes.add(edit.purpose)
        a, z = edit.crop_from, edit.crop_to
        for crop in (a, z):
            if max(abs(crop.x), abs(crop.y)) > (crop.scale - 1) / 2 + 1e-9:
                raise AuthError("MOTION_VIDEO_CROP_UNSAFE", 409)
        if max(abs(a.scale - z.scale) / 0.03, abs(a.x - z.x) / 0.02, abs(a.y - z.y) / 0.02) < 1 - 1e-9:
            raise AuthError("MOTION_VIDEO_MOTION_REQUIRED", 409)
        if (
            previous_crop is not None
            and max(
                abs(a.scale - previous_crop.scale) / 0.06,
                abs(a.x - previous_crop.x) / 0.04,
                abs(a.y - previous_crop.y) / 0.04,
            )
            < 1 - 1e-9
        ):
            raise AuthError("MOTION_VIDEO_CUT_REQUIRED", 409)
        previous_end, previous_crop = scene.end_ms, z
    if len(purposes) < 2:
        raise AuthError("MOTION_VIDEO_EDITORIAL_FUNCTION_REQUIRED", 409)
    if context.get("authorized_soundtrack") is not None:
        raise AuthError("MOTION_VIDEO_MUSIC_UNAVAILABLE", 409)


def guarded_video_edit_init(composition: HTMLMotionComposition, context: dict[str, Any], original: str) -> str:
    if not edit_rules(context):
        return original
    validate_video_edit(composition, context)
    try:
        source = SOURCE.read_bytes()
        if hashlib.sha256(source).hexdigest() != CONTRACT["sha256"]:
            raise ValueError
    except (OSError, ValueError) as exc:
        raise AuthError("MOTION_VIDEO_EDIT_GUARD_CHANGED", 409) from exc
    assert composition.motion_plan is not None
    payload = json.dumps(composition.motion_plan.model_dump(mode="json"), ensure_ascii=True)
    return original + "\n;(" + source.decode() + ")(" + payload + ");"
