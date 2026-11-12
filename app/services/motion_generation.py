"""Versioned wire projection; the supplied direction remains authoritative server input."""

import hashlib
import json
from typing import Any

from app.schemas.motion_generation import (
    CompactProvidedDirectionOutput,
    MotionImplementationOutput,
    MotionPlanningOutput,
    ProvidedDirectionOutput,
)
from app.schemas.motion_production import DirectedHTMLMotionComposition, MotionConstructionPlan
from app.services.auth import AuthError
from app.services.motion_visual_direction import supplied_direction

LEGACY_GENERATION_CONTRACT = {
    "version": "provided-direction-output-v1",
    "direction_source": "request.scene_direction",
    "response_rules": (
        "A direção fornecida já está preservada pelo servidor: não devolva scene_direction no JSON. "
        "Entregue concept, source_usage, audio, illustrations, motion_plan, html e scene_init completos. "
        "Use os IDs e a direção fornecidos. Cada elemento tem beats ordenados e sem sobreposição: "
        "ações simultâneas de suas partes são descritas em um único beat composto, com subintervalos "
        "no texto, sem duplicar o elemento ou mudar seus IDs. Não omita nem abrevie código com reticências."
    ),
}


GENERATION_CONTRACT = {
    **LEGACY_GENERATION_CONTRACT,
    "version": "provided-direction-output-v2",
    "response_rules": LEGACY_GENERATION_CONTRACT["response_rules"]
    + (
        " Nesta versão, cada beat usa chaves compactas: p=phase, s=start_ms, e=end_ms, "
        "a=start_state, z=end_state, path=trajectory, c=curve, cue=speech_cue_id (null sem vínculo). "
        "Curvas nomeadas usam somente a string linear/ease_in/ease_out/ease_in_out; "
        "cubic_bezier/spring mantêm o objeto kind/parameters completo. O servidor expande esses "
        "campos sem alterar valores para o motion_plan normal; código usa a API normal do runtime. "
        "Não repita holds entre ações se apenas mantêm o estado anterior: a timeline mantém esse "
        "estado nos intervalos. Para elemento totalmente estático, mantenha um hold descritivo. "
        "Conserve tempos, estados, relações e movimento significativo."
    ),
}

STAGED_GENERATION_CONTRACT = {
    "version": "provided-direction-output-v3",
    "direction_source": "request.scene_direction",
    "response_rules": (
        "A geração inicial tem duas etapas: plan e implementation. Cada uma tem seu schema próprio. "
        "A direção fornecida é preservada pelo servidor. Na etapa plan, entregue somente conceito, "
        "uso da fonte, áudio, declarações de imagem e plano compacto. Não escreva HTML ou JavaScript. "
        "Na etapa implementation, execute o plano validado fornecido; entregue somente plan_sha256, "
        "html e scene_init completos, sem repetir nem alterar o plano, áudio ou direção. "
        "As instruções de código/runtime do contexto se aplicam à implementation; as descrições "
        "criativas se aplicam ao planejamento e devem ser respeitadas na execução. "
        "Na correção posterior, use o contrato compacto v2 completo. "
    ),
    "plan_rules": GENERATION_CONTRACT["response_rules"].split(" Nesta versão,", 1)[1],
}

ASSET_INFORMED_GENERATION_CONTRACT = {
    **STAGED_GENERATION_CONTRACT,
    "version": "provided-direction-output-v4",
    "response_rules": STAGED_GENERATION_CONTRACT["response_rules"].replace(
        "Na etapa implementation, execute o plano validado fornecido; entregue somente plan_sha256, "
        "html e scene_init completos, sem repetir nem alterar o plano, áudio ou direção. ",
        "Na etapa implementation, respeite o plano validado e use o schema v4 para declarar sucesso ou "
        "necessidade de revisão; não repita nem altere plano, áudio ou direção. ",
    )
    + (
        " Antes da implementation, os materiais declarados são resolvidos e seus previews verificados são anexados. "
        "Use dimensões e transparência informadas, respeite as limitações do material e o hash do plano imutável. "
        "Imagem plana não permite revelar faces ocultas ou supor geometria 3D. Se o material inviabilizar "
        "o plano, use status requires_plan_revision, forneça revision_reason e não entregue código. "
        "Uma revisão posterior exige novo plano e novo hash; nunca altere o plano silenciosamente."
    ),
}


