"""Structured context rejects ambiguous or oversized owner input."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.editorial_context import ConfirmedFact, ContextContent, EditorialPreferences


def test_fact_and_preference_constraints():
    fact = {"id": uuid4(), "kind": "price", "statement": "Combo custa R$ 20", "source_detail": "Dono"}
    with pytest.raises(ValidationError):
        ConfirmedFact.model_validate(fact)
    assert ConfirmedFact.model_validate({**fact, "valid_until": "2026-12-31"}).kind == "price"
    assert ConfirmedFact.model_validate({**fact, "kind": "product"}).valid_until is None
    with pytest.raises(ValidationError):
        ContextContent.model_validate({"facts": [fact, fact]})
    with pytest.raises(ValidationError):
        ContextContent.model_validate({"facts": [{**fact, "kind": "product"}] * 2})
    with pytest.raises(ValidationError):
        EditorialPreferences.model_validate({"avoided_topics": [" "]})
    with pytest.raises(ValidationError):
        EditorialPreferences.model_validate({"avoided_topics": ["same", "same"]})
    with pytest.raises(ValidationError):
        EditorialPreferences.model_validate({"avoided_topics": ["x" * 81]})
    assert EditorialPreferences.model_validate({"avoided_topics": ["  assunto "]}).avoided_topics == ["assunto"]
