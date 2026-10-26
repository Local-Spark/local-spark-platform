"""Score consented mobile reviews of F04.2b clips against predeclared pilot gates."""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

REQUIRED = {
    "case_id",
    "segment",
    "source_kind",
    "consent_ref",
    "artifact_sha256",
    "mobile_review_yes_no",
    "legibility_1_to_5",
    "subject_visible_1_to_5",
    "cut_coherence_1_to_5",
    "fact_exact_yes_no",
    "critical_error_yes_no",
    "accepted_yes_no",
    "reviewer_role",
    "reviewed_at",
}
SCORES = ("legibility_1_to_5", "subject_visible_1_to_5", "cut_coherence_1_to_5")
DECISIONS = ("mobile_review_yes_no", "fact_exact_yes_no", "critical_error_yes_no", "accepted_yes_no")


def score(rows: list[dict[str, str]]) -> dict:
    if not rows:
        raise ValueError("At least one human review is required")
    seen: set[str] = set()
    seen_artifacts: set[str] = set()
    segments: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "accepted": 0, "critical": 0})
    kinds: dict[str, int] = defaultdict(int)
    quality = accepted = critical = mobile = 0
    for row in rows:
        if REQUIRED - row.keys() or any(
            not isinstance(row.get(field), str) or not row[field].strip() for field in REQUIRED
        ):
            raise ValueError("Review row has missing required provenance or scores")
        if row["case_id"] in seen:
            raise ValueError("Duplicate reviewed artifact")
        seen.add(row["case_id"])
        if row["source_kind"] not in {"photo", "clip", "none"}:
            raise ValueError("Unsupported source kind")
        if len(row["artifact_sha256"]) != 64 or any(c not in "0123456789abcdef" for c in row["artifact_sha256"]):
            raise ValueError("Invalid artifact hash")
        if row["artifact_sha256"] in seen_artifacts:
            raise ValueError("Duplicate reviewed artifact hash")
        seen_artifacts.add(row["artifact_sha256"])
        try:
            scores = [int(row[field]) for field in SCORES]
        except ValueError as exc:
            raise ValueError("Scores must be whole numbers") from exc
        if any(value not in range(1, 6) for value in scores):
            raise ValueError("Scores must be 1–5")
        if any(row[field] not in {"yes", "no"} for field in DECISIONS):
            raise ValueError("Decisions must be yes/no")
        is_critical = row["critical_error_yes_no"] == "yes" or row["fact_exact_yes_no"] == "no"
        is_accepted = row["accepted_yes_no"] == "yes"
        quality += all(value >= 4 for value in scores)
        accepted += is_accepted
        critical += is_critical
        mobile += row["mobile_review_yes_no"] == "yes"
        kinds[row["source_kind"]] += 1
        segment = segments[row["segment"]]
        segment["total"] += 1
        segment["accepted"] += is_accepted
        segment["critical"] += is_critical
    total = len(rows)
    gates = {
        "sample_at_least_20": total >= 20,
        "segments_at_least_4": len(segments) >= 4,
        "photos_at_least_5": kinds["photo"] >= 5,
        "clips_at_least_5": kinds["clip"] >= 5,
        "all_reviewed_on_mobile": mobile == total,
        "quality_at_least_90_percent": quality / total >= 0.9,
        "accepted_without_adjustment_at_least_80_percent": accepted / total >= 0.8,
        "zero_critical_errors": critical == 0,
    }
    return {
        "pilot_gate_passed": all(gates.values()),
        "gates": gates,
        "total": total,
        "quality_passes": quality,
        "accepted_without_adjustment": accepted,
        "critical_errors": critical,
        "segments": dict(segments),
        "source_kinds": dict(kinds),
    }


def score_csv(path: Path) -> dict:
    with path.open(newline="", encoding="utf-8") as handle:
        return score(list(csv.DictReader(handle)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reviews", type=Path, help="Private CSV containing consented human reviews")
    args = parser.parse_args()
    print(json.dumps(score_csv(args.reviews), ensure_ascii=False, indent=2))
