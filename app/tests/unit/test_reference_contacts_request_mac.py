import json
from dataclasses import replace
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.schemas.reference_contacts_effect import ContactsChargeableRequest
from app.services.reference_contacts_request_mac import ContactsBindingError, contacts_request_mac


def values():
    request = httpx.Request(
        "POST",
        "https://api.apify.com/v2/acts/actor-id/runs",
        params={
            "build": "1.2.3",
            "maxTotalChargeUsd": "0.00004",
            "timeout": "120",
            "memory": "1024",
            "restartOnError": "false",
            "forcePermissionLevel": "LIMITED_PERMISSIONS",
        },
        json={
            "placeIds": ["ChIJtest"],
            "scrapeContacts": True,
            "maxCrawledPlacesPerSearch": 1,
            "language": "pt-BR",
        },
    )
    return {
        "key": SecretStr("synthetic-contact-signing-key-0123456789"),
        "key_version": "key-1",
        "tariff_version": "price-1",
        "credential_version": "project-1",
        "tenant": uuid4(),
        "business": uuid4(),
        "actor": uuid4(),
        "cycle": uuid4(),
        "batch": uuid4(),
        "candidate": uuid4(),
        "place_id": "ChIJtest",
        "effect": uuid4(),
        "pilot": uuid4(),
        "context_version": 1,
        "reserved_usd_micros": 40,
        "build": "1.2.3",
        "request": ContactsChargeableRequest(
            request.method,
            str(request.url),
            request.content,
            SecretStr("synthetic-apify-key"),
            (("content-length", str(len(request.content))), ("content-type", "application/json")),
            "actor-id",
        ),
    }


def _body(request, body):
    content = json.dumps(body, separators=(",", ":")).encode()
    return replace(
        request, body=content, headers=(("content-length", str(len(content))), ("content-type", "application/json"))
    )


def test_mac_binds_source_cycle_budget_request_and_actual_credential_without_leaking():
    data = values()
    first = contacts_request_mac(**data)
    assert first == contacts_request_mac(**data) and len(first) == 64
    for field in ("tenant", "business", "actor", "cycle", "batch", "candidate", "effect", "pilot"):
        assert contacts_request_mac(**{**data, field: uuid4()}) != first
    for field, value in (
        ("key_version", "key-2"),
        ("tariff_version", "price-2"),
        ("credential_version", "project-2"),
        ("context_version", 2),
        ("reserved_usd_micros", 41),
    ):
        assert contacts_request_mac(**{**data, field: value}) != first
    request = data["request"]
    assert contacts_request_mac(**{**data, "request": replace(request, credential=SecretStr("another-key"))}) != first
    assert (
        contacts_request_mac(
            **{
                **data,
                "request": replace(
                    request,
                    provider_actor_id="actor-other",
                    url=request.url.replace("/acts/actor-id/", "/acts/actor-other/"),
                ),
            }
        )
        != first
    )
    assert (
        contacts_request_mac(
            **{
                **data,
                "build": "1.2.4",
                "request": replace(request, url=request.url.replace("build=1.2.3", "build=1.2.4")),
            }
        )
        != first
    )
    different_place = _body(
        request,
        {"placeIds": ["ChIJother"], "scrapeContacts": True, "maxCrawledPlacesPerSearch": 1, "language": "pt-BR"},
    )
    assert contacts_request_mac(**{**data, "place_id": "ChIJother", "request": different_place}) != first
    assert "ChIJtest" not in first and "synthetic-apify-key" not in first and "ChIJtest" not in repr(request)


@pytest.mark.parametrize(
    "field,value",
    [
        ("key", None),
        ("key", SecretStr("short")),
        ("key_version", ""),
        ("tariff_version", "!"),
        ("credential_version", None),
        ("tenant", "bad"),
        ("place_id", "bad\x00id"),
        ("context_version", True),
        ("context_version", 0),
        ("context_version", 9_223_372_036_854_775_808),
        ("reserved_usd_micros", True),
        ("reserved_usd_micros", 0),
        ("reserved_usd_micros", 5_000_001),
        ("build", "latest"),
        ("request", None),
    ],
)
def test_invalid_metadata_fails_closed(field, value):
    with pytest.raises(ContactsBindingError):
        contacts_request_mac(**{**values(), field: value})


