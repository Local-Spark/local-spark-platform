import json
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.adapters.jev_place_types import (
    JevPlaceTypeMapper,
    MappingInput,
    PlaceType,
    PlaceTypeMappingError,
)


class Guard:
    def __init__(self, result=True):
        self.result, self.operations, self.calls = result, set(), []

    async def claim(self, operation_id, request):
        self.calls.append((operation_id, request))
        if isinstance(self.result, Exception):
            raise self.result
        if operation_id in self.operations:
            return False
        self.operations.add(operation_id)
        return self.result


def inp(**overrides):
    values = {
        "terms": ("cafeteria",),
        "business_description": "Doces artesanais",
        "taxonomy_version": "v1",
        "taxonomy": (PlaceType("coffee_shop", "Cafeteria"), PlaceType("bakery", "Padaria")),
    }
    return MappingInput(**(values | overrides))


def answer(choice="match", **changes):
    choices = {
        "match": {"match": 0.8, "no_match": 0.1, "uncertain": 0.1},
        "no_match": {"match": 0.1, "no_match": 0.8, "uncertain": 0.1},
        "uncertain": {"match": 0.1, "no_match": 0.1, "uncertain": 0.8},
    }
    return {"type": "choice", "choice": choice, "confidence": 0.8, "probabilities": choices[choice], **changes}


def body(first=None, second=None, **changes):
    return {
        "model": "jev-actual-model",
        "usage": {"input_tokens": 123, "output_tokens": 10},
        "answers": {"type_0": first or answer(), "type_1": second or answer()},
        **changes,
    }


def mapper(handler, guard=None):
    return JevPlaceTypeMapper(
        SecretStr("secret"), "jev-alias", guard or Guard(), enabled=True, transport=httpx.MockTransport(handler)
    )


async def test_one_call_for_multi_type_with_claim_and_minimal_context(caplog):
    guard, operation, request = Guard(), uuid4(), inp()

    def handler(http_request):
        assert guard.calls == [(operation, request)]
        assert http_request.url == "https://api.typesafe.ai/v1/systemone"
        assert http_request.headers["Authorization"] == "Bearer secret"
        assert http_request.headers["X-Client-Request-Id"] == str(operation)
        payload = json.loads(http_request.content)
        assert payload["model"] == "jev-alias"
        assert payload["state"] == {"business_terms": ["cafeteria"], "business_description": "Doces artesanais"}
        assert set(payload["questions"]) == {"type_0", "type_1"}
        for question in payload["questions"].values():
            assert question["type"] == "choice" and set(question["criteria"]) == {"match", "no_match", "uncertain"}
        return httpx.Response(200, json=body())

    result = await mapper(handler, guard).map(request, operation)
    assert result.state == "mapped" and result.types == ("coffee_shop", "bakery")
    assert result.taxonomy_version == "v1" and result.provider_model == "jev-actual-model"
    assert (result.input_tokens, result.output_tokens) == (123, 10)
    assert "cafeteria" not in repr(request) and "coffee_shop" not in repr(result)
    assert "secret" not in caplog.text and "cafeteria" not in caplog.text


@pytest.mark.parametrize(
    "one,two,state,types",
    [
        ("match", "no_match", "mapped", ("coffee_shop",)),
        ("no_match", "no_match", "no_match", ()),
        ("match", "uncertain", "uncertain", ()),
    ],
)
async def test_classification_preserves_multiple_or_abstains(one, two, state, types):
    result = await mapper(lambda _: httpx.Response(200, json=body(answer(one), answer(two)))).map(inp(), uuid4())
    assert result.state == state and result.types == types


async def test_tied_maximum_abstains_without_confidence_threshold():
    tie = answer(probabilities={"match": 0.45, "no_match": 0.45, "uncertain": 0.1}, confidence=0.9)
    result = await mapper(lambda _: httpx.Response(200, json=body(tie))).map(inp(), uuid4())
    assert result.state == "uncertain" and result.types == ()


async def test_no_arbitrary_confidence_threshold():
    low = answer(confidence=0.01)
    result = await mapper(lambda _: httpx.Response(200, json=body(low))).map(inp(), uuid4())
    assert result.state == "mapped" and result.judgments[0].confidence == 0.01


async def test_business_characteristics_at_maximum_are_sent_without_truncation():
    description = "a" * 2000

    def handler(request):
        assert json.loads(request.content)["state"]["business_description"] == description
        return httpx.Response(200, json=body())

    assert (await mapper(handler).map(inp(business_description=description), uuid4())).state == "mapped"


