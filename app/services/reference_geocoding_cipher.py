"""Encrypt transient geocoding points with the project's existing Fernet key.

This helper does not store data, select a point, schedule cleanup or authorize
an owner. The future writer must enforce RLS, executor fences and deletion.
"""

import json
import math
from dataclasses import dataclass
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import Settings


class GeocodingCipherError(Exception):
    """Stable code without coordinates, ciphertext or key details."""


@dataclass(frozen=True, repr=False)
class GeocodingPointScope:
    tenant: UUID
    business: UUID
    origin: UUID
    effect: UUID
    candidate: UUID
    context_version: int


@dataclass(frozen=True, repr=False)
class GeocodingPoint:
    latitude: float
    longitude: float


def _scope(value: object) -> GeocodingPointScope:
    if (
        not isinstance(value, GeocodingPointScope)
        or any(
            not isinstance(item, UUID)
            for item in (value.tenant, value.business, value.origin, value.effect, value.candidate)
        )
        or type(value.context_version) is not int
        or not 0 < value.context_version <= 9_223_372_036_854_775_807
    ):
        raise GeocodingCipherError("GEOCODING_POINT_SCOPE_INVALID")
    return value


def _point(latitude: object, longitude: object) -> GeocodingPoint:
    try:
        if (
            isinstance(latitude, bool)
            or not isinstance(latitude, (int, float))
            or isinstance(longitude, bool)
            or not isinstance(longitude, (int, float))
        ):
            raise ValueError
        lat, lon = float(latitude), float(longitude)
        if not math.isfinite(lat) or not math.isfinite(lon) or not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise ValueError
        return GeocodingPoint(lat, lon)
    except (ValueError, TypeError, OverflowError):
        raise GeocodingCipherError("GEOCODING_POINT_INVALID") from None


def _cipher(settings: Settings) -> Fernet:
    if settings.meta_encryption_key is None:
        raise GeocodingCipherError("GEOCODING_POINT_KEY_REQUIRED")
    try:
        return Fernet(settings.meta_encryption_key.get_secret_value().encode())
    except (ValueError, TypeError, UnicodeError):
        raise GeocodingCipherError("GEOCODING_POINT_KEY_INVALID") from None


def _object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def encrypt_geocoding_point(settings: Settings, scope: GeocodingPointScope, latitude: object, longitude: object) -> str:
    """Return ciphertext only; never log or pass the point through Temporal."""
    valid_scope, point = _scope(scope), _point(latitude, longitude)
    payload = {
        "version": 1,
        "tenant": str(valid_scope.tenant),
        "business": str(valid_scope.business),
        "origin": str(valid_scope.origin),
        "effect": str(valid_scope.effect),
        "candidate": str(valid_scope.candidate),
        "context_version": valid_scope.context_version,
        "latitude": point.latitude,
        "longitude": point.longitude,
    }
    return _cipher(settings).encrypt(json.dumps(payload, separators=(",", ":"), allow_nan=False).encode()).decode()


def decrypt_geocoding_point(settings: Settings, scope: GeocodingPointScope, ciphertext: object) -> GeocodingPoint:
    """Authenticate the scope and return the point only inside a trusted activity."""
    valid_scope = _scope(scope)
    if not isinstance(ciphertext, str) or not 1 <= len(ciphertext) <= 4096:
        raise GeocodingCipherError("GEOCODING_POINT_UNAVAILABLE")
    try:
        value = json.loads(_cipher(settings).decrypt(ciphertext.encode()), object_pairs_hook=_object)
        if (
            not isinstance(value, dict)
            or set(value)
            != {
                "version",
                "tenant",
                "business",
                "origin",
                "effect",
                "candidate",
                "context_version",
                "latitude",
                "longitude",
            }
            or value["version"] != 1
            or type(value["version"]) is not int
            or value["tenant"] != str(valid_scope.tenant)
            or value["business"] != str(valid_scope.business)
            or value["origin"] != str(valid_scope.origin)
            or value["effect"] != str(valid_scope.effect)
            or value["candidate"] != str(valid_scope.candidate)
            or type(value["context_version"]) is not int
            or value["context_version"] != valid_scope.context_version
        ):
            raise ValueError
        return _point(value["latitude"], value["longitude"])
    except (InvalidToken, ValueError, UnicodeError, TypeError, KeyError, GeocodingCipherError):
        raise GeocodingCipherError("GEOCODING_POINT_UNAVAILABLE") from None
