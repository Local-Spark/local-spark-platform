"""Budget boundaries and multimodal preflight, without network or paid inference."""

import json
from uuid import uuid5

import httpx
import pytest

from app.adapters.motion_ai import MotionAIError
from app.adapters.motion_fixture import FixtureMotionProvider
from app.services.motion_budget import cost_bound
from app.tests.unit.test_motion_ai import composition, frame, provider, request


def test_long_context_boundary_and_fractional_microdollars_round_up():
    assert cost_bound(272000, 8000, 2500000, 10000000)["maximum_usd_micros"] == 760000
    assert cost_bound(1, 1, 2500000, 10000000)["maximum_usd_micros"] == 13


@pytest.mark.parametrize("kind", ["generate", "review", "correct"])
async def test_count_includes_instructions_schema_source_current_and_previous_images(kind):
    from app.schemas.motion_production import MotionReview
    from app.tests.unit.test_motion_ai import review_data

    seen = []

    def handler(http_request):
        seen.append(http_request)
        return httpx.Response(200, json={"object": "response.input_tokens", "input_tokens": 12345})

    model = provider(handler)
    req = request(
        kind,
        composition=composition(),
        source_frames=(frame(0),),
        frames=(frame(1),),
        incumbent_frames=(frame(2),),
        incumbent_composition=composition(),
        review=MotionReview.model_validate(review_data(revise=True)),
    )
    payload = model.build_request(req)
    before = json.dumps(payload, sort_keys=True)
    assert await model.count_input_tokens(req, payload) == 12345
    assert json.dumps(payload, sort_keys=True) == before
    assert len(seen) == 1 and seen[0].url.path == "/v1/responses/input_tokens"
    assert seen[0].headers["x-client-request-id"] == str(uuid5(req.operation_id, "input-token-count"))
    body = json.loads(seen[0].content)
    assert body == {key: payload[key] for key in ("model", "input", "instructions", "text", "reasoning")}
    assert sum(part["type"] == "input_image" for part in body["input"][0]["content"]) == 3


@pytest.mark.parametrize(
    "body",
    [
        {},
        [],
        None,
        {"object": "wrong", "input_tokens": 3},
        {"object": "response.input_tokens", "input_tokens": True},
        {"object": "response.input_tokens", "input_tokens": 0},
        {"object": "response.input_tokens", "input_tokens": -1},
        {"object": "response.input_tokens", "input_tokens": "100"},
    ],
)
async def test_invalid_count_fails_closed_without_echoing_response(body):
    model = provider(lambda _: httpx.Response(200, content=json.dumps(body).encode()))
    req = request()
    with pytest.raises(MotionAIError, match="^MOTION_AI_INPUT_COUNT_INVALID$"):
        await model.count_input_tokens(req, model.build_request(req))


@pytest.mark.parametrize("status", [302, 429, 500])
async def test_count_http_failure_is_not_retried_or_redirected(status):
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(status, headers={"Location": "https://example.invalid"}, content=b"private")

    model = provider(handler)
    req = request()
    with pytest.raises(MotionAIError, match="^MOTION_AI_INPUT_COUNT_FAILED$"):
        await model.count_input_tokens(req, model.build_request(req))
    assert len(calls) == 1


async def test_count_network_failure_is_not_retried():
    calls = []

    def handler(req):
        calls.append(req)
        raise httpx.ReadTimeout("private")

    model = provider(handler)
    req = request()
    with pytest.raises(MotionAIError, match="^MOTION_AI_INPUT_COUNT_FAILED$"):
        await model.count_input_tokens(req, model.build_request(req))
    assert len(calls) == 1


async def test_count_response_size_is_bounded():
    model = provider(lambda _: httpx.Response(200, content=b" " * 4097))
    req = request()
    with pytest.raises(MotionAIError, match="INPUT_COUNT_INVALID"):
        await model.count_input_tokens(req, model.build_request(req))


async def test_changed_payload_cannot_be_counted():
    model = provider(lambda _: pytest.fail("No network for changed payload"))
    req = request()
    payload = model.build_request(req)
    payload["instructions"] = "Changed"
    with pytest.raises(MotionAIError, match="REQUEST_CHANGED"):
        await model.count_input_tokens(req, payload)


async def test_fixture_count_has_no_external_effect():
    model = FixtureMotionProvider()
    req = request()
    assert await model.count_input_tokens(req, model.build_request(req)) == 0
