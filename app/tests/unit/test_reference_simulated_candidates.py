"""Scripted candidates never imply real similarity or real source data."""

from decimal import Decimal, localcontext

from app.services.reference_simulated_candidates import simulated_candidates


def test_similarity_filter_runs_before_reputation_and_scores_few_reviews(monkeypatch):
    from app.services import reference_simulated_candidates as fixtures

    actual_score = fixtures.experimental_penalized_reputation_score
    observations = []

    def score(rating, reviews):
        observations.append((rating, reviews))
        return actual_score(rating, reviews)

    monkeypatch.setattr(fixtures, "experimental_penalized_reputation_score", score)
    with localcontext() as context:
        context.prec = 4
        candidates = simulated_candidates()

    assert [candidate.number for candidate in candidates] == [1, 2, 3]
    assert observations == [(Decimal("4.8"), 2000), (Decimal("5.0"), 11), (Decimal("4.9"), 9)]
    assert candidates[0].reputation_score == Decimal("9.42")
    assert candidates[1].reputation_score == Decimal("8.97")
    assert candidates[0].reputation_score > candidates[1].reputation_score
    assert candidates[2].reputation_score == Decimal("8.62")
    assert [candidate.reputation_status for candidate in candidates] == ["scored", "scored", "scored"]


def test_candidates_without_reviews_or_rating_are_not_suggested(monkeypatch):
    from app.services import reference_simulated_candidates as fixtures

    monkeypatch.setattr(
        fixtures,
        "_FIXTURES",
        (
            fixtures._Candidate(1, "suitable", Decimal("5"), 0),
            fixtures._Candidate(2, "suitable", None, None),
            fixtures._Candidate(3, "suitable", Decimal("0"), 10),
            fixtures._Candidate(4, "suitable", Decimal("5"), -1),
        ),
    )
    candidates = simulated_candidates()
    assert candidates == ()


def test_candidates_are_ranked_by_unrounded_score_then_number(monkeypatch):
    from app.services import reference_simulated_candidates as fixtures

    monkeypatch.setattr(
        fixtures,
        "_FIXTURES",
        (
            fixtures._Candidate(3, "suitable", Decimal("4.8"), 1001),
            fixtures._Candidate(1, "suitable", Decimal("4.8"), 1000),
            fixtures._Candidate(2, "suitable", Decimal("4.8"), 1001),
        ),
    )
    with localcontext() as context:
        context.prec = 4
        candidates = simulated_candidates()
    assert [candidate.number for candidate in candidates] == [2, 3, 1]
    assert [candidate.reputation_score for candidate in candidates] == [Decimal("9.39")] * 3
    assert candidates[1].ordering_score > candidates[2].ordering_score
