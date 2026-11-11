"""Pure contracts for a private, feedback-guided creative comparison.

Observed motion, compliance with the updated brief, and human acceptance are
different claims. These contracts do not certify free-form HTML content or
perceptual motion/audio quality.
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import Field

from scripts.evals import motion_eval as base
from scripts.evals import motion_review_eval as review

RequirementId = Literal["theme_change", "window_transformation", "narrative_role"]
AlignmentStatus = Literal["met", "not_met", "uncertain"]
REQUIREMENT_IDS = frozenset({"theme_change", "window_transformation", "narrative_role"})
_FRAME = re.compile(r"^v[0-9]+:f[0-9]{4}$")
_REFERENCE_FRAME = re.compile(r"^ref:[a-z][a-z0-9-]{0,50}:f[0-9]{4}$")


class FeedbackCorrection(base.StrictModel):
    addressed_requirement_ids: list[RequirementId] = Field(min_length=3, max_length=3)
    changes: str = Field(min_length=1, max_length=3000)
    composition: base.Answer


class BriefAlignment(base.StrictModel):
    requirement_id: RequirementId
    status: AlignmentStatus
    evidence_ids: list[str] = Field(max_length=30)
    reference_evidence_ids: list[str] = Field(max_length=12)
    narrative_role: str = Field(min_length=1, max_length=2000)
    reason: str = Field(min_length=1, max_length=2000)


class CreativeCritique(review.Critique):
    brief_alignment: list[BriefAlignment] = Field(min_length=3, max_length=3)
    alignment_status: AlignmentStatus
    human_approval: Literal["pending"]


def strict_format(model: type[base.StrictModel], name: str) -> dict[str, Any]:
    """Close every object and require every property without default annotations."""
    result = review.strict_format(model, name)

    def strip_defaults(value: Any) -> None:
        if isinstance(value, dict):
            value.pop("default", None)
            for child in value.values():
                strip_defaults(child)
        elif isinstance(value, list):
            for child in value:
                strip_defaults(child)

    strip_defaults(result)
    return result


def validate_feedback_correction(correction: FeedbackCorrection, baseline: base.Answer) -> None:
    ids = correction.addressed_requirement_ids
    if len(ids) != len(REQUIREMENT_IDS) or set(ids) != REQUIREMENT_IDS:
        raise base.EvalError("feedback_requirements_missing_or_duplicated")
    if correction.composition.audio.model_dump(mode="json") != baseline.audio.model_dump(mode="json"):
        raise base.EvalError("audio_changed_in_visual_experiment")
    if correction.composition.html == baseline.html and correction.composition.scene_init == baseline.scene_init:
        raise base.EvalError("unchanged_composition")
    # Text, facts, licensing notices and asset use still need code/render review.
    # Comparing declarations in a free-form scene is not proof of these invariants.


def _validate_evidence_map(evidence: dict[str, int], pattern: re.Pattern[str]) -> None:
    if any(
        not pattern.fullmatch(name) or type(at_ms) is not int or not 0 <= at_ms <= 60_000
        for name, at_ms in evidence.items()
    ):
        raise base.EvalError("creative_evidence_manifest_invalid")


def validate_creative_critique(
    critique: CreativeCritique,
    *,
    evidence: dict[str, int],
    reference_evidence: dict[str, int],
) -> None:
    """Validate additional brief claims after the legacy video/critique binding.

    The caller separately runs ``review.validate_critique`` with verified local
    video evidence. These maps carry the same frame IDs and explicitly labelled
    reference samples. Times may be requested seeks; they are not promoted to
    measured presentation times by this validation.
    """
    _validate_evidence_map(evidence, _FRAME)
    _validate_evidence_map(reference_evidence, _REFERENCE_FRAME)
    if not evidence or critique.human_approval != "pending":
        raise base.EvalError("creative_review_cannot_approve_human_acceptance")
    if any(item not in evidence for item in critique.preference.evidence_ids):
        raise base.EvalError("creative_preference_uses_unsent_frame")
    checks: list[review.Assessment | review.Issue] = [*critique.criteria, *critique.issues]
    for check in checks:
        if any(item not in evidence and item != "technical" for item in check.evidence_ids):
            raise base.EvalError("creative_legacy_claim_uses_unsent_frame")
    rows = critique.brief_alignment
    if len(rows) != len(REQUIREMENT_IDS) or {row.requirement_id for row in rows} != REQUIREMENT_IDS:
        raise base.EvalError("creative_requirement_coverage_invalid")
    for row in rows:
        if any(item not in evidence for item in row.evidence_ids):
            raise base.EvalError("creative_unknown_evidence")
        if any(item not in reference_evidence for item in row.reference_evidence_ids):
            raise base.EvalError("creative_unknown_reference")
        current_times = {evidence[item] for item in row.evidence_ids if item.startswith(critique.version_id + ":")}
        if row.status != "uncertain" and len(current_times) < 2:
            raise base.EvalError("creative_temporal_claim_without_current_frames")
        if row.status != "uncertain" and not any(item.startswith("v0:") for item in row.evidence_ids):
            raise base.EvalError("creative_brief_comparison_missing_baseline")
    statuses = {row.status for row in rows}
    expected = "not_met" if "not_met" in statuses else "uncertain" if "uncertain" in statuses else "met"
    if critique.alignment_status != expected:
        raise base.EvalError("creative_alignment_aggregate_invalid")
    if expected == "not_met" and critique.overall == "adequate":
        raise base.EvalError("creative_unmet_requirement_cannot_be_adequate")
