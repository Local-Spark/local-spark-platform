"""A human explicitly reviews the particular file before full-piece approval."""

import pytest
from pydantic import ValidationError

from app.schemas.content_deliveries import VisualReviewConfirmation


def review():
    return {
        "preview_sha256": "a" * 64,
        "price_and_terms": True,
        "spelling": True,
        "identity": True,
        "fidelity": True,
        "legibility": True,
    }


def test_review_is_bound_to_the_exact_image_hash():
    value = VisualReviewConfirmation.model_validate(review())
    assert value.preview_sha256 == "a" * 64


@pytest.mark.parametrize("field", ["price_and_terms", "spelling", "identity", "fidelity", "legibility"])
def test_each_visual_review_item_must_be_explicitly_confirmed(field):
    with pytest.raises(ValidationError, match="VISUAL_REVIEW_INCOMPLETE"):
        VisualReviewConfirmation.model_validate({**review(), field: False})


def test_review_rejects_an_invalid_hash_and_non_boolean_values():
    with pytest.raises(ValidationError):
        VisualReviewConfirmation.model_validate({**review(), "preview_sha256": "wrong"})
    with pytest.raises(ValidationError):
        VisualReviewConfirmation.model_validate({**review(), "fidelity": "yes"})
