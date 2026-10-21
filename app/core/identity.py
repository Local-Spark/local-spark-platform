"""Stable application identities, independent of the retired external provider."""

from dataclasses import dataclass
from uuid import NAMESPACE_URL, UUID, uuid5


@dataclass(frozen=True)
class Identity:
    actor_id: UUID
    issuer: str
    subject: str
    display_name: str
    email: str | None = None
    email_verified: bool = False


def actor_for_subject(issuer: str, subject: str) -> UUID:
    """Only used to preserve the identifiers of the two bundled legacy demo accounts."""
    return uuid5(NAMESPACE_URL, f"{issuer}\x00{subject}")
