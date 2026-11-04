"""The feed commitment authenticates the exact transient, synthetic request."""

import json
from dataclasses import replace
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.adapters.apify_instagram_feed import ApifyInstagramFeed
from app.services.reference_feed_request_mac import FeedBindingError, _actor_limit, feed_request_mac


def example():
    token = SecretStr("synthetic-credential")
    request = ApifyInstagramFeed._request(
        "POST",
        "https://api.apify.com/v2/acts/apify~instagram-scraper/runs",
        token,
        params={
            "build": "1.2.3",
            "maxTotalChargeUsd": "0.05",
            "maxItems": "20",
            "timeout": "120",
            "memory": "1024",
            "restartOnError": "false",
            "forcePermissionLevel": "LIMITED_PERMISSIONS",
        },
        body={
            "directUrls": ["https://www.instagram.com/synthetic_profile/"],
            "resultsType": "posts",
            "resultsLimit": 20,
        },
    )
    return {
        "key": SecretStr("a" * 32),
        "key_version": "key-1",
        "tariff_version": "tariff-1",
        "credential_version": "credential-1",
        "tenant": uuid4(),
        "business": uuid4(),
        "actor": uuid4(),
        "reference": uuid4(),
        "association_version": 1,
        "analysis_window": uuid4(),
        "search": uuid4(),
        "selection": uuid4(),
        "effect": uuid4(),
        "pilot": uuid4(),
        "reserved_usd_micros": 50_000,
        "profile": "synthetic_profile",
        "build": "1.2.3",
        "request": ApifyInstagramFeed._bind(request, token),
    }


def bound(values):
    return feed_request_mac(**values)


def with_query(request, **changes):
    url = httpx.URL(request.url)
    return replace(request, url=str(url.copy_with(params=url.params.merge(changes))))


def with_body(request, **changes):
    payload = json.loads(request.body)
    payload.update(changes)
    return exact_body(request, json.dumps(payload).encode())


def exact_body(request, body):
    return replace(
        request, body=body, headers=(("content-length", str(len(body))), ("content-type", "application/json"))
    )


def test_exact_commitment_is_deterministic_and_private():
    values = example()
    first = bound(values)
    assert len(first) == 64 and first == bound(values)
    assert "synthetic_profile" not in first and "synthetic-credential" not in first
    for name in (
        "tenant",
        "business",
        "actor",
        "reference",
        "analysis_window",
        "search",
        "selection",
        "effect",
        "pilot",
    ):
        assert bound({**values, name: uuid4()}) != first
    for name in ("key_version", "tariff_version", "credential_version"):
        assert bound({**values, name: "another-v1"}) != first
    assert bound({**values, "association_version": 2}) != first
    assert bound({**values, "reserved_usd_micros": 50_001}) != first
    assert bound({**values, "search": None}) != first
    assert bound({**values, "selection": None}) != first
    assert bound({**values, "key": SecretStr("b" * 32)}) != first
    request = values["request"]
    assert bound({**values, "request": replace(request, credential=SecretStr("rotated"))}) != first
    assert bound({**values, "request": exact_body(request, request.body + b" ")}) != first
    assert bound({**values, "request": with_query(request, maxTotalChargeUsd="0.049999")}) != first
    assert bound({**values, "request": with_query(request, build="1.2.4"), "build": "1.2.4"}) != first
    assert (
        bound(
            {
                **values,
                "request": with_body(request, directUrls=["https://www.instagram.com/another/"]),
                "profile": "another",
            }
        )
        != first
    )


@pytest.mark.parametrize("key", [None, "a" * 32, SecretStr("short")])
def test_bad_signing_key_fails_closed(key):
    with pytest.raises(FeedBindingError, match="FEED_BINDING_KEY_INVALID"):
        bound({**example(), "key": key})


