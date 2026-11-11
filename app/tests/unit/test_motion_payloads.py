"""Large multimodal evidence stays exact, private and outside SQL locks."""

import hashlib
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr

from app.adapters.material_media import MaterialError, MaterialStore
from app.services.auth import AuthError
from app.services.motion_context import MotionContext, digest
from app.services.motion_payloads import INLINE_BYTES, MAX_PAYLOAD_BYTES, MotionPayloads
from app.tests.unit.test_motion_effects import setup


def payload_case():
    row = {key: uuid4() for key in ("tenant_id", "business_id", "id")}
    context = MotionContext(SimpleNamespace(meta_encryption_key=SecretStr(Fernet.generate_key().decode())))
    objects = {}

    async def put(key, media):
        objects[key] = media.data

    async def get(key):
        return objects[key]

    store = SimpleNamespace(
        single_attempt_put=True, put=AsyncMock(side_effect=put), get_motion_payload=AsyncMock(side_effect=get)
    )
    return row, context, store, MotionPayloads(context, store)


async def test_large_payload_roundtrips_exactly_while_sql_reference_stays_small():
    row, context, store, payloads = payload_case()
    value = {"input": "synthetic-frame-data" * 100_000, "instructions": "Preserve Café Pausa"}
    prepared = payloads.prepare(row, uuid4(), value)
    assert len(prepared.ciphertext) < INLINE_BYTES
    assert prepared.data and b"synthetic-frame-data" not in prepared.data
    await payloads.upload(prepared)
    assert await payloads.open(row, prepared.ciphertext) == value
    assert context.open(prepared.ciphertext)["payload_sha256"] == digest(value)
    store.put.assert_awaited_once()


async def test_inline_and_historical_records_do_not_require_storage():
    row, context, store, payloads = payload_case()
    value = {"old": "record"}
    prepared = payloads.prepare(row, uuid4(), value)
    assert prepared.data is None
    assert await payloads.open(row, context.seal(value)) == value
    store.get_motion_payload.assert_not_awaited()


@pytest.mark.parametrize("change", ["tenant", "size", "digest", "operation", "missing"])
async def test_reference_cannot_fetch_another_tenant_or_unbounded_object(change):
    row, context, store, payloads = payload_case()
    prepared = payloads.prepare(row, uuid4(), {"frames": "x" * 100_000})
    manifest = dict(prepared.manifest)
    if change == "tenant":
        row = {**row, "tenant_id": uuid4()}
    elif change == "size":
        manifest["size_bytes"] = MAX_PAYLOAD_BYTES + 1
    elif change == "digest":
        manifest["sha256"] = "not-a-hash"
    elif change == "operation":
        manifest["operation_id"] = "../../other"
    else:
        del manifest["object_key"]
    with pytest.raises(AuthError, match="REFERENCE_INVALID"):
        await payloads.open(row, context.seal(manifest))
    store.get_motion_payload.assert_not_awaited()


async def test_corruption_and_wrong_plaintext_hash_fail_closed():
    row, context, store, payloads = payload_case()
    prepared = payloads.prepare(row, uuid4(), {"frames": "x" * 100_000})
    store.get_motion_payload.side_effect = None
    store.get_motion_payload.return_value = b"corrupt"
    with pytest.raises(AuthError, match="BYTES_CHANGED"):
        await payloads.upload(prepared)
    await payloads.store.put(prepared.manifest["object_key"], SimpleNamespace(data=prepared.data))
    store.get_motion_payload.return_value = prepared.data
    manifest = {**prepared.manifest, "payload_sha256": "0" * 64}
    with pytest.raises(AuthError, match="BYTES_CHANGED"):
        await payloads.open(row, context.seal(manifest))


