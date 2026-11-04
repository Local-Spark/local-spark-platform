"""Opt-in Places Nearby (New) transport, with no persistence or ranking.

Only provider types explicitly supplied by a caller are accepted; mapping a
business segment to an official Google type is deliberately outside this adapter.
The budget guard must atomically reserve and claim one operation, commit and
release all database locks before returning. This transport is not wired to a
route or production guard.
"""

import json
import math
import re
from dataclasses import dataclass
from typing import Literal, Protocol
from uuid import UUID

import httpx
from pydantic import SecretStr

PLACES_FIELD_MASK = (
    "places.id,places.displayName,places.location,places.rating,places.userRatingCount,places.websiteUri,"
    "places.types,places.formattedAddress,places.addressComponents"
)


class PlacesError(Exception):
    """Stable code without request, response, or credential details."""


@dataclass(frozen=True, repr=False)
class PlacesChargeableRequest:
    """The exact chargeable request, held only in memory by the durable guard.

    It contains location and a wrapped credential so the guard can bind the
    actual billing key. Neither may be stored or logged as plaintext.
    """

    method: str
    url: str
    field_mask: str
    body: bytes
    credential: SecretStr


class PlacesBudgetGuard(Protocol):
    async def claim(self, operation_id: UUID, request: PlacesChargeableRequest) -> bool | Literal["completed_empty"]:
        """Bind and commit a one-shot reservation, then release all locks."""
        ...

    async def uncertain(self) -> None:
        """Retain a reservation when dispatch may have happened."""
        ...

    async def complete_empty(self) -> None:
        """Commit an executor-fenced, validated empty response."""
        ...


@dataclass(frozen=True, repr=False)
class PlacesAddressComponent:
    long_text: str
    short_text: str | None
    types: tuple[str, ...]


@dataclass(frozen=True, repr=False)
class PlaceCandidate:
    place_id: str
    name: str | None
    latitude: float | None
    longitude: float | None
    rating: float | None
    rating_count: int | None
    website: str | None
    types: tuple[str, ...] = ()
    formatted_address: str | None = None
    address_components: tuple[PlacesAddressComponent, ...] = ()


def _optional_text(value: object, maximum: int) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError
    return value


def _coordinate(value: object, lower: int, upper: int) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError
    if not math.isfinite(value) or not lower <= value <= upper:
        raise ValueError
    return float(value)


def _candidate(value: object) -> PlaceCandidate:
    try:
        if not isinstance(value, dict):
            raise ValueError
        place_id = _optional_text(value.get("id"), 2048)
        if place_id is None:
            raise ValueError
        name_obj = value.get("displayName")
        if name_obj is not None and not isinstance(name_obj, dict):
            raise ValueError
        name = _optional_text(name_obj.get("text") if name_obj is not None else None, 300)
        location = value.get("location")
        if location is None:
            latitude, longitude = None, None
        else:
            if not isinstance(location, dict):
                raise ValueError
            # Protobuf JSON can omit zero-valued coordinate fields.
            latitude = _coordinate(location.get("latitude", 0), -90, 90)
            longitude = _coordinate(location.get("longitude", 0), -180, 180)
        rating = value.get("rating")
        if rating is not None and (
            type(rating) not in (int, float) or not math.isfinite(rating) or not 0 <= rating <= 5
        ):
            raise ValueError
        count = value.get("userRatingCount")
        if count is not None and (type(count) is not int or count < 0):
            raise ValueError
        website = _optional_text(value.get("websiteUri"), 2048)
        formatted_address = _optional_text(value.get("formattedAddress"), 1000)
        raw_components = value.get("addressComponents", [])
        if not isinstance(raw_components, list) or len(raw_components) > 100:
            raise ValueError
        components = []
        for component in raw_components:
            if not isinstance(component, dict):
                raise ValueError
            # ProtoJSON may omit default strings/repeated fields. Validate the
            # present values before ignoring components without usable evidence.
            raw_long_text = component.get("longText")
            raw_short_text = component.get("shortText")
            long_text = _optional_text(None if raw_long_text == "" else raw_long_text, 300)
            short_text = _optional_text(None if raw_short_text == "" else raw_short_text, 300)
            component_types = component.get("types", [])
            if (
                not isinstance(component_types, list)
                or len(component_types) > 100
                or any(not isinstance(item, str) or not 1 <= len(item) <= 100 for item in component_types)
            ):
                raise ValueError
            if long_text is not None and component_types:
                components.append(PlacesAddressComponent(long_text, short_text, tuple(component_types)))
        types = value.get("types", [])
        if (
            not isinstance(types, list)
            or len(types) > 50
            or any(not isinstance(item, str) or re.fullmatch(r"[a-z][a-z0-9_]{0,79}", item) is None for item in types)
            or len(set(types)) != len(types)
        ):
            raise ValueError
        return PlaceCandidate(
            place_id,
            name,
            latitude,
            longitude,
            float(rating) if rating is not None else None,
            count,
            website,
            tuple(types),
            formatted_address,
            tuple(components),
        )
    except (TypeError, ValueError, OverflowError):
        raise PlacesError("PLACES_RESPONSE_INVALID") from None


