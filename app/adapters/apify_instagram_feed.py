"""Bounded Instagram collection with explicit network and budget admission.

Raw posts, captions and image URLs remain in memory, never database, logs or
Temporal. Recovery inspects the persisted run instead of starting another one.
"""

import json
import re
import unicodedata
from dataclasses import dataclass, replace
from typing import Literal, Protocol, cast
from uuid import UUID

import httpx
from pydantic import SecretStr

from app.adapters.apify_run_metadata import terminal_run_cost, terminal_run_cost_ready, validate_actor_price
from app.schemas.owner_references import instagram_handle


class InstagramFeedError(Exception):
    """A stable error which never includes a username, post or provider body."""


@dataclass(frozen=True, repr=False)
class FeedChargeableRequest:
    """Exact request and wrapped credential, passed only to a durable guard."""

    method: str
    url: str
    body: bytes
    credential: SecretStr
    headers: tuple[tuple[str, str], ...]


@dataclass(frozen=True, repr=False)
class SubmittedInstagramFeed:
    submission_id: UUID
    username: str
    run_id: str
    dataset_id: str
    key_value_store_id: str
    request_queue_id: str
    build_number: str
    build_id: str
    results_limit: int


@dataclass(frozen=True, repr=False)
class FeedInspectionIntent:
    """Both read requests and the run identity must be bound to the guard."""

    submission: SubmittedInstagramFeed
    run_request: FeedChargeableRequest
    dataset_request: FeedChargeableRequest


class InstagramFeedGuard(Protocol):
    async def claim_submission(self, operation_id: UUID, request: FeedChargeableRequest) -> bool:
        """Commit a bound, one-shot reservation before the POST and release locks."""
        ...

    async def claim_inspection(self, operation_id: UUID, intent: FeedInspectionIntent) -> bool:
        """Bind the prior run and both read requests before inspection."""
        ...

    async def submission_uncertain(self, operation_id: UUID, request: FeedChargeableRequest) -> None:
        """Retain the budget and mark a potentially dispatched POST uncertain."""
        ...

    async def inspection_uncertain(self, operation_id: UUID, intent: FeedInspectionIntent) -> None:
        """Retain the identity of an inspection whose result is unknown."""
        ...


@dataclass(frozen=True, repr=False)
class InstagramFeedPost:
    post_id: str
    caption: str | None
    image_urls: tuple[str, ...]


@dataclass(frozen=True, repr=False)
class InstagramFeedResult:
    state: Literal["pending", "available", "partial", "unavailable"]
    posts: tuple[InstagramFeedPost, ...] = ()
    # Even a successful actor response does not prove that all posts were seen.
    coverage: Literal["unconfirmed", "partial"] = "unconfirmed"
    reported_cost_usd_micros: int | None = None
    profile_name: str | None = None


_ACTOR_ENDPOINT = "https://api.apify.com/v2/acts/apify~instagram-scraper/runs"
_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")
_BUILD = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
_POST_ID = re.compile(r"[A-Za-z0-9_-]{1,128}")


def _valid_id(value: object) -> bool:
    return isinstance(value, str) and _ID.fullmatch(value) is not None


def _valid_build(value: object) -> bool:
    return isinstance(value, str) and len(value) <= 64 and _BUILD.fullmatch(value) is not None


def _username(value: object) -> str:
    if not isinstance(value, str) or len(value) > 200:
        raise InstagramFeedError("FEED_INPUT_INVALID")
    try:
        return instagram_handle(value)
    except ValueError:
        raise InstagramFeedError("FEED_INPUT_INVALID") from None


def _image_url(value: object) -> str | None:
    if not isinstance(value, str) or not 1 <= len(value) <= 2048:
        return None
    try:
        url = httpx.URL(value)
        host = url.host.lower()
        allowed_host = any(
            host == suffix or host.endswith("." + suffix) for suffix in ("cdninstagram.com", "fbcdn.net")
        )
        if url.scheme != "https" or not allowed_host or url.userinfo or url.port not in (None, 443) or url.fragment:
            return None
        return value
    except (httpx.InvalidURL, ValueError, AttributeError):
        return None


