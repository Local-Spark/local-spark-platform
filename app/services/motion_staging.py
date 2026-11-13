"""Planning data consumed by validation, implementation and temporal evidence selection."""

from typing import TYPE_CHECKING, Any

from app.services.auth import AuthError

if TYPE_CHECKING:
    from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan
    from app.services.motion_protocols import MotionModelRequest

STAGING_CONTRACT = {
    "version": "motion-staging-v1",
    "rules": (
        "Planeje a peça inteira em staging.moments, um por cena, mesmos IDs/ordem. contribution diz qual "
        "informação/sensação nova a imagem desenvolve; development descreve a ação e sua consequência; "
        "sustained_value explica o que sustenta uma permanência, sem exigir movimento contínuo. "
        "Escolha protagonista existente e media_relation (recording_dominant, integrated ou graphic). "
        "material_element_ids enumera exatamente os elementos imagem/vídeo daquela cena. "
        "inspect_start_ms/inspect_end_ms delimitam a ação ou permanência de maior risco dentro da cena. "
        "Para cada passagem, transition liga next_scene_id, elementos existentes das duas cenas e intervalo "
        "que cruza sua fronteira. Descreva origin/crossing/destination como estados relacionados; última "
        "cena usa null. Esses intervalos serão renderizados e entregues à crítica. "
        "Se faltar material indispensável, liste unavailable_materials; implementação será bloqueada para "
        "revisar direção/obtenção, nunca substitua silenciosamente por desenho simples. Lista vazia exige "
        "direção realizável com os materiais fornecidos ou ilustrações explicitamente habilitadas/declaradas. "
        "Não existem vídeo gerado, tomadas novas, reconstrução 3D ou segmentação automática de pessoas. "
        "Uma fonte pode participar de tipografia, oclusão e camadas, preservando tempo/voz/ação relevante. "
        "Não imponha número de cenas, efeitos ou cortes. Conteúdo declarado não comprova qualidade: "
        "a crítica deve observar a peça e distinguir direção/material de implementação."
        " Na crítica, cada issue inclui repair_kind: implementation para defeito local corrigível sem mudar "
        "o plano; direction/material para insuficiência da direção ou material; uncertain sem evidência. "
        "Somente implementation pode ser actionable. Problema major/blocking de direction/material exige "
        "verdict reject: o fluxo preserva a candidata e encaminha revisão ao planejamento, sem remendar "
        "silenciosamente o plano aprovado. Omissões de inspeção impedem certificar cobertura integral."
    ),
}


def staging_enabled(context: dict[str, Any]) -> bool:
    contract = context.get("staging_contract")
    if contract is None:
        return False
    if contract != STAGING_CONTRACT:
        raise AuthError("MOTION_STAGING_CONTRACT_CHANGED", 409)
    return True


def validate_staging(artifact: "MotionConstructionPlan | HTMLMotionComposition", context: dict[str, Any]) -> None:
    enabled = staging_enabled(context)
    staging, plan = artifact.staging, artifact.motion_plan
    if not enabled:
        if staging is not None:
            raise AuthError("MOTION_STAGING_UNEXPECTED", 409)
        return
    if staging is None or plan is None:
        raise AuthError("MOTION_STAGING_REQUIRED", 409)
    if [m.scene_id for m in staging.moments] != [s.id for s in plan.scenes]:
        raise AuthError("MOTION_STAGING_SCENES_INVALID", 409)
    for index, (moment, scene) in enumerate(zip(staging.moments, plan.scenes, strict=True)):
        elements = {e.id: e for e in scene.elements}
        materials = {e.id for e in scene.elements if e.role in {"image", "video"}}
        if (
            moment.protagonist_id not in elements
            or len(set(moment.material_element_ids)) != len(moment.material_element_ids)
            or set(moment.material_element_ids) != materials
            or not scene.start_ms <= moment.inspect_start_ms < moment.inspect_end_ms <= scene.end_ms
            or (moment.media_relation != "graphic" and not any(e.role == "video" for e in scene.elements))
        ):
            raise AuthError("MOTION_STAGING_MOMENT_INVALID", 409)
        transition = moment.transition
        if index == len(plan.scenes) - 1:
            if transition is not None:
                raise AuthError("MOTION_STAGING_TRANSITION_INVALID", 409)
            continue
        following = plan.scenes[index + 1]
        targets = set(elements) | {e.id for e in following.elements}
        if (
            transition is None
            or transition.next_scene_id != following.id
            or len(set(transition.element_ids)) != len(transition.element_ids)
            or not set(transition.element_ids) <= targets
            or not scene.start_ms <= transition.start_ms < transition.end_ms <= following.end_ms
            # An overlapping handoff may start exactly when the incoming scene starts.
            # It must then cover the overlap through the outgoing scene's end.
            or not (
                transition.start_ms < following.start_ms < transition.end_ms
                or transition.start_ms <= following.start_ms < scene.end_ms <= transition.end_ms
            )
        ):
            raise AuthError("MOTION_STAGING_TRANSITION_INVALID", 409)


def require_staging_materials(artifact: "MotionConstructionPlan", context: dict[str, Any]) -> None:
    validate_staging(artifact, context)
    if artifact.staging is not None and artifact.staging.unavailable_materials:
        raise AuthError("MOTION_STAGING_REQUIRES_PLAN_REVISION", 409)


def staging_input(job: "MotionModelRequest") -> dict[str, Any] | None:
    if not staging_enabled(job.context):
        return None
    return {
        "version": "motion-material-inventory-v1",
        "assets": [{"asset_id": a.id, "mime_type": a.mime_type, "sha256": a.sha256} for a in job.assets],
        "source_samples": [{"at_ms": f.ms, "sha256": f.sha256} for f in job.source_frames],
        "image_generation": job.context.get("illustration_generation"),
        "limits": (
            "Inventário de bytes disponíveis, não análise semântica automática. Observe os anexos e descreva "
            "somente ações/detalhes visíveis; quadros esparsos não provam continuidade. Ilustrações habilitadas "
            "são conceituais, não novas fotos documentais do negócio. Zoom não cria outra tomada. "
            "Campos de staging serão preservados no código e usados para escolher evidência da revisão."
        ),
    }
