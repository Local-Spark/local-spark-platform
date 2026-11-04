"""Experimental reputation score, independent of business similarity.

This pure calculation is used only by closed, fictional discovery fixtures.
It is not connected to external sources or a production ranking.
"""

from decimal import ROUND_HALF_EVEN, Decimal, localcontext

_PRIOR_RATING = Decimal("4")
_PRIOR_REVIEWS = Decimal("50")
_SCALE = Decimal("2.5")
_EXPERIMENTAL_PENALTY = Decimal("3.4")
# Change this identifier whenever the experimental calculation changes.
EXPERIMENTAL_PENALIZED_VERSION = "penalized-3.4-v1"


def _validated_observation(
    rating: Decimal | float | int | None, review_count: int | None
) -> tuple[Decimal, Decimal] | None:
    if rating is None or review_count is None:
        return None
    if type(review_count) is not int or review_count < 0:
        raise ValueError("review_count must be a non-negative integer")
    if type(rating) not in (Decimal, float, int):
        raise ValueError("rating must be a finite number between 1 and 5")
    observed = Decimal(str(rating))
    if not observed.is_finite() or not Decimal(1) <= observed <= Decimal(5):
        raise ValueError("rating must be a finite number between 1 and 5")
    if review_count == 0:
        return None
    return observed, Decimal(review_count)


def experimental_reputation_score(rating: Decimal | float | int | None, review_count: int | None) -> Decimal | None:
    """Return a score from 0 to 10, or None when reputation data is absent.

    The initial prior is 4 out of 5 with the weight of 50 reviews. Zero
    reviews or missing data produce no score. The prior can increase low
    observed ratings. Values
    are not rounded for presentation; this is an experiment, not a final
    ranking.
    """
    values = _validated_observation(rating, review_count)
    if values is None:
        return None
    observed, count = values
    with localcontext() as context:
        context.prec = 28
        context.rounding = ROUND_HALF_EVEN
        smoothed = (count * observed + _PRIOR_REVIEWS * _PRIOR_RATING) / (count + _PRIOR_REVIEWS)
        return _SCALE * (smoothed - Decimal(1))


def experimental_penalized_reputation_score(
    rating: Decimal | float | int | None, review_count: int | None
) -> Decimal | None:
    """Experiment with a provisional penalty, not a statistical confidence interval.

    Zero reviews or missing data produce no score. A penalty of
    3.4 / sqrt(review_count) is subtracted from the normalized rating, with
    a floor of zero. The coefficient is an illustrative product calibration.
    """
    values = _validated_observation(rating, review_count)
    if values is None:
        return None
    observed, count = values
    with localcontext() as context:
        context.prec = 28
        context.rounding = ROUND_HALF_EVEN
        normalized = _SCALE * (observed - Decimal(1))
        return max(Decimal(0), normalized - _EXPERIMENTAL_PENALTY / count.sqrt())
