"""Apify Compass contacts for one Place ID with explicitly admitted spending.

The caller must provide a durable guard, releasing locks before network I/O.
The product does not require deletion of provider-managed datasets. Actor event
limits are not a bound on separate platform charges. Provenance must bind the
response to the authorized search before its profile association is used.
"""

import json
import re
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Literal, Protocol, cast
from uuid import UUID

import httpx
from pydantic import SecretStr

from app.adapters.apify_run_metadata import terminal_run_cost, terminal_run_cost_ready, validate_actor_price
from app.schemas.reference_contacts_effect import ContactsChargeableRequest, valid_place_id


class PlaceContactsError(Exception):
    """Stable code only; provider data and secrets never enter errors."""


class PlaceContactsGuard(Protocol):
    async def claim_submission(self, operation_id: UUID, request: ContactsChargeableRequest) -> bool:
        """Durably bind input, reserve budget and claim once before network I/O."""
        ...

    async def claim_inspection(self, operation_id: UUID, intent: "ContactsInspectionIntent") -> bool:
        """Commit a separate authorized read claim bound to the submitted run."""
        ...

    async def submission_uncertain(self, operation_id: UUID, request: ContactsChargeableRequest) -> None:
        """Hold a possibly billed submission for reconciliation."""
        ...

    async def inspection_uncertain(self, operation_id: UUID, intent: "ContactsInspectionIntent") -> None:
        """Hold a possibly sent inspection for reconciliation."""
        ...


@dataclass(frozen=True, repr=False)
class SubmittedPlaceContacts:
    submission_id: UUID
    place_id: str
    run_id: str
    dataset_id: str
    key_value_store_id: str
    request_queue_id: str
    build_id: str
    build_number: str
    provider_actor_id: str


@dataclass(frozen=True, repr=False)
class ContactsInspectionIntent:
    submission: SubmittedPlaceContacts
    run_request: ContactsChargeableRequest
    dataset_request: ContactsChargeableRequest


@dataclass(frozen=True, repr=False)
class SocialLink:
    platform: str
    url: str
    source: Literal["business_website"] = "business_website"


@dataclass(frozen=True, repr=False)
class PlaceContactsResult:
    state: Literal["pending", "found", "not_found_unconfirmed", "association_unverified", "unavailable"]
    website: str | None = None
    website_source: Literal["google_maps"] = "google_maps"
    social_links: tuple[SocialLink, ...] = ()
    association_confirmed: Literal[False] = False
    identity_verified: Literal[False] = False
    reported_cost_usd_micros: int | None = None
    terminal_failure: Literal["FAILED", "TIMED-OUT", "ABORTED"] | None = None


def _valid_id(value: object) -> bool:
    return valid_place_id(value)


def _valid_run_id(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value) is not None


def _safe_url(value: object) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= 2048:
        raise ValueError
    url = httpx.URL(value)
    if url.scheme not in {"http", "https"} or not url.host or url.userinfo:
        raise ValueError
    return value


def _result(rows: object, expected_place_id: str) -> PlaceContactsResult:
    if rows == []:
        return PlaceContactsResult("not_found_unconfirmed")
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise PlaceContactsError("CONTACTS_RESULT_UNCERTAIN")
    row = rows[0]
    if "error" in row or not isinstance(row.get("placeId"), str) or not row["placeId"]:
        raise PlaceContactsError("CONTACTS_RESULT_UNCERTAIN")
    # Different formats are not proof of the same place, even if the actor
    # returns a Maps CID in response to a Places API identifier.
    if row["placeId"] != expected_place_id:
        return PlaceContactsResult("association_unverified")
    try:
        website = _safe_url(row["website"]) if row.get("website") is not None else None
        links = row.get("instagrams", [])
        if not isinstance(links, list) or len(links) > 100:
            raise ValueError
        social = []
        for link in links:
            social.append(SocialLink("instagram", _safe_url(link)))
        return PlaceContactsResult("found", website=website, social_links=tuple(social))
    except (ValueError, TypeError, httpx.InvalidURL):
        raise PlaceContactsError("CONTACTS_RESULT_UNCERTAIN") from None


