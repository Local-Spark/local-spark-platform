"""Score consented, human-reviewed static art against the F04.1b pilot gates."""

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

REQUIRED = {
    "case_id",
    "segment",
    "format",
    "consent_ref",
    "artifact_sha256",
    "legibility_1_to_5",
    "product_visible_1_to_5",
    "fact_exact_yes_no",
    "critical_error_yes_no",
    "accepted_yes_no",
    "reviewer_role",
    "reviewed_at",
}


def score(rows: list[dict[str, str]]) -> dict:
    if not rows:
        raise ValueError("At least one human review is required")
    seen = set()
    segments: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "accepted": 0, "critical": 0})
    formats = set()
    legible = accepted = critical = 0
    for row in rows:
        if REQUIRED - row.keys() or any(
            not isinstance(row.get(field), str) or not row[field].strip() for field in REQUIRED
        ):
            raise ValueError("Review row has missing required provenance or scores")
        if row["case_id"] in seen:
            raise ValueError("Duplicate reviewed artifact")
        seen.add(row["case_id"])
        if row["format"] not in {"photo", "story"}:
            raise ValueError("Unsupported static-art format")
        formats.add(row["format"])
        if len(row["artifact_sha256"]) != 64 or any(c not in "0123456789abcdef" for c in row["artifact_sha256"]):
            raise ValueError("Invalid artifact hash")
        try:
            clarity = int(row["legibility_1_to_5"])
            visibility = int(row["product_visible_1_to_5"])
        except ValueError as exc:
            raise ValueError("Scores must be whole numbers") from exc
        if clarity not in range(1, 6) or visibility not in range(1, 6):
            raise ValueError("Scores must be 1–5")
        if any(
            row[field] not in {"yes", "no"}
            for field in ("fact_exact_yes_no", "critical_error_yes_no", "accepted_yes_no")
        ):
            raise ValueError("Decisions must be yes/no")
        is_critical = row["critical_error_yes_no"] == "yes" or row["fact_exact_yes_no"] == "no"
        is_accepted = row["accepted_yes_no"] == "yes"
        legible += clarity >= 4 and visibility >= 4
        accepted += is_accepted
        critical += is_critical
        segment = segments[row["segment"]]
        segment["total"] += 1
        segment["accepted"] += is_accepted
        segment["critical"] += is_critical
    total = len(rows)
    gates = {
        "sample_at_least_20": total >= 20,
        "segments_at_least_4": len(segments) >= 4,
        "both_formats": formats == {"photo", "story"},
        "legibility_and_visibility_at_least_90_percent": legible / total >= 0.9,
        "accepted_without_adjustment_at_least_80_percent": accepted / total >= 0.8,
        "zero_critical_errors": critical == 0,
    }
    return {
        "pilot_gate_passed": all(gates.values()),
        "gates": gates,
        "total": total,
        "legible_and_visible": legible,
        "accepted_without_adjustment": accepted,
        "critical_errors": critical,
        "segments": dict(segments),
        "formats": sorted(formats),
    }


def score_csv(path: Path) -> dict:
    with path.open(newline="", encoding="utf-8") as handle:
        return score(list(csv.DictReader(handle)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reviews", type=Path, help="Private CSV containing consented human reviews")
    args = parser.parse_args()
    print(json.dumps(score_csv(args.reviews), ensure_ascii=False, indent=2))
