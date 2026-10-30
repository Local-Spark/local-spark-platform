"""Isolated Images API adapter. Caller must authorize assets and reserve budget first."""

import base64
import binascii
import hashlib
import io
import json
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

import httpx
from PIL import Image, UnidentifiedImageError

_MODELS = frozenset(
    {
        "gpt-image-2.5-flare",
        "gpt-image-2.5-flare-2026-09-08",
        "gpt-image-2.5-sunburst",
        "gpt-image-2.5-sunburst-2026-09-08",
    }
)
_MIME = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}
_MAX_INPUT_BYTES = 5 * 1024 * 1024
_MAX_OUTPUT_BYTES = 15 * 1024 * 1024
_MAX_PIXELS = 12_000_000


class VisualAIError(Exception):
    """Stable error code; uncertain means a provider charge may have occurred."""

    def __init__(self, code: str, *, uncertain: bool = False) -> None:
        super().__init__(code)
        self.code = code
        self.uncertain = uncertain


@dataclass(frozen=True)
class VisualReference:
    content: bytes = field(repr=False)
    mime_type: str


@dataclass(frozen=True)
class VisualRequest:
    prompt: str = field(repr=False)
    model: str
    quality: str
    size: str
    output_format: str
    request_id: UUID
    references: tuple[VisualReference, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class VisualResult:
    content: bytes = field(repr=False)
    mime_type: str
    sha256: str
    width: int
    height: int
    usage: dict[str, Any] | None = field(repr=False)
    provider_request_id: str | None


def _safe_usage(value: Any) -> dict[str, Any] | None:
    """Keep only validated token counts; invalid or absent usage means unknown cost."""
    if not isinstance(value, dict):
        return None
    result: dict[str, Any] = {}
    for name in ("input_tokens", "output_tokens", "total_tokens"):
        if name not in value:
            if name != "total_tokens":
                return None
            continue
        count = value[name]
        if type(count) is not int or count < 0:
            return None
        result[name] = count
    for name in ("input_tokens_details", "output_tokens_details"):
        if name not in value:
            continue
        details = value[name]
        if not isinstance(details, dict):
            return None
        safe_details: dict[str, int] = {}
        for token_name in ("image_tokens", "text_tokens"):
            if token_name in details:
                count = details[token_name]
                if type(count) is not int or count < 0:
                    return None
                safe_details[token_name] = count
        result[name] = safe_details
    return result


def _dimensions(content: bytes, mime_type: str, *, output: bool) -> tuple[int, int]:
    code = "VISUAL_PROVIDER_INVALID" if output else "VISUAL_INVALID_REFERENCE"
    try:
        with Image.open(io.BytesIO(content)) as img:
            width, height = img.size
            if _MIME.get(img.format or "") != mime_type or not (1 <= width <= 4096 and 1 <= height <= 4096):
                raise ValueError
            if width * height > _MAX_PIXELS:
                raise ValueError
            img.verify()
    except (ValueError, OSError, UnidentifiedImageError, Image.DecompressionBombError):
        raise VisualAIError(code, uncertain=output) from None
    return width, height


def _validate(request: VisualRequest) -> tuple[int, int]:
    if request.model not in _MODELS or request.quality not in {"low", "medium", "high"}:
        raise VisualAIError("VISUAL_INVALID_SETTINGS")
    if request.output_format not in {"png", "jpeg", "webp"} or not 1 <= len(request.prompt.strip()) <= 32000:
        raise VisualAIError("VISUAL_INVALID_SETTINGS")
    try:
        width, height = (int(part) for part in request.size.split("x"))
    except ValueError:
        raise VisualAIError("VISUAL_INVALID_SETTINGS") from None
    if (
        width < 256
        or height < 256
        or width > 2048
        or height > 2048
        or width % 16
        or height % 16
        or not 655_360 <= width * height <= 2560 * 1440
        or width > height * 3
        or height > width * 3
    ):
        raise VisualAIError("VISUAL_INVALID_SETTINGS")
    if len(request.references) > 5:
        raise VisualAIError("VISUAL_INVALID_REFERENCE")
    for reference in request.references:
        if reference.mime_type not in _MIME.values() or not 1 <= len(reference.content) <= _MAX_INPUT_BYTES:
            raise VisualAIError("VISUAL_INVALID_REFERENCE")
        _dimensions(reference.content, reference.mime_type, output=False)
    return width, height


def visual_request_http_parts(request: VisualRequest) -> tuple[str, dict[str, Any]]:
    """Return the endpoint and non-image JSON fields used by the Images API."""
    endpoint = "edits" if request.references else "generations"
    return f"/v1/images/{endpoint}", {
        "model": request.model,
        "prompt": request.prompt,
        "quality": request.quality,
        "size": request.size,
        "output_format": request.output_format,
        "n": 1,
    }


class OpenAIVisualProvider:
    """No retries; the request ID supports tracing, not provider-side idempotency."""

    def __init__(self, api_key: str, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        if not api_key.strip():
            raise VisualAIError("VISUAL_PROVIDER_DISABLED")
        self._api_key = api_key
        self._transport = transport

    async def generate(self, request: VisualRequest) -> VisualResult:
        width, height = _validate(request)
        path, body = visual_request_http_parts(request)
        if request.references:
            body["images"] = [
                {"image_url": f"data:{ref.mime_type};base64,{base64.b64encode(ref.content).decode('ascii')}"}
                for ref in request.references
            ]
        try:
            async with httpx.AsyncClient(
                timeout=180, follow_redirects=False, trust_env=False, transport=self._transport
            ) as client:
                async with client.stream(
                    "POST",
                    f"https://api.openai.com{path}",
                    json=body,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "X-Client-Request-Id": str(request.request_id),
                    },
                ) as response:
                    if response.status_code != 200:
                        if 400 <= response.status_code < 500 and response.status_code not in {408, 409}:
                            raise VisualAIError("VISUAL_PROVIDER_REJECTED", uncertain=True)
                        raise VisualAIError("VISUAL_PROVIDER_UNCERTAIN", uncertain=True)
                    provider_request_id = response.headers.get("x-request-id")
                    raw = bytearray()
                    max_body = 4 * ((_MAX_OUTPUT_BYTES + 2) // 3) + 65_536
                    async for chunk in response.aiter_bytes(chunk_size=65_536):
                        if len(raw) + len(chunk) > max_body:
                            raise VisualAIError("VISUAL_PROVIDER_INVALID", uncertain=True)
                        raw.extend(chunk)
        except httpx.HTTPError:
            raise VisualAIError("VISUAL_PROVIDER_UNCERTAIN", uncertain=True) from None
        try:
            data = json.loads(raw)
            encoded = data["data"][0]["b64_json"]
            if (
                len(data["data"]) != 1
                or not isinstance(encoded, str)
                or len(encoded) > 4 * ((_MAX_OUTPUT_BYTES + 2) // 3)
            ):
                raise ValueError
            content = base64.b64decode(encoded, validate=True)
            if not content or len(content) > _MAX_OUTPUT_BYTES:
                raise ValueError
            usage = _safe_usage(data.get("usage"))
        except (ValueError, TypeError, KeyError, IndexError, binascii.Error):
            raise VisualAIError("VISUAL_PROVIDER_INVALID", uncertain=True) from None
        mime_type = f"image/{request.output_format}"
        if _dimensions(content, mime_type, output=True) != (width, height):
            raise VisualAIError("VISUAL_PROVIDER_INVALID", uncertain=True)
        return VisualResult(
            content=content,
            mime_type=mime_type,
            sha256=hashlib.sha256(content).hexdigest(),
            width=width,
            height=height,
            usage=usage,
            provider_request_id=provider_request_id,
        )
