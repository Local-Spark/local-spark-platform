"""Only mock Jev recommendations, bound to the authorized candidates."""

import json
from dataclasses import replace
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.adapters.jev_reference_recommendations import (
    JevReferenceRecommendations,
    RecommendationCandidate,
    RecommendationError,
    RecommendationInput,
    _parse,
)


class Guard:
    def __init__(self, result=True, fail_uncertain=False):
        self.result, self.fail_uncertain, self.calls = result, fail_uncertain, []

    async def claim(self, operation, binding):
        self.calls.append((operation, binding))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result

    async def uncertain(self):
        self.calls.append("uncertain")
        if self.fail_uncertain:
            raise RuntimeError("private provider message")


def inputs(count=3):
    return RecommendationInput(
        ("cafe",),
        "private context",
        tuple(RecommendationCandidate(uuid4(), f"private {i}", ("cafe",), Decimal("8.2")) for i in range(count)),
    )


def answer(choices, count):
    options = ["none", *(f"candidate_{i}" for i in range(count))]
    return {
        "answers": {
            f"rank_{rank}": {
                "type": "choice",
                "choice": choice,
                "probabilities": {option: 1 if option == choice else 0 for option in options},
            }
            for rank, choice in enumerate(choices, 1)
        }
    }


_MISSING = object()


def adapter(handler, guard=_MISSING, **updates):
    return JevReferenceRecommendations(
        **{
            **{
                "key": SecretStr("private-token"),
                "model": "test-model",
                "guard": Guard() if guard is _MISSING else guard,
                "enabled": True,
                "transport": httpx.MockTransport(handler),
            },
            **updates,
        }
    )


async def test_recommendations_are_guarded_bounded_and_never_return_provider_text(caplog):
    values, operation, guard = inputs(), uuid4(), Guard()

    def handler(request):
        ident, binding = guard.calls[0]
        assert ident == operation and binding.body == request.content
        assert binding.credential.get_secret_value() == "private-token"
        body = json.loads(request.content)
        assert len(body["questions"]) == 3 and body["state"]["candidates"]["candidate_0"]["score"] == "8.2"
        assert "private" not in repr(binding)
        return httpx.Response(200, json=answer(["candidate_2", "candidate_0", "none"], 3))

    result = await adapter(handler, guard).recommend(values, operation)
    assert [(item.candidate_id, item.rank) for item in result] == [
        (values.candidates[2].candidate_id, 1),
        (values.candidates[0].candidate_id, 2),
    ]
    assert all(item.criteria == ("similarity", "reputation") for item in result)
    assert "private" not in repr(result) and "private-token" not in caplog.text


def test_parse_allows_zero_and_fewer_than_three_recommendations():
    candidates = inputs(2).candidates
    assert _parse(answer(["none", "none"], 2), candidates) == ()
    result = _parse(answer(["candidate_0", "none"], 2), candidates)
    assert len(result) == 1 and result[0].candidate_id == candidates[0].candidate_id


@pytest.mark.parametrize(
    "response",
    [
        None,
        {},
        {"answers": []},
        {"answers": {}},
        {"answers": {"rank_1": None, "rank_2": None, "rank_3": None}},
        answer(["candidate_0", "candidate_0", "none"], 3),
        answer(["none", "candidate_1", "none"], 3),
    ],
)
def test_malformed_duplicate_or_unordered_abstention_is_uncertain(response):
    with pytest.raises(RecommendationError, match="RECOMMENDATION_RESULT_UNCERTAIN"):
        _parse(response, inputs().candidates)


@pytest.mark.parametrize(
    "field,value",
    [
        ("choice", "unknown"),
        ("choice", None),
        ("type", "bad"),
        ("probabilities", {}),
        ("probabilities", {"none": True, "candidate_0": 0, "candidate_1": 0, "candidate_2": 0}),
        ("probabilities", {"none": -1, "candidate_0": 2, "candidate_1": 0, "candidate_2": 0}),
        ("probabilities", {"none": float("nan"), "candidate_0": 1, "candidate_1": 0, "candidate_2": 0}),
        ("probabilities", {"none": 0.5, "candidate_0": 0.5, "candidate_1": 0, "candidate_2": 0}),
        ("probabilities", {"none": 0, "candidate_0": 0.5, "candidate_1": 0, "candidate_2": 0}),
        ("probabilities", {"none": 1, "candidate_0": 0, "candidate_1": 0, "candidate_2": 0}),
    ],
)
def test_incoherent_choices_and_probabilities_are_uncertain(field, value):
    response = answer(["candidate_0", "candidate_1", "candidate_2"], 3)
    response["answers"]["rank_1"][field] = value
    with pytest.raises(RecommendationError, match="RECOMMENDATION_RESULT_UNCERTAIN"):
        _parse(response, inputs().candidates)


