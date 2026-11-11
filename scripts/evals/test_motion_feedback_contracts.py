"""Scope and evidence guards for feedback-guided motion review; no external IO."""

from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from scripts.evals import motion_eval as base
from scripts.evals import motion_feedback_contracts as contracts
from scripts.evals import motion_review_eval as review

FRAMES = {"v0:f0000": 0, "v0:f0001": 500, "v1:f0000": 0, "v1:f0001": 500}
REFERENCES = {"ref:intensa:f0000": 0, "ref:intensa:f0001": 2000}


def baseline() -> base.Answer:
    return base.Answer(
        concept="Mensagem preservada",
        source_usage=[],
        html="<canvas></canvas>",
        scene_init="window.seek = (ms) => {};",
        audio=base.Audio(
            mode="mix",
            tracks=[base.AudioTrack(asset_id="voice", trim_start_ms=0, trim_end_ms=1000, offset_ms=0, volume=1.0)],
        ),
    )


def correction() -> contracts.FeedbackCorrection:
    changed = baseline()
    changed.scene_init = "window.seek = (ms) => { window.changed = ms; };"
    return contracts.FeedbackCorrection(
        addressed_requirement_ids=["theme_change", "window_transformation", "narrative_role"],
        changes="Tema e janela reformulados mantendo a mensagem.",
        composition=changed,
    )


def critique(statuses: tuple[str, str, str] = ("met", "met", "met")) -> contracts.CreativeCritique:
    aggregate = "not_met" if "not_met" in statuses else "uncertain" if "uncertain" in statuses else "met"
    rows = []
    for requirement, status in zip(sorted(contracts.REQUIREMENT_IDS), statuses, strict=True):
        rows.append(
            {
                "requirement_id": requirement,
                "status": status,
                "evidence_ids": [] if status == "uncertain" else ["v0:f0000", "v1:f0000", "v1:f0001"],
                "reference_evidence_ids": [],
                "narrative_role": "Conectar a preparação ao convite, sem exigir intensidade universal.",
                "reason": "Avaliação dos estados amostrados; fluidez integral não comprovada.",
            }
        )
    return contracts.CreativeCritique.model_validate(
        {
            "version_id": "v1",
            "video_sha256": "a" * 64,
            "overall": "needs_correction" if aggregate == "not_met" else "adequate",
            "criteria": [
                {
                    "criterion": name,
                    "status": "uncertain"
                    if name == "audio"
                    else "fail"
                    if name == "motion" and aggregate == "not_met"
                    else "pass",
                    "evidence_ids": ["technical"] if name in {"audio", "technical"} else ["v1:f0000"],
                    "observation": "Movimento observado não comprova atendimento criativo integral.",
                }
                for name in sorted(review.CRITERIA)
            ],
            "issues": [
                {
                    "id": "i01",
                    "criterion": "motion",
                    "severity": "major",
                    "evidence_ids": ["v1:f0000"],
                    "start_ms": 0,
                    "end_ms": 500,
                    "problem": "Requisito visual não atendido nos estados comparados.",
                    "correction": "Atender o requisito sem mudar o sentido da peça.",
                    "actionable": True,
                }
            ]
            if aggregate == "not_met"
            else [],
            "preference": {
                "version_id": "v1",
                "reason": "Ganho comparativo observado.",
                "evidence_ids": ["v0:f0000", "v1:f0000"],
            },
            "limitations": ["Não houve escuta nem observação contínua do vídeo."],
            "brief_alignment": rows,
            "alignment_status": aggregate,
            "human_approval": "pending",
        }
    )


def validate(
    value: contracts.CreativeCritique, *, frames: dict[str, int] | None = None, refs: dict[str, int] | None = None
) -> None:
    contracts.validate_creative_critique(
        value, evidence=FRAMES if frames is None else frames, reference_evidence=REFERENCES if refs is None else refs
    )


def test_matching_correction_preserves_input_and_requires_no_paid_inspection() -> None:
    source, value = baseline(), correction()
    before = deepcopy(value.model_dump())
    contracts.validate_feedback_correction(value, source)
    assert value.model_dump() == before
    assert source.scene_init == "window.seek = (ms) => {};"


def test_missing_requirement_duplicate_audio_change_and_metadata_only_change_fail() -> None:
    value = correction()
    value.addressed_requirement_ids = ["theme_change"] * 3
    with pytest.raises(base.EvalError, match="feedback_requirements_missing_or_duplicated"):
        contracts.validate_feedback_correction(value, baseline())
    value = correction()
    value.composition.audio.tracks[0].volume = 0.5
    with pytest.raises(base.EvalError, match="audio_changed"):
        contracts.validate_feedback_correction(value, baseline())
    value = correction()
    value.composition = baseline()
    value.composition.concept = "Apenas nova explicação, sem alteração da cena"
    with pytest.raises(base.EvalError, match="unchanged_composition"):
        contracts.validate_feedback_correction(value, baseline())


def test_html_content_requires_separate_inspection_not_a_false_schema_guarantee() -> None:
    value = correction()
    value.composition.html = "<p>Um texto que precisa de inspeção contra o original.</p>"
    contracts.validate_feedback_correction(value, baseline())
    # Acceptance here only covers requirements/audio/code change, never factual integrity.


