"""Fictional examples and properties of the experimental reputation score."""

from decimal import ROUND_DOWN, ROUND_HALF_EVEN, ROUND_UP, Decimal, localcontext

import pytest

from app.services.reference_reputation import experimental_penalized_reputation_score as penalized_score
from app.services.reference_reputation import experimental_reputation_score as score


def test_examples_favor_a_well_supported_rating_over_ten_reviews():
    few = score(5, 10)
    many = score(4.7, 2000)
    assert few is not None and many is not None
    assert float(few) == pytest.approx(7.916666667)
    assert float(many) == pytest.approx(9.207317073)
    assert many > few
    assert few != Decimal("7.92")  # Presentation rounding must not decide order.


@pytest.mark.parametrize("rating,count", [(None, None), (None, 10), (4.5, None)])
def test_missing_observations_are_not_assigned_a_score(rating, count):
    assert score(rating, count) is None


@pytest.mark.parametrize("calculate", [score, penalized_score])
def test_zero_reviews_has_no_score(calculate):
    assert calculate(5, 0) is None


@pytest.mark.parametrize("count", range(1, 10))
def test_fewer_than_ten_reviews_can_be_scored(count):
    assert score(5, count) is not None
    assert penalized_score(5, count) is not None


def test_ten_reviews_are_sufficient():
    assert score(5, 10) is not None


@pytest.mark.parametrize("rating", [0, 5.1, -1, float("nan"), float("inf"), Decimal("-Infinity"), True, "4"])
def test_rejects_invalid_ratings(rating):
    with pytest.raises(ValueError, match="rating"):
        score(rating, 2)


@pytest.mark.parametrize("count", [-1, 1.5, True, "2"])
def test_rejects_invalid_review_counts(count):
    with pytest.raises(ValueError, match="review_count"):
        score(4, count)


def test_scores_stay_in_range_and_increase_with_rating():
    scores = [score(Decimal(rating), 100) for rating in ("1", "2", "3", "4", "5")]
    assert all(value is not None and 0 < value < 10 for value in scores)
    assert scores == sorted(scores)
    assert len(set(scores)) == len(scores)


def test_more_reviews_move_score_towards_observed_rating_not_always_upwards():
    assert score(5, 10) < score(5, 2000) < 10
    assert 0 < score(1, 2000) < score(1, 10)
    assert score(4, 10) == score(4, 2000) == Decimal("7.5")


def test_more_evidence_can_make_a_lower_rating_rank_above_a_higher_rating():
    assert score(4.7, 2000) > score(5, 10)
    assert score(5, 2000) > score(4.7, 2000)


def test_threshold_does_not_correct_prior_inflating_a_low_rating():
    assert score(1, 11) > score(3, 2000)


@pytest.mark.parametrize("rating,count", [(None, None), (None, 10), (5, None), (5, 0)])
def test_penalized_score_requires_positive_count_and_both_inputs(rating, count):
    assert penalized_score(rating, count) is None


@pytest.mark.parametrize("rating,count", [(True, 10), (float("nan"), 10), (0, 10), (5.1, 10), (4, -1), (4, True)])
def test_penalized_score_rejects_invalid_observations(rating, count):
    with pytest.raises(ValueError):
        penalized_score(rating, count)


def test_penalized_score_rejects_inflated_one_star_and_favors_evidence():
    assert penalized_score(1, 11) == 0
    assert penalized_score(1, 2000) == 0
    assert penalized_score(1, 11) < penalized_score(3, 2000)
    assert penalized_score(4.8, 1000) > penalized_score(5, 11)
    assert float(penalized_score(4.8, 1000)) == pytest.approx(9.392482556)
    assert float(penalized_score(5, 11)) == pytest.approx(8.974861428)


def test_penalty_applies_even_to_a_five_star_business_with_very_few_reviews():
    assert float(penalized_score(5, 1)) == pytest.approx(6.6)
    assert float(penalized_score(5, 9)) == pytest.approx(8.866666667)
    assert penalized_score(5, 1) < penalized_score(5, 9) < penalized_score(5, 10)


def test_penalized_score_respects_rating_bounds_and_never_boosts_observation():
    for count in (10, 100, 1000):
        scores = [penalized_score(Decimal(rating), count) for rating in ("1", "1.1", "2", "3", "4", "5")]
        assert all(value is not None and 0 <= value <= 10 for value in scores)
        assert scores == sorted(scores)  # The floor can produce ties at zero.
        for rating, value in zip(("1", "1.1", "2", "3", "4", "5"), scores, strict=True):
            assert value <= Decimal("2.5") * (Decimal(rating) - 1)


def test_penalized_score_grows_with_evidence_unless_zero_floor_causes_ties():
    assert penalized_score(4.8, 10) < penalized_score(4.8, 100) < penalized_score(4.8, 1000)
    assert penalized_score(1.1, 10) == penalized_score(1.1, 100) == 0
    assert penalized_score(1.1, 1000) > 0
    assert penalized_score(5, 10) != Decimal("8.92")


@pytest.mark.parametrize("calculate", [score, penalized_score])
def test_score_does_not_depend_on_callers_decimal_precision(calculate):
    expected = calculate(Decimal("4.8"), 1000)
    expected_next = calculate(Decimal("4.8"), 1001)
    with localcontext() as context:
        context.prec = 4
        assert calculate(Decimal("4.8"), 1000) == expected
        assert calculate(Decimal("4.8"), 1001) == expected_next
        assert expected < expected_next


@pytest.mark.parametrize("calculate", [score, penalized_score])
def test_score_does_not_depend_on_callers_decimal_rounding(calculate):
    with localcontext() as context:
        context.rounding = ROUND_HALF_EVEN
        expected = calculate(Decimal("4.8"), 2000)
    for rounding in (ROUND_DOWN, ROUND_UP):
        with localcontext() as context:
            context.rounding = rounding
            assert calculate(Decimal("4.8"), 2000) == expected
