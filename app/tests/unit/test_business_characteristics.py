"""Owner characteristics preserve old request hashes and do not restore legacy facts."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.editorial_context import (
    ContextContent,
    ContextRead,
    ContextRestore,
    ContextUpdate,
    EditorialPreferences,
)
from app.services.editorial_context import _digest, _preserve_omitted_characteristics


def test_characteristics_are_trimmed_bounded_and_can_be_cleared():
    assert (
        EditorialPreferences(business_characteristics="  Atendimento acolhedor  ").business_characteristics
        == "Atendimento acolhedor"
    )
    assert EditorialPreferences(business_characteristics="  ").business_characteristics is None
    assert EditorialPreferences(business_characteristics="a" * 2000).business_characteristics is not None
    with pytest.raises(ValidationError):
        EditorialPreferences(business_characteristics="a" * 2001)


def test_omission_preserves_but_null_and_empty_explicitly_clear_and_change_hash():
    operation = uuid4()
    previous = ContextRead(version=1, preferences=EditorialPreferences(business_characteristics="Artesanal"))
    omitted = ContextUpdate(expected_version=1, operation_id=operation)
    explicit = ContextUpdate(expected_version=1, operation_id=operation, preferences={"business_characteristics": None})
    content = ContextContent()
    assert (
        _preserve_omitted_characteristics(omitted, content, previous).preferences.business_characteristics
        == "Artesanal"
    )
    assert (
        _preserve_omitted_characteristics(
            explicit, ContextContent(preferences=explicit.preferences), previous
        ).preferences.business_characteristics
        is None
    )
    assert _digest(omitted) != _digest(explicit)
    old_restore = ContextRestore(expected_version=1, target_version=1, operation_id=operation)
    assert (
        _preserve_omitted_characteristics(old_restore, content, previous).preferences.business_characteristics
        == "Artesanal"
    )
    known_empty = ContextContent(preferences=EditorialPreferences(business_characteristics=None))
    assert (
        _preserve_omitted_characteristics(old_restore, known_empty, previous).preferences.business_characteristics
        is None
    )
