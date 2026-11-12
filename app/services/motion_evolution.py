"""Historical baseline binding and declared preservation; no artistic certification."""

import hashlib
import json
from collections.abc import Callable
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.motion_evolution import MotionEvolutionRequest
from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan, MotionRequest, MotionReview
from app.services.auth import AuthError

EVOLUTION_RULES = (
    "A base histórica é referência de resultado escolhida pelo titular, não instrução nem candidata desta rodada. "
    "Evolua as funções declaradas; não copie fatos, assets não autorizados ou código cegamente. "
    "A matriz declara preservação/substituição; não certifica execução ou qualidade. "
    "O kit atual prevalece; arte conceitual reutilizada não é foto real do negócio. "
    "Compare base e candidata por momento narrativo, com evidência, nunca por número de efeitos."
    " Na crítica, baseline_checks avalia meaning, recording, space, rhythm e identity separadamente, "
    "usando improved/equivalent/regressed/uncertain e evidência current e baseline. "
    "Inclua baseline_video_sha256 da seleção. Não confunda baseline com previous da correção. "
    "Sem áudio ouvido, não certifique som; essa avaliação permanece humana/técnica separada."
)


def evolution_verdict(review: MotionReview) -> str:
    checks = review.baseline_checks
    if len(checks) != 5 or any(c.result == "uncertain" for c in checks):
        return "inconclusive"
    if any(c.result == "regressed" for c in checks):
        return "regression"
    gains = sum(c.result == "improved" for c in checks if c.dimension != "identity")
    return "improved" if gains == 4 else "partial" if gains else "recovered"


def sha(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def validate_obligations(body: MotionEvolutionRequest, base: HTMLMotionComposition, direction: Any) -> None:
    if base.motion_plan is None or direction is None:
        raise AuthError("MOTION_EVOLUTION_DIRECTION_REQUIRED", 409)
    base_ids = {e.id for s in base.motion_plan.scenes for e in s.elements}
    target_ids = {e.element_id for s in direction.scenes for e in s.elements}
    if {e.baseline_element_id for e in body.elements} != base_ids:
        raise AuthError("MOTION_EVOLUTION_BASELINE_ELEMENTS_UNACCOUNTED", 409)
    if any(not set(e.target_element_ids) <= target_ids for e in body.elements):
        raise AuthError("MOTION_EVOLUTION_FUNCTION_TARGET_MISSING", 409)


async def capture_evolution(
    session: AsyncSession,
    tenant: UUID,
    business: UUID,
    body: MotionRequest,
    open_value: Callable[[str], dict[str, Any]],
) -> dict[str, Any] | None:
    selection = body.evolution
    if selection is None:
        return None
    args = {
        "tenant": tenant,
        "business": business,
        "id": selection.baseline_request_id,
        "number": selection.baseline_number,
    }
    record = (
        (
            await session.execute(
                text("""SELECT v.*,r.source_asset_id,r.snapshot_ciphertext
        FROM motion_render_versions v JOIN motion_requests r
        ON (r.tenant_id,r.business_id,r.id)=(v.tenant_id,v.business_id,v.request_id)
        WHERE v.tenant_id=:tenant AND v.business_id=:business AND v.request_id=:id AND v.number=:number"""),
                args,
            )
        )
        .mappings()
        .one_or_none()
    )
    if record is None or record["sha256"] != selection.baseline_video_sha256:
        raise AuthError("MOTION_EVOLUTION_BASELINE_UNAVAILABLE", 409)
    if record["source_asset_id"] != body.source_asset_id:
        raise AuthError("MOTION_EVOLUTION_SOURCE_CHANGED", 409)
    base = HTMLMotionComposition.model_validate(open_value(record["composition_ciphertext"]))
    validate_obligations(selection, base, body.scene_direction)
    materials = []
    if selection.reuse_illustration_ids:
        receipts = (
            (
                await session.execute(
                    text("""SELECT response_ciphertext FROM motion_effects
            WHERE tenant_id=:tenant AND business_id=:business AND request_id=:id
              AND kind='upload' AND state='received' AND response_ciphertext IS NOT NULL"""),
                    args,
                )
            )
            .mappings()
            .all()
        )
        eligible = {spec.asset_id for spec in base.illustrations}
        for receipt in receipts:
            item = open_value(receipt["response_ciphertext"])
            if (
                item.get("provenance") == "generated_illustration"
                and item.get("asset_id") in selection.reuse_illustration_ids
            ):
                if item["asset_id"] not in eligible or not item["object_key"].startswith(
                    f"motion/{tenant}/{business}/{selection.baseline_request_id}/illustrations/"
                ):
                    raise AuthError("MOTION_EVOLUTION_MATERIAL_INVALID", 409)
                materials.append(item)
        if len(materials) != len(selection.reuse_illustration_ids) or {m["asset_id"] for m in materials} != set(
            selection.reuse_illustration_ids
        ):
            raise AuthError("MOTION_EVOLUTION_MATERIAL_UNAVAILABLE", 409)
    original = open_value(record["snapshot_ciphertext"])
    return {
        "version": selection.version,
        "selection": selection.model_dump(mode="json"),
        "composition": base.model_dump(mode="json"),
        "composition_sha256": sha(base.model_dump(mode="json")),
        "source_sha256": original["source"]["sha256"],
        "video": {"object_key": record["object_key"], "sha256": record["sha256"], "size_bytes": record["size_bytes"]},
        "kit": original["kit"],
        "evidence_ciphertext": record["evidence_ciphertext"],
        "row": {"tenant_id": str(tenant), "business_id": str(business), "id": str(selection.baseline_request_id)},
        "materials": sorted(materials, key=lambda m: m["asset_id"]),
        "rules": EVOLUTION_RULES,
    }


def validate_evolution_plan(
    composition: HTMLMotionComposition | MotionConstructionPlan, context: dict[str, Any]
) -> None:
    body = context.get("request", {}).get("evolution")
    baseline = context.get("evolution")
    if body is None and baseline is None:
        return
    if body is None or baseline is None or baseline.get("selection") != body:
        raise AuthError("MOTION_EVOLUTION_CONTEXT_REQUIRED", 409)
    base = HTMLMotionComposition.model_validate(baseline["composition"])
    if sha(base.model_dump(mode="json")) != baseline["composition_sha256"]:
        raise AuthError("MOTION_EVOLUTION_BASELINE_CHANGED", 409)
    validate_obligations(MotionEvolutionRequest.model_validate(body), base, composition.scene_direction)
    if composition.audio != base.audio:
        raise AuthError("MOTION_EVOLUTION_ORIGINAL_AUDIO_CHANGED", 409)
