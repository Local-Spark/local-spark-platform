"""Mock-only Instagram profile display-name retrieval, with no persistence.

The fixed actor reads Instagram profiles, not Google Maps. Run and dataset
identities must be fenced by a later durable integration. The result does not
prove that the profile belongs to a particular establishment.

The actor's documented profile response can include recent posts in its remote
dataset even when only ``fullName`` is needed. Extra fields must be discarded
without storing them in this platform. The product does not require deletion
of the provider's internal resources.
"""

import json
import re
from dataclasses import dataclass
from typing import Literal, Protocol, cast
from uuid import UUID

import httpx
from pydantic import SecretStr

from app.schemas.owner_references import instagram_handle


class InstagramNameError(Exception):
    """A stable failure without account names, credentials or raw responses."""


@dataclass(frozen=True, repr=False)
class NameRequest:
    method: str
    url: str
    body: bytes
    credential: SecretStr
    headers: tuple[tuple[str, str], ...]


@dataclass(frozen=True, repr=False)
class NameRun:
    submission_id: UUID
    handle: str
    actor_id: str
    run_id: str
    dataset_id: str
    key_value_store_id: str
    request_queue_id: str
    build_number: str
    build_id: str


@dataclass(frozen=True, repr=False)
class NameInspection:
    run: NameRun
    run_request: NameRequest
    dataset_request: NameRequest


@dataclass(frozen=True, repr=False)
class InstagramNameResult:
    state: Literal["pending", "found", "unavailable"]
    full_name: str | None = None
    association_confirmed: Literal[False] = False


class InstagramNameGuard(Protocol):
    async def claim_submission(self, operation: UUID, request: NameRequest) -> bool:
        """Bind exact actor request, billing credential and reservation."""
        ...

    async def claim_inspection(self, operation: UUID, intent: NameInspection) -> bool:
        """Bind the original run identity and both reads before inspection."""
        ...

    async def submission_uncertain(self, operation: UUID, request: NameRequest) -> None:
        """Keep a dispatched attempt fenced and its budget reserved."""
        ...

    async def inspection_uncertain(self, operation: UUID, intent: NameInspection) -> None:
        """Keep an inconclusive inspection fenced for recovery."""
        ...


_ENDPOINT = "https://api.apify.com/v2/acts/apify~instagram-profile-scraper/runs"
_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")
_BUILD = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")


def _id(value: object) -> bool:
    return isinstance(value, str) and _ID.fullmatch(value) is not None


def _build(value: object) -> bool:
    return isinstance(value, str) and len(value) <= 64 and _BUILD.fullmatch(value) is not None


def _handle(value: object) -> str:
    if not isinstance(value, str) or len(value) > 200:
        raise InstagramNameError("INSTAGRAM_NAME_INPUT_INVALID")
    try:
        return instagram_handle(value)
    except ValueError:
        raise InstagramNameError("INSTAGRAM_NAME_INPUT_INVALID") from None


def _request(
    method: str,
    url: str,
    credential: SecretStr,
    *,
    params: dict[str, str] | None = None,
    body: dict[str, object] | None = None,
) -> httpx.Request:
    return httpx.Request(
        method,
        url,
        headers={"Authorization": f"Bearer {credential.get_secret_value()}"},
        params=params,
        json=body,
        extensions={"timeout": {"connect": 5.0, "read": 15.0, "write": 5.0, "pool": 5.0}},
    )


def _bind(request: httpx.Request, credential: SecretStr) -> NameRequest:
    if request.headers.get("authorization") != f"Bearer {credential.get_secret_value()}":
        raise InstagramNameError("INSTAGRAM_NAME_INPUT_INVALID")
    headers = tuple(
        (name, request.headers[name]) for name in ("content-length", "content-type") if name in request.headers
    )
    return NameRequest(request.method, str(request.url), request.content, credential, headers)


async def _json(request: httpx.Request, transport: httpx.MockTransport, expected_status: int) -> object:
    try:
        async with transport:
            response = await transport.handle_async_request(request)
            try:
                if response.status_code != expected_status:
                    raise ValueError
                data = bytearray()
                async for chunk in response.aiter_bytes():
                    data.extend(chunk)
                    if len(data) > 1_000_000:
                        raise ValueError
                return json.loads(data)
            finally:
                await response.aclose()
    except Exception:
        raise InstagramNameError("INSTAGRAM_NAME_RESULT_UNCERTAIN") from None


def _name(rows: object, expected: str) -> InstagramNameResult:
    if rows == []:
        return InstagramNameResult("unavailable")
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise InstagramNameError("INSTAGRAM_NAME_RESULT_UNCERTAIN")
    row = rows[0]
    username = row.get("username")
    try:
        if (
            "error" in row
            or not isinstance(username, str)
            or username.lower() != _handle(username)
            or _handle(username) != expected
        ):
            raise ValueError
        value = row.get("fullName")
        if value is None or value == "":
            return InstagramNameResult("unavailable")
        if not isinstance(value, str) or not value.strip() or len(value) > 200 or any(ord(c) < 32 for c in value):
            raise ValueError
        value.encode("utf-8")
        return InstagramNameResult("found", value.strip())
    except (ValueError, UnicodeEncodeError, InstagramNameError):
        raise InstagramNameError("INSTAGRAM_NAME_RESULT_UNCERTAIN") from None


