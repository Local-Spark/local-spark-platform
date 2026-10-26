"""The synthetic art corpus produces reviewable, private local artifacts."""

import csv
import json

import pytest
from PIL import Image

from scripts.evaluate_static_art import CASES, generate, synthetic_photo


def test_static_art_eval_generates_contact_sheet_and_review_form(tmp_path):
    cases = json.loads(CASES.read_text())
    assert len(cases) >= 8
    results = generate(cases, tmp_path)
    assert len(results) == len(cases)
    assert {item["segment"] for item in results} >= {"alimentacao", "beleza", "servicos", "varejo"}
    assert {item["source_shape"] for item in results} >= {"none", "portrait", "landscape", "panorama"}
    assert {item["format"] for item in results} == {"photo", "story"}
    assert all(item["human_review"] == "pending" for item in results)
    assert all(item["bytes"] > 0 and len(item["sha256"]) == 64 for item in results)
    with Image.open(tmp_path / "contact-sheet.jpg") as sheet:
        assert sheet.size == (1200, ((len(cases) + 3) // 4) * 430)
    assert len(list(csv.DictReader((tmp_path / "human-review.csv").open()))) == len(cases)
    assert len(json.loads((tmp_path / "measurements.json").read_text())) == len(cases)
    assert all((tmp_path / f"{item['case_id']}.jpg").is_file() for item in results)
    assert synthetic_photo("none") is None


@pytest.mark.parametrize("cases", [[], [{"id": "../escape"}]])
def test_static_art_eval_rejects_empty_and_unsafe_cases(cases, tmp_path):
    with pytest.raises(ValueError):
        generate(cases, tmp_path)


def test_static_art_eval_rejects_duplicate_case_ids(tmp_path):
    case = json.loads(CASES.read_text())[0]
    with pytest.raises(ValueError, match="unique"):
        generate([case, case], tmp_path)