def asset_informed_enabled(context: dict[str, Any]) -> bool:
    return context.get("generation_contract") == ASSET_INFORMED_GENERATION_CONTRACT


def staged_generation_enabled(context: dict[str, Any]) -> bool:
    provided_output_enabled(context)
    return context.get("generation_contract") in (STAGED_GENERATION_CONTRACT, ASSET_INFORMED_GENERATION_CONTRACT)


def construction_plan_hash(plan: MotionConstructionPlan) -> str:
    encoded = json.dumps(plan.model_dump(mode="json"), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def decode_construction_plan(text: str, context: dict[str, Any]) -> MotionConstructionPlan:
    data = expand_compact_output(MotionPlanningOutput.model_validate_json(text).model_dump(mode="json"))
    return MotionConstructionPlan.model_validate({**data, "scene_direction": supplied_direction(context)})


def decode_implementation(text: str, plan: MotionConstructionPlan) -> DirectedHTMLMotionComposition:
    output = MotionImplementationOutput.model_validate_json(text)
    if output.plan_sha256 != construction_plan_hash(plan):
        raise ValueError("Implementation must reference the supplied plan")
    return DirectedHTMLMotionComposition.model_validate(
        {**plan.model_dump(mode="json"), "html": output.html, "scene_init": output.scene_init}
    )


def generation_wire_model(
    context: dict[str, Any],
) -> type[ProvidedDirectionOutput] | type[CompactProvidedDirectionOutput]:
    if not provided_output_enabled(context):
        raise AuthError("MOTION_GENERATION_CONTRACT_REQUIRED", 409)
    return (
        CompactProvidedDirectionOutput
        if context["generation_contract"] != LEGACY_GENERATION_CONTRACT
        else ProvidedDirectionOutput
    )


def expand_compact_output(data: dict[str, Any]) -> dict[str, Any]:
    """Expand validated wire data; full validators still reject invalid intervals/links/curves."""
    aliases = {
        "p": "phase",
        "s": "start_ms",
        "e": "end_ms",
        "a": "start_state",
        "z": "end_state",
        "path": "trajectory",
        "c": "curve",
        "cue": "speech_cue_id",
    }
    for scene in data["motion_plan"]["scenes"]:
        for element in scene["elements"]:
            for index, beat in enumerate(element["beats"]):
                expanded = {aliases[key]: value for key, value in beat.items()}
                if isinstance(expanded["curve"], str):
                    expanded["curve"] = {"kind": expanded["curve"], "parameters": []}
                element["beats"][index] = expanded
    return data


def provided_output_enabled(context: dict[str, Any]) -> bool:
    contract = context.get("generation_contract")
    if contract is None:
        return False
    if contract not in (LEGACY_GENERATION_CONTRACT, GENERATION_CONTRACT, STAGED_GENERATION_CONTRACT,
                        ASSET_INFORMED_GENERATION_CONTRACT):
        raise AuthError("MOTION_GENERATION_CONTRACT_UNKNOWN", 409)
    if supplied_direction(context) is None:
        raise AuthError("MOTION_VISUAL_DIRECTION_REQUIRED", 409)
    return True


def decode_provided_output(text: str, context: dict[str, Any]) -> DirectedHTMLMotionComposition:
    if not provided_output_enabled(context):
        raise AuthError("MOTION_GENERATION_CONTRACT_REQUIRED", 409)
    wire = generation_wire_model(context).model_validate_json(text)
    data = wire.model_dump(mode="json")
    if isinstance(wire, CompactProvidedDirectionOutput):
        data = expand_compact_output(data)
    return DirectedHTMLMotionComposition.model_validate({**data, "scene_direction": supplied_direction(context)})
