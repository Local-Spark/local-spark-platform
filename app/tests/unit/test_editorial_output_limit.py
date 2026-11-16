"""A truncated editorial response must be diagnosed, never retried as a new call."""

import json
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.adapters import editorial_ai
from app.adapters.editorial_ai import EditorialProviderError, OpenAIEditorialProvider


async def test_full_piece_has_room_and_reports_truncation_without_retry(settings, monkeypatch):
    configured = settings.model_copy(update={"editorial_ai_mode": "openai", "openai_api_key": SecretStr("fake")})
    calls = []
    body = {
        "status": "incomplete",
        "incomplete_details": {"reason": "max_output_tokens"},
        "usage": {"input_tokens": 2312, "output_tokens": 1200},
        "output": [],
    }

    def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200, json=body)

    client = httpx.AsyncClient
    monkeypatch.setattr(
        editorial_ai.httpx, "AsyncClient", lambda **kw: client(transport=httpx.MockTransport(handler), **kw)
    )
    observer = AsyncMock()
    with pytest.raises(EditorialProviderError) as error:
        await OpenAIEditorialProvider(configured).propose(
            {"editorial_skill": {"id": "instagram-feed-v1"}}, uuid4(), response_observer=observer
        )
    assert error.value.code == "EDITORIAL_OUTPUT_LIMIT_EXCEEDED"
    assert len(calls) == 1
    assert calls[0]["max_output_tokens"] == 4096
    observer.assert_awaited_once_with(body)
