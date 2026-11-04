import json
from contextlib import asynccontextmanager
from dataclasses import replace
from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.adapters.jev_reference_post_analysis import PostAnalysisResult
from app.adapters.jev_reference_similarity import JevChargeableRequest
from app.services.reference_post_analysis_guard import (
    DatabasePostAnalysisGuard,
    PostGuardContext,
    PostGuardError,
    load_post_analysis,
    post_request_mac,
    post_sample_mac,
)


def context():
    return PostGuardContext(
        tenant=uuid4(),
        business=uuid4(),
        actor=uuid4(),
        window=uuid4(),
        reference=uuid4(),
        association_version=1,
        parent_feed_effect=uuid4(),
        parent_feed_token=uuid4(),
        effect=uuid4(),
        sample_mac="a" * 64,
        pilot=uuid4(),
        key=SecretStr("fake-key-with-at-least-32-characters"),
        key_version="v1",
        tariff_version="tariff-v1",
        credential_version="credential-v1",
        reserved_usd_micros=3000,
        caption_mac="b" * 64,
    )


def request():
    return JevChargeableRequest(
        "POST",
        "https://api.typesafe.ai/v1/systemone",
        b'{"model":"jev-test","state":{"caption":"private fixture"}}',
        "jev-test",
        SecretStr("fake-api-key"),
    )


class Database:
    def __init__(self, result):
        self.result, self.calls = result, []

    @asynccontextmanager
    async def transaction(self, tenant, actor):
        self.calls.append((tenant, actor))
        yield self

    async def scalar(self, statement, params):
        self.calls.append((str(statement), params))
        return self.result

    async def execute(self, statement, params):
        self.calls.append((str(statement), params))


def test_sample_is_stable_private_and_distinguishes_window_post_image():
    c = context()
    one = post_sample_mac(c.key, c.window, "post-1", None)
    assert one == post_sample_mac(c.key, c.window, "post-1", None) and len(one) == 64
    assert (
        len(
            {
                one,
                post_sample_mac(c.key, c.window, "post-2", None),
                post_sample_mac(c.key, c.window, "post-1", 0),
                post_sample_mac(c.key, uuid4(), "post-1", None),
            }
        )
        == 4
    )


@pytest.mark.parametrize(
    ("key", "window", "post", "index"),
    [
        (None, uuid4(), "post", None),
        (SecretStr("short"), uuid4(), "post", None),
        (SecretStr("x" * 32), "wrong", "post", None),
        (SecretStr("x" * 32), uuid4(), None, None),
        (SecretStr("x" * 32), uuid4(), "https://private", None),
        (SecretStr("x" * 32), uuid4(), "post", True),
        (SecretStr("x" * 32), uuid4(), "post", -1),
    ],
)
def test_sample_invalid_input(key, window, post, index):
    with pytest.raises(PostGuardError, match="IDENTITY_INVALID"):
        post_sample_mac(key, window, post, index)


def test_mac_binds_all_context_request_bytes_and_credentials():
    c, r = context(), request()
    first = post_request_mac(c, r)
    assert first == post_request_mac(c, r) and len(first) == 64
    for field in (
        "tenant",
        "business",
        "actor",
        "window",
        "reference",
        "parent_feed_effect",
        "parent_feed_token",
        "effect",
        "pilot",
    ):
        assert post_request_mac(replace(c, **{field: uuid4()}), r) != first
    for field, value in [
        ("key", SecretStr("another-key-with-at-least-32-characters")),
        ("key_version", "v2"),
        ("tariff_version", "other"),
        ("credential_version", "other"),
        ("association_version", 2),
        ("reserved_usd_micros", 2999),
        ("sample_mac", "b" * 64),
    ]:
        assert post_request_mac(replace(c, **{field: value}), r) != first
    assert post_request_mac(c, replace(r, body=r.body + b" ")) != first
    assert post_request_mac(c, replace(r, credential=SecretStr("another"))) != first
    assert "private fixture" not in repr(c) + repr(r) + first


@pytest.mark.parametrize("key", [None, SecretStr("short")])
def test_invalid_signing_key(key):
    with pytest.raises(PostGuardError, match="KEY_INVALID"):
        post_request_mac(replace(context(), key=key), request())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("actor", None),
        ("key_version", None),
        ("tariff_version", "!"),
        ("credential_version", ""),
        ("association_version", True),
        ("association_version", 0),
        ("reserved_usd_micros", True),
        ("reserved_usd_micros", 0),
        ("reserved_usd_micros", 5000001),
        ("sample_mac", None),
        ("sample_mac", "bad"),
        ("caption_mac", "bad"),
    ],
)
def test_invalid_metadata(field, value):
    with pytest.raises(PostGuardError, match="BINDING_INVALID"):
        post_request_mac(replace(context(), **{field: value}), request())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("method", "GET"),
        ("url", "https://example.invalid"),
        ("model", None),
        ("model", "!"),
        ("body", "text"),
        ("body", b""),
        ("body", b"x" * (16 * 1024 * 1024 + 1)),
        ("body", b"not json"),
        ("body", b"\xff"),
        ("body", b"[]"),
        ("body", b'{"model":"another"}'),
        ("credential", None),
        ("credential", SecretStr("")),
    ],
)
def test_invalid_request(field, value):
    with pytest.raises(PostGuardError, match="BINDING_INVALID"):
        post_request_mac(context(), replace(request(), **{field: value}))


def test_missing_request():
    with pytest.raises(PostGuardError, match="BINDING_INVALID"):
        post_request_mac(context(), None)


