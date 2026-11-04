from uuid import uuid4

import pytest
from sqlalchemy.exc import DBAPIError

from app.services.reference_cost_guard import ReferenceCostError, _digest, _translate_error


def test_unknown_database_error_is_not_misclassified():
    error = DBAPIError("SELECT 1", {}, RuntimeError("unexpected failure"))
    with pytest.raises(DBAPIError) as caught:
        _translate_error(error)
    assert caught.value is error


def test_effect_fingerprint_binds_amount_provider_request_and_discovery():
    business, actor, discovery = uuid4(), uuid4(), uuid4()
    base = _digest(business, actor, discovery, "google", "a" * 64, 10)
    assert base == _digest(business, actor, discovery, "google", "a" * 64, 10)
    assert base != _digest(business, actor, uuid4(), "google", "a" * 64, 10)
    assert base != _digest(business, actor, discovery, "apify", "a" * 64, 10)
    assert base != _digest(business, actor, discovery, "google", "a" * 64, 11)
    with pytest.raises(ReferenceCostError, match="INVALID_PROVIDER"):
        _digest(business, actor, discovery, "unknown", "a" * 64, 10)
    for bad_hash, amount in (("oops", 10), ("z" * 64, 10), ("a" * 64, 0), ("a" * 64, True)):
        with pytest.raises(ReferenceCostError, match="INVALID_CLAIM"):
            _digest(business, actor, discovery, "google", bad_hash, amount)
