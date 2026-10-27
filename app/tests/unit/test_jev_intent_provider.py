import json
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.adapters.jev_intent_ai import JevIntentError, JevIntentProvider, _choice


def answer(choice, options, confidence=1.0):
    return {
        "type": "choice",
        "choice": choice,
        "confidence": confidence,
        "probabilities": {option: float(option == choice) for option in options},
    }


@pytest.fixture
def candidate():
    return {"id": str(uuid4()), "kind": "product", "name": "Dog da Casa"}


def response_body(candidate_count=1):
    options = {f"item_{i}" for i in range(candidate_count)} | {"none", "clarify"}
    return {
        "model": "jev-1.14.0",
        "usage": {"input_tokens": 720, "output_tokens": 15},
        "answers": {
            "intent": answer("content_request", {"content_request", "price", "availability", "question", "other"}),
            "offering": answer("item_0" if candidate_count else "none", options),
            "format": answer("photo", {"photo", "story", "unspecified", "unsupported"}),
        },
    }


@pytest.mark.asyncio
async def test_jev_interprets_a_single_candidate_without_exposing_secrets(candidate):
    def handler(request):
        body = json.loads(request.content)
        assert body["model"] == "jev-1.14.0"
        assert len(body["questions"]) == 3
        assert "Dog da Casa" in body["state"]
        assert "sensitive-key" not in body["state"]
        return httpx.Response(200, json=response_body())

    provider = JevIntentProvider(SecretStr("sensitive-key"), "jev-1.14.0", transport=httpx.MockTransport(handler))
    result = await provider.interpret("Crie uma foto do Dog da Casa", [candidate], ["photo", "story"], uuid4())
    assert result.decision == "selected"
    assert str(result.offering_id) == candidate["id"]
    assert result.intent == "content_request" and result.format == "photo"
    assert (result.input_tokens, result.output_tokens) == (720, 15)


@pytest.mark.asyncio
async def test_no_match_is_never_promoted_to_a_product():
    provider = JevIntentProvider(
        SecretStr("key"),
        "jev-1.14.0",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=response_body(0))),
    )
    result = await provider.interpret("Quero divulgar algo", [], ["photo", "story"], uuid4())
    assert result.decision == "none" and result.offering_id is None


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["low_confidence", "question", "malformed", "wrong_model", "provider_error"])
async def test_jev_abstains_or_fails_closed_on_bad_responses(candidate, case):
    body = response_body()
    if case == "low_confidence":
        body["answers"]["offering"]["confidence"] = 0.2
    elif case == "question":
        body["answers"]["intent"] = answer("question", set(body["answers"]["intent"]["probabilities"]))
    elif case == "malformed":
        body["answers"]["offering"]["probabilities"] = ["none", "clarify"]
    elif case == "wrong_model":
        body["model"] = "unknown"
    provider = JevIntentProvider(
        SecretStr("key"),
        "jev-1.14.0",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(429 if case == "provider_error" else 200, json=body)
        ),
    )
    if case in {"low_confidence", "question"}:
        result = await provider.interpret("Dog da Casa", [candidate], ["photo", "story"], uuid4())
        assert result.decision == "clarify" and result.offering_id is None
    else:
        with pytest.raises(JevIntentError, match="JEV_RESULT_UNCERTAIN"):
            await provider.interpret("Dog da Casa", [candidate], ["photo", "story"], uuid4())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "message,candidates,formats",
    [
        ("x", [{"id": str(uuid4()), "kind": "product", "name": "x"}] * 9, ["photo"]),
        ("", [], ["photo"]),
        ("x" * 4001, [], ["photo"]),
        ("x", [{"id": "bad"}], ["photo"]),
        ("x", [], ["video"]),
        ("x", [], ["photo", "photo"]),
    ],
)
async def test_invalid_inputs_never_call_provider(message, candidates, formats):
    provider = JevIntentProvider(
        SecretStr("key"),
        "jev-1.14.0",
        transport=httpx.MockTransport(lambda request: pytest.fail("invalid inputs must not make a network request")),
    )
    with pytest.raises(JevIntentError, match="JEV_INPUT_INVALID"):
        await provider.interpret(message, candidates, formats, uuid4())


@pytest.mark.parametrize(
    "value",
    [
        {"type": "choice", "choice": "a", "confidence": True, "probabilities": {"a": 1.0, "b": 0.0}},
        {"type": "choice", "choice": "a", "confidence": 1.0, "probabilities": {"a": True, "b": 0.0}},
        {"type": "choice", "choice": "a", "confidence": float("nan"), "probabilities": {"a": 1.0, "b": 0.0}},
        {"type": "choice", "choice": "a", "confidence": 1.0, "probabilities": {"a": -1.0, "b": 2.0}},
        {"type": "choice", "choice": "a", "confidence": 1.0, "probabilities": {"a": 0.2, "b": 0.2}},
        {"type": "choice", "choice": "a", "confidence": 1.0, "probabilities": {"a": 0.2, "b": 0.8}},
    ],
)
def test_invalid_probability_data_cannot_be_used_for_decisions(value):
    with pytest.raises(JevIntentError, match="JEV_RESPONSE_INVALID"):
        _choice({"answers": {"q": value}}, "q", {"a", "b"}, 0.5)


@pytest.mark.parametrize("alteration", ["duplicate", "kind", "empty_name", "invalid_usage"])
async def test_invalid_candidate_or_usage_rejected(candidate, alteration):
    candidates = [candidate]
    body = response_body()
    if alteration == "duplicate":
        candidates.append(candidate)
    elif alteration == "kind":
        candidate["kind"] = "unknown"
    elif alteration == "empty_name":
        candidate["name"] = ""
    else:
        body["usage"]["input_tokens"] = -1
    provider = JevIntentProvider(
        SecretStr("key"), "jev-1.14.0", transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body))
    )
    with pytest.raises(JevIntentError):
        await provider.interpret("Quero uma foto", candidates, ["photo", "story"], uuid4())


@pytest.mark.parametrize("field", ["intent", "format"])
async def test_low_confidence_never_invents_an_intent_or_format(candidate, field):
    body = response_body()
    body["answers"][field]["confidence"] = 0.1
    provider = JevIntentProvider(
        SecretStr("key"), "jev-1.14.0", transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body))
    )
    result = await provider.interpret("Quero divulgar", [candidate], ["photo", "story"], uuid4())
    if field == "intent":
        assert result.decision == "clarify" and result.intent == "other"
    else:
        assert result.format is None


async def test_unsupported_video_requests_ask_for_clarification(candidate):
    body = response_body()
    body["answers"]["format"] = answer("unsupported", {"photo", "story", "unspecified", "unsupported"})
    provider = JevIntentProvider(
        SecretStr("key"), "jev-1.14.0", transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body))
    )
    result = await provider.interpret("Crie um vídeo", [candidate], ["photo", "story"], uuid4())
    assert result.decision == "clarify" and result.offering_id is None and result.format is None


async def test_video_word_fails_closed_even_when_model_misclassifies_format(candidate):
    provider = JevIntentProvider(
        SecretStr("key"),
        "jev-1.14.0",
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=response_body())),
    )
    result = await provider.interpret("Crie um vídeo do Dog", [candidate], ["photo", "story"], uuid4())
    assert result.decision == "clarify" and result.format is None
