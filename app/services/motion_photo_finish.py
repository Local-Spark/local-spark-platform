"""S1–S3 supplement for new captures; v10 and its DOM guard remain immutable."""

import hashlib
import json
from pathlib import Path
from typing import Any

from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan
from app.services.auth import AuthError
from app.services.motion_photo_energy import _state, energetic

FINISH_PATH = Path(__file__).resolve().parents[1] / "assets/motion_photo/photo-finish-v1.js"
PHOTO_FINISH_CONTRACT = {
    "version": "motion-photo-finish-v1",
    "dom_guard_sha256": "b665ade55c2fbe656181f5f7e254df237d9743d8b7b1718b6a4258aeff508ca9",
    "rules": (
        "S1–S3 complementam intent v10/guarda v2, sem substituir crop v5 ou gates anteriores. "
        "S1: contain_blur é uma única exceção estruturada de no máximo 2000 ms, inclusive no miolo; "
        "cover exclusivo >=2/3 permanece obrigatório. Se crop inviável, escolha outra foto. "
        "Texto sobre cover usa scrim local, nunca faixa escura full-width + janela. "
        "S2: cada beat de foto/logo após handoffEnd precisa de velocidade >=0.01 scale/s ou "
        ">=0.5 ponto percentual/s de pan, estados canônicos lineares distintos até end. "
        "Na última cena ao menos um text tem enter/exit linear com estados canônicos, "
        "amplitude >=0.04 scale ou >=2 pontos percentuais e velocidade >=0.02 scale/s ou >=1 pp/s. "
        "Execute o transform no id do texto, visível durante a animação; não basta declará-lo. "
        "CTA mantém entrada aprovada e leitura >=1500 ms até end; não anime sua saída nessa janela. "
        "S3: quando há assets/logo.png no inventário, staging.photo_identity_reviews inspeciona "
        "cada foto selecionada: {asset_id, verdict:clean|third_party|uncertain, evidence}. "
        "Observe os previews: logo/watermark legível de terceiros (Belize, Mackbear, Red Bull etc.) "
        "exige third_party; dúvida exige uncertain. Só clean pode ser selecionado com logo do kit. "
        "Prefira outro material autorizado; se insuficiente, requires_plan_revision. Não apague nem "
        "redesenhe marcas. Não acrescente 'Imagens ilustrativas.' ao CTA por padrão; somente se pedido "
        "explicitamente pelo titular. A declaração não é OCR nem prova semântica dos pixels."
    ),
}


def finish_enabled(context: dict[str, Any]) -> bool:
    contract = context.get("photo_finish_contract")
    if contract is None:
        return False
    if contract != PHOTO_FINISH_CONTRACT:
        raise AuthError("MOTION_PHOTO_FINISH_CONTRACT_CHANGED", 409)
    return True


def typography_beats(artifact: HTMLMotionComposition | MotionConstructionPlan) -> list[dict[str, Any]]:
    assert artifact.motion_plan is not None
    return [
        {"id": e.id, "start": b.start_ms, "end": b.end_ms, "a": _state(b.start_state), "z": _state(b.end_state)}
        for e in artifact.motion_plan.scenes[-1].elements
        if e.role == "text"
        for b in e.beats
        if b.phase in {"enter", "exit"} and energetic(b.model_copy(update={"phase": "transform"}), stronger=True)
    ]


def validate_photo_finish(
    artifact: HTMLMotionComposition | MotionConstructionPlan,
    context: dict[str, Any],
    *,
    handoff_end: int,
    asset_ids: set[str],
) -> None:
    if not finish_enabled(context):
        return
    plan = artifact.motion_plan
    assert plan is not None
    for scene in plan.scenes:
        if scene.photo_layout and scene.photo_layout.mode == "contain_blur" and scene.end_ms - scene.start_ms > 2000:
            raise AuthError("MOTION_PHOTO_SHORT_EXCEPTION_REQUIRED", 409)
    final = plan.scenes[-1]
    for element in final.elements:
        if element.asset_id == "assets/logo.png" or (element.asset_id or "").startswith("assets/photo-"):
            if any(b.end_ms > handoff_end and not energetic(b) for b in element.beats):
                raise AuthError("MOTION_PHOTO_CLOSING_ENERGY_REQUIRED", 409)
    assert final.photo_closing is not None
    cta = next(e for e in final.elements if e.id == final.photo_closing.cta_element_id)
    if any(b.phase == "exit" and b.end_ms > handoff_end for b in cta.beats):
        raise AuthError("MOTION_PHOTO_CTA_WINDOW_INVALID", 409)
    if not typography_beats(artifact):
        raise AuthError("MOTION_PHOTO_TYPOGRAPHY_REQUIRED", 409)
    if "assets/logo.png" in asset_ids:
        selected = {
            e.asset_id for s in plan.scenes for e in s.elements if (e.asset_id or "").startswith("assets/photo-")
        }
        reviews = artifact.staging.photo_identity_reviews if artifact.staging else None
        if (
            reviews is None
            or len(reviews) != len(selected)
            or {r.asset_id for r in reviews} != selected
            or any(r.verdict != "clean" or not r.evidence.strip() for r in reviews)
        ):
            raise AuthError("MOTION_PHOTO_IDENTITY_REQUIRES_PLAN_REVISION", 409)


def finish_scene_init(composition: HTMLMotionComposition, context: dict[str, Any]) -> str:
    if not finish_enabled(context):
        return composition.scene_init
    source = FINISH_PATH.read_bytes()
    if hashlib.sha256(source).hexdigest() != PHOTO_FINISH_CONTRACT["dom_guard_sha256"]:
        raise AuthError("MOTION_PHOTO_FINISH_GUARD_CHANGED", 409)
    assert composition.motion_plan is not None
    payload = json.dumps(
        {
            "typography": typography_beats(composition),
            "scenes": [
                {"start": s.start_ms, "end": s.end_ms, "texts": [e.id for e in s.elements if e.role == "text"]}
                for s in composition.motion_plan.scenes
            ],
        }
    )
    return composition.scene_init + "\n;(" + source.decode() + ")(" + payload + ");"