def _post(row: object, username: str) -> tuple[InstagramFeedPost | None, bool]:
    """Keep direct-author captions/images; videos contribute only their cover."""
    if not isinstance(row, dict):
        return None, True
    kind = row.get("type")
    if kind not in ("Image", "Sidecar", "Video") or (row.get("productType") == "clips" and kind != "Video"):
        return None, True
    owner = row.get("ownerUsername")
    try:
        if _username(owner) != username:
            return None, True
    except InstagramFeedError:
        return None, True
    post_id = row.get("id")
    if not isinstance(post_id, str) or _POST_ID.fullmatch(post_id) is None:
        return None, True
    # Covers do not establish the contents of the video itself.
    incomplete = kind == "Video"
    caption = row.get("caption")
    if caption is not None and (not isinstance(caption, str) or len(caption) > 10_000):
        caption, incomplete = None, True
    values: list[object] = []
    if row.get("displayUrl") is not None:
        values.append(row["displayUrl"])
    if kind != "Video":
        for key in ("images", "carouselImages"):
            if key in row:
                items = row[key]
                if not isinstance(items, list):
                    incomplete = True
                else:
                    values.extend(items)
        children = row.get("childPosts", [])
        if not isinstance(children, list):
            incomplete = True
        else:
            if any(not isinstance(child, dict) or child.get("type") != "Image" for child in children):
                # Mixed carousel arrays cannot be matched to individual media.
                # Use typed children's image/cover URLs, never videoUrl.
                values, incomplete = [], True
            for child in children:
                if not isinstance(child, dict) or child.get("type") not in ("Image", "Video"):
                    incomplete = True
                elif child.get("displayUrl") is not None:
                    values.append(child["displayUrl"])
                else:
                    incomplete = True
    images: list[str] = []
    seen_images: set[str] = set()
    for item in values:
        url = _image_url(item)
        if url is None:
            incomplete = True
        elif url not in seen_images:
            images.append(url)
            seen_images.add(url)
    if caption is None and not images:
        return None, True
    return InstagramFeedPost(post_id, caption, tuple(images)), incomplete


def _profile_name(rows: list[object], username: str) -> str | None:
    """A profile name from this same Instagram dataset, never a Maps title."""
    names: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("ownerFullName") is None:
            continue
        try:
            if _username(row.get("ownerUsername")) != username:
                continue
        except InstagramFeedError:
            continue
        value = row["ownerFullName"]
        if (
            not isinstance(value, str)
            or not value.strip()
            or len(value) > 200
            or any(unicodedata.category(character) == "Cc" for character in value)
        ):
            return None
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            return None
        names.add(value.strip())
    return next(iter(names)) if len(names) == 1 else None


def _posts(rows: object, username: str, limit: int, *, provider_partial: bool) -> InstagramFeedResult:
    if not isinstance(rows, list) or len(rows) > limit:
        raise InstagramFeedError("FEED_RESULT_UNCERTAIN")
    seen: set[str] = set()
    posts: list[InstagramFeedPost] = []
    partial = provider_partial
    for row in rows:
        post, incomplete = _post(row, username)
        partial = partial or incomplete
        if post is not None:
            if post.post_id in seen:
                partial = True
            else:
                seen.add(post.post_id)
                posts.append(post)
    if not posts:
        return InstagramFeedResult(
            "unavailable",
            coverage="partial" if partial else "unconfirmed",
            profile_name=_profile_name(rows, username),
        )
    return InstagramFeedResult(
        "partial" if partial else "available",
        tuple(posts),
        "partial" if partial else "unconfirmed",
        profile_name=_profile_name(rows, username),
    )


