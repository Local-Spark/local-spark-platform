"""Opt-in Google Geocoding v4 adapter; no persistence or implicit selection.

The caller must use a durable budget guard that commits a one-shot operation
claim before returning. No database lock may remain held during the request.
The shop-address activity wires this adapter to its durable address and cost guards.
"""

import json
import math
from dataclasses import dataclass
from typing import Literal, Protocol
from uuid import UUID

import httpx
from pydantic import SecretStr


class GeocodingError(Exception):
    """Stable code only; never include addresses, keys, or provider bodies."""


GEOCODING_FIELD_MASK = (
    "results.placeId,results.formattedAddress,results.location,"
    "results.granularity,results.postalAddress.regionCode,results.addressComponents"
)


class GeocodingBudgetGuard(Protocol):
    async def claim(self, operation_id: UUID, request: "GeocodingChargeableRequest") -> bool:
        """Commit a durable reservation and one-shot claim, then release locks."""
        ...

    async def uncertain(self) -> None:
        """Keep the reservation if a response may have been billed."""
        ...


@dataclass(frozen=True, repr=False)
class GeocodingChargeableRequest:
    """Private exact request, passed only to the internal budget guard."""

    method: str
    url: str
    field_mask: str
    credential: SecretStr


@dataclass(frozen=True, repr=False)
class GeocodingAddressComponent:
    long_text: str
    short_text: str | None
    types: tuple[str, ...]


@dataclass(frozen=True, repr=False)
class GeocodingCandidate:
    place_id: str
    formatted_address: str
    latitude: float
    longitude: float
    granularity: str
    country: str | None
    address_components: tuple[GeocodingAddressComponent, ...] = ()
    confirmed: Literal[False] = False


def _candidate(value: object) -> GeocodingCandidate:
    try:
        if not isinstance(value, dict):
            raise ValueError
        place_id, address = value["placeId"], value["formattedAddress"]
        location, granularity = value["location"], value["granularity"]
        if not isinstance(place_id, str) or not 1 <= len(place_id) <= 2048:
            raise ValueError
        if not isinstance(address, str) or not 1 <= len(address.strip()) <= 500:
            raise ValueError
        if not isinstance(location, dict) or not isinstance(granularity, str) or not 1 <= len(granularity) <= 100:
            raise ValueError
        latitude, longitude = location["latitude"], location["longitude"]
        if any(type(item) not in (int, float) or not math.isfinite(item) for item in (latitude, longitude)):
            raise ValueError
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError
        postal = value.get("postalAddress", {})
        if not isinstance(postal, dict):
            raise ValueError
        country = postal.get("regionCode")
        if country is not None and (not isinstance(country, str) or len(country) != 2 or not country.isascii()):
            raise ValueError
        components = value.get("addressComponents", [])
        if not isinstance(components, list) or len(components) > 100:
            raise ValueError
        parsed = []
        for component in components:
            if not isinstance(component, dict):
                raise ValueError
            long_text, short_text, types = component.get("longText"), component.get("shortText"), component.get("types")
            if (
                not isinstance(long_text, str)
                or not 1 <= len(long_text.strip()) <= 300
                or (short_text is not None and (not isinstance(short_text, str) or not 1 <= len(short_text) <= 300))
                or not isinstance(types, list)
                or not 1 <= len(types) <= 100
                or any(not isinstance(item, str) or not 1 <= len(item) <= 100 for item in types)
            ):
                raise ValueError
            parsed.append(GeocodingAddressComponent(long_text, short_text, tuple(types)))
        return GeocodingCandidate(
            place_id, address, float(latitude), float(longitude), granularity, country, tuple(parsed)
        )
    except (KeyError, TypeError, ValueError, OverflowError):
        raise GeocodingError("GEOCODING_RESPONSE_INVALID") from None


class GoogleGeocoding:
    def __init__(
        self,
        key: SecretStr | None = None,
        guard: GeocodingBudgetGuard | None = None,
        *,
        enabled: bool = False,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._key, self._guard, self._enabled, self._transport = key, guard, enabled, transport

    async def geocode(self, address: str, operation_id: UUID) -> tuple[GeocodingCandidate, ...]:
        if not isinstance(address, str) or not 1 <= len(address.strip()) <= 300 or not isinstance(operation_id, UUID):
            raise GeocodingError("GEOCODING_INPUT_INVALID")
        if (
            not self._enabled
            or not isinstance(self._key, SecretStr)
            or not self._key.get_secret_value()
            or self._guard is None
        ):
            raise GeocodingError("GEOCODING_DISABLED")
        try:
            address.encode("utf-8")
        except UnicodeEncodeError:
            raise GeocodingError("GEOCODING_INPUT_INVALID") from None
        try:
            key_bytes = self._key.get_secret_value().encode("ascii")
            if any(byte < 33 or byte > 126 for byte in key_bytes):
                raise ValueError
        except (UnicodeEncodeError, ValueError):
            raise GeocodingError("GEOCODING_DISABLED") from None
        request = httpx.Request(
            "GET",
            "https://geocode.googleapis.com/v4/geocode/address",
            params={"address.addressLines": address.strip(), "address.regionCode": "BR", "languageCode": "pt-BR"},
            headers={
                "X-Goog-Api-Key": self._key.get_secret_value(),
                "X-Goog-FieldMask": GEOCODING_FIELD_MASK,
            },
            extensions={"timeout": {"connect": 5.0, "read": 10.0, "write": 5.0, "pool": 5.0}},
        )
        binding = GeocodingChargeableRequest(
            method=request.method,
            url=str(request.url),
            field_mask=request.headers["X-Goog-FieldMask"],
            credential=self._key,
        )
        try:
            claimed = await self._guard.claim(operation_id, binding)
        except Exception:
            raise GeocodingError("GEOCODING_BUDGET_UNAVAILABLE") from None
        if claimed is not True:
            raise GeocodingError("GEOCODING_BUDGET_UNAVAILABLE")
        transport = self._transport or httpx.AsyncHTTPTransport(retries=0, trust_env=False)
        try:
            # Calling the transport directly avoids httpx's INFO log containing the private address URL.
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
                    body = json.loads(content)
                finally:
                    await response.aclose()
            if (
                not isinstance(body, dict)
                or "error" in body
                or (body and "results" not in body)
                or not isinstance(body.get("results", []), list)
            ):
                raise ValueError
            results = body.get("results", [])
            if len(results) > 100:
                raise ValueError
            return tuple(_candidate(item) for item in results)
        except GeocodingError:
            try:
                await self._guard.uncertain()
            except Exception:
                pass
            raise
        except Exception:
            try:
                await self._guard.uncertain()
            except Exception:
                pass
            raise GeocodingError("GEOCODING_RESULT_UNCERTAIN") from None
