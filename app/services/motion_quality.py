"""Product quality obligations independent of a customer's previously generated pieces."""

from typing import TYPE_CHECKING, Any

from app.services.auth import AuthError

if TYPE_CHECKING:
    from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan
    from app.services.motion_protocols import MotionModelRequest

LEGACY_QUALITY_CONTRACT: dict[str, Any] = {
    "version": "motion-production-quality-v1",
    "requirements": [
        {
            "id": "meaning",
            "expectation": "Desenvolver a mensagem com ações visuais pertinentes e consequências claras.",
        },
        {"id": "recording", "expectation": "Integrar a gravação, protegendo sua ação relevante, voz e tempo original."},
        {
            "id": "space",
            "expectation": "Organizar hierarquia, escala e relações coerentes entre os elementos escolhidos.",
        },
        {
            "id": "continuity",
            "expectation": "Conectar momentos e transferir atenção sem lacunas narrativas involuntárias.",
        },
        {
            "id": "rhythm",
            "expectation": "Justificar preparação, acento, leitura e repouso conforme a mensagem e material.",
        },
        {
            "id": "identity",
            "expectation": "Aplicar kit/fatos vigentes e distinguir conceito visual de registro documental.",
        },
        {
            "id": "sound",
            "expectation": "Preservar a voz; justificar complementos ou omissão e declarar escuta pendente.",
        },
    ],
    "rules": (
        "Este é o piso do produto para uma nova peça, independente de peças anteriores do cliente. "
        "Para cada requisito, declare em audiovisual.functions function_id, disposition=satisfy_requirement, "
        "IDs dos elementos escolhidos, justificativa, verificação e limitações. A mesma composição pode atender "
        "vários requisitos; não há quantidade prescrita de cenas, elementos, objetos ou efeitos. "
        "Escolha representações conforme a mensagem, contexto e materiais desta solicitação. "
        "Espaço não exige objeto fotográfico/3D, som não exige efeito adicional e continuidade não exige "
        "ocultar e retornar à gravação. Não importar layouts, fatos, mídia ou restrições de ensaios anteriores. "
        "Cobertura no plano registra intenção; código, contagem de elementos e declaração do modelo não "
        "comprovam qualidade. Revisão do plano e fidelidade ao código precedem qualquer render. "
        "Estados, movimento contínuo, voz e som precisam de avaliação posterior autorizada. "
        "A crítica existente aplica seus critérios e evidências à própria candidata. Comparações com "
        "ensaios de referência pertencem à avaliação do produto, fora do contexto desta geração."
    ),
}

QUALITY_CONTRACT: dict[str, Any] = {
    **LEGACY_QUALITY_CONTRACT,
    "version": "motion-production-quality-v2",
    "requirements": [
        *LEGACY_QUALITY_CONTRACT["requirements"],
        {
            "id": "visual_development",
            "expectation": (
                "Desenvolver relações entre gesto, representação, texto e espaço com consequência narrativa. "
                "Explicitar estados anteriores/posteriores e como a interação escolhida muda a leitura da mensagem. "
                "Justificar a evolução da composição ou sua permanência; reposicionar a mesma janela com "
                "títulos e barras não comprova, por si só, a elaboração buscada."
            ),
        },
    ],
    "rules": LEGACY_QUALITY_CONTRACT["rules"]
    + (
        " Neste perfil, desenvolvimento visual é responsabilidade do produto mesmo quando o cliente pede "
        "apenas um Reel; não espere que ele solicite tecnicamente motion elaborado. As condicionais de "
        "elaboração nas orientações gerais não dispensam este requisito. Antes de fechar a direção, "
        "considere outra maneira de desenvolver a mensagem e explique em visual_development por que a "
        "solução escolhida transforma relações, além de trocar frases, escala ou posição da mesma janela. "
        "Tipografia pode ser protagonista; não proíba barras, estilo editorial ou repouso, nem imponha objeto, "
        "3D, tela cheia, alternância de vídeo ou quantidade de cenas. Vincule a justificativa a estados e "
        "elementos reais do plano; a revisão humana julga sua suficiência. "
        "No som, diferencie arquivo disponível, relato humano do arquivo isolado e avaliação futura do evento/"
        "mistura. planning_input explicita essas etapas: not_listened nas medições descreve o sistema, "
        "não apaga o relato humano vinculado. A falta de escuta da mistura futura, sozinha, não justifica "
        "omitir um candidato nem impede propô-lo com verificações pendentes. Pode-se optar por voz sozinha: "
        "explique a função narrativa dessa escolha ou a evidência concreta de inadequação/duplicação/ausência "
        "de ação. Não invente correspondência contínua a partir de quadros. Não crie ações para usar sons."
        " Uma ação dentro da gravação pode motivar um evento mesmo com a janela de vídeo imóvel "
        "(beat hold); hold descreve o layout, não certifica ausência de ação no conteúdo filmado. "
        "Declare o intervalo da ação dentro da duração da fonte e mantenha sincronismo/adequação pendentes "
        "de revisão; não mova a janela nem invente um grafismo só para habilitar o som."
    ),
}


