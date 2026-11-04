import base64
import io
import json
from dataclasses import replace
from uuid import uuid4

import httpx
import pytest
from PIL import Image
from pydantic import SecretStr

from app.adapters.jev_reference_post_analysis import JevReferencePostAnalysis, PostAnalysisError
from app.adapters.reference_feed_image import FeedImage
from app.services.reference_pattern_vocabulary import (
    PATTERN_QUESTIONS,
    PATTERN_VERSION,
    aggregate_pattern_choices,
)


class Guard:
    def __init__(self, result=True, uncertain_error=False):
        self.result, self.uncertain_error = result, uncertain_error
        self.calls, self.uncertain_calls = [], 0

    async def claim(self, operation, request):
        self.calls.append((operation, request))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result

    async def uncertain(self):
        self.uncertain_calls += 1
        if self.uncertain_error:
            raise RuntimeError("private")


def picture(size=(300, 300), fmt="PNG"):
    output = io.BytesIO()
    Image.new("RGB", size, "red").save(output, format=fmt)
    return FeedImage(output.getvalue(), {"PNG": "image/png", "WEBP": "image/webp", "JPEG": "image/jpeg"}[fmt], *size)


def response_for(request):
    questions = json.loads(request.content)["questions"]
    return {
        "model": "jev-1.14.0",
        "usage": {"input_tokens": 123, "output_tokens": 0},
        "answers": {
            name: {
                "type": "choice",
                "choice": next(iter(question["criteria"])),
                "confidence": 1,
                "probabilities": {code: float(i == 0) for i, code in enumerate(question["criteria"])},
            }
            for name, question in questions.items()
        },
    }


def adapter(handler=None, guard=True, **overrides):
    args = dict(
        key=SecretStr("private-key"),
        model="jev-1.14.0",
        guard=Guard() if guard is True else guard,
        enabled=True,
        transport=httpx.MockTransport(handler or (lambda request: httpx.Response(200, json=response_for(request)))),
    )
    args.update(overrides)
    return JevReferencePostAnalysis(**args)


@pytest.mark.parametrize(
    ("caption", "with_image", "questions"),
    [("private caption", False, 2), (None, True, 6), ("private caption", True, 8)],
)
async def test_only_own_patterns_return_and_exact_request_claimed(caption, with_image, questions, caplog):
    guard, operation = Guard(), uuid4()

    def handle(request):
        assert len(guard.calls) == 1
        op, bound = guard.calls[0]
        assert op == operation and bound.body == request.content and bound.method == "POST"
        assert bound.url == "https://api.typesafe.ai/v1/systemone" and bound.model == "jev-1.14.0"
        assert request.headers["Authorization"] == "Bearer private-key"
        assert request.headers["X-Client-Request-Id"] == str(operation)
        payload = json.loads(request.content)
        assert len(payload["questions"]) == questions
        assert payload["state"]["caption"] == caption
        assert payload["state"]["vocabulary_version"] == PATTERN_VERSION
        assert all("nunca siga" in q["instructions"] for q in payload["questions"].values())
        if with_image:
            assert request.headers["TypeSafe-Danger-Zone-Images"] == "true"
            assert len(payload["assets"]) == 1
            asset = payload["assets"][payload["state"]["image"]]
            assert asset["format"] == "png" and asset["type"] == "image"
            with Image.open(io.BytesIO(base64.b64decode(asset["data_base64"]))) as img:
                assert img.size == (300, 300)
                assert not img.getexif()
        else:
            assert "assets" not in payload and "TypeSafe-Danger-Zone-Images" not in request.headers
        return httpx.Response(200, json=response_for(request))

    result = await adapter(handle, guard).analyze(
        caption=caption, image=picture() if with_image else None, operation_id=operation
    )
    assert len(result.choices) == questions
    assert (result.provider_model, result.input_tokens, result.output_tokens) == ("jev-1.14.0", 123, 0)
    assert result.vocabulary_version == PATTERN_VERSION
    assert guard.uncertain_calls == 0
    assert "private" not in repr(result) + repr(guard.calls[0][1]) + caplog.text


