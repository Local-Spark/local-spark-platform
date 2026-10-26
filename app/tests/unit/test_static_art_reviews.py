"""Pilot review gates never treat the synthetic corpus as commercial approval."""

import csv

import pytest

from scripts.score_static_art_reviews import REQUIRED, score, score_csv


def review(index: int) -> dict[str, str]:
    return {
        "case_id": f"private-{index}",
        "segment": ("food", "beauty", "retail", "services")[index % 4],
        "format": "photo" if index % 2 else "story",
        "consent_ref": f"consent-{index}",
        "artifact_sha256": f"{index:064x}",
        "legibility_1_to_5": "4",
        "product_visible_1_to_5": "5",
        "fact_exact_yes_no": "yes",
        "critical_error_yes_no": "no",
        "accepted_yes_no": "yes",
        "reviewer_role": "merchant",
        "reviewed_at": "2026-10-26T12:00:00Z",
    }


def test_review_score_passes_only_consented_human_sample(tmp_path):
    rows = [review(index) for index in range(20)]
    path = tmp_path / "reviews.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted(REQUIRED))
        writer.writeheader()
        writer.writerows(rows)
    result = score_csv(path)
    assert result["pilot_gate_passed"] is True
    assert result["total"] == 20
    assert len(result["segments"]) == 4
    assert result["formats"] == ["photo", "story"]


def test_review_score_reports_each_failed_gate():
    rows = [review(index) for index in range(19)]
    rows[0]["legibility_1_to_5"] = "3"
    rows[1]["product_visible_1_to_5"] = "2"
    for row in rows[:5]:
        row["accepted_yes_no"] = "no"
    rows[2]["fact_exact_yes_no"] = "no"
    rows[3]["critical_error_yes_no"] = "yes"
    for row in rows:
        row["segment"] = "food"
        row["format"] = "photo"
    result = score(rows)
    assert result["pilot_gate_passed"] is False
    assert all(value is False for value in result["gates"].values())
    assert result["critical_errors"] == 2
    assert result["segments"]["food"] == {"total": 19, "accepted": 14, "critical": 2}


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"consent_ref": ""}, "missing"),
        ({"consent_ref": None}, "missing"),
        ({"format": "video"}, "format"),
        ({"artifact_sha256": "xyz"}, "hash"),
        ({"artifact_sha256": "z" * 64}, "hash"),
        ({"legibility_1_to_5": "bad"}, "whole"),
        ({"product_visible_1_to_5": "6"}, "1–5"),
        ({"accepted_yes_no": "maybe"}, "yes/no"),
    ],
)
def test_review_score_rejects_invalid_rows(change, message):
    with pytest.raises(ValueError, match=message):
        score([review(0) | change])


def test_review_score_rejects_missing_columns_duplicates_and_empty():
    with pytest.raises(ValueError, match="one human"):
        score([])
    with pytest.raises(ValueError, match="missing"):
        score([{"case_id": "one"}])
    with pytest.raises(ValueError, match="Duplicate"):
        score([review(0), review(0)])
