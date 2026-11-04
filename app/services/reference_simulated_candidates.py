"""Closed, synthetic inputs for the private discovery simulation only.

Similarity is a scripted outcome, not a Jev assessment of the user's business.
Keep this fixture version stable: previously persisted candidates refer to its numbers.
"""

from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import Literal

from app.services.reference_reputation import experimental_penalized_reputation_score

SIMULATED_FIXTURE_VERSION = "synthetic-v1"


@dataclass(frozen=True)
class _Candidate:
    number: int
    similarity: Literal["suitable", "unsuitable"]
    rating: Decimal | None
    reviews: int | None


@dataclass(frozen=True)
class SimulatedCandidate:
    number: int
    reputation_score: Decimal
    reputation_status: Literal["scored"]
    ordering_score: Decimal


# All values are made up. Candidate 4 is deliberately ineligible despite its
# strong rating; candidate 3 tests a score with fewer than ten reviews.
_FIXTURES = (
    _Candidate(1, "suitable", Decimal("4.8"), 2000),
    _Candidate(2, "suitable", Decimal("5.0"), 11),
    _Candidate(3, "suitable", Decimal("4.9"), 9),
    _Candidate(4, "unsuitable", Decimal("5.0"), 5000),
)


def simulated_candidates() -> tuple[SimulatedCandidate, ...]:
    """Reject unsuitable fixtures before calculating any reputation score.

    Drop fixtures without a score, then order by the full experimental score,
    using fixture number only to make equal scores deterministic. Scores are
    only for local experiments.
    """
    eligible = (candidate for candidate in _FIXTURES if candidate.similarity == "suitable")
    results = []
    for candidate in eligible:
        try:
            score = experimental_penalized_reputation_score(candidate.rating, candidate.reviews)
        except ValueError:
            # A malformed fictional observation cannot be recommended either.
            continue
        if score is None:
            continue
        with localcontext() as context:
            context.prec = 28
            results.append(
                SimulatedCandidate(
                    number=candidate.number,
                    reputation_score=score.quantize(Decimal("0.01")),
                    reputation_status="scored",
                    ordering_score=score,
                )
            )
    by_number = sorted(results, key=lambda candidate: candidate.number)
    return tuple(sorted(by_number, key=lambda candidate: candidate.ordering_score, reverse=True))
