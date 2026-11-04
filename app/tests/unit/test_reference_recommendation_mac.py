"""Recommendation commitment binds actual credentials, effects and shortlist."""

from dataclasses import replace
from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.adapters.jev_reference_recommendations import RecommendationRequest
from app.schemas.reference_filtered_batch import FilteredBatch
from app.services.reference_recommendation_mac import RecommendationBindingError, recommendation_request_mac


def arguments():
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
        "shortlist": FilteredBatch(
            candidates=(
                {
                    "candidate_id": uuid4(),
                    "place_id": "private-place",
                    "reputation_score": "8.2",
                    "reputation_formula_version": "penalized-3.4-v1",
                },
            )
        ),
        "request": RecommendationRequest(
            "POST",
            "https://api.typesafe.ai/v1/systemone",
            "test-model",
            body,
            SecretStr("secret-provider-credential"),
            (
                ("content-length", str(len(body))),
                ("content-type", "application/json"),
                ("x-client-request-id", str(effect)),
            ),
        ),
    }


def test_mac_binds_scope_finances_body_credential_and_private_shortlist():
    args = arguments()
    mac = recommendation_request_mac(**args)
    assert mac == recommendation_request_mac(**args) and len(mac) == 64
    assert "private" not in mac and "secret" not in mac
    for field in ("tenant", "business", "actor", "search", "pilot", "google_effect", "similarity_effect", "batch_id"):
        assert recommendation_request_mac(**{**args, field: uuid4()}) != mac
    new_effect = uuid4()
    new_headers = (*args["request"].headers[:2], ("x-client-request-id", str(new_effect)))
    assert (
        recommendation_request_mac(
            **{**args, "effect": new_effect, "request": replace(args["request"], headers=new_headers)}
        )
        != mac
    )
    for field, value in (
        ("key", SecretStr("other-synthetic-key-01234567890123456")),
        ("key_version", "v2"),
        ("tariff_version", "v2"),
        ("credential_version", "v2"),
        ("context_version", 2),
        ("source_batch_mac", "b" * 64),
        ("reserved_usd_micros", 101),
    ):
        assert recommendation_request_mac(**{**args, field: value}) != mac
    req = args["request"]
    body = req.body + b" "
    headers = (
        ("content-length", str(len(body))),
        ("content-type", "application/json"),
        ("x-client-request-id", str(args["effect"])),
    )
    assert recommendation_request_mac(**{**args, "request": replace(req, body=body, headers=headers)}) != mac
    assert recommendation_request_mac(**{**args, "request": replace(req, credential=SecretStr("other-secret"))}) != mac
    candidate = args["shortlist"].candidates[0]
    changed = FilteredBatch(candidates=(candidate.model_copy(update={"candidate_id": uuid4()}),))
    assert recommendation_request_mac(**{**args, "shortlist": changed}) != mac


@pytest.mark.parametrize("key", [None, SecretStr("short"), SecretStr("x" * 32 + "\ud800")])
def test_bad_key_rejected(key):
    with pytest.raises(RecommendationBindingError, match="RECOMMENDATION_BINDING_KEY_INVALID"):
        recommendation_request_mac(**{**arguments(), "key": key})


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
        ("shortlist", None),
        ("shortlist", FilteredBatch(candidates=())),
        ("request", None),
    ],
)
def test_invalid_metadata_is_rejected(field, value):
    with pytest.raises(RecommendationBindingError, match="RECOMMENDATION_BINDING_INVALID"):
        recommendation_request_mac(**{**arguments(), field: value})


def test_more_than_ten_candidates_and_duplicate_effect_ids_are_rejected():
    args = arguments()
    many = FilteredBatch(
        candidates=tuple(
            {
                "candidate_id": uuid4(),
                "place_id": str(i),
                "reputation_score": "8",
                "reputation_formula_version": "penalized-3.4-v1",
            }
            for i in range(11)
        )
    )
    for change in ({"shortlist": many}, {"effect": args["google_effect"]}):
        with pytest.raises(RecommendationBindingError, match="RECOMMENDATION_BINDING_INVALID"):
            recommendation_request_mac(**{**args, **change})


@pytest.mark.parametrize(
    "changes",
    [
        {"method": "GET"},
        {"url": "https://wrong"},
        {"model": "!"},
        {"model": "other"},
        {"body": b""},
        {"body": b"x"},
        {"body": b"[]"},
        {"credential": None},
        {"credential": SecretStr("")},
        {"headers": ()},
        {"credential": SecretStr("\ud800")},
    ],
)
def test_invalid_request_is_rejected(changes):
    args = arguments()
    with pytest.raises(RecommendationBindingError, match="RECOMMENDATION_BINDING_INVALID"):
        recommendation_request_mac(**{**args, "request": replace(args["request"], **changes)})


@pytest.mark.parametrize("body", [b"x", b"[]", b'{"model":"wrong"}'])
def test_body_must_be_json_object_for_expected_model(body):
    args = arguments()
    headers = (
        ("content-length", str(len(body))),
        ("content-type", "application/json"),
        ("x-client-request-id", str(args["effect"])),
    )
    with pytest.raises(RecommendationBindingError, match="RECOMMENDATION_BINDING_INVALID"):
        recommendation_request_mac(**{**args, "request": replace(args["request"], body=body, headers=headers)})
