"""Opt-in, one-profile Apify transport; not wired to a real budget or product.

The budget guard must atomically reserve and claim each operation before I/O,
commit and release every database lock, and verify ownership of the saved run.
Event charge limits do not necessarily cap other Apify platform charges.
The provider creates a remote dataset; retention and deletion need a separate
policy before integration. This adapter never persists or logs its response.
"""

import json
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal, Protocol
from uuid import UUID

import httpx
from pydantic import SecretStr

from app.schemas.owner_references import instagram_handle


class ProfileCheckError(Exception):
    """Stable code only; never include a profile, token, or provider payload."""


class ProfileBudgetGuard(Protocol):
    async def claim_submission(self, operation_id: UUID, username: str) -> int | None:
        """Bind normalized username, commit budget and one-shot claim before I/O."""
        ...

    async def claim_inspection(
        self, operation_id: UUID, submission_id: UUID, username: str, run_id: str, dataset_id: str
    ) -> bool:
        """Verify the bound username and run, then claim metadata and dataset reads."""
        ...


@dataclass(frozen=True, repr=False)
class SubmittedProfileCheck:
    submission_id: UUID
    username: str
    run_id: str
    dataset_id: str


@dataclass(frozen=True, repr=False)
class ProfileCheckResult:
    state: Literal["pending", "public", "private", "partial", "not_found_unconfirmed", "invalid", "unavailable"]
    provider_status: str | None
    retryable: bool
    association_confirmed: Literal[False] = False
    posts_analyzed: Literal[False] = False


def _valid_remote_id(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value) is not None


def _normalize(value: str) -> str:
    try:
        if not isinstance(value, str) or not 1 <= len(value) <= 200:
            raise ValueError
        return instagram_handle(value)
    except ValueError:
        raise ProfileCheckError("PROFILE_INPUT_INVALID") from None


def _parse_result(rows: object, expected: str) -> ProfileCheckResult:
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise ProfileCheckError("PROFILE_RESULT_UNCERTAIN")
    row = rows[0]
    try:
        if _normalize(row["input"]) != expected:
            raise ValueError
        status = row["status"]
        if not isinstance(status, str):
            raise ValueError
        if status in {"SUCCESS", "PARTIAL_RESULT"}:
            if _normalize(row["username"]) != expected:
                raise ValueError
            private = row.get("isPrivate")
            if private is not None and type(private) is not bool:
                raise ValueError
            if private is True:
                return ProfileCheckResult("private", status, False)
            if status == "PARTIAL_RESULT" or private is None:
                return ProfileCheckResult("partial", status, True)
            return ProfileCheckResult("public", status, False)
        if status == "PROFILE_NOT_FOUND":
            # This actor may use an unidentified fallback; do not claim the @ is nonexistent.
            return ProfileCheckResult("not_found_unconfirmed", status, True)
        if status == "INVALID_INPUT":
            return ProfileCheckResult("invalid", status, False)
        if status in {
            "PROFILE_UNAVAILABLE",
            "RATE_LIMITED",
            "LOGIN_WALL",
            "BLOCKED",
            "TEMPORARY_INSTAGRAM_ERROR",
            "PROVIDER_ERROR",
        }:
            return ProfileCheckResult("unavailable", status, True)
        raise ValueError
    except (KeyError, TypeError, ValueError, ProfileCheckError):
        raise ProfileCheckError("PROFILE_RESULT_UNCERTAIN") from None


