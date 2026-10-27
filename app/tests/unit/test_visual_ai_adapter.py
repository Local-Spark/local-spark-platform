import base64
import io
from dataclasses import replace
from uuid import uuid4

import httpx
import pytest
from PIL import Image

from app.adapters.visual_ai import OpenAIVisualProvider, VisualAIError, VisualReference, VisualRequest


def image_bytes(width=1024, height=1024, format="PNG"):
    stream = io.BytesIO()
    Image.new("RGB", (width, height), "purple").save(stream, format=format)
    return stream.getvalue()


def request(**kwargs):
    base = VisualRequest(
        prompt="Anúncio de café",
        model="gpt-image-2.5-flare",
        quality="medium",
        size="1024x1024",
        output_format="png",
        request_id=uuid4(),
    )
    return replace(base, **kwargs)


def response_body():
    return {
        "data": [{"b64_json": base64.b64encode(image_bytes()).decode()}],
        "usage": {"input_tokens": 10, "output_tokens": 20},
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("with_reference", [False, True])
async def test_real_request_shape_with_mock_transport(with_reference):
    sent = []

    def handler(req):
        import json

        body = json.loads(req.content)
        sent.append((req.url.path, body, req.headers))
        return httpx.Response(200, json=response_body(), headers={"x-request-id": "provider-123"})

    original = request(references=(VisualReference(image_bytes(), "image/png"),) if with_reference else ())
    result = await OpenAIVisualProvider("secret-key", transport=httpx.MockTransport(handler)).generate(original)
    path, body, headers = sent[0]
    assert path == ("/v1/images/edits" if with_reference else "/v1/images/generations")
    assert body["n"] == 1 and body["prompt"] == original.prompt
    assert headers["x-client-request-id"] == str(original.request_id)
    assert headers["authorization"] == "Bearer secret-key"
    assert bool(body.get("images")) == with_reference
    assert result.content == image_bytes() and result.usage["input_tokens"] == 10
    assert (result.width, result.height, result.mime_type, result.provider_request_id) == (
        1024,
        1024,
        "image/png",
        "provider-123",
    )
    assert "secret-key" not in repr(result) and original.prompt not in repr(original)


def test_disabled_key():
    with pytest.raises(VisualAIError, match="VISUAL_PROVIDER_DISABLED"):
        OpenAIVisualProvider(" ")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "changes",
    [
        {"model": "unknown"},
        {"quality": "max"},
        {"output_format": "gif"},
        {"prompt": " "},
        {"size": "x"},
        {"size": "0x256"},
        {"size": "257x256"},
        {"size": "256x1024"},
        {"references": tuple(VisualReference(b"bad", "image/png") for _ in range(5))},
        {"references": (VisualReference(b"bad", "image/gif"),)},
        {"references": (VisualReference(b"bad", "image/png"),)},
        {"references": (VisualReference(image_bytes(), "image/jpeg"),)},
    ],
)
async def test_bad_input_never_calls_provider(changes):
    def handler(req):
        raise AssertionError("must not send")

    with pytest.raises(VisualAIError) as err:
        await OpenAIVisualProvider("key", transport=httpx.MockTransport(handler)).generate(request(**changes))
    assert not err.value.uncertain


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status,uncertain", [(400, True), (429, True), (408, True), (409, True), (500, True), (302, True)]
)
async def test_failure_does_not_retry_or_expose_body(status, uncertain):
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(status, text="sensitive provider body")

    with pytest.raises(VisualAIError) as err:
        await OpenAIVisualProvider("secret", transport=httpx.MockTransport(handler)).generate(request())
    assert err.value.uncertain is uncertain
    assert "sensitive" not in str(err.value) and len(calls) == 1


@pytest.mark.asyncio
async def test_transport_failure_is_uncertain():
    def handler(req):
        raise httpx.ReadTimeout("sensitive body", request=req)

    with pytest.raises(VisualAIError) as err:
        await OpenAIVisualProvider("secret", transport=httpx.MockTransport(handler)).generate(request())
    assert err.value.uncertain and "sensitive" not in str(err.value)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body",
    [
        {},
        {"data": []},
        {"data": [{"b64_json": "@@"}]},
        {"data": [{"b64_json": ""}]},
        {"data": [{"b64_json": base64.b64encode(b"bad").decode()}]},
        {"data": [{"b64_json": base64.b64encode(image_bytes(512, 512)).decode()}]},
    ],
)
async def test_bad_provider_output_is_uncertain(body):
    with pytest.raises(VisualAIError) as err:
        await OpenAIVisualProvider(
            "secret", transport=httpx.MockTransport(lambda req: httpx.Response(200, json=body))
        ).generate(request())
    assert err.value.code == "VISUAL_PROVIDER_INVALID" and err.value.uncertain


