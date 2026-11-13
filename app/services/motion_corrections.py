"""Deterministic admission and raster comparison; no paid effects or artistic verdicts."""

import hashlib
import json
import re
from typing import Any

from app.adapters.motion_html_renderer import RenderedMotion
from app.schemas.motion_correction import MotionCorrectionRegion
from app.schemas.motion_production import HTMLMotionComposition, MotionIssue, MotionReview
from app.services.auth import AuthError

CORRECTION_POLICY = {
    "version": "motion-correction-v1",
    "plan_policy": "immutable",
    "comparison": "all-preencode-frames-exact-sha256",
    "margin_limit_ms": 1000,
    "rules": (
        "Cada issue major/blocking acionável inclui localization: scene_id, element_ids, start_ms, end_ms, "
        "margin_before_ms e margin_after_ms explícitos (0 quando dispensáveis, máximo 1000). "
        "Use tempos absolutos, intervalo central dentro da cena e contendo a evidência; margens dentro da fonte. "
        "correction descreve o resultado esperado. A correção trata somente o primeiro problema priorizado, "
        "sem trocar plano, direção, texto planejado, assets ou áudio. Fora do intervalo com margens, todos os "
        "quadros devem ser idênticos. Se exigir replanejamento ou mudança global, marque não acionável. "
        "Não alegue isolamento de elementos pelo código nem qualidade comprovada pelo hash."
    ),
}


def correction_enabled(context: dict[str, Any]) -> bool:
    policy = context.get("correction_contract")
    if policy is None:
        return False
    if policy != CORRECTION_POLICY:
        raise AuthError("MOTION_CORRECTION_CONTRACT_UNKNOWN", 409)
    return True


def fingerprint(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def review_diagnostics(diagnostics: dict[str, Any]) -> dict[str, Any]:
    """All-frame evidence stays durable locally, not repeated as model tokens."""
    result = {key: value for key, value in diagnostics.items() if key != "frame_fingerprints"}
    if "frame_fingerprints" in diagnostics:
        result["frame_fingerprints_sha256"] = fingerprint(diagnostics["frame_fingerprints"])
    return result


def validate_location(composition: HTMLMotionComposition, issue: MotionIssue) -> MotionCorrectionRegion:
    region = issue.localization
    plan = composition.motion_plan
    if region is None or plan is None:
        raise AuthError("MOTION_CORRECTION_LOCATION_REQUIRED", 409)
    scene = next((item for item in plan.scenes if item.id == region.scene_id), None)
    start, end = region.window
    if (
        scene is None
        or not scene.start_ms <= region.start_ms <= issue.at_ms < region.end_ms <= scene.end_ms
        or end > plan.duration_ms
        or not set(region.element_ids) <= {item.id for item in scene.elements}
        or (start == 0 and end >= plan.duration_ms)
    ):
        raise AuthError("MOTION_CORRECTION_LOCATION_INVALID", 409)
    return region


def correction_scope(composition: HTMLMotionComposition, review: MotionReview) -> dict[str, Any]:
    index, issue = next(
        (i, item) for i, item in enumerate(review.issues) if item.actionable and item.severity in {"blocking", "major"}
    )
    region = validate_location(composition, issue)
    return {
        "version": "motion-correction-scope-v1",
        "issue_index": index,
        "region": region.model_dump(mode="json"),
        "expected_result": issue.correction,
        "evidence": {"at_ms": issue.at_ms, "sha256": issue.evidence_sha256},
        "base_composition_sha256": fingerprint(composition.model_dump(mode="json")),
        "deferred_issue_indices": [
            i for i, item in enumerate(review.issues) if i != index and item.actionable and item.severity != "minor"
        ],
    }


def validate_candidate(base: HTMLMotionComposition, candidate: HTMLMotionComposition) -> None:
    # This slice fixes implementation defects. Replanning is a separate explicit request.
    protected = {"html", "scene_init"}
    if base.model_dump(mode="json", exclude=protected) != candidate.model_dump(mode="json", exclude=protected):
        raise AuthError("MOTION_CORRECTION_PROTECTED_PLAN_CHANGED", 409)


def compare_frames(base: RenderedMotion, candidate: RenderedMotion, scope: dict[str, Any]) -> dict[str, Any]:
    """Exact comparison includes immediate neighbors; uncertainty rejects the candidate."""
    region = MotionCorrectionRegion.model_validate(scope["region"])
    a, b = base.diagnostics, candidate.diagnostics
    keys = ("executor_image", "fingerprint_environment", "width", "height", "fps", "duration_ms", "frame_count")
    if (
        any(a.get(key) is None or a.get(key) != b.get(key) for key in keys)
        or not re.fullmatch(r"(?:[a-zA-Z0-9./:_-]+@)?sha256:[a-f0-9]{64}", str(a.get("executor_image")))
        or not re.fullmatch(r"[a-f0-9]{64}", str(a.get("fingerprint_environment")))
        or a.get("fps") != 30
        or type(a.get("duration_ms")) is not int
    ):
        raise AuthError("MOTION_CORRECTION_ENVIRONMENT_CHANGED", 409)
    duration = a["duration_ms"]
    assert isinstance(duration, int)
    count = (duration * 30 + 999) // 1000
    left, right = a.get("frame_fingerprints"), b.get("frame_fingerprints")
    if (
        not 1 <= count <= 1800
        or a["frame_count"] != count
        or any(
            not isinstance(seq, list)
            or len(seq) != count
            or any(not isinstance(h, str) or re.fullmatch(r"[a-f0-9]{64}", h) is None for h in seq)
            for seq in (left, right)
        )
    ):
        raise AuthError("MOTION_CORRECTION_EVIDENCE_INCOMPLETE", 409)
    start, end = region.window
    protected = [i for i in range(count) if not start * 30 <= i * 1000 < end * 30]
    if not protected or end > duration:
        raise AuthError("MOTION_CORRECTION_LOCATION_INVALID", 409)
    assert isinstance(left, list) and isinstance(right, list)
    changed = [i for i in range(count) if left[i] != right[i]]
    regressions = sorted(set(protected).intersection(changed))
    return {
        "version": "motion-correction-check-v1",
        "accepted": not regressions and bool(changed),
        "reason": (
            "outside_interval_changed" if regressions else "no_visible_change" if not changed else "bounded_change"
        ),
        "basis": "preencode-jpeg-sha256",
        "protected_frames": len(protected),
        "changed_frame_indices": changed,
        "regression_frame_indices": regressions,
        "base_frames_sha256": fingerprint(left),
        "candidate_frames_sha256": fingerprint(right),
        "scope_sha256": fingerprint(scope),
        "executor_image": a["executor_image"],
        "fingerprint_environment": a["fingerprint_environment"],
        "quality_validated": False,
    }
