"""A synthetic or incomplete review cannot open the commercial video pilot."""

import csv

import pytest

from scripts.score_video_reviews import score, score_csv


def _row(index: int) -> dict[str, str]:
    return {
        "case_id": f"case-{index}",
        "segment": ("alimentacao", "beleza", "servicos", "varejo")[index % 4],
        "source_kind": "clip" if index % 2 else "photo",
        "consent_ref": f"consent-{index}",
        "artifact_sha256": f"{index:064x}",
        "mobile_review_yes_no": "yes",
        "legibility_1_to_5": "4",
        "subject_visible_1_to_5": "4",
        "cut_coherence_1_to_5": "4",
        "fact_exact_yes_no": "yes",
        "critical_error_yes_no": "no",
        "accepted_yes_no": "yes",
        "reviewer_role": "comerciante",
        "reviewed_at": "2026-10-26T12:00:00Z",
    }


def test_video_pilot_gate_needs_all_declared_evidence(tmp_path):
    rows = [_row(index) for index in range(20)]
    report = score(rows)
    assert report["pilot_gate_passed"] is True
    assert all(report["gates"].values())
    rows[0]["cut_coherence_1_to_5"] = "2"
    rows[1]["accepted_yes_no"] = "no"
    rows[2]["critical_error_yes_no"] = "yes"
    rows[3]["mobile_review_yes_no"] = "no"
    report = score(rows)
    assert report["pilot_gate_passed"] is False
    assert report["quality_passes"] == 19
    assert report["accepted_without_adjustment"] == 19
    assert report["critical_errors"] == 1
    assert report["segments"]["servicos"]["critical"] == 1
    assert report["gates"]["all_reviewed_on_mobile"] is False
    path = tmp_path / "reviews.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    assert score_csv(path)["pilot_gate_passed"] is False


@pytest.mark.parametrize(
    "change,problem",
    [
        ({"consent_ref": ""}, "missing required"),
        ({"artifact_sha256": "abc"}, "Invalid artifact hash"),
        ({"source_kind": "avatar"}, "Unsupported source"),
        ({"legibility_1_to_5": "four"}, "whole numbers"),
        ({"legibility_1_to_5": "6"}, "1–5"),
        ({"accepted_yes_no": "maybe"}, "yes/no"),
    ],
)
def test_invalid_video_review_is_rejected(change, problem):
    with pytest.raises(ValueError, match=problem):
        score([_row(0) | change])


def test_duplicate_or_missing_review_is_rejected():
    with pytest.raises(ValueError, match="At least one"):
        score([])
    with pytest.raises(ValueError, match="Duplicate"):
        score([_row(0), _row(0)])
    with pytest.raises(ValueError, match="Duplicate reviewed artifact hash"):
        score([_row(0), _row(1) | {"artifact_sha256": _row(0)["artifact_sha256"]}])
    with pytest.raises(ValueError, match="missing required"):
        score([{"case_id": "x"}])


def test_small_or_imbalanced_sample_cannot_pass():
    rows = [_row(index) for index in range(19)]
    assert score(rows)["gates"]["sample_at_least_20"] is False
    rows = [_row(index) | {"source_kind": "none"} for index in range(20)]
    assert score(rows)["pilot_gate_passed"] is False
    rows = [_row(index) | {"segment": "alimentacao"} for index in range(20)]
    assert score(rows)["gates"]["segments_at_least_4"] is False
    rows = [_row(index) | {"accepted_yes_no": "no"} if index < 5 else _row(index) for index in range(20)]
    assert score(rows)["gates"]["accepted_without_adjustment_at_least_80_percent"] is False
    rows = [_row(index) | {"legibility_1_to_5": "3"} if index < 3 else _row(index) for index in range(20)]
    assert score(rows)["gates"]["quality_at_least_90_percent"] is False