class GooglePlacesNearby:
    def __init__(
        self,
        key: SecretStr | None = None,
        guard: PlacesBudgetGuard | None = None,
        *,
        enabled: bool = False,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._key, self._guard, self._enabled, self._transport = key, guard, enabled, transport

    async def search(
        self,
        place_type: str | None,
        latitude: float,
        longitude: float,
        radius_km: int,
        operation_id: UUID,
        *,
        primary_types: list[str] | tuple[str, ...] | None = None,
        max_results: int = 10,
    ) -> tuple[PlaceCandidate, ...]:
        """Use either one general type or explicit primary types, never their intersection."""
        try:
            if primary_types is None:
                if not isinstance(place_type, str) or re.fullmatch(r"[a-z][a-z0-9_]{0,79}", place_type) is None:
                    raise ValueError
                type_filter = {"includedTypes": [place_type]}
            else:
                if (
                    place_type is not None
                    or not isinstance(primary_types, (list, tuple))
                    or not 1 <= len(primary_types) <= 50
                    or any(
                        not isinstance(item, str) or re.fullmatch(r"[a-z][a-z0-9_]{0,79}", item) is None
                        for item in primary_types
                    )
                    or len(set(primary_types)) != len(primary_types)
                ):
                    raise ValueError
                type_filter = {"includedPrimaryTypes": list(primary_types)}
            if type(max_results) is not int or not 1 <= max_results <= 20:
                raise ValueError
            latitude, longitude = _coordinate(latitude, -90, 90), _coordinate(longitude, -180, 180)
            if type(radius_km) is not int or radius_km not in (5, 20, 50) or not isinstance(operation_id, UUID):
                raise ValueError
        except (TypeError, ValueError, OverflowError):
            raise PlacesError("PLACES_INPUT_INVALID") from None
        if (
            not self._enabled
            or not isinstance(self._key, SecretStr)
            or not self._key.get_secret_value()
            or self._guard is None
        ):
            raise PlacesError("PLACES_DISABLED")
        try:
            key_bytes = self._key.get_secret_value().encode("ascii")
            if any(byte < 33 or byte > 126 for byte in key_bytes):
                raise ValueError
        except (UnicodeEncodeError, ValueError):
            raise PlacesError("PLACES_DISABLED") from None
        body = {
            **type_filter,
            "maxResultCount": max_results,
            "languageCode": "pt-BR",
            "locationRestriction": {
                "circle": {"center": {"latitude": latitude, "longitude": longitude}, "radius": radius_km * 1000}
            },
        }
        request = httpx.Request(
            "POST",
            "https://places.googleapis.com/v1/places:searchNearby",
            json=body,
            headers={
                "X-Goog-Api-Key": self._key.get_secret_value(),
                "X-Goog-FieldMask": PLACES_FIELD_MASK,
            },
            extensions={"timeout": {"connect": 5.0, "read": 10.0, "write": 5.0, "pool": 5.0}},
        )
        binding = PlacesChargeableRequest(
            method=request.method,
            url=str(request.url),
            field_mask=request.headers["X-Goog-FieldMask"],
            body=request.content,
            credential=self._key,
        )
        try:
            claimed = await self._guard.claim(operation_id, binding)
        except Exception:
            raise PlacesError("PLACES_BUDGET_UNAVAILABLE") from None
        if claimed == "completed_empty":
            return ()
        if claimed is not True:
            raise PlacesError("PLACES_BUDGET_UNAVAILABLE")
        transport = self._transport or httpx.AsyncHTTPTransport(retries=0, trust_env=False)
        try:
            async with transport:
                response = await transport.handle_async_request(request)
                try:
                    response.request = request
                    response.raise_for_status()
                    if response.status_code != 200:
                        raise ValueError
                    content = bytearray()
                    async for chunk in response.aiter_bytes():
                        content.extend(chunk)
                        if len(content) > 1_000_000:
                            raise ValueError
                    data = json.loads(content)
                finally:
                    await response.aclose()
            if (
                not isinstance(data, dict)
                or "error" in data
                or (data and "places" not in data)
                or not isinstance(data.get("places", []), list)
            ):
                raise ValueError
            places = data.get("places", [])
            if len(places) > max_results:
                raise ValueError
            candidates = tuple(_candidate(item) for item in places)
            if not candidates:
                try:
                    await self._guard.complete_empty()
                except Exception:
                    raise PlacesError("PLACES_RESULT_UNCERTAIN") from None
            return candidates
        except PlacesError:
            try:
                await self._guard.uncertain()
            except Exception:
                # A lost confirmation must leave the existing reservation held.
                pass
            raise
        except Exception:
            try:
                await self._guard.uncertain()
            except Exception:
                # Recovery can only reconcile this attempt; it must not resend.
                pass
            raise PlacesError("PLACES_RESULT_UNCERTAIN") from None
