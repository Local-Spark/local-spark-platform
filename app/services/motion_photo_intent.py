"""Photo direction projected from the immutable plan, without aesthetic thresholds."""

from typing import Any

from app.schemas.motion_production import MotionConstructionPlan
from app.services.auth import AuthError
from app.services.motion_generation import construction_plan_hash

PHOTO_INTENT_CONTRACT = {
    "version": "motion-photo-intent-v1",
    "rules": (
        "Planeje e implemente progressão perceptível pela intenção: cada cena desenvolve sua mensagem, "
        "dirige a atenção e prepara a próxima. Registre isso em development, sustained_value e transition. "
        "Um hold pode sustentar leitura ou contemplação; não substitua intenção por movimento contínuo. "
        "Tipografia: traduza appearance, purpose e attention_order em hierarquia, contraste, tamanho, "
        "quebras de linha e espaço adequados ao quadro final. Preserve texto autorizado e tempo para leitura "
        "nos beats; entrada/saída não devem consumir a janela de leitura. Evite texto sobre área fotográfica "
        "que prejudique contraste ou esconda o protagonista. "
        "Handoffs realizam origin, crossing e destination do plano, preservando a continuidade da atenção. "
        "Implemente em HTML/CSS/SVG/Canvas e seek determinístico conforme os recursos autorizados. "
        "MotionV1 é uma ferramenta disponível, não requisito estético; scale, zoom, efeitos, quantidade de "
        "cortes e CTA não são obrigatórios. Escolha mecanismos pela intenção, sem inventar ação na foto. "
        "photo_implementation_intent é projeção do plano validado: execute seus tempos e relações, "
        "sem replanejar ou alterar a trilha. Na revisão/correção, compare a intenção com os quadros fornecidos; "
        "não presuma movimento entre amostras nem imponha limiares estéticos ou checklist de efeitos."
    ),
}


def photo_intent_rules(context: dict[str, Any]) -> str:
    contract = context.get("photo_intent_contract")
    if contract is None:
        return ""
    if contract != PHOTO_INTENT_CONTRACT:
        raise AuthError("MOTION_PHOTO_INTENT_CONTRACT_INVALID", 409)
    return str(contract["rules"])


def implementation_intent(plan: MotionConstructionPlan) -> dict[str, Any]:
    """Keep exact declared beats and direction; do not infer reading speed or effects."""
    assert plan.motion_plan is not None and plan.scene_direction is not None and plan.staging is not None
    directions = {scene.scene_id: scene for scene in plan.scene_direction.scenes}
    moments = {moment.scene_id: moment for moment in plan.staging.moments}
    return {
        "version": PHOTO_INTENT_CONTRACT["version"],
        "plan_sha256": construction_plan_hash(plan),
        "scenes": [
            {
                "scene_id": scene.id,
                "start_ms": scene.start_ms,
                "end_ms": scene.end_ms,
                "message": scene.message,
                "direction": directions[scene.id].model_dump(mode="json"),
                "progression_and_handoff": moments[scene.id].model_dump(mode="json"),
                "typography": [element.model_dump(mode="json") for element in scene.elements if element.role == "text"],
            }
            for scene in plan.motion_plan.scenes
        ],
    }
