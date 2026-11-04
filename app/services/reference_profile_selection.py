"""Rules for choosing a suggested business when Instagram profiles are ambiguous.

This pure helper proves neither provider provenance nor current owner access.
The caller must verify the search and effects, authorize the actor, and commit
any selection together with its audit/outbox before using the result.
"""

from dataclasses import dataclass
from typing import Literal

from app.schemas.owner_references import instagram_handle
from app.schemas.reference_real_results import ReferenceRealCandidate


class ReferenceProfileSelectionError(ValueError):
    """A stable selection error without a profile value in the message."""


@dataclass(frozen=True, repr=False)
class ReferenceProfileChoice:
    handle: str | None
    association: Literal["not_available", "provider_trusted", "owner_confirmed"]
    access_status: Literal["not_checked"] = "not_checked"


@dataclass(frozen=True, repr=False)
class OwnerProvidedProfile:
    """An explicit owner indication, with no claim that the profile was accessed."""

    handle: str
    source: Literal["owner"] = "owner"
    access_status: Literal["not_checked"] = "not_checked"
    association: Literal["owner_confirmed"] = "owner_confirmed"


def choose_reference_profile(
    candidate: ReferenceRealCandidate,
    confirmed_option: str | None,
    *,
    apify_source_proven: bool = False,
    apify_primary: str | None = None,
) -> ReferenceProfileChoice:
    """Select an Instagram profile using the provider's original order.

    Zero profiles permit selection without an Instagram account. One option
    from a proven Apify effect is trusted without owner confirmation, but this
    is not independent verification or proof of profile access. If several
    options exist, a primary explicitly identified by a proven Apify effect is
    trusted; otherwise the first returned option is used. The caller
    must establish provenance from the durable effect before passing
    ``apify_source_proven=True`` or a primary; an input label is never proof.
    """
    options = tuple(option.handle for option in candidate.instagram_options)
    if options and apify_source_proven is not True:
        raise ReferenceProfileSelectionError("REFERENCE_PROFILE_PROVENANCE_REQUIRED")
    if confirmed_option is not None:
        if not isinstance(confirmed_option, str):
            raise ReferenceProfileSelectionError("REFERENCE_PROFILE_OPTION_INVALID")
        try:
            confirmed = instagram_handle(confirmed_option)
        except (ValueError, TypeError):
            raise ReferenceProfileSelectionError("REFERENCE_PROFILE_OPTION_INVALID") from None
        if confirmed not in options:
            raise ReferenceProfileSelectionError("REFERENCE_PROFILE_OPTION_INVALID")
        return ReferenceProfileChoice(confirmed, "owner_confirmed")
    if apify_primary is not None:
        if not isinstance(apify_primary, str):
            raise ReferenceProfileSelectionError("REFERENCE_PROFILE_OPTION_INVALID")
        try:
            primary = instagram_handle(apify_primary)
        except (ValueError, TypeError):
            raise ReferenceProfileSelectionError("REFERENCE_PROFILE_OPTION_INVALID") from None
        if primary not in options:
            raise ReferenceProfileSelectionError("REFERENCE_PROFILE_OPTION_INVALID")
        return ReferenceProfileChoice(primary, "provider_trusted")
    if options:
        return ReferenceProfileChoice(options[0], "provider_trusted")
    return ReferenceProfileChoice(None, "not_available")


def provide_owner_reference_profile(
    candidate: ReferenceRealCandidate, owner_handle: str, *, confirmed: bool
) -> OwnerProvidedProfile:
    """Accept a confirmed owner indication regardless of provider suggestions.

    The owner-provided value remains unaccessed and is not attributed to Apify.
    Supplying a value is not equivalent to a provider or independent verification.
    """
    if not isinstance(candidate, ReferenceRealCandidate):
        raise ReferenceProfileSelectionError("REFERENCE_CANDIDATE_INVALID")
    if confirmed is not True:
        raise ReferenceProfileSelectionError("REFERENCE_PROFILE_CONFIRMATION_REQUIRED")
    if not isinstance(owner_handle, str):
        raise ReferenceProfileSelectionError("REFERENCE_PROFILE_OPTION_INVALID")
    try:
        normalized = instagram_handle(owner_handle)
    except ValueError:
        raise ReferenceProfileSelectionError("REFERENCE_PROFILE_OPTION_INVALID") from None
    return OwnerProvidedProfile(normalized)