class ApifyProfileCheck:
    def __init__(
        self,
        token: SecretStr | None = None,
        guard: ProfileBudgetGuard | None = None,
        *,
        enabled: bool = False,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._token, self._guard, self._enabled, self._transport = token, guard, enabled, transport

    def _configured(self) -> tuple[SecretStr, ProfileBudgetGuard]:
        if not self._enabled or self._token is None or not self._token.get_secret_value() or self._guard is None:
            raise ProfileCheckError("PROFILE_CHECK_DISABLED")
        return self._token, self._guard

    async def _request_json(self, request: httpx.Request) -> object:
        transport = self._transport or httpx.AsyncHTTPTransport(retries=0, trust_env=False)
        try:
            # Use the transport directly so httpx cannot log profile data in a request URL.
            async with transport:
                response = await transport.handle_async_request(request)
                try:
                    response.request = request
                    response.raise_for_status()
                    content = bytearray()
                    async for chunk in response.aiter_bytes():
                        content.extend(chunk)
                        if len(content) > 1_000_000:
                            raise ValueError
                    return json.loads(content)
                finally:
                    await response.aclose()
        except (httpx.HTTPError, ValueError, TypeError):
            raise ProfileCheckError("PROFILE_RESULT_UNCERTAIN") from None

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

    async def submit(self, profile: str, operation_id: UUID) -> SubmittedProfileCheck:
        username = _normalize(profile)
        if not isinstance(operation_id, UUID):
            raise ProfileCheckError("PROFILE_INPUT_INVALID")
        token, guard = self._configured()
        try:
            max_event_micros = await guard.claim_submission(operation_id, username)
        except Exception:
            raise ProfileCheckError("PROFILE_BUDGET_UNAVAILABLE") from None
        if type(max_event_micros) is not int or not 0 < max_event_micros <= 100_000_000:
            raise ProfileCheckError("PROFILE_BUDGET_UNAVAILABLE")
        request = self._request(
            "POST",
            "https://api.apify.com/v2/acts/coregent~instagram-profile-scraper/runs",
            token,
            params={
                "maxTotalChargeUsd": str(Decimal(max_event_micros) / Decimal(1_000_000)),
                "timeout": "120",
                "memory": "1024",
                "restartOnError": "false",
                "forcePermissionLevel": "LIMITED_PERMISSIONS",
            },
            body={
                "profiles": [username],
                "includeBusinessContact": False,
                "includeBioLinks": False,
                "includeRelatedProfiles": False,
                "includeRecentPosts": False,
                "maxConcurrency": 1,
                "maxRetries": 0,
                "debugMode": False,
            },
        )
        try:
            body = await self._request_json(request)
            if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
                raise ValueError
            data = body["data"]
            if not _valid_remote_id(data.get("id")) or not _valid_remote_id(data.get("defaultDatasetId")):
                raise ValueError
            return SubmittedProfileCheck(operation_id, username, data["id"], data["defaultDatasetId"])
        except (ValueError, ProfileCheckError):
            # A timed-out or malformed submission may still have started remotely.
            raise ProfileCheckError("PROFILE_SUBMISSION_UNCERTAIN") from None

    async def inspect(self, run: SubmittedProfileCheck, operation_id: UUID) -> ProfileCheckResult:
        if (
            not isinstance(run, SubmittedProfileCheck)
            or not isinstance(run.submission_id, UUID)
            or not isinstance(operation_id, UUID)
            or not _valid_remote_id(run.run_id)
            or not _valid_remote_id(run.dataset_id)
            or _normalize(run.username) != run.username
        ):
            raise ProfileCheckError("PROFILE_INPUT_INVALID")
        token, guard = self._configured()
        try:
            claimed = await guard.claim_inspection(
                operation_id, run.submission_id, run.username, run.run_id, run.dataset_id
            )
        except Exception:
            raise ProfileCheckError("PROFILE_BUDGET_UNAVAILABLE") from None
        if claimed is not True:
            raise ProfileCheckError("PROFILE_BUDGET_UNAVAILABLE")
        body = await self._request_json(
            self._request("GET", f"https://api.apify.com/v2/actor-runs/{run.run_id}", token)
        )
        if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
            raise ProfileCheckError("PROFILE_RESULT_UNCERTAIN")
        data = body["data"]
        if data.get("id") != run.run_id or data.get("defaultDatasetId") != run.dataset_id:
            raise ProfileCheckError("PROFILE_RESULT_UNCERTAIN")
        status = data.get("status")
        if not isinstance(status, str):
            raise ProfileCheckError("PROFILE_RESULT_UNCERTAIN")
        if status in {"READY", "RUNNING", "TIMING-OUT", "ABORTING"}:
            return ProfileCheckResult("pending", None, True)
        if status in {"FAILED", "TIMED-OUT", "ABORTED"}:
            return ProfileCheckResult("unavailable", None, True)
        if status != "SUCCEEDED":
            raise ProfileCheckError("PROFILE_RESULT_UNCERTAIN")
        rows = await self._request_json(
            self._request(
                "GET",
                f"https://api.apify.com/v2/datasets/{run.dataset_id}/items",
                token,
                params={"clean": "true", "limit": "2"},
            )
        )
        return _parse_result(rows, run.username)
