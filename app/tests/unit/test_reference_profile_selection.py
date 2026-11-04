"""Profile choices preserve uncertainty and require input when ambiguous."""

from decimal import Decimal

import pytest

from app.schemas.reference_real_results import ReferenceRealCandidate
from app.services.reference_profile_selection import (
    ReferenceProfileSelectionError,
    choose_reference_profile,
    provide_owner_reference_profile,
)


def candidate(*handles):
    return ReferenceRealCandidate(
        place_id="synthetic-place",
        reputation_score=Decimal("8.5"),
        reputation_formula_version="test-v1",
        instagram_options=tuple({"handle": handle} for handle in handles),
    )


def test_business_without_profile_remains_selectable():
    choice = choose_reference_profile(candidate(), None)
    assert choice.handle is None
    assert choice.association == "not_available"


def test_single_suggestion_from_proven_apify_is_trusted_without_independent_verification():
    choice = choose_reference_profile(candidate("@Test.Profile"), None, apify_source_proven=True)
    assert choice.handle == "test.profile"
    assert choice.association == "provider_trusted"
    assert choice.access_status == "not_checked"
    assert "test.profile" not in repr(choice)


def test_multiple_suggestions_fall_back_to_first_returned_but_allow_owner_choice():
    value = candidate("@profile_two", "@profile_one")
    first = choose_reference_profile(value, None, apify_source_proven=True)
    assert first.handle == "profile_two" and first.association == "provider_trusted"
    choice = choose_reference_profile(value, "https://www.instagram.com/PROFILE_TWO/", apify_source_proven=True)
    assert choice.handle == "profile_two"
    assert choice.association == "owner_confirmed"
    assert choose_reference_profile(value, "@profile_two", apify_source_proven=True) == choice


def test_multiple_suggestions_use_only_explicit_primary_from_proven_source():
    value = candidate("@profile_one", "@profile_two")
    choice = choose_reference_profile(value, None, apify_source_proven=True, apify_primary="@PROFILE_TWO")
    assert choice.handle == "profile_two" and choice.association == "provider_trusted"
    assert choice.access_status == "not_checked"
    with pytest.raises(ReferenceProfileSelectionError, match="REFERENCE_PROFILE_PROVENANCE_REQUIRED"):
        choose_reference_profile(value, None, apify_primary="profile_two")


@pytest.mark.parametrize("primary", [42, "bad-profile!", "unoffered"])
def test_primary_must_be_a_valid_offered_profile(primary):
    with pytest.raises(ReferenceProfileSelectionError, match="REFERENCE_PROFILE_OPTION_INVALID"):
        choose_reference_profile(candidate("one", "two"), None, apify_source_proven=True, apify_primary=primary)


@pytest.mark.parametrize("selection", ["bad-profile!", "different_profile", 42])
def test_owner_cannot_confirm_an_invalid_or_unoffered_option(selection):
    with pytest.raises(ReferenceProfileSelectionError, match="REFERENCE_PROFILE_OPTION_INVALID") as error:
        choose_reference_profile(candidate("suggested"), selection, apify_source_proven=True)
    assert str(selection) not in str(error.value)


def test_unproven_source_label_cannot_enable_a_profile():
    with pytest.raises(ReferenceProfileSelectionError, match="REFERENCE_PROFILE_PROVENANCE_REQUIRED"):
        choose_reference_profile(candidate("suggested"), None)
    with pytest.raises(ReferenceProfileSelectionError, match="REFERENCE_PROFILE_PROVENANCE_REQUIRED"):
        choose_reference_profile(candidate("suggested"), "suggested", apify_source_proven=1)


def test_owner_can_explicitly_supply_a_profile_when_none_was_suggested():
    result = provide_owner_reference_profile(candidate(), "@Cafe.Exemplo", confirmed=True)
    assert result.handle == "cafe.exemplo"
    assert result.source == "owner"
    assert result.access_status == "not_checked"
    assert result.association == "owner_confirmed"
    assert "cafe.exemplo" not in repr(result)
    assert (
        provide_owner_reference_profile(candidate(), "https://www.instagram.com/cafe.exemplo/", confirmed=True)
        == result
    )


@pytest.mark.parametrize("confirmed", [False, None, 1])
def test_owner_supplied_profile_requires_explicit_boolean_confirmation(confirmed):
    with pytest.raises(ReferenceProfileSelectionError, match="REFERENCE_PROFILE_CONFIRMATION_REQUIRED"):
        provide_owner_reference_profile(candidate(), "some_profile", confirmed=confirmed)


@pytest.mark.parametrize("handle", ["invalid/profile", 42])
def test_invalid_owner_supplied_handle_fails_without_echoing_it(handle):
    with pytest.raises(ReferenceProfileSelectionError, match="REFERENCE_PROFILE_OPTION_INVALID") as error:
        provide_owner_reference_profile(candidate(), handle, confirmed=True)
    assert str(handle) not in str(error.value)


def test_owner_can_replace_incorrect_provider_suggestions_with_their_own_profile():
    result = provide_owner_reference_profile(candidate("first", "second"), "another", confirmed=True)
    assert result.handle == "another"
    assert result.source == "owner" and result.access_status == "not_checked"


def test_owner_provided_profile_requires_valid_candidate():
    with pytest.raises(ReferenceProfileSelectionError, match="REFERENCE_CANDIDATE_INVALID"):
        provide_owner_reference_profile(None, "another", confirmed=True)
