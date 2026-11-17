"""Photo direction projected from the immutable plan, without aesthetic thresholds."""

from typing import Any

from app.schemas.motion_production import MotionConstructionPlan
from app.services.auth import AuthError
from app.services.motion_generation import construction_plan_hash

PHOTO_INTENT_CONTRACT_V1 = {
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


PHOTO_VISUAL_RULES = (
    "P1: durante todo hold de fotografia, implemente Ken Burns contínuo: scale suave "
    "(referência 1,00→1,06–1,12) e pan leve com margem de cobertura, sem revelar bordas nem cortar "
    "o protagonista. Anime o enquadramento da foto inteira, nunca objetos internos ou falsa filmagem. "
    "Planeje em development/sustained_value o percurso durante a leitura; evite trechos de mais de ~2 s "
    "sem mudança perceptível. Isso é orientação de construção, não limiar automático A5b. "
    "P2: planeje entrada e saída tipográficas com deslocamento/máscara e stagger por linha ou hierarquia "
    "temporal, não só opacity fade + hold. Declare as janelas nos beats; reserve leitura integral e "
    "conclua a saída antes do handoff, mantendo Ken Burns durante a leitura. "
    "P3: na entrega à marca, declare origin/crossing/destination com acento de scale: push ou scale-down "
    "da origem e assentamento do destino. Preserve proporções do logo; máscara/sombra são opcionais. "
    "Use wrappers distintos para foto, texto e handoff para não sobrescrever transforms. "
    "Adapte os exemplos pinados do repertório em scene_init, instancie-os e chame seus retornos em "
    "seek(ms) absoluto; helpers não são instalados automaticamente. Sem relógio incremental ou IO. "
    "Preserve materiais, texto, kit, duração, tempos validados e trilha autorizada. Não replaneje "
    "na implementação. Na revisão compare intenção/evidência, sem inferir movimento entre amostras "
    "ou criar gates estéticos automáticos."
)
PHOTO_INTENT_CONTRACT_V2 = {"version": "motion-photo-intent-v2", "rules": PHOTO_VISUAL_RULES}
PHOTO_QUALITY_RULES = (
    "L1: quando assets/logo.png estiver disponível, declare no plano pelo menos um elemento "
    "role=image com asset_id=assets/logo.png. No HTML do fecho, renderize obrigatoriamente "
    '<img src="assets/logo.png"> visível, seguindo os tempos de fecho/handoff do plano; '
    "declarar o asset no plano não basta. brand_name tipográfico "
    "pode coexistir como copy, mas não substitui o PNG. Preserve proporções e legibilidade da logo. "
    "P4/L2: planeje holds de leitura curtos, de até ~2–2,5 s; divida copy longa em beats legíveis. "
    "Em 15 s, prefira gancho → acento → segundo material vivo → handoff → marca/CTA. "
    "Durante o fecho/handoff, nos tempos definidos pelo plano, mantenha Ken Burns nas fotos/díptico "
    "e micro-movimento de scale/assentamento "
    "na logo até o fim; nenhum fecho de ~2 s ou mais sem mudança perceptível. "
    "L3: foto dominante full-bleed 9:16 com object-fit:cover e foco protegido é a composição padrão. "
    "Evite janela landscape e faixas mortas; justifique inset na intenção quando necessário. "
    "Tipografia/overlay sobre foto com contraste e protagonista protegido, sem cartaz estático. "
    "Ritmo e composição são orientação forte, não gates automáticos A5b; preserve a trilha."
)
PHOTO_INTENT_CONTRACT = {"version": "motion-photo-intent-v3", "rules": PHOTO_VISUAL_RULES + " " + PHOTO_QUALITY_RULES}


def photo_intent_rules(context: dict[str, Any]) -> str:
    contract = context.get("photo_intent_contract")
    if contract is None:
        return ""
    if contract not in (PHOTO_INTENT_CONTRACT_V1, PHOTO_INTENT_CONTRACT_V2, PHOTO_INTENT_CONTRACT):
        raise AuthError("MOTION_PHOTO_INTENT_CONTRACT_INVALID", 409)
    return str(contract["rules"])


def implementation_intent(
    plan: MotionConstructionPlan, contract: dict[str, Any] = PHOTO_INTENT_CONTRACT
) -> dict[str, Any]:
    """Keep exact declared beats and direction; do not infer reading speed or effects."""
    photo_intent_rules({"photo_intent_contract": contract})
    assert plan.motion_plan is not None and plan.scene_direction is not None and plan.staging is not None
    directions = {scene.scene_id: scene for scene in plan.scene_direction.scenes}
    moments = {moment.scene_id: moment for moment in plan.staging.moments}
    return {
        "version": contract["version"],
        **({"visual_execution": contract["rules"]} if contract != PHOTO_INTENT_CONTRACT_V1 else {}),
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
