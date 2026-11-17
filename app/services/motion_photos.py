"""Product policy for reels built from authorized photographs, without a recording."""

import re
from typing import TYPE_CHECKING, Any

from app.adapters.motion_html_renderer import RenderAsset
from app.services.auth import AuthError
from app.services.motion_sound_library import capture_sound_library, load_sound_library

if TYPE_CHECKING:
    from app.schemas.motion_production import MotionRequest

PHOTO_MOTION_RULES = (
    "Esta peça parte de fotografias autorizadas, sem vídeo de entrada. "
    "Não crie nem referencie assets/source.mp4, quadros de gravação, fala ou transcrição. "
    "As regras relativas à preservação de vídeo/voz só se aplicam quando existe uma gravação. "
    "Planeje uma narrativa visual usando as fotos pertinentes, o kit, textos curtos e grafismos. "
    "Não é obrigatório usar todas as fotos. Escolha enquadramentos, movimento suave quando pedido, "
    "entradas de texto e transições com função narrativa; preserve leitura e aparência dos materiais. "
    "Use exatamente output.duration_ms. Não apresente movimento de câmera sobre foto como filmagem real. "
    "Use somente o áudio autorizado pelo servidor; sem trilha disponível, mantenha silêncio."
)


def photo_duration_ms(message: str) -> int:
    """Honor explicit numeric seconds; a short unspecified photo reel defaults to 15s."""
    pattern = r"(?<![\w.,])([0-9]+)\s*(?:segundos?|segs?|s)\b"
    latest_reply = message.rsplit("Resposta do solicitante:", 1)[-1]
    if re.search(pattern, latest_reply, re.IGNORECASE):
        message = latest_reply
    values = {int(value) for value in re.findall(pattern, message, re.IGNORECASE)}
    if not values:
        return 15000
    if len(values) != 1 or not 5 <= next(iter(values)) <= 60:
        raise AuthError("MOTION_PHOTO_DURATION_REQUIRED", 409)
    return next(iter(values)) * 1000


def photo_music(duration_ms: int) -> dict[str, Any] | None:
    """Only explicitly curated background music qualifies; sound effects never do."""
    library = capture_sound_library("public-cc0-v1")
    for item in library["items"]:
        if (
            item.get("role") == "music"
            and item.get("default_for_photo_reels") is True
            and item.get("license") == "CC0-1.0"
            and item["duration_ms"] >= duration_ms
        ):
            return {"library_id": library["id"], "candidate_id": item["id"], "sha256": item["sha256"]}
    return None


def load_photo_music(selection: dict[str, Any], duration_ms: int) -> tuple[RenderAsset, dict[str, Any]]:
    """Read pinned licensed bytes locally; never download or synthesize music implicitly."""
    if selection != photo_music(duration_ms):
        raise AuthError("MOTION_SOUND_LIBRARY_CHANGED", 409)
    identifier = selection["library_id"]
    assets = load_sound_library(
        {"request": {"sound_library_id": identifier}, "sound_library": capture_sound_library(identifier)}
    )
    asset = next(asset for asset in assets if asset.id == f"assets/sfx-{selection['candidate_id']}.mp3")
    return asset, music_soundtrack(asset.id, duration_ms)


def music_soundtrack(asset_id: str, duration_ms: int) -> dict[str, Any]:
    return {
        "version": "motion-audio-v2",
        "mode": "mix",
        "ducking": None,
        "tracks": [
            {
                "asset_id": asset_id,
                "role": "music",
                "offset_ms": 0,
                "trim_start_ms": 0,
                "trim_end_ms": duration_ms,
                "volume": 0.18,
                "fade_in_ms": 500,
                "fade_out_ms": 800,
            }
        ],
    }


def planned_photo_request(
    request: "MotionRequest", photos: list[dict[str, Any]], *, human_review: bool
) -> "MotionRequest":
    """Shared lab/WhatsApp request; evidence refers to authorized photographs, never video frames."""
    from app.schemas.motion_production import MotionRequest
    from app.services.motion_music import music_mood

    if not photos:
        raise AuthError("MOTION_PHOTOS_REQUIRED", 409)
    data = request.model_dump(mode="json")
    message = request.instruction
    data.update(
        propose_direction=True,
        sound_library_id="public-cc0-v1" if music_mood(message) is not None else None,
        review_checkpoints=human_review,
        storyboard=human_review,
        automatic_plan=not human_review,
        preparation={
            "client_message": message,
            "decisions": [
                {
                    "id": f"request-{i}",
                    "kind": "requirement",
                    "origin": "client",
                    "source_excerpt": message[i : i + 1000],
                    "interpretation": "Preservar o sentido do pedido no planejamento com fotos autorizadas.",
                    "scope": "request",
                }
                for i in range(0, len(message), 1000)
            ],
            "evidence": [
                {
                    "id": f"photo-{i}",
                    "kind": "material",
                    "asset_id": f"assets/photo-{photo['id']}.png",
                    "observation": "Fotografia autorizada; observar os detalhes visíveis ao planejar.",
                    "intended_use": "Fundamentar a narrativa visual sem simular uma gravação.",
                    "limitations": "A foto não comprova movimento, som, faces ocultas ou continuidade temporal.",
                }
                for i, photo in enumerate(photos)
            ],
        },
    )
    return MotionRequest.model_validate(data)
