import json
from dataclasses import replace
from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.adapters.jev_reference_similarity import JevChargeableRequest
from app.services.reference_jev_request_mac import JevBindingError, jev_request_mac


def _values():
    return {
        "key": SecretStr("synthetic-key-for-testing-only-0123456789"),
        "key_version": "test-key-v1",
        "tariff_version": "synthetic-price-v1",
        "credential_version": "synthetic-project-v1",
        "tenant": uuid4(),
        "business": uuid4(),
        "actor": uuid4(),
        "search": uuid4(),
        "effect": uuid4(),
        "pilot": uuid4(),
        "parent_google_effect": uuid4(),
        "source_batch_mac": "a" * 64,
        "context_version": 1,
        "reserved_usd_micros": 10000,
        "request": JevChargeableRequest(
            "POST",
            "https://api.typesafe.ai/v1/systemone",
            json.dumps({"model": "jev-test", "state": {"name": "sensitive-fake-name"}}).encode(),
            "jev-test",
            SecretStr("synthetic-api-key"),
        ),
    }


def test_mac_binds_parent_batch_context_credential_request_and_budget():
    values = _values()
    first = jev_request_mac(**values)
    assert first == jev_request_mac(**values) and len(first) == 64
    for name in ("tenant", "business", "actor", "search", "effect", "pilot", "parent_google_effect"):
        assert jev_request_mac(**{**values, name: uuid4()}) != first
    for name, value in (
        ("key", SecretStr("different-synthetic-key-0123456789abcdef")),
        ("key_version", "test-key-v2"),
        ("tariff_version", "synthetic-price-v2"),
        ("credential_version", "synthetic-project-v2"),
        ("source_batch_mac", "b" * 64),
        ("context_version", 2),
        ("reserved_usd_micros", 10001),
    ):
        assert jev_request_mac(**{**values, name: value}) != first
    request = values["request"]
    assert jev_request_mac(**{**values, "request": replace(request, body=request.body + b" ")}) != first
    assert jev_request_mac(**{**values, "request": replace(request, credential=SecretStr("different"))}) != first
    assert "sensitive-fake-name" not in first and "synthetic-api-key" not in repr(request)


@pytest.mark.parametrize("key", [None, SecretStr("short")])
def test_key_must_be_explicit_and_long_enough(key):
    with pytest.raises(JevBindingError, match="JEV_BINDING_KEY_INVALID"):
        jev_request_mac(**{**_values(), "key": key})


@pytest.mark.parametrize(
    "field,value",
    [
        ("key_version", None),
        ("key_version", ""),
        ("tariff_version", None),
        ("tariff_version", "!"),
        ("credential_version", None),
        ("credential_version", "!"),
        ("tenant", "bad"),
        ("parent_google_effect", "bad"),
        ("source_batch_mac", None),
        ("source_batch_mac", "invalid"),
        ("context_version", True),
        ("context_version", 0),
        ("reserved_usd_micros", True),
        ("reserved_usd_micros", 0),
        ("reserved_usd_micros", 5_000_001),
        ("request", None),
    ],
)
def test_invalid_metadata_is_rejected(field, value):
    with pytest.raises(JevBindingError, match="JEV_BINDING_INVALID"):
        jev_request_mac(**{**_values(), field: value})


@pytest.mark.parametrize(
    "field,value",
    [
        ("method", "GET"),
        ("url", "https://untrusted.invalid/"),
        ("model", None),
        ("model", "!"),
        ("body", "not bytes"),
        ("body", b""),
        ("body", b"a" * 262145),
        ("body", b"not json"),
        ("body", b"[]"),
        ("body", b'{"model":"different"}'),
        ("credential", None),
        ("credential", SecretStr("")),
    ],
)
def test_invalid_jev_request_is_rejected(field, value):
    values = _values()
    with pytest.raises(JevBindingError, match="JEV_BINDING_INVALID"):
        jev_request_mac(**{**values, "request": replace(values["request"], **{field: value})})
