"""The provider contract is structured, bounded and never stores responses."""

import json
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.adapters import editorial_ai as module
from app.adapters.editorial_ai import EditorialProviderError, OpenAIEditorialProvider
from app.schemas.editorial_proposals import ProposalDraft


def _response(*, status="completed", output=None, usage=None):
    draft = {
        "title": "Mostre seu trabalho",
        "format": "photo",
        "angle": "Mostre o resultado aos clientes.",
        "fact_ids": [],
        "hypotheses": [],
        "questions": [],
    }
    return {
        "status": status,
        "output": output
        if output is not None
        else [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(draft)}]}],
        "usage": usage if usage is not None else {"input_tokens": 12, "output_tokens": 8},
    }


async def test_provider_request_and_success(settings, monkeypatch):
    configured = settings.model_copy(update={"editorial_ai_mode": "openai", "openai_api_key": SecretStr("fake")})
    captured = {}

    def handler(request):
        captured["request"] = request
        return httpx.Response(200, json=_response())

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        module.httpx, "AsyncClient", lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs)
    )
    draft, input_tokens, output_tokens = await OpenAIEditorialProvider(configured).propose(
        {"material": "Foto do lanche"}, uuid4()
    )
    assert isinstance(draft, ProposalDraft)
    assert (input_tokens, output_tokens) == (12, 8)
    sent = json.loads(captured["request"].content)
    assert sent["store"] is False
    assert sent["max_output_tokens"] == 1200
    assert sent["reasoning"] == {"effort": "low"}
    assert sent["tools"] == []
    assert sent["text"]["format"]["strict"] is True
    assert sent["text"]["format"]["schema"]["properties"]["questions"]["maxItems"] == 3
    assert captured["request"].headers["authorization"] == "Bearer fake"


@pytest.mark.parametrize(
    "body,code",
    [
        (_response(status="incomplete"), "EDITORIAL_PROVIDER_INCOMPLETE"),
        ({"status": "completed", "output": [], "usage": {}}, "EDITORIAL_PROVIDER_INVALID"),
        (
            _response(output=[{"type": "message", "content": [{"type": "output_text", "text": "bad"}]}]),
            "EDITORIAL_PROVIDER_INVALID",
        ),
        (
            _response(output=[{"type": "message", "content": [{"type": "output_text", "text": "{}"}]}]),
            "EDITORIAL_PROVIDER_INVALID",
        ),
        (_response(usage={"input_tokens": -1, "output_tokens": 2}), "EDITORIAL_PROVIDER_INVALID"),
        (_response(usage={"input_tokens": 2, "output_tokens": -1}), "EDITORIAL_PROVIDER_INVALID"),
        ({"status": "completed", "usage": None, "output": []}, "EDITORIAL_PROVIDER_INVALID"),
        ({"status": "completed", "usage": {}, "output": None}, "EDITORIAL_PROVIDER_INVALID"),
        (_response(output=[{"type": "message", "content": []}]), "EDITORIAL_PROVIDER_INVALID"),
    ],
)
async def test_provider_rejects_invalid_output(settings, monkeypatch, body, code):
    configured = settings.model_copy(update={"editorial_ai_mode": "openai", "openai_api_key": SecretStr("fake")})
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        module.httpx,
        "AsyncClient",
        lambda **kwargs: real_client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body)), **kwargs),
    )
    with pytest.raises(EditorialProviderError, match=code):
        await OpenAIEditorialProvider(configured).propose({}, uuid4())


async def test_provider_disabled_and_transport_failure(settings, monkeypatch):
    with pytest.raises(EditorialProviderError, match="EDITORIAL_PROVIDER_DISABLED"):
        await OpenAIEditorialProvider(settings).propose({}, uuid4())
    configured = settings.model_copy(update={"editorial_ai_mode": "openai", "openai_api_key": SecretStr("fake")})
    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        module.httpx,
        "AsyncClient",
        lambda **kwargs: real_client(transport=httpx.MockTransport(lambda _: httpx.Response(503)), **kwargs),
    )
    with pytest.raises(EditorialProviderError, match="EDITORIAL_PROVIDER_UNCERTAIN"):
        await OpenAIEditorialProvider(configured).propose({}, uuid4())


async def test_adapter_rejects_non_json_response(settings, monkeypatch):
    configured = settings.model_copy(update={"editorial_ai_mode": "openai", "openai_api_key": SecretStr("fake")})
    client = AsyncMock()
    client.__aenter__.return_value = client
    response = Mock()
    response.json.side_effect = ValueError("bad JSON")
    client.post.return_value = response
    monkeypatch.setattr(module.httpx, "AsyncClient", lambda **kwargs: client)
    with pytest.raises(EditorialProviderError, match="EDITORIAL_PROVIDER_UNCERTAIN"):
        await OpenAIEditorialProvider(configured).propose({}, uuid4())