@pytest.mark.parametrize(
    "field,value",
    [
        ("provider_actor_id", "bad/id"),
        ("provider_actor_id", "another-actor"),
        ("provider_actor_id", None),
        ("method", "GET"),
        ("url", "https://untrusted.invalid"),
        ("url", "x" * 4097),
        ("body", b""),
        ("body", b"x" * 65537),
        ("credential", None),
        ("credential", SecretStr("")),
        ("headers", ()),
    ],
)
def test_invalid_request_fails_closed(field, value):
    data = values()
    with pytest.raises(ContactsBindingError, match="CONTACTS_BINDING_INVALID"):
        contacts_request_mac(**{**data, "request": replace(data["request"], **{field: value})})


@pytest.mark.parametrize(
    "url_change",
    [
        lambda url: url.replace("build=1.2.3", "build=latest"),
        lambda url: url.replace("maxTotalChargeUsd=0.00004", "maxTotalChargeUsd=0.00005"),
        lambda url: url.replace("maxTotalChargeUsd=0.00004", "maxTotalChargeUsd=nan"),
        lambda url: url + "&memory=1024",
        lambda url: url + "#fragment",
    ],
)
def test_tampered_actor_parameters_fail_closed(url_change):
    data = values()
    with pytest.raises(ContactsBindingError, match="CONTACTS_BINDING_INVALID"):
        contacts_request_mac(**{**data, "request": replace(data["request"], url=url_change(data["request"].url))})


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"placeIds": ["another"], "scrapeContacts": True, "maxCrawledPlacesPerSearch": 1, "language": "pt-BR"},
        {"placeIds": ["ChIJtest"], "scrapeContacts": False, "maxCrawledPlacesPerSearch": 1, "language": "pt-BR"},
        {"placeIds": ["ChIJtest"], "scrapeContacts": True, "maxCrawledPlacesPerSearch": True, "language": "pt-BR"},
    ],
)
def test_tampered_actor_body_fails_closed(body):
    data = values()
    with pytest.raises(ContactsBindingError, match="CONTACTS_BINDING_INVALID"):
        contacts_request_mac(**{**data, "request": _body(data["request"], body)})


def test_duplicate_json_keys_fail_closed():
    data = values()
    raw = b'{"placeIds":[],"placeIds":["ChIJtest"]}'
    request = replace(
        data["request"], body=raw, headers=(("content-length", str(len(raw))), ("content-type", "application/json"))
    )
    with pytest.raises(ContactsBindingError, match="CONTACTS_BINDING_INVALID"):
        contacts_request_mac(**{**data, "request": request})


def test_place_id_technical_limit_and_opaque_characters_are_explicit():
    data = values()
    place_id = "x" * 2047 + "/"
    body = {"placeIds": [place_id], "scrapeContacts": True, "maxCrawledPlacesPerSearch": 1, "language": "pt-BR"}
    assert len(contacts_request_mac(**{**data, "place_id": place_id, "request": _body(data["request"], body)})) == 64
    for invalid in ("x" * 2049, " leading", "trailing ", "bad\x00id", "\ud800"):
        with pytest.raises(ContactsBindingError, match="CONTACTS_BINDING_INVALID"):
            contacts_request_mac(**{**data, "place_id": invalid})


@pytest.mark.parametrize("secret", ["private\ud800", "private\nvalue", "private é"])
def test_invalid_credential_never_leaks_or_binds(secret):
    data = values()
    with pytest.raises(ContactsBindingError, match="CONTACTS_BINDING_INVALID") as error:
        contacts_request_mac(**{**data, "request": replace(data["request"], credential=SecretStr(secret))})
    assert "private" not in str(error.value)


def test_invalid_signing_key_never_leaks():
    with pytest.raises(ContactsBindingError, match="CONTACTS_BINDING_KEY_INVALID") as error:
        contacts_request_mac(**{**values(), "key": SecretStr("private\ud800")})
    assert "private" not in str(error.value)
