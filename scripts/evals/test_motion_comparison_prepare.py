"""Comparison preparation binds the existing product payload without pretending execution."""

import json
from dataclasses import replace

import pytest

from app.tests.unit.test_motion_plan import planned
from scripts.evals import motion_comparison_prepare as compare
from scripts.evals import motion_external_export as export
from scripts.evals.test_motion_external_export import recorded_case  # noqa: F401


@pytest.fixture
def comparison_case(recorded_case, tmp_path):  # noqa: F811
    prior, source, direction, brief = recorded_case
    data = json.loads(prior.read_bytes())
    data.update(model="gpt-6.1-sol", max_output_tokens=54000)
    prior.write_bytes(export.pretty(data))
    job, provenance = export.prepare_case(prior, source, direction, brief, repertoire_id="business-reel-v2")
    video = tmp_path / "baseline.mp4"
    video.write_bytes(b"\x00\x00\x00\x20ftyp-synthetic-not-a-render")
    composition = tmp_path / "baseline-composition.json"
    composition.write_text(planned().model_dump_json())
    args = {
        "prior_payload": prior,
        "baseline_video": video,
        "baseline_sha256": export.sha(video.read_bytes()),
        "baseline_composition": composition,
    }
    return job, provenance, args


def test_product_package_is_exact_and_future_calls_are_pending_without_credentials(comparison_case, tmp_path):
    job, provenance, args = comparison_case
    files = compare.comparison_files(job, provenance, **args)
    assert files["generation-request.json"] == export.assemble_files(job, provenance)["generation-request.json"]
    assert b"must-not-appear-in-export" not in b"".join(files.values())
    assert files["baseline/video.mp4"] == args["baseline_video"].read_bytes()
    report = json.loads(files["comparison.json"])
    assert all(report["preserved"].values()) and not report["execution_ready"]
    assert report["source_samples"] == 6 and report["finish_references"] == 5
    stages = json.loads(files["pipeline.json"])
    assert stages[0]["exact_payload"] == "generation-request.json"
    assert all(stage["exact_payload"] is None for stage in stages[1:])
    assert not json.loads(files["manifest.json"])["paid_calls_authorized"]
    assert all(row["verdict"] == "not_evaluated" for row in json.loads(files["rubric.json"])["dimensions"])
    assert "localization" in str(json.loads(files["contracts/review.json"]))
    assert json.loads(files["budget-proposal.json"])["maximum_reserves_usd_micros"] == 6_250_000
    folder = tmp_path / "comparison"
    export.write_export(folder, files)
    export.verify_export(folder)
    (folder / "baseline/video.mp4").write_bytes(b"changed")
    with pytest.raises(ValueError, match="FILE_CHANGED"):
        export.verify_export(folder)


def test_changed_baseline_context_video_or_unprepared_sound_stops_export(comparison_case):
    job, provenance, args = comparison_case
    with pytest.raises(ValueError, match="BASELINE_CHANGED"):
        compare.comparison_files(job, provenance, **{**args, "baseline_sha256": "0" * 64})
    for key in ("kit", "transcript", "authorized_audio", "source"):
        changed = replace(job, context={**job.context, key: {"unexpected": True}})
        with pytest.raises(ValueError, match="BASELINE_CONTEXT_CHANGED"):
            compare.comparison_files(changed, provenance, **args)
    with pytest.raises(ValueError, match="AUDIO_MATERIALS"):
        compare.comparison_files(
            replace(job, context={**job.context, "authorized_soundtrack": {"mode": "mix"}}), provenance, **args
        )
    with pytest.raises(ValueError, match="CURRENT_PLANNING"):
        compare.comparison_files(replace(job, context={}), provenance, **args)


def test_new_proposed_budget_counts_both_correction_calls_and_never_claims_token_estimate():
    policy = {"max_images": 1, "reservation_usd_micros": 500_000}
    proposal = compare.budget_proposal("gpt-6.1-sol", 54000, policy)
    assert proposal["maximum_reserves_usd_micros"] == 6_750_000
    assert proposal["initial_reserves_usd_micros"] == 4_250_000
    assert proposal["construction_bound_at_input_limit"]["maximum_usd_micros"] == 1_220_000
    assert not proposal["authorized"] and proposal["input_tokens"] is None
    assert proposal["estimated_cost_usd_micros"] is None and proposal["max_corrections"] == 1
    with pytest.raises(ValueError, match="PROPOSED_RESERVE"):
        compare.budget_proposal("gpt-6.1-sol", 64000, None)
    with pytest.raises(ValueError, match="ONE_IMAGE"):
        compare.budget_proposal("gpt-6.1-sol", 54000, {**policy, "max_images": 2})


def test_rebuilt_executor_is_not_misrepresented_as_qualified(comparison_case):
    job, provenance, args = comparison_case
    with pytest.raises(ValueError, match="DIGEST_REQUIRED"):
        compare.comparison_files(job, provenance, **args, executor_image="latest")
    files = compare.comparison_files(job, provenance, **args, executor_image="sha256:" + "a" * 64)
    report = json.loads(files["comparison.json"])
    assert report["executor_image"] == "sha256:" + "a" * 64
    assert not report["executor_qualified"] and not report["execution_ready"]