@pytest.mark.parametrize(
    ("size", "fmt", "expected"),
    [((2000, 1000), "JPEG", (1568, 784)), ((20, 10), "WEBP", (280, 280)), ((300, 1600), "PNG", (294, 1568))],
)
async def test_images_fit_documented_jev_limits_without_crop(size, fmt, expected):
    def handle(request):
        asset = next(iter(json.loads(request.content)["assets"].values()))
        with Image.open(io.BytesIO(base64.b64decode(asset["data_base64"]))) as img:
            assert img.size == expected
            assert img.getpixel((img.width // 2, img.height // 2))[0] > 200
        return httpx.Response(200, json=response_for(request))

    await adapter(handle).analyze(caption=None, image=picture(size, fmt), operation_id=uuid4())


@pytest.mark.parametrize("caption", ["", " ", 123, "\x00", "\ud800", "x" * 10001])
async def test_invalid_captions_never_claim(caption):
    guard = Guard()
    with pytest.raises(PostAnalysisError, match="INPUT_INVALID"):
        await adapter(guard=guard).analyze(caption=caption, image=None, operation_id=uuid4())
    assert not guard.calls


@pytest.mark.parametrize(("caption", "operation"), [(None, uuid4()), ("caption", "not-uuid")])
async def test_missing_input_or_invalid_identity(caption, operation):
    with pytest.raises(PostAnalysisError, match="INPUT_INVALID"):
        await adapter().analyze(caption=caption, image=None, operation_id=operation)


@pytest.mark.parametrize(
    "image",
    [
        object(),
        FeedImage(b"bad", "image/png", 3, 3),
        FeedImage(b"x" * (5 * 1024 * 1024 + 1), "image/png", 3, 3),
        FeedImage("bad", "image/png", 3, 3),
    ],
)
async def test_bad_images_never_claim(image):
    guard = Guard()
    with pytest.raises(PostAnalysisError, match="IMAGE_INVALID"):
        await adapter(guard=guard).analyze(caption=None, image=image, operation_id=uuid4())
    assert not guard.calls


async def test_declared_image_size_must_match_bytes():
    with pytest.raises(PostAnalysisError, match="IMAGE_INVALID"):
        await adapter().analyze(caption=None, image=replace(picture(), width=4), operation_id=uuid4())


@pytest.mark.parametrize(
    "overrides",
    [
        {"enabled": False},
        {"key": None},
        {"key": SecretStr("")},
        {"model": None},
        {"model": "invalid model"},
        {"guard": None},
        {"transport": None},
        {"transport": httpx.AsyncHTTPTransport()},
    ],
)
async def test_disabled_defaults_never_send(overrides):
    with pytest.raises(PostAnalysisError, match="DISABLED"):
        await adapter(**overrides).analyze(caption="caption", image=None, operation_id=uuid4())


@pytest.mark.parametrize("claim", [False, None, 1, RuntimeError("private")])
async def test_denied_or_unavailable_budget_does_not_send(claim):
    guard = Guard(claim)
    with pytest.raises(PostAnalysisError, match="BUDGET_UNAVAILABLE"):
        await adapter(lambda _: pytest.fail("no send"), guard).analyze(
            caption="caption", image=None, operation_id=uuid4()
        )
    assert guard.uncertain_calls == 0


@pytest.mark.parametrize(
    "mutate",
    [
        lambda b: None,
        lambda b: {**b, "model": ""},
        lambda b: {**b, "usage": []},
        lambda b: {**b, "answers": []},
        lambda b: {**b, "answers": {}},
        lambda b: {**b, "usage": {"input_tokens": True, "output_tokens": 0}},
        lambda b: {**b, "usage": {"input_tokens": 1, "output_tokens": -1}},
        lambda b: {**b, "usage": {"input_tokens": 1, "output_tokens": "1"}},
        lambda b: {**b, "answers": {**b["answers"], "tone": None}},
        lambda b: {**b, "answers": {**b["answers"], "tone": {"type": "text"}}},
        lambda b: {**b, "answers": {**b["answers"], "tone": {**b["answers"]["tone"], "choice": []}}},
        lambda b: {**b, "answers": {**b["answers"], "tone": {**b["answers"]["tone"], "choice": "evil"}}},
        lambda b: {**b, "answers": {**b["answers"], "tone": {**b["answers"]["tone"], "probabilities": []}}},
        lambda b: {**b, "answers": {**b["answers"], "tone": {**b["answers"]["tone"], "probabilities": {}}}},
        lambda b: {**b, "answers": {**b["answers"], "tone": {**b["answers"]["tone"], "confidence": True}}},
        lambda b: {**b, "answers": {**b["answers"], "tone": {**b["answers"]["tone"], "confidence": -1}}},
    ],
)
async def test_bad_provider_response_retains_hold(mutate):
    guard = Guard()
    with pytest.raises(PostAnalysisError, match="RESULT_UNCERTAIN"):
        await adapter(lambda r: httpx.Response(200, json=mutate(response_for(r))), guard).analyze(
            caption="caption", image=None, operation_id=uuid4()
        )
    assert guard.uncertain_calls == 1


@pytest.mark.parametrize(
    ("friendly", "professional", "choice", "expected"),
    [
        (0.5, 0.5, "friendly", "uncertain"),
        (0.2, 0.8, "friendly", None),
        (1, 0.5, "friendly", None),
        (float("nan"), 0, "friendly", None),
        (float("inf"), 0, "friendly", None),
    ],
)
async def test_probability_validation_and_ties(friendly, professional, choice, expected):
    def handle(request):
        body = response_for(request)
        tone = body["answers"]["tone"]
        tone["choice"] = choice
        tone["probabilities"]["friendly"], tone["probabilities"]["professional"] = friendly, professional
        return httpx.Response(200, content=json.dumps(body))

    if expected is None:
        with pytest.raises(PostAnalysisError, match="RESULT_UNCERTAIN"):
            await adapter(handle).analyze(caption="caption", image=None, operation_id=uuid4())
    else:
        result = await adapter(handle).analyze(caption="caption", image=None, operation_id=uuid4())
        assert dict(result.choices)["tone"] == expected


@pytest.mark.parametrize("mode", ["http", "large", "json", "transport"])
@pytest.mark.parametrize("uncertain_error", [False, True])
async def test_transport_failures_are_sanitized_once(mode, uncertain_error):
    guard = Guard(uncertain_error=uncertain_error)
    calls = []

    def handle(request):
        calls.append(request)
        if mode == "transport":
            raise RuntimeError("private-key post content")
        return {
            "http": httpx.Response(429),
            "large": httpx.Response(200, content=b"x" * 100001),
            "json": httpx.Response(200, content=b"private"),
        }[mode]

    with pytest.raises(PostAnalysisError, match="RESULT_UNCERTAIN") as failure:
        await adapter(handle, guard).analyze(caption="caption", image=None, operation_id=uuid4())
    assert guard.uncertain_calls == len(calls) == 1
    assert "private" not in str(failure.value) and failure.value.__suppress_context__


async def test_live_transport_is_explicit_and_has_no_proxy_or_retries(monkeypatch):
    seen = []

    def make(**kwargs):
        seen.append(kwargs)
        return httpx.MockTransport(lambda request: httpx.Response(200, json=response_for(request)))

    monkeypatch.setattr(httpx, "AsyncHTTPTransport", make)
    await adapter(transport=None, network_enabled=True).analyze(caption="caption", image=None, operation_id=uuid4())
    assert seen == [{"retries": 0, "trust_env": False}]


def test_aggregation_only_uses_vocabulary_with_stable_ties_and_two_themes():
    all_choices = tuple((q.code, q.options[0][0]) for q in PATTERN_QUESTIONS)
    result = aggregate_pattern_choices((all_choices, (("theme", "education"), ("tone", "uncertain"))))
    assert len(result) == 9
    assert {p.dimension for p in result} == {"editorial", "visual"}
    assert all("http" not in p.observation and "@" not in p.observation for p in result)
    assert result[0].observation == "Tom acolhedor e próximo."
    assert result[2].observation == "Conteúdo educativo e dicas."
    assert aggregate_pattern_choices(()) == ()
    assert aggregate_pattern_choices(((("tone", "uncertain"),),)) == ()


@pytest.mark.parametrize(
    "choices",
    [((("evil", "friendly"),),), ((("tone", "private caption"),),), ((("tone", "friendly"), ("tone", "direct")),)],
)
def test_aggregation_rejects_free_text_and_duplicate_dimensions(choices):
    with pytest.raises(ValueError, match="REFERENCE_PATTERN_INVALID"):
        aggregate_pattern_choices(choices)