class ApifyInstagramFeed:
    """Disabled by default; network requires an explicit switch and durable guard."""

    def __init__(
        self,
        token: SecretStr | None = None,
        guard: InstagramFeedGuard | None = None,
        *,
        enabled: bool = False,
        transport: httpx.AsyncBaseTransport | None = None,
        network_enabled: bool = False,
        actor_build: str | None = None,
        max_actor_usd_micros: int = 0,
    ) -> None:
        self._token, self._guard, self._enabled, self._transport = token, guard, enabled, transport
        self._actor_build, self._max_actor_usd_micros = actor_build, max_actor_usd_micros
        self._network_enabled = network_enabled

    def _configured(self) -> tuple[SecretStr, InstagramFeedGuard, httpx.AsyncBaseTransport | None]:
        if (
            not self._enabled
            or not isinstance(self._token, SecretStr)
            or not self._token.get_secret_value()
            or self._guard is None
            or (not isinstance(self._transport, httpx.MockTransport) and not self._network_enabled)
            or not _valid_build(self._actor_build)
            or type(self._max_actor_usd_micros) is not int
            or not 0 < self._max_actor_usd_micros <= 5_000_000
        ):
            raise InstagramFeedError("FEED_DISABLED")
        return self._token, self._guard, self._transport

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
    def _bind(request: httpx.Request, credential: SecretStr) -> FeedChargeableRequest:
        if request.headers.get("authorization") != f"Bearer {credential.get_secret_value()}":
            raise InstagramFeedError("FEED_INPUT_INVALID")
        headers = tuple(
            (name, request.headers[name]) for name in ("content-length", "content-type") if name in request.headers
        )
        return FeedChargeableRequest(request.method, str(request.url), request.content, credential, headers)

    async def _json(self, request: httpx.Request, transport: httpx.AsyncBaseTransport | None) -> object:
        if request.url.scheme != "https" or request.url.host != "api.apify.com":
            raise InstagramFeedError("FEED_INPUT_INVALID")
        transport = transport or httpx.AsyncHTTPTransport(retries=0, trust_env=False)
        try:
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
        except Exception:
            raise InstagramFeedError("FEED_RESULT_UNCERTAIN") from None

    async def submit(self, profile: str, operation_id: UUID, *, results_limit: int = 20) -> SubmittedInstagramFeed:
        username = _username(profile)
        if not isinstance(operation_id, UUID) or type(results_limit) is not int or not 1 <= results_limit <= 20:
            raise InstagramFeedError("FEED_INPUT_INVALID")
        token, guard, transport = self._configured()
        if self._network_enabled:
            payload = await self._json(
                self._request("GET", "https://api.apify.com/v2/acts/shu8hvrXbJbY3Eb9W", token), transport
            )
            try:
                validate_actor_price(
                    payload,
                    actor_id="shu8hvrXbJbY3Eb9W",
                    build=cast(str, self._actor_build),
                    maximum_usd_micros=self._max_actor_usd_micros,
                )
            except ValueError:
                raise InstagramFeedError("FEED_PRICING_UNAVAILABLE") from None
        dollars, micros = divmod(self._max_actor_usd_micros, 1_000_000)
        charge_limit = str(dollars) if not micros else f"{dollars}.{micros:06d}".rstrip("0")
        request = self._request(
            "POST",
            _ACTOR_ENDPOINT,
            token,
            params={
                "build": cast(str, self._actor_build),
                "maxTotalChargeUsd": charge_limit,
                "maxItems": str(results_limit),
                "timeout": "120",
                "memory": "1024",
                "restartOnError": "false",
                "forcePermissionLevel": "LIMITED_PERMISSIONS",
            },
            body={
                "directUrls": [f"https://www.instagram.com/{username}/"],
                "resultsType": "posts",
                "resultsLimit": results_limit,
            },
        )
        binding = self._bind(request, token)
        try:
            claimed = await guard.claim_submission(operation_id, binding)
        except Exception:
            raise InstagramFeedError("FEED_BUDGET_UNAVAILABLE") from None
        if claimed is not True:
            raise InstagramFeedError("FEED_BUDGET_UNAVAILABLE")
        try:
            response = await self._json(request, transport)
            if not isinstance(response, dict) or not isinstance(response.get("data"), dict):
                raise ValueError
            data = response["data"]
            ids = tuple(
                data.get(key)
                for key in ("id", "defaultDatasetId", "defaultKeyValueStoreId", "defaultRequestQueueId", "buildId")
            )
            if (
                not all(_valid_id(value) for value in ids)
                or data.get("buildNumber") != self._actor_build
                or (self._network_enabled and data.get("actId") != "shu8hvrXbJbY3Eb9W")
            ):
                raise ValueError
            return SubmittedInstagramFeed(
                operation_id,
                username,
                cast(str, ids[0]),
                cast(str, ids[1]),
                cast(str, ids[2]),
                cast(str, ids[3]),
                cast(str, self._actor_build),
                cast(str, ids[4]),
                results_limit,
            )
        except (ValueError, InstagramFeedError):
            try:
                await guard.submission_uncertain(operation_id, binding)
            except Exception:
                # A failed acknowledgement cannot release the existing hold.
                pass
            raise InstagramFeedError("FEED_SUBMISSION_UNCERTAIN") from None

    async def inspect(self, submitted: SubmittedInstagramFeed, operation_id: UUID) -> InstagramFeedResult:
        if (
            not isinstance(submitted, SubmittedInstagramFeed)
            or not isinstance(submitted.submission_id, UUID)
            or not isinstance(operation_id, UUID)
            or not isinstance(submitted.username, str)
            or not _valid_build(submitted.build_number)
            or not all(
                _valid_id(value)
                for value in (
                    submitted.run_id,
                    submitted.dataset_id,
                    submitted.key_value_store_id,
                    submitted.request_queue_id,
                    submitted.build_id,
                )
            )
            or type(submitted.results_limit) is not int
            or not 1 <= submitted.results_limit <= 20
        ):
            raise InstagramFeedError("FEED_INPUT_INVALID")
        if _username(submitted.username) != submitted.username:
            raise InstagramFeedError("FEED_INPUT_INVALID")
        token, guard, transport = self._configured()
        run_request = self._request("GET", f"https://api.apify.com/v2/actor-runs/{submitted.run_id}", token)
        dataset_request = self._request(
            "GET",
            f"https://api.apify.com/v2/datasets/{submitted.dataset_id}/items",
            token,
            params={"clean": "true", "limit": str(submitted.results_limit + 1)},
        )
        intent = FeedInspectionIntent(submitted, self._bind(run_request, token), self._bind(dataset_request, token))
        try:
            claimed = await guard.claim_inspection(operation_id, intent)
        except Exception:
            raise InstagramFeedError("FEED_BUDGET_UNAVAILABLE") from None
        if claimed is not True:
            raise InstagramFeedError("FEED_BUDGET_UNAVAILABLE")
        try:
            return await self._inspect_claimed(submitted, run_request, dataset_request, transport)
        except InstagramFeedError:
            try:
                await guard.inspection_uncertain(operation_id, intent)
            except Exception:
                # The caller must reconcile the prior read, not repeat blindly.
                pass
            raise

    async def _inspect_claimed(
        self,
        submitted: SubmittedInstagramFeed,
        run_request: httpx.Request,
        dataset_request: httpx.Request,
        transport: httpx.AsyncBaseTransport | None,
    ) -> InstagramFeedResult:
        response = await self._json(run_request, transport)
        if not isinstance(response, dict) or not isinstance(response.get("data"), dict):
            raise InstagramFeedError("FEED_RESULT_UNCERTAIN")
        data = response["data"]
        expected = {
            "id": submitted.run_id,
            "defaultDatasetId": submitted.dataset_id,
            "defaultKeyValueStoreId": submitted.key_value_store_id,
            "defaultRequestQueueId": submitted.request_queue_id,
            "buildNumber": submitted.build_number,
            "buildId": submitted.build_id,
        }
        if self._network_enabled:
            expected["actId"] = "shu8hvrXbJbY3Eb9W"
        if any(data.get(key) != value for key, value in expected.items()):
            raise InstagramFeedError("FEED_RESULT_UNCERTAIN")
        status = data.get("status")
        if not isinstance(status, str):
            raise InstagramFeedError("FEED_RESULT_UNCERTAIN")
        if status in {"READY", "RUNNING", "TIMING-OUT", "ABORTING"}:
            return InstagramFeedResult("pending")
        if status not in {"SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"}:
            raise InstagramFeedError("FEED_RESULT_UNCERTAIN")
        if not terminal_run_cost_ready(data):
            return InstagramFeedResult("pending")
        rows = await self._json(dataset_request, transport)
        try:
            cost = terminal_run_cost(data)
        except ValueError:
            raise InstagramFeedError("FEED_RESULT_UNCERTAIN") from None
        return replace(
            _posts(rows, submitted.username, submitted.results_limit, provider_partial=status != "SUCCEEDED"),
            reported_cost_usd_micros=cost,
        )
