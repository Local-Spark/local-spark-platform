"""Bind declared intent/evidence to actual model attachments, without creative scoring."""

import hashlib
from typing import TYPE_CHECKING, Any

from app.schemas.motion_preparation import MotionPreparation
from app.services.auth import AuthError

if TYPE_CHECKING:
    from app.services.motion_protocols import MotionModelRequest

PREPARATION_RULES = {
    "version": "motion-preparation-v1",
    "rules": (
        "request.preparation conserva a mensagem do cliente e a origem/alcance de cada decisão. "
        "Somente requirement é requisito explícito; observation descreve avaliação, example é possibilidade "
        "e hypothesis é escolha a testar. Não universalize exemplos, não converta hipótese em exigência do cliente. "
        "A direção fornecida continua vinculante nesta execução; limitações devem ficar explícitas em concept "
        "e source_usage para a revisão do plano antes do código. Não declare aprovação artística. "
        "preparation_evidence vincula intenção declarada a anexos efetivamente enviados; observações são "
        "afirmações de quem preparou o pedido, não fatos verificados pelo servidor. Interprete a sequência "
        "e suas limitações, sem inventar escuta, fluidez ou faces ocultas. Preserve funções da base ou "
        "explique as substituições; contagem de elementos não comprova qualidade."
    ),
}


def preparation(context: dict[str, Any]) -> MotionPreparation | None:
    raw = context.get("request", {}).get("preparation")
    return MotionPreparation.model_validate(raw) if raw is not None else None


def additional_source_times(context: dict[str, Any], duration_ms: int) -> tuple[int, ...]:
    value = preparation(context)
    times = sorted({ms for item in value.evidence if item.kind == "source" for ms in item.at_ms}) if value else []
    if len(times) > 14 or any(ms >= duration_ms for ms in times):
        raise AuthError("MOTION_PREPARATION_SOURCE_LIMIT", 409)
    return tuple(times)


def evidence_bindings(job: "MotionModelRequest") -> list[dict[str, Any]]:
    value = preparation(job.context)
    if value is None:
        return []
    if job.context.get("preparation_contract") != PREPARATION_RULES:
        raise AuthError("MOTION_PREPARATION_CONTRACT_CHANGED", 409)
    bound = []
    for item in value.evidence:
        refs: list[dict[str, Any]] = []
        if item.kind in {"source", "baseline"}:
            frames = job.source_frames if item.kind == "source" else job.baseline_frames
            for ms in item.at_ms:
                frame = next((f for f in frames if f.ms == ms), None)
                if frame is None or hashlib.sha256(frame.png).hexdigest() != frame.sha256:
                    raise AuthError("MOTION_PREPARATION_EVIDENCE_MISSING", 409)
                refs.append({"at_ms": ms, "sha256": frame.sha256})
        elif item.kind == "reference":
            for identifier in item.reference_ids:
                image = next((f for f in job.reference_images if f.id == identifier), None)
                if image is None or hashlib.sha256(image.data).hexdigest() != image.sha256:
                    raise AuthError("MOTION_PREPARATION_EVIDENCE_MISSING", 409)
                refs.append({"reference_id": identifier, "sha256": image.sha256})
        else:
            asset = next((a for a in job.assets if a.id == item.asset_id), None)
            preview = next((p for key, p in job.asset_previews if key == item.asset_id), None)
            if asset is None or preview is None or hashlib.sha256(asset.data).hexdigest() != asset.sha256:
                raise AuthError("MOTION_PREPARATION_EVIDENCE_MISSING", 409)
            refs.append({"asset_id": asset.id, "sha256": asset.sha256, "preview_sha256": preview.sha256})
        bound.append({**item.model_dump(mode="json"), "attachments": refs})
    return bound
