"""Explicit opt-in for illustrative assets, separate from commercial product imagery."""

from typing import Any

from app.core.config import Settings
from app.services.auth import AuthError

MODEL = "gpt-image-2.5-flare-2026-09-08"
POLICY = "motion-illustrations-v1"


def illustration_policy(settings: Settings) -> dict[str, Any] | None:
    if not settings.motion_illustrations_enabled:
        return None
    reserve = settings.motion_illustration_reservation_usd_micros
    budget = settings.motion_illustration_budget_usd_micros
    if (
        settings.motion_ai_mode != "openai"
        or not settings.openai_api_key
        or not settings.openai_api_key.get_secret_value().strip()
        or not 0 < reserve <= budget
        or budget + 2 * settings.motion_ai_reservation_usd_micros > settings.motion_request_budget_usd_micros
        or settings.visual_ai_monthly_budget_usd_micros <= 0
        or settings.visual_ai_global_monthly_budget_usd_micros <= 0
    ):
        raise AuthError("MOTION_ILLUSTRATION_NOT_CONFIGURED", 409)
    return {
        "version": POLICY,
        "model": MODEL,
        "quality": "medium",
        "size": "1024x1024",
        "output_format": "png",
        "background": "transparent",
        "max_images": min(2, budget // reserve),
        "reservation_usd_micros": reserve,
        "budget_usd_micros": budget,
        "cost_policy": "image-2.5-standard-2026-11-09",
        "rules": (
            "Use illustrations=[] quando acervo/componentes/código atenderem à cena. Só peça uma ilustração "
            "se ela acrescentar uma representação útil que as opções disponíveis não resolvem. "
            "Para cada imagem, declare asset_id assets/illustration-<nome>.png, description detalhando objeto, "
            "partes, enquadramento e linguagem visual do kit, e purpose justificando sua função narrativa. "
            "Use esse asset_id no motion_plan com role=image e construction=generated_asset na direção. "
            "O serviço gerará o PNG antes de renderizar. Reserve o espaço no HTML; mantenha texto, logo e "
            "animação fora da imagem. Só ilustrações genéricas/conceituais: não invente foto de produto, pessoa, "
            "local, resultado ou atributos reais do negócio. No máximo max_images, sem imagens decorativas "
            "gratuitas. Recortes transparentes podem ser reutilizados em várias cenas. "
            "A correção conserva integralmente illustrations e reutiliza os mesmos arquivos; não regenera. "
            "A imagem ainda não foi vista na geração inicial: a crítica recebe os pixels efetivamente gerados."
        ),
    }


def image_estimate(usage: dict[str, Any] | None) -> int | None:
    """Standard price, no cache discount. Estimate is not an invoice or preflight cap."""
    if not isinstance(usage, dict):
        return None
    inp, out = usage.get("input_tokens"), usage.get("output_tokens")
    if type(inp) is not int or type(out) is not int or min(inp, out) < 0:
        return None
    details = usage.get("input_tokens_details", {})
    if not isinstance(details, dict):
        return None
    image_tokens = details.get("image_tokens", 0)
    if type(image_tokens) is not int or not 0 <= image_tokens <= inp:
        return None
    text_tokens = details.get("text_tokens", inp - image_tokens)
    if type(text_tokens) is not int or text_tokens != inp - image_tokens:
        return None
    # $5/M input text, $8/M input image, $30/M output image = integer microdollars/token.
    return text_tokens * 5 + image_tokens * 8 + out * 30
