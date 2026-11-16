"""Bounded Responses SSE transport; partial text is never a validated result.

Protocol: https://developers.openai.com/api/reference/resources/responses/streaming-events
"""

import json
import time
from collections.abc import Awaitable, Callable

import httpx


async def read_responses_stream(
    response: httpx.Response, observe: Callable[[str], Awaitable[None]], *, maximum: int = 4 * 1024 * 1024
) -> bytes:
    response.raise_for_status()
    if "text/event-stream" not in response.headers.get("content-type", ""):
        raise ValueError("RESPONSES_STREAM_REQUIRED")
    buffer = b""
    total = 0
    pending = ""
    emitted = 0
    flushed = time.monotonic()
    async for chunk in response.aiter_bytes():
        total += len(chunk)
        if total > 8 * maximum:
            raise ValueError("RESPONSES_STREAM_TOO_LARGE")
        buffer += chunk
        buffer = buffer.replace(b"\r\n", b"\n")
        while b"\n\n" in buffer:
            block, buffer = buffer.split(b"\n\n", 1)
            lines = [line[5:].lstrip() for line in block.split(b"\n") if line.startswith(b"data:")]
            if not lines:
                continue
            data = b"\n".join(lines)
            if data == b"[DONE]":
                continue
            event = json.loads(data)
            if not isinstance(event, dict):
                raise ValueError("RESPONSES_STREAM_INVALID")
            kind = event.get("type")
            if kind == "response.output_text.delta":
                delta = event.get("delta")
                if not isinstance(delta, str) or len(delta.encode()) > 65536:
                    raise ValueError("RESPONSES_STREAM_INVALID")
                emitted += len(delta.encode())
                if emitted > maximum:
                    raise ValueError("RESPONSES_STREAM_TOO_LARGE")
                pending += delta
                if len(pending) >= 2048 or time.monotonic() - flushed >= 1:
                    await observe(pending)
                    pending = ""
                    flushed = time.monotonic()
            if kind in {"response.completed", "response.incomplete", "response.failed"}:
                terminal = event.get("response")
                if not isinstance(terminal, dict):
                    raise ValueError("RESPONSES_STREAM_INVALID")
                raw = json.dumps(terminal, ensure_ascii=False, separators=(",", ":")).encode()
                if len(raw) > maximum:
                    raise ValueError("RESPONSES_STREAM_TOO_LARGE")
                if pending:
                    await observe(pending)
                return raw
            if kind == "error":
                raise ValueError("RESPONSES_STREAM_FAILED")
        if len(buffer) > maximum:
            raise ValueError("RESPONSES_STREAM_TOO_LARGE")
    if pending:
        await observe(pending)
    raise ValueError("RESPONSES_STREAM_INCOMPLETE")
