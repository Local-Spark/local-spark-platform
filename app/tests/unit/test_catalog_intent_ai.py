"""Closed, content-free provider contract; tests never contact the network."""

import json
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.adapters.catalog_intent_ai import CatalogInterpretationError, OpenAICatalogIntentProvider


@pytest.fixture
def example():
    item = uuid4()
    return {
        "id": item,
        "candidates": [{"id": str(item), "kind": "product", "name": "Croissant"}],
        "draft": {"intent": "content_request", "decision": "selected", "offering_id": str(item), "format": "photo"},
    }


def response(draft, *, status="completed", usage=None, output=None):
    return {
        "status": status,
        "usage": usage if usage is not None else {"input_tokens": 100, "output_tokens": 20},
        "output": output
        if output is not None
        else [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(draft)}]}],
    }


def provider(handler):
    return OpenAICatalogIntentProvider(SecretStr("test-key"), "gpt-test", transport=httpx.MockTransport(handler))


async def test_structured_provider_selects_only_eligible_id_and_format(example):
    captured = []

    def handler(request):
        captured.append(request)
        return httpx.Response(200, json=response(example["draft"]))

    operation = uuid4()
    result = await provider(handler).interpret(
        "Crie uma imagem do croissant", example["candidates"], ["photo"], operation
    )
    assert result.offering_id == example["id"] and result.format == "photo"
    assert result.intent == "content_request" and result.decision == "selected"
    assert (result.input_tokens, result.output_tokens) == (100, 20)
    sent = json.loads(captured[0].content)
    assert sent["store"] is False and sent["tools"] == []
    assert sent["text"]["format"]["strict"] is True
    assert sent["max_output_tokens"] == 320
    assert captured[0].headers["x-client-request-id"] == str(operation)
    assert json.loads(sent["input"][1]["content"])["candidates"] == example["candidates"]


async def test_negation_blocks_even_a_selected_provider_output(example):
    result = await provider(lambda _: httpx.Response(200, json=response(example["draft"]))).interpret(
        "Não crie imagem do croissant", example["candidates"], ["photo"], uuid4()
    )
    assert result.decision == "clarify" and result.offering_id is None and result.format is None
    assert result.negation_guarded is True
    assert (result.input_tokens, result.output_tokens) == (100, 20)


@pytest.mark.parametrize("decision", ["none", "clarify"])
async def test_provider_can_abstain(example, decision):
    draft = {**example["draft"], "decision": decision, "offering_id": None, "format": None}
    result = await provider(lambda _: httpx.Response(200, json=response(draft))).interpret(
        "Crie uma imagem", example["candidates"], [], uuid4()
    )
    assert result.decision == decision and result.offering_id is None


@pytest.mark.parametrize("key,model", [("", "gpt-test"), ("key", ""), ("key", "m" * 81)])
def test_disabled_requires_key_and_model(key, model):
    with pytest.raises(CatalogInterpretationError, match="CATALOG_INTERPRETER_DISABLED"):
        OpenAICatalogIntentProvider(SecretStr(key), model)


@pytest.mark.parametrize(
    "case",
    [
        "empty",
        "oversize",
        "too_many",
        "duplicate",
        "bad_candidate",
        "extra_candidate",
        "invalid_formats",
        "duplicate_formats",
    ],
)
async def test_invalid_input_never_calls_provider(example, case):
    message, candidates, formats = "Crie uma imagem", list(example["candidates"]), ["photo"]
    if case == "empty":
        message = " "
    elif case == "oversize":
        message = "x" * 4001
    elif case == "too_many":
        candidates = [{"id": str(uuid4()), "kind": "product", "name": "x"} for _ in range(9)]
    elif case == "duplicate":
        candidates *= 2
    elif case == "bad_candidate":
        candidates = [{"id": "bad", "kind": "product", "name": "x"}]
    elif case == "extra_candidate":
        candidates = [{**candidates[0], "private_data": "x"}]
    elif case == "invalid_formats":
        formats = ["video"]
    else:
        formats = ["photo", "photo"]
    called = False

    def handler(_):
        nonlocal called
        called = True
        return httpx.Response(200)

    with pytest.raises(CatalogInterpretationError, match="CATALOG_INTERPRETER_INPUT_INVALID") as exc:
        await provider(handler).interpret(message, candidates, formats, uuid4())
    assert not exc.value.uncertain and not called


@pytest.mark.parametrize("case", ["http", "transport", "non_json"])
async def test_provider_failures_are_uncertain_and_content_free(example, case):
    def handler(request):
        if case == "transport":
            raise httpx.ReadTimeout("sensitive payload", request=request)
        if case == "non_json":
            return httpx.Response(200, content=b"not json")
        return httpx.Response(503, text="sensitive payload")

    with pytest.raises(CatalogInterpretationError, match="CATALOG_INTERPRETER_UNCERTAIN") as exc:
        await provider(handler).interpret("Crie uma imagem", example["candidates"], ["photo"], uuid4())
    assert exc.value.uncertain and "sensitive" not in str(exc.value)


@pytest.mark.parametrize(
    "case",
    [
        "non_dict",
        "incomplete",
        "missing_usage",
        "invalid_usage",
        "negative_usage",
        "bad_output",
        "no_text",
        "multiple_text",
        "bad_json",
        "invalid_schema",
        "missing_selected",
        "id_on_none",
        "other_id",
        "ineligible_format",
    ],
)
async def test_invalid_provider_response_is_not_a_decision(example, case):
    draft = dict(example["draft"])
    body = response(draft)
    if case == "non_dict":
        body = []
    elif case == "incomplete":
        body["status"] = "incomplete"
    elif case == "missing_usage":
        del body["usage"]
    elif case == "invalid_usage":
        body["usage"] = {"input_tokens": True, "output_tokens": 1}
    elif case == "negative_usage":
        body["usage"] = {"input_tokens": 1, "output_tokens": -1}
    elif case == "bad_output":
        body["output"] = None
    elif case == "no_text":
        body["output"] = [{"type": "reasoning"}, {"type": "message", "content": [{"type": "refusal"}]}]
    elif case == "multiple_text":
        body["output"] = [{"type": "message", "content": [{"type": "output_text", "text": "{}"}] * 2}]
    elif case == "bad_json":
        body["output"] = [{"type": "message", "content": [{"type": "output_text", "text": "bad"}]}]
    elif case == "invalid_schema":
        body = response({**draft, "other": "x"})
    elif case == "missing_selected":
        body = response({**draft, "offering_id": None})
    elif case == "id_on_none":
        body = response({**draft, "decision": "none"})
    elif case == "other_id":
        body = response({**draft, "offering_id": str(uuid4())})
    else:
        body = response({**draft, "format": "story"})
    with pytest.raises(CatalogInterpretationError, match="CATALOG_INTERPRETER_INVALID") as exc:
        await provider(lambda _: httpx.Response(200, json=body)).interpret(
            "Crie uma imagem", example["candidates"], ["photo"], uuid4()
        )
    assert exc.value.uncertain