class ApifyPlaceContacts:
    def __init__(
        self,
        token: SecretStr | None = None,
        guard: PlaceContactsGuard | None = None,
        *,
        enabled: bool = False,
        transport: httpx.MockTransport | None = None,
        actor_build: str | None = None,
        provider_actor_id: str | None = None,
        max_actor_usd_micros: int = 0,
        network_enabled: bool = False,
    ) -> None:
        self._token, self._guard, self._enabled, self._transport = token, guard, enabled, transport
        self._actor_build, self._max_actor_usd_micros = actor_build, max_actor_usd_micros
        self._provider_actor_id = provider_actor_id
        self._network_enabled = network_enabled

    def _configured(self) -> tuple[SecretStr, PlaceContactsGuard]:
        if (
            not self._enabled
            or not isinstance(self._token, SecretStr)
            or not self._token.get_secret_value()
            or self._guard is None
            or (not isinstance(self._transport, httpx.MockTransport) and not self._network_enabled)
            or (self._network_enabled and self._provider_actor_id != "nwua9Gu5YrADL7ZDj")
            or not _valid_run_id(self._provider_actor_id)
            or not isinstance(self._actor_build, str)
            or len(self._actor_build) > 64
            or re.fullmatch(r"[0-9]+[.][0-9]+[.][0-9]+", self._actor_build) is None
            or type(self._max_actor_usd_micros) is not int
            or not 0 < self._max_actor_usd_micros <= 5_000_000
        ):
            raise PlaceContactsError("CONTACTS_DISABLED")
        try:
            token_bytes = self._token.get_secret_value().encode("ascii")
            if any(byte < 33 or byte > 126 for byte in token_bytes):
                raise ValueError
        except (UnicodeEncodeError, ValueError):
            raise PlaceContactsError("CONTACTS_DISABLED") from None
        return self._token, self._guard

    async def _request_json(self, request: httpx.Request) -> object:
        transport: httpx.AsyncBaseTransport | None = self._transport
        if not isinstance(transport, httpx.MockTransport) and not self._network_enabled:
            raise PlaceContactsError("CONTACTS_DISABLED")
        if request.url.scheme != "https" or request.url.host != "api.apify.com":
            raise PlaceContactsError("CONTACTS_INPUT_INVALID")
        transport = transport or httpx.AsyncHTTPTransport(retries=0, trust_env=False)
        try:
            async with transport:
                response = await transport.handle_async_request(request)
                try:
                    response.request = request
                    response.raise_for_status()
                    if response.status_code != (201 if request.method == "POST" else 200):
                        raise ValueError
                    content = bytearray()
                    async for chunk in response.aiter_bytes():
                        content.extend(chunk)
                        if len(content) > 1_000_000:
                            raise ValueError
                    return json.loads(content)
                finally:
                    await response.aclose()
        except Exception:
            raise PlaceContactsError("CONTACTS_RESULT_UNCERTAIN") from None

    async def _check_current_pricing(self, token: SecretStr) -> None:
        """A metadata GET never runs an Actor or consumes the search allowance."""
        payload = await self._request_json(
            self._request("GET", f"https://api.apify.com/v2/acts/{self._provider_actor_id}", token)
        )
        try:
            validate_actor_price(
                payload,
                actor_id=cast(str, self._provider_actor_id),
                build=cast(str, self._actor_build),
                maximum_usd_micros=self._max_actor_usd_micros,
            )
        except ValueError:
            raise PlaceContactsError("CONTACTS_PRICING_UNAVAILABLE") from None

    @staticmethod
    def _request(
        method: str,
        url: str,
        token: SecretStr,
        *,
        params: dict[str, str] | None = None,
        body: dict[str, object] | None = None,
    ) -> httpx.Request:
        return httpx.Request(
            method,
            url,
            headers={"Authorization": f"Bearer {token.get_secret_value()}"},
            extensions={"timeout": {"connect": 5.0, "read": 15.0, "write": 5.0, "pool": 5.0}},
            params=params,
            json=body,
        )

    @staticmethod
    def _bind(request: httpx.Request, credential: SecretStr, provider_actor_id: str) -> ContactsChargeableRequest:
        if request.headers.get("authorization") != f"Bearer {credential.get_secret_value()}":
            raise PlaceContactsError("CONTACTS_INPUT_INVALID")
        headers = tuple(
            (name, request.headers[name]) for name in ("content-length", "content-type") if name in request.headers
        )
        return ContactsChargeableRequest(
            request.method, str(request.url), request.content, credential, headers, provider_actor_id
        )

    async def submit(self, place_id: str, operation_id: UUID) -> SubmittedPlaceContacts:
        if not _valid_id(place_id) or not isinstance(operation_id, UUID):
            raise PlaceContactsError("CONTACTS_INPUT_INVALID")
        token, guard = self._configured()
        if self._network_enabled:
            await self._check_current_pricing(token)
        build = cast(str, self._actor_build)
        request = self._request(
            "POST",
            f"https://api.apify.com/v2/acts/{self._provider_actor_id}/runs",
            token,
            params={
                "build": build,
                "maxTotalChargeUsd": str(Decimal(self._max_actor_usd_micros) / Decimal(1_000_000)),
                "timeout": "120",
                "memory": "1024",
                "restartOnError": "false",
                "forcePermissionLevel": "LIMITED_PERMISSIONS",
            },
            body={
                "placeIds": [place_id],
                "scrapeContacts": True,
                "maxCrawledPlacesPerSearch": 1,
                "language": "pt-BR",
            },
        )
        binding = self._bind(request, token, cast(str, self._provider_actor_id))
        try:
            claimed = await guard.claim_submission(operation_id, binding)
        except Exception:
            raise PlaceContactsError("CONTACTS_BUDGET_UNAVAILABLE") from None
        if claimed is not True:
            raise PlaceContactsError("CONTACTS_BUDGET_UNAVAILABLE")
        try:
            body = await self._request_json(request)
            if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
                raise ValueError
            data = body["data"]
            ids = tuple(
                data.get(key)
                for key in ("id", "defaultDatasetId", "defaultKeyValueStoreId", "defaultRequestQueueId", "buildId")
            )
            if (
                not all(_valid_run_id(value) for value in ids)
                or data.get("buildNumber") != self._actor_build
                or data.get("actId") != self._provider_actor_id
            ):
                raise ValueError
            return SubmittedPlaceContacts(
                operation_id,
                place_id,
                cast(str, ids[0]),
                cast(str, ids[1]),
                cast(str, ids[2]),
                cast(str, ids[3]),
                cast(str, ids[4]),
                build,
                cast(str, self._provider_actor_id),
            )
        except (ValueError, PlaceContactsError):
            try:
                await guard.submission_uncertain(operation_id, binding)
            except Exception:
                pass
            raise PlaceContactsError("CONTACTS_SUBMISSION_UNCERTAIN") from None

    async def inspect(self, run: SubmittedPlaceContacts, operation_id: UUID) -> PlaceContactsResult:
        if (
            not isinstance(run, SubmittedPlaceContacts)
            or not isinstance(run.submission_id, UUID)
            or not isinstance(operation_id, UUID)
            or not _valid_id(run.place_id)
            or not _valid_run_id(run.run_id)
            or not _valid_run_id(run.dataset_id)
            or not _valid_run_id(run.key_value_store_id)
            or not _valid_run_id(run.request_queue_id)
            or not _valid_run_id(run.build_id)
            or not _valid_run_id(run.provider_actor_id)
            or not isinstance(run.build_number, str)
            or re.fullmatch(r"[0-9]+[.][0-9]+[.][0-9]+", run.build_number) is None
        ):
            raise PlaceContactsError("CONTACTS_INPUT_INVALID")
        token, guard = self._configured()
        if run.provider_actor_id != self._provider_actor_id:
            raise PlaceContactsError("CONTACTS_INPUT_INVALID")
        run_request = self._request("GET", f"https://api.apify.com/v2/actor-runs/{run.run_id}", token)
        dataset_request = self._request(
            "GET",
            f"https://api.apify.com/v2/datasets/{run.dataset_id}/items",
            token,
            params={"clean": "true", "limit": "2"},
        )
        intent = ContactsInspectionIntent(
            run,
            self._bind(run_request, token, run.provider_actor_id),
            self._bind(dataset_request, token, run.provider_actor_id),
        )
        try:
            claimed = await guard.claim_inspection(operation_id, intent)
        except Exception:
            raise PlaceContactsError("CONTACTS_BUDGET_UNAVAILABLE") from None
        if claimed is not True:
            raise PlaceContactsError("CONTACTS_BUDGET_UNAVAILABLE")
        try:
            return await self._inspect_claimed(run, run_request, dataset_request)
        except PlaceContactsError:
            try:
                await guard.inspection_uncertain(operation_id, intent)
            except Exception:
                pass
            raise

    async def _inspect_claimed(
        self, run: SubmittedPlaceContacts, run_request: httpx.Request, dataset_request: httpx.Request
    ) -> PlaceContactsResult:
        body = await self._request_json(run_request)
        if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
            raise PlaceContactsError("CONTACTS_RESULT_UNCERTAIN")
        data = body["data"]
        if (
            data.get("actId") != run.provider_actor_id
            or data.get("id") != run.run_id
            or data.get("defaultDatasetId") != run.dataset_id
            or data.get("defaultKeyValueStoreId") != run.key_value_store_id
            or data.get("defaultRequestQueueId") != run.request_queue_id
            or data.get("buildId") != run.build_id
            or data.get("buildNumber") != run.build_number
        ):
            raise PlaceContactsError("CONTACTS_RESULT_UNCERTAIN")
        status = data.get("status")
        if not isinstance(status, str):
            raise PlaceContactsError("CONTACTS_RESULT_UNCERTAIN")
        if status in {"READY", "RUNNING", "TIMING-OUT", "ABORTING"}:
            return PlaceContactsResult("pending")
        if status not in {"SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"}:
            raise PlaceContactsError("CONTACTS_RESULT_UNCERTAIN")
        if not terminal_run_cost_ready(data):
            return PlaceContactsResult("pending")
        if status in {"FAILED", "TIMED-OUT", "ABORTED"}:
            return PlaceContactsResult(
                "unavailable",
                reported_cost_usd_micros=_reported_cost(data),
                terminal_failure=cast(Literal["FAILED", "TIMED-OUT", "ABORTED"], status),
            )
        rows = await self._request_json(dataset_request)
        return replace(_result(rows, run.place_id), reported_cost_usd_micros=_reported_cost(data))


def _reported_cost(data: dict[str, object]) -> int | None:
    """Authenticated run total, rounded up; absence never becomes a zero bill."""
    try:
        return terminal_run_cost(data)
    except ValueError:
        raise PlaceContactsError("CONTACTS_RESULT_UNCERTAIN") from None