async def test_non_utf8_blob_and_non_single_attempt_store_are_rejected():
    row, context, store, payloads = payload_case()
    prepared = payloads.prepare(row, uuid4(), {"frames": "x" * 100_000})
    store.single_attempt_put = False
    with pytest.raises(AuthError, match="SINGLE_ATTEMPT"):
        await payloads.upload(prepared)
    store.put.assert_not_awaited()
    store.get_motion_payload.side_effect = None
    store.get_motion_payload.return_value = b"\xff"
    manifest = {**prepared.manifest, "size_bytes": 1, "sha256": hashlib.sha256(b"\xff").hexdigest()}
    with pytest.raises(AuthError, match="REFERENCE_INVALID"):
        await payloads.open(row, context.seal(manifest))


def test_oversize_payload_is_refused_before_storage(monkeypatch):
    row, _, store, payloads = payload_case()
    monkeypatch.setattr("app.services.motion_payloads.MAX_PAYLOAD_BYTES", INLINE_BYTES)
    with pytest.raises(AuthError, match="TOO_LARGE"):
        payloads.prepare(row, uuid4(), {"frames": "x" * INLINE_BYTES})
    store.put.assert_not_awaited()


@pytest.mark.parametrize("failure", [None, "upload", "checksum", "replay"])
async def test_real_effect_flow_offloads_before_paid_dispatch_without_io_under_locks(failure):
    case = setup()
    _, context, store, payloads = payload_case()
    case.requests.context = context
    case.effects.payloads = payloads
    case.provider.build_request.return_value = {"max_output_tokens": 5, "input": "synthetic-frame" * 100_000}
    case.session.scalar.side_effect = [None, 0, None, 0, 1]
    original_put = store.put.side_effect
    original_get = store.get_motion_payload.side_effect

    async def put(key, media):
        assert not any(case.active.values())
        assert "owner_commit" in case.order
        if failure == "upload":
            raise MaterialError("MATERIAL_STORAGE_UNAVAILABLE")
        await original_put(key, media)

    async def get(key):
        assert not any(case.active.values())
        return b"wrong" if failure == "checksum" else await original_get(key)

    store.put.side_effect, store.get_motion_payload.side_effect = put, get
    if failure == "replay":
        case.session.scalar.side_effect = [1]
    if failure:
        with pytest.raises((MaterialError, AuthError)):
            await case.effects.model(case.row, case.token, case.provider, case.request)
        case.provider.submit.assert_not_awaited()
        case.effects.ledger.reserve.assert_not_awaited()
        if failure == "replay":
            store.put.assert_not_awaited()
    else:
        await case.effects.model(case.row, case.token, case.provider, case.request)
        inserts = [call.args[1] for call in case.session.execute.await_args_list if "payload" in call.args[1]]
        assert len(inserts) == 2 and all(len(item["payload"]) < INLINE_BYTES for item in inserts)
        restored = await payloads.open(case.row, inserts[-1]["payload"])
        assert restored["payload"] == case.provider.submit.await_args.args[1]
        assert digest(restored) == inserts[-1]["hash"]
        case.provider.submit.assert_awaited_once()
        case.effects.ledger.reserve.assert_awaited_once()


@pytest.mark.parametrize("failure", [None, "header", "body", "network", "bucket"])
async def test_bounded_private_storage_read_closes_stream(settings, monkeypatch, failure):
    store = MaterialStore(
        settings.model_copy(update={"material_storage_bucket": "private" if failure != "bucket" else None})
    )
    body = Mock()
    body.read.return_value = b"ciphertext" if failure != "body" else b"x" * (MAX_PAYLOAD_BYTES + 1)
    client = Mock()
    client.get_object.return_value = {
        "Body": body,
        "ContentLength": MAX_PAYLOAD_BYTES + 1 if failure == "header" else 10,
    }
    if failure == "network":
        client.get_object.side_effect = RuntimeError("unavailable")
    monkeypatch.setattr(store, "_client", lambda: client)
    if failure:
        with pytest.raises(MaterialError):
            await store.get_motion_payload("private/payload")
    else:
        assert await store.get_motion_payload("private/payload") == b"ciphertext"
        body.read.assert_called_once_with(MAX_PAYLOAD_BYTES + 1)
    if failure not in {"network", "bucket"}:
        body.close.assert_called_once()