def validate_quality_context(context: dict[str, Any]) -> bool:
    contract = context.get("quality_contract")
    if contract is None:
        return False
    if contract not in (LEGACY_QUALITY_CONTRACT, QUALITY_CONTRACT):
        raise AuthError("MOTION_QUALITY_CONTRACT_CHANGED", 409)
    if context.get("request", {}).get("evolution") is not None or context.get("evolution") is not None:
        raise AuthError("MOTION_QUALITY_HISTORICAL_CONTEXT_FORBIDDEN", 409)
    return True


def validate_quality_input(job: "MotionModelRequest") -> None:
    if not validate_quality_context(job.context):
        return
    if (
        job.baseline_frames
        or (job.kind == "generate" and (job.composition is not None or job.incumbent_composition is not None))
        or any(
            e.get("kind") == "baseline"
            for e in job.context.get("request", {}).get("preparation", {}).get("evidence", [])
        )
        or any(m.get("role") == "reused_illustration" for m in job.context.get("available_materials", []))
    ):
        raise AuthError("MOTION_QUALITY_HISTORICAL_CONTEXT_FORBIDDEN", 409)


def require_quality_readiness(context: dict[str, Any]) -> None:
    """Do not spend on a production plan with unresolved intake or missing speech."""
    if not validate_quality_context(context):
        return
    if context.get("request", {}).get("preparation", {}).get("unresolved"):
        raise AuthError("MOTION_PREPARATION_UNRESOLVED", 409)
    if context.get("source", {}).get("has_audio") and context.get("transcript") is None:
        raise AuthError("MOTION_QUALITY_SPEECH_REQUIRED", 409)


def validate_quality_plan(artifact: "MotionConstructionPlan | HTMLMotionComposition", context: dict[str, Any]) -> None:
    if not validate_quality_context(context):
        return
    design, plan = artifact.audiovisual, artifact.motion_plan
    if design is None or plan is None:
        raise AuthError("MOTION_QUALITY_COVERAGE_REQUIRED", 409)
    functions = design.functions
    required = {item["id"] for item in context["quality_contract"]["requirements"]}
    targets = {element.id for scene in plan.scenes for element in scene.elements}
    if (
        len(functions) != len(required)
        or {f.function_id for f in functions} != required
        or any(f.disposition != "satisfy_requirement" or not set(f.target_element_ids) <= targets for f in functions)
    ):
        raise AuthError("MOTION_QUALITY_COVERAGE_INVALID", 409)


def planning_input(context: dict[str, Any], bindings: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Expose planning stages and hash-bound human observations without inferring their meaning."""
    if not validate_quality_context(context) or context["quality_contract"] != QUALITY_CONTRACT:
        return None

    def reports(identifier: str, sha256: str) -> list[dict[str, Any]]:
        return [
            {key: item[key] for key in ("id", "observation", "intended_use", "limitations")}
            for item in bindings
            if item["kind"] == "audio" and item["asset_id"] == identifier and item["asset_sha256"] == sha256
        ]

    source = context["source"]
    return {
        "version": "motion-planning-input-v1",
        "visual_development": {
            "required_by": "product_quality_profile_not_client_technical_wording",
            "review": "Explain concrete before/after relationships; declared coverage is not artistic approval.",
        },
        "sound": {
            "source": {
                "asset_id": source["asset_id"],
                "sha256": source["sha256"],
                "human_file_evidence": reports(source["asset_id"], source["sha256"]),
            },
            "candidates": [
                {
                    "candidate_id": item["id"],
                    "asset_id": f"assets/sfx-{item['id']}.mp3",
                    "sha256": item["sha256"],
                    "file_status": "available_verified_by_loader_and_builder",
                    "human_file_evidence": reports(f"assets/sfx-{item['id']}.mp3", item["sha256"]),
                    "event_and_mix_status": "not_planned_or_listened_yet",
                }
                for item in context.get("sound_library", {}).get("items", [])
            ],
            "system_listening": False,
            "rules": (
                "Human observations concern the bound file only. Read their stated scope; do not infer approval "
                "of an event, trim, gain, timing or mix. Propose a motivated event or give a narrative/evidence "
                "reason for omission; pending future mix listening is not a standalone reason for omission. "
                "Keep event suitability, source duplication and voice intelligibility checks pending until "
                "the appropriate later review, without erasing the file-level human evidence."
            ),
        },
    }
