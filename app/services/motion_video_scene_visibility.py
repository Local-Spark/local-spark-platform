"""Pinned scene ownership for video text scrims, shared by storyboard and render."""

import hashlib
import json
from pathlib import Path
from typing import Any

from app.schemas.motion_production import HTMLMotionComposition
from app.services.auth import AuthError
from app.services.motion_video_reel import VIDEO_REEL_CONTRACT

SOURCE = Path(__file__).resolve().parents[1] / "assets/motion_video/scene-visibility-v1.js"
CONTRACT = {
    "version": "motion-video-scene-visibility-v1",
    "sha256": "81549f12024416a65410dc86bbadd7d43ba477ff2b158c3e29c664088add95f4",
    "rules": (
        "O executor controla display do pai direto de cada texto conforme a cena ativa do motion_plan, "
        "antes e depois de cada seek. Cada text_element_id de todas as cenas deve existir no DOM, "
        "com pai exclusivo de scrim, contendo somente aquele elemento e seu texto. Não compartilhar "
        "scrim com outro texto, mídia, logo ou conteúdo. Não remover esses nós durante seek. "
        "O runtime torna o pai ativo display:block e os demais display:none, inclusive em seeks reversos. "
        "A implementação continua responsável por texto puro, beats, posição, scrim, fonte, logo e "
        "um único VIDEO contínuo. Não altera o plano nem os gates e não oculta elementos desconhecidos."
    ),
}


def capture_scene_visibility(*, video: bool, previous: dict[str, Any] | None) -> dict[str, Any]:
    if previous is not None:
        return (
            {"video_scene_visibility_contract": previous["video_scene_visibility_contract"]}
            if "video_scene_visibility_contract" in previous
            else {}
        )
    return {"video_scene_visibility_contract": dict(CONTRACT)} if video else {}


def scoped_video_scene_init(composition: HTMLMotionComposition, context: dict[str, Any], original: str) -> str:
    contract = context.get("video_scene_visibility_contract")
    if contract is None:
        return original
    if contract != CONTRACT or context.get("video_reel_contract") != VIDEO_REEL_CONTRACT:
        raise AuthError("MOTION_VIDEO_SCENE_CONTRACT_CHANGED", 409)
    if composition.motion_plan is None:
        raise AuthError("MOTION_VIDEO_PLAN_REQUIRED", 409)
    try:
        source = SOURCE.read_bytes()
        if hashlib.sha256(source).hexdigest() != CONTRACT["sha256"]:
            raise ValueError
    except (OSError, ValueError) as exc:
        raise AuthError("MOTION_VIDEO_SCENE_RUNTIME_CHANGED", 409) from exc
    payload = json.dumps(composition.motion_plan.model_dump(mode="json"), ensure_ascii=True)
    return original + "\n;(" + source.decode() + ")(" + payload + ");"
