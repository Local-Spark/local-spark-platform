"""Stable application identities, independent of the retired external provider."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Identity:
    actor_id: UUID
    issuer: str
    subject: str
    display_name: str
    email: str | None = None
    email_verified: bool = False
