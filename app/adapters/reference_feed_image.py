"""Bounded retrieval of a selected Instagram feed image into memory.

Only HTTPS Instagram/Meta CDN hosts are accepted. Redirects, proxies and
transport retries are disabled. A trusted guard binds the selected run/post/URL;
raw bytes and signed URLs never enter database, logs or Temporal history.
"""

import io
import re
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

import httpx
from PIL import Image, UnidentifiedImageError

from app.adapters.apify_instagram_feed import InstagramFeedPost, SubmittedInstagramFeed, _image_url
from app.schemas.owner_references import instagram_handle

_MAX_BYTES = 5 * 1024 * 1024
_MAX_PIXELS = 12_000_000
_MIMES = {"image/png": "PNG", "image/jpeg": "JPEG", "image/webp": "WEBP"}


class FeedImageError(Exception):
    """Stable error without signed URLs, account or image content."""


@dataclass(frozen=True, repr=False)
class FeedImageIntent:
    run: SubmittedInstagramFeed
    post_id: str
    url: str
    method: str = "GET"


@dataclass(frozen=True, repr=False)
class FeedImage:
    content: bytes
    mime_type: str
    width: int
    height: int


class FeedImageGuard(Protocol):
    async def authorize(self, operation_id: UUID, intent: FeedImageIntent) -> bool:
        """Verify the selected reference, exact run, post, URL and operation."""
        ...


def _validate(run: object, post: object, url: object, operation: object) -> FeedImageIntent:
    if (
        not isinstance(run, SubmittedInstagramFeed)
        or not isinstance(run.submission_id, UUID)
        or not isinstance(run.username, str)
        or type(run.results_limit) is not int
        or not 1 <= run.results_limit <= 20
        or any(
            not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value) is None
            for value in (run.run_id, run.dataset_id, run.key_value_store_id, run.request_queue_id, run.build_id)
        )
        or not isinstance(run.build_number, str)
        or len(run.build_number) > 64
        or re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", run.build_number) is None
        or not isinstance(post, InstagramFeedPost)
        or not isinstance(post.post_id, str)
        or re.fullmatch(r"[A-Za-z0-9_-]{1,128}", post.post_id) is None
        or not isinstance(post.image_urls, tuple)
        or not isinstance(url, str)
        or _image_url(url) != url
        or url not in post.image_urls
        or not isinstance(operation, UUID)
    ):
        raise FeedImageError("REFERENCE_FEED_IMAGE_INPUT_INVALID")
    try:
        if instagram_handle(run.username) != run.username:
            raise ValueError
    except ValueError:
        raise FeedImageError("REFERENCE_FEED_IMAGE_INPUT_INVALID") from None
    return FeedImageIntent(run, post.post_id, url)


def _image(data: bytes, mime: str) -> FeedImage:
    try:
        with Image.open(io.BytesIO(data)) as image:
            width, height = image.size
            if (
                _MIMES.get(mime) != image.format
                or not 1 <= width <= 4096
                or not 1 <= height <= 4096
                or width * height > _MAX_PIXELS
                or getattr(image, "n_frames", 1) != 1
            ):
                raise ValueError
            image.verify()
        return FeedImage(data, mime, width, height)
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise FeedImageError("REFERENCE_FEED_IMAGE_INVALID") from None


class FeedImageDownloader:
    def __init__(
        self,
        guard: FeedImageGuard | None = None,
        *,
        enabled: bool = False,
        transport: httpx.AsyncBaseTransport | None = None,
        network_enabled: bool = False,
    ) -> None:
        self._guard, self._enabled, self._transport = guard, enabled, transport
        self._network_enabled = network_enabled

    async def fetch(self, run: SubmittedInstagramFeed, post: InstagramFeedPost, url: str, operation: UUID) -> FeedImage:
        intent = _validate(run, post, url, operation)
        if (
            not self._enabled
            or self._guard is None
            or (not isinstance(self._transport, httpx.MockTransport) and not self._network_enabled)
        ):
            raise FeedImageError("REFERENCE_FEED_IMAGE_DISABLED")
        try:
            allowed = await self._guard.authorize(operation, intent)
        except Exception:
            raise FeedImageError("REFERENCE_FEED_IMAGE_NOT_AUTHORIZED") from None
        if allowed is not True:
            raise FeedImageError("REFERENCE_FEED_IMAGE_NOT_AUTHORIZED")
        request = httpx.Request(
            "GET", url, extensions={"timeout": {"connect": 5.0, "read": 15.0, "write": 5.0, "pool": 5.0}}
        )
        try:
            transport = self._transport or httpx.AsyncHTTPTransport(retries=0, trust_env=False)
            async with transport:
                response = await transport.handle_async_request(request)
                try:
                    if response.status_code != 200:
                        raise FeedImageError("REFERENCE_FEED_IMAGE_UNAVAILABLE")
                    mime = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                    if mime not in _MIMES:
                        raise FeedImageError("REFERENCE_FEED_IMAGE_INVALID")
                    length = response.headers.get("content-length")
                    if length is not None and (
                        not length.isascii() or not length.isdecimal() or len(length) > 10 or int(length) > _MAX_BYTES
                    ):
                        raise FeedImageError("REFERENCE_FEED_IMAGE_INVALID")
                    data = bytearray()
                    async for chunk in response.aiter_bytes():
                        data.extend(chunk)
                        if len(data) > _MAX_BYTES:
                            raise FeedImageError("REFERENCE_FEED_IMAGE_INVALID")
                    if length is not None and int(length) != len(data):
                        raise FeedImageError("REFERENCE_FEED_IMAGE_INVALID")
                    return _image(bytes(data), mime)
                finally:
                    await response.aclose()
        except FeedImageError:
            raise
        except Exception:
            raise FeedImageError("REFERENCE_FEED_IMAGE_UNAVAILABLE") from None


# Compatibility for existing local tests; production uses the neutral name.
MockFeedImageDownloader = FeedImageDownloader