@pytest.mark.parametrize(
    "change",
    [
        {"business_terms": ()},
        {"business_terms": ["cafe"]},
        {"business_terms": (" ",)},
        {"business_description": "\x00"},
        {"business_description": "\ud800"},
        {"candidates": ()},
        {"candidates": []},
        {"candidates": inputs(11).candidates},
    ],
)
async def test_invalid_input_never_claims(change):
    guard = Guard()
    with pytest.raises(RecommendationError, match="RECOMMENDATION_INPUT_INVALID"):
        await adapter(lambda _: pytest.fail("no call"), guard).recommend(replace(inputs(), **change), uuid4())
    assert not guard.calls


@pytest.mark.parametrize(
    "change",
    [
        {"candidate_id": "bad"},
        {"name": " "},
        {"types": []},
        {"types": ("bad-type",)},
        {"types": ("cafe", "cafe")},
        {"name": None, "types": ()},
        {"reputation_score": 4},
        {"reputation_score": Decimal("NaN")},
        {"reputation_score": Decimal("11")},
    ],
)
async def test_invalid_candidate_never_claims(change):
    value = inputs(1)
    with pytest.raises(RecommendationError, match="RECOMMENDATION_INPUT_INVALID"):
        await adapter(lambda _: pytest.fail("no call")).recommend(
            replace(value, candidates=(replace(value.candidates[0], **change),)), uuid4()
        )


async def test_duplicate_candidates_and_invalid_outer_input_are_rejected():
    value = inputs(1)
    for item, operation in (
        (None, uuid4()),
        (value, "bad"),
        (replace(value, candidates=value.candidates * 2), uuid4()),
        (replace(value, candidates=(None,)), uuid4()),
    ):
        with pytest.raises(RecommendationError, match="RECOMMENDATION_INPUT_INVALID"):
            await adapter(lambda _: pytest.fail("no call")).recommend(item, operation)


@pytest.mark.parametrize(
    "change",
    [
        {"enabled": False},
        {"key": None},
        {"key": SecretStr("")},
        {"model": None},
        {"guard": None},
        {"transport": None},
        {"transport": httpx.AsyncHTTPTransport()},
    ],
)
async def test_disabled_configuration_never_calls_provider(change):
    with pytest.raises(RecommendationError, match="RECOMMENDATION_DISABLED"):
        await adapter(lambda _: pytest.fail("no call"), **change).recommend(inputs(), uuid4())


@pytest.mark.parametrize("decision", [False, RuntimeError("private failure")])
async def test_guard_failure_does_not_dispatch(decision):
    with pytest.raises(RecommendationError, match="RECOMMENDATION_BUDGET_UNAVAILABLE"):
        await adapter(lambda _: pytest.fail("no call"), Guard(decision)).recommend(inputs(), uuid4())


async def test_credential_binding_rejects_modified_header_before_claim(monkeypatch):
    real_request = httpx.Request

    def altered_request(*args, **kwargs):
        request = real_request(*args, **kwargs)
        request.headers["Authorization"] = "Bearer wrong"
        return request

    monkeypatch.setattr(httpx, "Request", altered_request)
    guard = Guard()
    with pytest.raises(RecommendationError, match="RECOMMENDATION_INPUT_INVALID"):
        await adapter(lambda _: pytest.fail("no call"), guard).recommend(inputs(), uuid4())
    assert guard.calls == []


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(500),
        httpx.Response(200, content=b"bad json"),
        httpx.Response(200, json={}),
        httpx.Response(200, content=b"x" * 1_000_001),
    ],
)
@pytest.mark.parametrize("fail_uncertain", [False, True])
async def test_provider_failures_retain_uncertainty(response, fail_uncertain):
    guard = Guard(fail_uncertain=fail_uncertain)
    with pytest.raises(RecommendationError, match="RECOMMENDATION_RESULT_UNCERTAIN"):
        await adapter(lambda _: response, guard).recommend(inputs(), uuid4())
    assert guard.calls[-1] == "uncertain"