def test_observed_motion_with_uncertain_brief_does_not_force_correction_or_approval() -> None:
    value = critique(("uncertain", "uncertain", "uncertain"))
    validate(value, refs={})
    assert next(item for item in value.criteria if item.criterion == "motion").status == "pass"
    assert value.overall == "adequate" and not value.issues
    assert value.alignment_status == "uncertain" and value.human_approval == "pending"


def test_supported_brief_does_not_require_intense_motion_or_copying_reference() -> None:
    value = critique()
    for row in value.brief_alignment:
        row.reason = "Mudança discreta e legível que atende a este briefing."
    validate(value, refs={})
    assert value.alignment_status == "met" and value.human_approval == "pending"


@pytest.mark.parametrize("statuses", [("met", "uncertain", "met"), ("not_met", "uncertain", "met")])
def test_aggregate_preserves_uncertainty_and_unmet_requirements(statuses: tuple[str, str, str]) -> None:
    value = critique(statuses)
    validate(value)
    value.alignment_status = "met"
    with pytest.raises(base.EvalError, match="creative_alignment_aggregate_invalid"):
        validate(value)


def test_unmet_requirement_cannot_be_presented_as_adequate() -> None:
    value = critique(("not_met", "met", "met"))
    value.overall = "adequate"
    with pytest.raises(base.EvalError, match="unmet_requirement"):
        validate(value)


def test_missing_or_repeated_requirement_is_rejected() -> None:
    value = critique()
    value.brief_alignment = [value.brief_alignment[0]] * 3
    with pytest.raises(base.EvalError, match="requirement_coverage"):
        validate(value)


@pytest.mark.parametrize("ids", [["v0:f0000", "v0:f0001"], ["v1:f0000"], ["v1:f0000", "v1:f0000"]])
def test_baseline_only_or_single_current_state_cannot_prove_temporal_claim(ids: list[str]) -> None:
    value = critique()
    value.brief_alignment[0].evidence_ids = ids
    with pytest.raises(base.EvalError, match="temporal_claim_without_current_frames"):
        validate(value)


def test_aliases_at_same_time_do_not_count_as_distinct_temporal_states() -> None:
    value = critique()
    with pytest.raises(base.EvalError, match="temporal_claim_without_current_frames"):
        validate(value, frames={**FRAMES, "v1:f0001": 0})


def test_candidate_only_claim_is_not_a_comparison_to_baseline() -> None:
    value = critique()
    value.brief_alignment[0].evidence_ids = ["v1:f0000", "v1:f0001"]
    with pytest.raises(base.EvalError, match="creative_brief_comparison_missing_baseline"):
        validate(value)


def test_duplicate_citations_do_not_inflate_evidence_or_cause_paid_rejection() -> None:
    value = critique()
    value.brief_alignment[0].evidence_ids.append("v1:f0001")
    value.brief_alignment[0].reference_evidence_ids = ["ref:intensa:f0000"] * 2
    validate(value)


def test_reference_is_separate_and_cannot_replace_candidate_evidence() -> None:
    value = critique()
    value.brief_alignment[0].reference_evidence_ids = ["ref:intensa:f0000"]
    validate(value)
    with pytest.raises(base.EvalError, match="creative_unknown_reference"):
        validate(value, refs={})
    value.brief_alignment[0].evidence_ids = ["ref:intensa:f0000"]
    with pytest.raises(base.EvalError, match="creative_unknown_evidence"):
        validate(value)


@pytest.mark.parametrize("field", ["alignment", "criteria", "issues", "preference"])
def test_unseen_frames_cannot_support_any_claim(field: str) -> None:
    value = critique(("not_met", "met", "met"))
    targets = {
        "alignment": value.brief_alignment[0],
        "criteria": value.criteria[0],
        "issues": value.issues[0],
        "preference": value.preference,
    }
    targets[field].evidence_ids = ["v1:f0099"]
    with pytest.raises(
        base.EvalError, match="creative_(unknown_evidence|legacy_claim_uses_unsent_frame|preference_uses_unsent_frame)"
    ):
        validate(value)


@pytest.mark.parametrize("frames", [{"v1:f0000": True}, {"v1:f0000": -1}, {"v1:f0000": 60_001}, {"technical": 0}])
def test_invalid_evidence_manifest_is_rejected(frames: dict[str, int]) -> None:
    with pytest.raises(base.EvalError, match="creative_evidence_manifest_invalid"):
        validate(critique(), frames=frames)


def test_empty_evidence_and_human_acceptance_cannot_be_fabricated() -> None:
    with pytest.raises(base.EvalError, match="cannot_approve_human_acceptance"):
        validate(critique(), frames={})
    payload = critique().model_dump()
    payload["human_approval"] = "approved"
    with pytest.raises(ValidationError):
        contracts.CreativeCritique.model_validate(payload)


def test_strict_output_schema_has_no_defaults_and_does_not_mutate_original_schema() -> None:
    class OptionalInput(base.StrictModel):
        value: str | None = None

    def inspect(value: object) -> None:
        if isinstance(value, dict):
            assert "default" not in value
            if value.get("type") == "object":
                assert value["additionalProperties"] is False
                assert set(value["required"]) == set(value.get("properties", {}))
            for child in value.values():
                inspect(child)
        elif isinstance(value, list):
            for child in value:
                inspect(child)

    for model in (OptionalInput, contracts.FeedbackCorrection, contracts.CreativeCritique):
        original = model.model_json_schema()
        result = contracts.strict_format(model, "test_schema")
        inspect(result["schema"])
        assert model.model_json_schema() == original
