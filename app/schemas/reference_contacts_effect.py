"""Private chargeable contacts request retained in memory only."""

from dataclasses import dataclass

from pydantic import SecretStr


def valid_place_id(value: object) -> bool:
    """Apply the current technical bound to an otherwise opaque Place ID."""
    if (
        not isinstance(value, str)
        or not 1 <= len(value) <= 2048
        or value != value.strip()
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        return False
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


@dataclass(frozen=True, repr=False)
class ContactsChargeableRequest:
    method: str
    url: str
    body: bytes
    credential: SecretStr
    headers: tuple[tuple[str, str], ...]
    provider_actor_id: str