class ApifyInstagramName:
    """Explicitly disabled without a configured guard and mock transport."""

    def __init__(
        self,
        token: SecretStr | None = None,
        guard: InstagramNameGuard | None = None,
        *,
        enabled: bool = False,
        transport: httpx.MockTransport | None = None,
        actor_id: str | None = None,
        actor_build: str | None = None,
        max_actor_usd_micros: int = 0,
    ) -> None:
        self._token, self._guard, self._enabled, self._transport = token, guard, enabled, transport
        self._actor_id, self._actor_build, self._limit = actor_id, actor_build, max_actor_usd_micros

    def _configured(self) -> tuple[SecretStr, InstagramNameGuard, httpx.MockTransport]:
        if (
            not self._enabled
            or not isinstance(self._token, SecretStr)
            or not self._token.get_secret_value()
            or self._guard is None
            or not isinstance(self._transport, httpx.MockTransport)
            or not _id(self._actor_id)
            or not _build(self._actor_build)
            or type(self._limit) is not int
            or not 0 < self._limit <= 5_000_000
        ):
            raise InstagramNameError("INSTAGRAM_NAME_DISABLED")
        return self._token, self._guard, self._transport

    async def submit(self, profile: str, operation: UUID) -> NameRun:
        handle = _handle(profile)
        if not isinstance(operation, UUID):
            raise InstagramNameError("INSTAGRAM_NAME_INPUT_INVALID")
        token, guard, transport = self._configured()
        dollars, micros = divmod(self._limit, 1_000_000)
        charge = str(dollars) if not micros else f"{dollars}.{micros:06d}".rstrip("0")
        request = _request(
            "POST",
            _ENDPOINT,
            token,
            params={
                "build": cast(str, self._actor_build),
                "maxTotalChargeUsd": charge,
                "maxItems": "1",
                "timeout": "120",
                "memory": "1024",
                "restartOnError": "false",
                "forcePermissionLevel": "LIMITED_PERMISSIONS",
            },
            body={"usernames": [handle], "includeAboutSection": False},
        )
        binding = _bind(request, token)
        try:
            claimed = await guard.claim_submission(operation, binding)
        except Exception:
            raise InstagramNameError("INSTAGRAM_NAME_BUDGET_UNAVAILABLE") from None
        if claimed is not True:
            raise InstagramNameError("INSTAGRAM_NAME_BUDGET_UNAVAILABLE")
        try:
            body = await _json(request, transport, 201)
            if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
                raise ValueError
            data = body["data"]
            ids = tuple(
                data.get(key)
                for key in (
                    "id",
                    "actId",
                    "defaultDatasetId",
                    "defaultKeyValueStoreId",
                    "defaultRequestQueueId",
                    "buildId",
                )
            )
            if (
                not all(_id(value) for value in ids)
                or ids[1] != self._actor_id
                or data.get("buildNumber") != self._actor_build
            ):
                raise ValueError
            return NameRun(
                operation,
                handle,
                cast(str, ids[1]),
                cast(str, ids[0]),
                cast(str, ids[2]),
                cast(str, ids[3]),
                cast(str, ids[4]),
                cast(str, self._actor_build),
                cast(str, ids[5]),
            )
        except (InstagramNameError, ValueError):
            try:
                await guard.submission_uncertain(operation, binding)
            except Exception:
                pass
            raise InstagramNameError("INSTAGRAM_NAME_SUBMISSION_UNCERTAIN") from None

    async def inspect(self, run: NameRun, operation: UUID) -> InstagramNameResult:
        if (
            not isinstance(run, NameRun)
            or not isinstance(operation, UUID)
            or not isinstance(run.submission_id, UUID)
            or not all(
                _id(value)
                for value in (
                    run.actor_id,
                    run.run_id,
                    run.dataset_id,
                    run.key_value_store_id,
                    run.request_queue_id,
                    run.build_id,
                )
            )
            or not _build(run.build_number)
            or _handle(run.handle) != run.handle
        ):
            raise InstagramNameError("INSTAGRAM_NAME_INPUT_INVALID")
        token, guard, transport = self._configured()
        if run.actor_id != self._actor_id or run.build_number != self._actor_build:
            raise InstagramNameError("INSTAGRAM_NAME_INPUT_INVALID")
        run_request = _request("GET", f"https://api.apify.com/v2/actor-runs/{run.run_id}", token)
        dataset_request = _request(
            "GET",
            f"https://api.apify.com/v2/datasets/{run.dataset_id}/items",
            token,
            params={"clean": "true", "limit": "2"},
        )
        intent = NameInspection(run, _bind(run_request, token), _bind(dataset_request, token))
        try:
            claimed = await guard.claim_inspection(operation, intent)
        except Exception:
            raise InstagramNameError("INSTAGRAM_NAME_BUDGET_UNAVAILABLE") from None
        if claimed is not True:
            raise InstagramNameError("INSTAGRAM_NAME_BUDGET_UNAVAILABLE")
        try:
            body = await _json(run_request, transport, 200)
            if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
                raise ValueError
            data = body["data"]
            expected = {
                "id": run.run_id,
                "actId": run.actor_id,
                "defaultDatasetId": run.dataset_id,
                "defaultKeyValueStoreId": run.key_value_store_id,
                "defaultRequestQueueId": run.request_queue_id,
                "buildNumber": run.build_number,
                "buildId": run.build_id,
            }
            if any(data.get(key) != value for key, value in expected.items()):
                raise ValueError
            status = data.get("status")
            if status in ("READY", "RUNNING", "TIMING-OUT", "ABORTING"):
                return InstagramNameResult("pending")
            if status in ("FAILED", "TIMED-OUT", "ABORTED"):
                return InstagramNameResult("unavailable")
            if status != "SUCCEEDED":
                raise ValueError
            return _name(await _json(dataset_request, transport, 200), run.handle)
        except (InstagramNameError, ValueError):
            try:
                await guard.inspection_uncertain(operation, intent)
            except Exception:
                pass
            raise InstagramNameError("INSTAGRAM_NAME_RESULT_UNCERTAIN") from None
