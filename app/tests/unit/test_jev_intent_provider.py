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
async def test_implicit_advertising_request_has_explicit_criteria_without_promoting_price_updates(candidate):
    def handler(request):
        body = json.loads(request.content)
        question = body["questions"]["intent"]
        assert "quer divulgar" in question["criteria"]["content_request"]
        assert "sem pedir divulgação" in question["criteria"]["price"]
        assert "informação isolada não é pedido de publicação" in question["instructions"]
        selected = response_body()
        selected["answers"]["format"] = answer("unspecified", {"photo", "story", "unspecified", "unsupported"})
        return httpx.Response(200, json=selected)

    provider = JevIntentProvider(SecretStr("key"), "jev-1.14.0", transport=httpx.MockTransport(handler))
    result = await provider.interpret("Quero divulgar o Dog da Casa", [candidate], ["photo", "story"], uuid4())
    assert result.intent == "content_request" and result.decision == "selected" and result.format is None


@pytest.mark.asyncio
async def test_no_match_is_never_promoted_to_a_product():
    def handler(request):
        request_data = json.loads(request.content)
        assert set(request_data["questions"]) == {"intent", "format"}
        assert json.loads(request_data["state"])["candidates"] == []
        body = response_body(0)
        del body["answers"]["offering"]
        return httpx.Response(200, json=body)

    provider = JevIntentProvider(
        SecretStr("key"),
        "jev-1.14.0",
        transport=httpx.MockTransport(handler),
    )
    result = await provider.interpret("Quero divulgar algo", [], ["photo", "story"], uuid4())
    assert result.decision == "none" and result.offering_id is None
    assert result.intent == "content_request" and result.format == "photo"


@pytest.mark.parametrize("uncertain_field", ["intent", "format"])
async def test_no_candidates_keeps_motion_intent_and_format_uncertainty(uncertain_field):
    eligible = ["photo", "story", "reel"]
    body = response_body(0)
    del body["answers"]["offering"]
    body["answers"]["format"] = answer("reel", set(eligible) | {"unspecified", "unsupported"})
    body["answers"][uncertain_field]["confidence"] = 0.1

    def handler(request):
        assert "offering" not in json.loads(request.content)["questions"]
        return httpx.Response(200, json=body)

    provider = JevIntentProvider(SecretStr("key"), "jev-1.14.0", transport=httpx.MockTransport(handler))
    result = await provider.interpret("Faça um reel", [], eligible, uuid4())
    assert result.decision == "clarify" and result.offering_id is None and result.format is None
    assert result.intent == ("other" if uncertain_field == "intent" else "content_request")


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


@pytest.mark.parametrize(
    "message,format",
    [
        ("Edite um reel do Dog", "reel"),
        ("Edite minha gravação para story", "story_video"),
        ("Faça um story animado", "story_video"),
        ("Crie um carrossel animado do Dog", "carousel_motion"),
        ("Crie um carrossel do Dog", "carousel_motion"),
        ("Carrossel animado com fotos", "carousel_motion"),
        ("Faça carrossel com as fotos que enviei", "carousel_motion"),
        ("Faça carrossel animado sem vídeo", "carousel_motion"),
        ("Crie um carrossel em vídeo", "carousel_motion"),
        ("Edite o vídeo como reel", "reel"),
        ("Faça um reel com a gravação para divulgar nos stories", "reel"),
        ("Faça reel sem música", "reel"),
        ("Faça vídeo", "story_video"),
        ("Quero uma peça em movimento", "reel"),
    ],
)
async def test_motion_format_available_only_when_explicitly_eligible(candidate, message, format):
    eligible = ["photo", "story", format]

    def handler(request):
        body = json.loads(request.content)
        criteria = body["questions"]["format"]["criteria"]
        assert "evidência suficiente" in body["questions"]["format"]["instructions"]
        assert set(criteria) == set(eligible) | {"unspecified", "unsupported"}
        assert "indisponível" not in criteria["unsupported"] or "opções" in criteria["unsupported"]
        assert "estática" in criteria["story"] and "vídeo" in criteria[format].lower()
        result = response_body()
        result["answers"]["format"] = answer(format, set(criteria))
        return httpx.Response(200, json=result)

    provider = JevIntentProvider(SecretStr("key"), "jev-1.14.0", transport=httpx.MockTransport(handler))
    result = await provider.interpret(message, [candidate], eligible, uuid4())
    assert result.decision == "selected" and result.format == format


@pytest.mark.parametrize(
    "message,chosen",
    [
        ("Faça vídeo", "photo"),
        ("Faça vídeo para story", "story"),
        ("Faça vídeo para story", "unspecified"),
        ("Faça um story animado", "story"),
        ("Faça carrossel animado", "photo"),
        ("Quero foto", "unsupported"),
    ],
)
async def test_motion_requests_do_not_fall_through_to_static_format(candidate, message, chosen):
    eligible = ["photo", "story", "reel", "story_video", "carousel_motion"]
    body = response_body()
    body["answers"]["format"] = answer(chosen, set(eligible) | {"unspecified", "unsupported"})
    provider = JevIntentProvider(
        SecretStr("key"), "jev-1.14.0", transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body))
    )
    result = await provider.interpret(message, [candidate], eligible, uuid4())
    assert result.decision == "clarify" and result.offering_id is None and result.format is None


@pytest.mark.parametrize("message", ["Faça um reel", "Faça um story em vídeo", "Faça carrossel animado"])
async def test_default_formats_still_refuse_motion_even_if_model_returns_story(candidate, message):
    body = response_body()
    body["answers"]["format"] = answer("story", {"photo", "story", "unspecified", "unsupported"})
    provider = JevIntentProvider(
        SecretStr("key"), "jev-1.14.0", transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body))
    )
    result = await provider.interpret(message, [candidate], ["photo", "story"], uuid4())
    assert result.decision == "clarify" and result.format is None


async def test_provider_cannot_select_motion_format_outside_eligible_formats(candidate):
    body = response_body()
    body["answers"]["format"] = answer("reel", {"photo", "story", "reel", "unspecified", "unsupported"})
    provider = JevIntentProvider(
        SecretStr("key"), "jev-1.14.0", transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body))
    )
    with pytest.raises(JevIntentError, match="JEV_RESULT_UNCERTAIN"):
        await provider.interpret("Faça um reel", [candidate], ["photo", "story"], uuid4())


async def test_uncertain_motion_format_is_not_silently_treated_as_unspecified(candidate):
    eligible = ["photo", "story", "reel"]
    body = response_body()
    body["answers"]["format"] = answer("reel", set(eligible) | {"unspecified", "unsupported"}, confidence=0.1)
    provider = JevIntentProvider(
        SecretStr("key"), "jev-1.14.0", transport=httpx.MockTransport(lambda _: httpx.Response(200, json=body))
    )
    result = await provider.interpret("Faça reel", [candidate], eligible, uuid4())
    assert result.decision == "clarify" and result.format is None