@pytest.mark.asyncio
async def test_optional_usage_is_not_fabricated():
    body = response_body()
    del body["usage"]
    result = await OpenAIVisualProvider(
        "key", transport=httpx.MockTransport(lambda req: httpx.Response(200, json=body))
    ).generate(request())
    assert result.usage is None


@pytest.mark.asyncio
async def test_large_reference_dimensions_are_rejected():
    image = image_bytes(4000, 4000)
    with pytest.raises(VisualAIError, match="VISUAL_INVALID_REFERENCE"):
        await OpenAIVisualProvider(
            "key", transport=httpx.MockTransport(lambda req: pytest.fail("unexpected request"))
        ).generate(request(references=(VisualReference(image, "image/png"),)))


@pytest.mark.asyncio
@pytest.mark.parametrize("items", [[{"b64_json": 12}], [{"b64_json": "abc"}, {"b64_json": "abc"}]])
async def test_response_shape_is_uncertain(items):
    with pytest.raises(VisualAIError) as err:
        await OpenAIVisualProvider(
            "key", transport=httpx.MockTransport(lambda req: httpx.Response(200, json={"data": items}))
        ).generate(request())
    assert err.value.uncertain


@pytest.mark.asyncio
async def test_too_large_encoded_result_is_uncertain(monkeypatch):
    monkeypatch.setattr("app.adapters.visual_ai._MAX_OUTPUT_BYTES", 2)
    with pytest.raises(VisualAIError) as err:
        await OpenAIVisualProvider(
            "key", transport=httpx.MockTransport(lambda req: httpx.Response(200, json=response_body()))
        ).generate(request())
    assert err.value.uncertain


@pytest.mark.asyncio
async def test_streamed_body_is_capped():
    body = b"a" * (21 * 1024 * 1024)
    with pytest.raises(VisualAIError) as err:
        await OpenAIVisualProvider(
            "key", transport=httpx.MockTransport(lambda req: httpx.Response(200, content=body))
        ).generate(request())
    assert err.value.uncertain and err.value.code == "VISUAL_PROVIDER_INVALID"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "usage",
    [
        "bad",
        {},
        {"input_tokens": True, "output_tokens": 20},
        {"input_tokens": -1, "output_tokens": 20},
        {"input_tokens": 10.5, "output_tokens": 20},
        {"input_tokens": 10, "output_tokens": 20, "input_tokens_details": "bad"},
        {"input_tokens": 10, "output_tokens": 20, "input_tokens_details": {"image_tokens": -1}},
    ],
)
async def test_untrusted_usage_never_becomes_zero_cost(usage):
    body = response_body()
    body["usage"] = usage
    result = await OpenAIVisualProvider(
        "key", transport=httpx.MockTransport(lambda req: httpx.Response(200, json=body))
    ).generate(request())
    assert result.usage is None and result.content == image_bytes()


@pytest.mark.asyncio
async def test_usage_allowlist_excludes_provider_extra_fields():
    body = response_body()
    body["usage"].update(
        {
            "total_tokens": 30,
            "input_tokens_details": {"image_tokens": 4, "text_tokens": 6, "private": "do not expose"},
            "output_tokens_details": {"image_tokens": 20},
            "private": "do not expose",
        }
    )
    result = await OpenAIVisualProvider(
        "key", transport=httpx.MockTransport(lambda req: httpx.Response(200, json=body))
    ).generate(request())
    assert result.usage == {
        "input_tokens": 10,
        "output_tokens": 20,
        "total_tokens": 30,
        "input_tokens_details": {"image_tokens": 4, "text_tokens": 6},
        "output_tokens_details": {"image_tokens": 20},
    }
    assert "do not expose" not in repr(result) and "usage=" not in repr(result)