@pytest.mark.parametrize(
    "field,value",
    [
        ("key_version", None),
        ("tariff_version", "bad space"),
        ("credential_version", ""),
        ("tenant", "tenant"),
        ("business", None),
        ("actor", 1),
        ("reference", "ref"),
        ("analysis_window", "window"),
        ("effect", False),
        ("pilot", "pilot"),
        ("search", "search"),
        ("selection", "selection"),
        ("association_version", True),
        ("association_version", 0),
        ("reserved_usd_micros", True),
        ("reserved_usd_micros", 0),
        ("reserved_usd_micros", 5_000_001),
        ("profile", None),
        ("profile", "@Not-Normalized"),
        ("profile", "Valid_Name"),
        ("profile", ""),
        ("build", None),
        ("build", "x" * 65),
        ("build", "latest"),
    ],
)
def test_invalid_scope_is_rejected(field, value):
    with pytest.raises(FeedBindingError, match="FEED_BINDING_INVALID"):
        bound({**example(), field: value})


@pytest.mark.parametrize("value", ["", "-1", "1e-6", "0.0000001", "+1", "00.1"])
def test_bad_actor_dollar_value_fails(value):
    with pytest.raises(FeedBindingError, match="FEED_BINDING_INVALID"):
        _actor_limit(value)


def test_actor_dollars_are_exact_integer_micros():
    assert _actor_limit("5") == 5_000_000
    assert _actor_limit("0.000001") == 1


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: None,
        lambda r: replace(r, method="GET"),
        lambda r: replace(r, url=None),
        lambda r: replace(r, url="x" * 4097),
        lambda r: replace(r, body=None),
        lambda r: replace(r, body=b""),
        lambda r: replace(r, body=b"x" * 65_537),
        lambda r: replace(r, credential="bad"),
        lambda r: replace(r, credential=SecretStr("")),
        lambda r: replace(r, headers=()),
        lambda r: replace(r, headers=(("content-length", "1"), ("content-type", "application/json"))),
        lambda r: replace(r, headers=(("content-length", str(len(r.body))), ("content-type", "text/plain"))),
        lambda r: replace(r, headers=((*r.headers, ("authorization", "Bearer synthetic-credential")))),
        lambda r: replace(r, url=r.url.replace("api.apify.com", "attacker.test")),
        lambda r: replace(r, url=r.url + "#fragment"),
        lambda r: replace(r, url=r.url.replace("https://", "https://user@")),
        lambda r: replace(r, url=r.url + "&build=1.2.3"),
        lambda r: replace(r, url=r.url + "&extra=1"),
        lambda r: with_query(r, build="1.2.4"),
        lambda r: with_query(r, timeout="121"),
        lambda r: with_query(r, memory="2048"),
        lambda r: with_query(r, restartOnError="true"),
        lambda r: with_query(r, forcePermissionLevel="FULL"),
        lambda r: with_query(r, maxItems="21"),
        lambda r: with_query(r, maxTotalChargeUsd="0"),
        lambda r: with_query(r, maxTotalChargeUsd="0.050001"),
        lambda r: with_query(r, maxTotalChargeUsd="1e-2"),
        lambda r: exact_body(r, b"\xff"),
        lambda r: exact_body(r, b"[]"),
        lambda r: exact_body(r, b'{"x":1,"x":2}'),
        lambda r: with_body(r, extra="synthetic"),
        lambda r: with_body(r, directUrls=["https://www.instagram.com/other/"]),
        lambda r: with_body(r, resultsType="profile"),
        lambda r: with_body(r, resultsLimit=True),
        lambda r: with_body(r, resultsLimit=19),
        lambda r: with_body(r, skipPinnedPosts=False),
    ],
)
def test_invalid_request_never_creates_binding_or_exposes_inputs(mutation):
    values = example()
    request = mutation(values["request"])
    with pytest.raises(FeedBindingError, match="FEED_BINDING_INVALID") as error:
        bound({**values, "request": request})
    assert "synthetic_profile" not in str(error.value)
    assert "synthetic-credential" not in str(error.value)
