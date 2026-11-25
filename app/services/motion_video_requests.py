"""New automatic video requests, preserving the client's message and source."""

from app.schemas.motion_production import MotionRequest


def planned_video_request(request: MotionRequest) -> MotionRequest:
    """Bind source evidence before capture; never upgrade a previous snapshot."""
    from app.services.motion_music import music_mood

    message = request.instruction
    return MotionRequest.model_validate(
        request.model_dump(mode="json")
        | {
            "propose_direction": True,
            "sound_library_id": request.sound_library_id or ("public-cc0-v1" if music_mood(message) else None),
            "automatic_plan": True,
            "preparation": {
                "client_message": message,
                "decisions": [
                    {
                        "id": f"request-{i}",
                        "kind": "requirement",
                        "origin": "client",
                        "source_excerpt": message[i : i + 1000],
                        "interpretation": "Preservar o sentido do pedido na gravação autorizada.",
                        "scope": "request",
                    }
                    for i in range(0, len(message), 1000)
                ],
                "evidence": [
                    {
                        "id": "recording",
                        "kind": "source",
                        "at_ms": [0],
                        "observation": "Frame inicial da gravação autorizada; observar as demais amostras ao planejar.",
                        "intended_use": (
                            "Planejar segmentos com função e reenquadramento; preservar fala e áudio da fonte."
                        ),
                        "limitations": "A seleção não comprova conteúdo, sincronismo ou escuta.",
                    }
                ],
            },
        }
    )
