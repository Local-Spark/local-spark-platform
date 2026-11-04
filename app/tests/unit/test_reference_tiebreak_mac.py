"""The commitment authenticates exact scope, tied candidate order and request."""

from dataclasses import replace
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.adapters.jev_reference_similarity import SimilarityCandidate, SimilarityInput
from app.adapters.jev_reference_tiebreak import JevReferenceTieBreak, TieBreakRequest
from app.services.reference_tiebreak_mac import TieBreakBindingError, tiebreak_request_mac


def args():
    effect = uuid4()
    body = b'{"model":"test-model","private":"body"}'
    return {
        "key": SecretStr("synthetic-key-not-for-production-0123456789"),
        "key_version": "key-v1",
        "tariff_version": "tariff-v1",
        "credential_version": "credential-v1",
        "tenant": uuid4(),
        "business": uuid4(),
        "actor": uuid4(),
        "search": uuid4(),
        "effect": effect,
        "pilot": uuid4(),
        "google_effect": uuid4(),
        "similarity_effect": uuid4(),
        "batch_id": uuid4(),
        "context_version": 1,
        "source_batch_mac": "a" * 64,
        "reserved_usd_micros": 100,
        "tied_candidate_ids": (uuid4(), uuid4()),
        "request": TieBreakRequest(
            "POST",
            "https://api.typesafe.ai/v1/systemone",
            (
                ("content-length", str(len(body))),
                ("content-type", "application/json"),
                ("host", "api.typesafe.ai"),
                ("x-client-request-id", str(effect)),
            ),
            body,
            "test-model",
            SecretStr("secret-provider-credential"),
        ),
    }


def test_commits_scope_versions_finances_and_ordered_candidates_without_disclosure(caplog):
    values = args()
    mac = tiebreak_request_mac(**values)
    assert len(mac) == 64 and mac == tiebreak_request_mac(**values)
    for field in ("tenant", "business", "actor", "search", "pilot", "google_effect", "similarity_effect", "batch_id"):
        assert tiebreak_request_mac(**(values | {field: uuid4()})) != mac
    for field, value in (
        ("key", SecretStr("other-synthetic-key-01234567890123456")),
        ("key_version", "v2"),
        ("tariff_version", "v2"),
        ("credential_version", "v2"),
        ("context_version", 2),
        ("source_batch_mac", "b" * 64),
        ("reserved_usd_micros", 101),
        ("tied_candidate_ids", (values["tied_candidate_ids"][1], values["tied_candidate_ids"][0])),
        ("tied_candidate_ids", (values["tied_candidate_ids"][0], uuid4())),
    ):
        assert tiebreak_request_mac(**(values | {field: value})) != mac
    effect = uuid4()
    req = values["request"]
    assert (
        tiebreak_request_mac(
            **(
                values
                | {
                    "effect": effect,
                    "request": replace(
                        req,
                        headers=(
                            *req.headers[:3],
                            ("x-client-request-id", str(effect)),
                        ),
                    ),
                }
            )
        )
        != mac
    )
    new_body = req.body + b" "
    headers = (("content-length", str(len(new_body))), *req.headers[1:])
    assert tiebreak_request_mac(**(values | {"request": replace(req, body=new_body, headers=headers)})) != mac
    assert tiebreak_request_mac(**(values | {"request": replace(req, credential=SecretStr("other-secret"))})) != mac
    assert "private" not in mac + caplog.text and "secret" not in mac + caplog.text


async def test_real_mock_request_matches_binding_and_cannot_replay_under_another_effect():
    values = args()
    candidates = tuple(SimilarityCandidate(id_, "Empresa") for id_ in values["tied_candidate_ids"])
    source = SimilarityInput(("cafeteria",), "Atendimento", candidates)

    class Guard:
        async def claim(self, operation, binding):
            values["request"] = binding
            assert operation == values["effect"]
            self.mac = tiebreak_request_mac(**values)
            with pytest.raises(TieBreakBindingError, match="TIE_BREAK_BINDING_INVALID"):
                tiebreak_request_mac(**(values | {"effect": uuid4()}))
            return True

        async def uncertain(self):
            pytest.fail("No uncertain result expected")

    guard = Guard()

    def handler(http_request):
        assert guard.mac == tiebreak_request_mac(**values)
        assert values["request"].body == http_request.content
        return httpx.Response(
            200,
            json={
                "model": "test-model",
                "usage": {"input_tokens": 1, "output_tokens": 1},
                "answers": {
                    "tie_break": {
                        "type": "choice",
                        "choice": "uncertain",
                        "probabilities": {"candidate_0": 0.1, "candidate_1": 0.1, "uncertain": 0.8},
                    }
                },
            },
        )

    result = await JevReferenceTieBreak(
        SecretStr("credential"), "test-model", guard, enabled=True, transport=httpx.MockTransport(handler)
    ).decide(source, values["effect"])
    assert result.candidate_id is None


@pytest.mark.parametrize("key", [None, SecretStr("short"), SecretStr("x" * 32 + "\ud800")])
def test_invalid_key(key):
    with pytest.raises(TieBreakBindingError, match="TIE_BREAK_BINDING_KEY_INVALID"):
        tiebreak_request_mac(**(args() | {"key": key}))


@pytest.mark.parametrize(
    "field,value",
    [
        ("key_version", None),
        ("tariff_version", "!"),
        ("credential_version", ""),
        ("tenant", "x"),
        ("context_version", True),
        ("context_version", 0),
        ("context_version", 2**63),
        ("source_batch_mac", "bad"),
        ("reserved_usd_micros", 0),
        ("reserved_usd_micros", True),
        ("reserved_usd_micros", 5_000_001),
        ("tied_candidate_ids", None),
        ("tied_candidate_ids", ()),
        ("tied_candidate_ids", (uuid4(),)),
        ("tied_candidate_ids", tuple(uuid4() for _ in range(21))),
        ("tied_candidate_ids", ("bad", uuid4())),
        ("request", None),
    ],
)
def test_invalid_metadata_rejected(field, value):
    with pytest.raises(TieBreakBindingError, match="TIE_BREAK_BINDING_INVALID"):
        tiebreak_request_mac(**(args() | {field: value}))


def test_duplicate_candidates_and_effects_are_rejected():
    values = args()
    for change in ({"tied_candidate_ids": (values["tied_candidate_ids"][0],) * 2}, {"effect": values["google_effect"]}):
        with pytest.raises(TieBreakBindingError, match="TIE_BREAK_BINDING_INVALID"):
            tiebreak_request_mac(**(values | change))


@pytest.mark.parametrize(
    "changes",
    [
        {"method": "GET"},
        {"url": "https://wrong"},
        {"model": "!"},
        {"model": "other"},
        {"body": b""},
        {"credential": None},
        {"credential": SecretStr("")},
        {"headers": ()},
        {"credential": SecretStr("\ud800")},
    ],
)
def test_invalid_request_rejected(changes):
    values = args()
    with pytest.raises(TieBreakBindingError, match="TIE_BREAK_BINDING_INVALID"):
        tiebreak_request_mac(**(values | {"request": replace(values["request"], **changes)}))


@pytest.mark.parametrize("body", [b"x", b"[]", b'{"model":"wrong"}'])
def test_request_body_must_be_json_object_matching_model(body):
    values = args()
    req = values["request"]
    headers = (("content-length", str(len(body))), *req.headers[1:])
    with pytest.raises(TieBreakBindingError, match="TIE_BREAK_BINDING_INVALID"):
        tiebreak_request_mac(**(values | {"request": replace(req, body=body, headers=headers)}))