@pytest.mark.parametrize(
    "mapping_input",
    [
        None,
        inp(terms=[]),
        inp(terms=()),
        inp(terms=(" ",)),
        inp(terms=("x" * 101,)),
        inp(terms=("x",) * 51),
        inp(business_description=" "),
        inp(business_description="a" * 2001),
        inp(taxonomy_version=" "),
        inp(taxonomy=[]),
        inp(taxonomy=()),
        inp(taxonomy=(PlaceType("x", "x"),) * 51),
        inp(taxonomy=("bad",)),
        inp(taxonomy=(PlaceType("invalid/type", "x"),)),
        inp(taxonomy=(PlaceType("x", "x"), PlaceType("x", "x"))),
        inp(taxonomy=(PlaceType("x", " "),)),
    ],
)
async def test_invalid_inputs_rejected_before_guard(mapping_input):
    guard = Guard()
    with pytest.raises(PlaceTypeMappingError, match="TYPE_MAPPING_INPUT_INVALID"):
        await mapper(lambda _: pytest.fail("network"), guard).map(mapping_input, uuid4())
    assert guard.calls == []


async def test_invalid_operation():
    with pytest.raises(PlaceTypeMappingError, match="TYPE_MAPPING_INPUT_INVALID"):
        await mapper(lambda _: pytest.fail("network")).map(inp(), "bad")


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"enabled": True},
        {"enabled": True, "key": SecretStr("")},
        {"enabled": True, "key": SecretStr("key"), "model": "m"},
        {"enabled": True, "key": SecretStr("key"), "guard": Guard()},
    ],
)
async def test_disabled_without_explicit_configuration(kwargs):
    with pytest.raises(PlaceTypeMappingError, match="TYPE_MAPPING_DISABLED"):
        await JevPlaceTypeMapper(**kwargs).map(inp(), uuid4())


@pytest.mark.parametrize("value", [False, None, 1, ValueError("secret")])
async def test_guard_failure_denies_network(value):
    with pytest.raises(PlaceTypeMappingError, match="TYPE_MAPPING_BUDGET_UNAVAILABLE"):
        await mapper(lambda _: pytest.fail("network"), Guard(value)).map(inp(), uuid4())


async def test_uncertain_timeout_never_retries_same_operation():
    operation, guard, calls = uuid4(), Guard(), []

    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("secret")

    adapter = mapper(handler, guard)
    with pytest.raises(PlaceTypeMappingError, match="TYPE_MAPPING_RESULT_UNCERTAIN"):
        await adapter.map(inp(), operation)
    with pytest.raises(PlaceTypeMappingError, match="TYPE_MAPPING_BUDGET_UNAVAILABLE"):
        await adapter.map(inp(), operation)
    assert len(calls) == 1


@pytest.mark.parametrize("status,content", [(500, b""), (200, b"not json"), (200, b"x" * 1_000_001)])
async def test_bad_network_response_is_uncertain(status, content):
    with pytest.raises(PlaceTypeMappingError, match="TYPE_MAPPING_RESULT_UNCERTAIN"):
        await mapper(lambda _: httpx.Response(status, content=content)).map(inp(), uuid4())


@pytest.mark.parametrize(
    "result",
    [
        None,
        {},
        body(model=""),
        body(usage=None),
        body(answers=None),
        body(usage={}),
        body(usage={"input_tokens": True, "output_tokens": 1}),
        body(usage={"input_tokens": 1, "output_tokens": -1}),
        body(answers={}),
        body(answers={"type_0": answer(), "type_1": answer(), "type_2": answer()}),
        body(first={"type": "noul"}),
        body(first=answer(type="noul")),
        body(first={**answer(), "choice": "illegal"}),
        body(first=answer(probabilities={})),
        body(first=answer(confidence=True)),
        body(first=answer(confidence=float("nan"))),
        body(first=answer(confidence=2)),
        body(first=answer(probabilities={"match": 0.5, "no_match": 0.1, "uncertain": 0.1})),
        body(first=answer(probabilities={"match": 0.1, "no_match": 0.8, "uncertain": 0.1})),
        body(first=answer(probabilities={"match": 2, "no_match": 0, "uncertain": 0})),
        body(first=answer(probabilities={"match": True, "no_match": 0, "uncertain": 0})),
    ],
)
async def test_untrusted_response_is_rejected(result):
    with pytest.raises(PlaceTypeMappingError, match="TYPE_MAPPING_RESULT_UNCERTAIN"):
        await mapper(lambda _: httpx.Response(200, json=result)).map(inp(), uuid4())