async def test_guard_transaction_precedes_effect_and_repeat_is_refused():
    c, token = context(), uuid4()
    db = Database({"created": True, "executor_token": str(token)})
    guard = DatabasePostAnalysisGuard(db, c)
    assert await guard.claim(uuid4(), request()) is False
    with pytest.raises(PostGuardError, match="EXECUTOR_REQUIRED"):
        await guard.uncertain()
    assert await guard.claim(c.effect, request()) is True
    assert guard.execution_token() == token
    assert await guard.claim(c.effect, request()) is False
    assert db.calls[0] == (c.tenant, c.actor)
    _, params = db.calls[1]
    assert params["mac"] == post_request_mac(c, request()) and params["parent_token"] == c.parent_feed_token
    assert "private fixture" not in json.dumps(params, default=str)
    await guard.uncertain()
    assert db.calls[-1][1] == {"business": c.business, "effect": c.effect, "token": token}
    result = PostAnalysisResult((("tone", "friendly"),), "reference-patterns-v1", "jev-test", 100, 0)
    await guard.record(result)
    assert json.loads(db.calls[-1][1]["choices"]) == {"tone": "friendly"}
    assert db.calls[-1][1]["token"] == token


async def test_guard_does_not_adopt_existing_executor_token():
    c = context()
    guard = DatabasePostAnalysisGuard(Database({"created": False, "executor_token": str(uuid4())}), c)
    assert await guard.claim(c.effect, request()) is False
    with pytest.raises(PostGuardError, match="EXECUTOR_REQUIRED"):
        guard.execution_token()


async def test_read_result_returns_only_codes_and_own_metadata():
    c = context()
    db = Database(None)
    assert await load_post_analysis(db, c.tenant, c.actor, c.business, c.window, c.sample_mac) is None
    db.result = {
        "choices": {"tone": "friendly"},
        "vocabulary_version": "reference-patterns-v1",
        "provider_model": "jev-test",
        "input_tokens": 100,
        "output_tokens": 0,
    }
    result = await load_post_analysis(db, c.tenant, c.actor, c.business, c.window, c.sample_mac)
    assert result.choices == (("tone", "friendly"),)
    assert result.input_tokens == 100 and result.vocabulary_version == "reference-patterns-v1"


@pytest.mark.parametrize("actual", [None, 0, 7])
async def test_feed_receipt_passes_exact_effect_and_absent_cost_remains_absent(actual):
    from app.services.reference_post_analysis_guard import record_feed_terminal_cost

    c, db = context(), Database(None)
    await record_feed_terminal_cost(
        db, c.tenant, c.actor, c.business, c.parent_feed_effect, c.parent_feed_token, actual
    )
    assert db.calls[0] == (c.tenant, c.actor)
    assert db.calls[1][1] == {
        "business": c.business,
        "effect": c.parent_feed_effect,
        "token": c.parent_feed_token,
        "actual": actual,
    }


def test_caption_anchor_matches_body_and_is_bound():
    c, r = context(), request()
    assert post_request_mac(c, r) != post_request_mac(replace(c, caption_mac="c" * 64), r)
    with pytest.raises(PostGuardError, match="BINDING_INVALID"):
        post_request_mac(replace(c, caption_mac=None), r)
    without = replace(r, body=b'{"model":"jev-test","state":{"caption":null}}')
    assert post_request_mac(replace(c, caption_mac=None), without)
    with pytest.raises(PostGuardError, match="BINDING_INVALID"):
        post_request_mac(c, without)
    with pytest.raises(PostGuardError, match="BINDING_INVALID"):
        post_request_mac(c, replace(r, body=b'{"model":"jev-test"}'))


async def test_sample_metadata_allows_recovery_without_replaying_uncertain_caption():
    from app.services.reference_post_analysis_guard import caption_claimed, load_post_sample

    c, db = context(), Database(None)
    assert await load_post_sample(db, c.tenant, c.actor, c.business, c.window, c.sample_mac) is None
    assert await caption_claimed(db, c.tenant, c.actor, c.business, c.window, c.caption_mac) is False
    db.result = True
    assert await caption_claimed(db, c.tenant, c.actor, c.business, c.window, c.caption_mac) is True
    db.result = {"state": "uncertain", "includes_caption": True, "result": None}
    sample = await load_post_sample(db, c.tenant, c.actor, c.business, c.window, c.sample_mac)
    assert sample.state == "uncertain" and sample.includes_caption and sample.result is None
    db.result = {
        "state": "completed",
        "includes_caption": False,
        "result": {
            "choices": {"format": "photo"},
            "vocabulary_version": "reference-patterns-v1",
            "provider_model": "jev-test",
            "input_tokens": 10,
            "output_tokens": 0,
        },
    }
    sample = await load_post_sample(db, c.tenant, c.actor, c.business, c.window, c.sample_mac)
    assert not sample.includes_caption and sample.result.choices == (("format", "photo"),)


async def test_caption_reader_recovers_editorial_result_even_when_image_disappeared():
    from app.services.reference_post_analysis_guard import load_caption_sample

    c, db = context(), Database(None)
    assert await load_caption_sample(db, c.tenant, c.actor, c.business, c.window, c.caption_mac) is None
    db.result = {"state": "uncertain", "includes_caption": True, "result": None}
    result = await load_caption_sample(db, c.tenant, c.actor, c.business, c.window, c.caption_mac)
    assert result.state == "uncertain" and result.result is None
    db.result = {
        "state": "completed",
        "includes_caption": True,
        "result": {
            "choices": {"tone": "friendly"},
            "vocabulary_version": "reference-patterns-v1",
            "provider_model": "jev-test",
            "input_tokens": 10,
            "output_tokens": 0,
        },
    }
    result = await load_caption_sample(db, c.tenant, c.actor, c.business, c.window, c.caption_mac)
    assert result.result.choices == (("tone", "friendly"),) and result.includes_caption
