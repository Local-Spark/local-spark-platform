"""Webhook boundary tests use synthetic payloads, never customer content."""

import hashlib
import hmac
import json
from unittest.mock import AsyncMock

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from app.adapters.meta_whatsapp import MetaWebhookError, extract_events, verify_challenge, verify_signature
from app.main import create_app
from app.services.whatsapp_ingest import save_events


@pytest.fixture
def meta_settings(settings):
    return settings.model_copy(
        update={
            "meta_webhook_mode": "cloud",
            "meta_database_url": SecretStr("postgresql+asyncpg://unit:unit@localhost/unit"),
            "meta_verify_token": SecretStr("challenge-secret"),
            "meta_app_secret": SecretStr("app-secret"),
            "meta_waba_id": "waba-1",
            "meta_phone_number_id": "phone-1",
            "meta_encryption_key": SecretStr(Fernet.generate_key().decode()),
        }
    )


def signed(body: bytes) -> str:
    return "sha256=" + hmac.new(b"app-secret", body, hashlib.sha256).hexdigest()


def payload(*, entry=None):
    return {
        "object": "whatsapp_business_account",
        "entry": [
            entry
            or {
                "id": "waba-1",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "metadata": {"phone_number_id": "phone-1"},
                            "messages": [
                                {"id": "wamid-1", "from": "5511999999999", "type": "text", "text": {"body": "Olá"}}
                            ],
                            "statuses": [{"id": "wamid-out", "status": "delivered", "timestamp": "123"}],
                        },
                    }
                ],
            }
        ],
    }


def test_challenge_and_signature_are_fail_closed(settings, meta_settings):
    with pytest.raises(MetaWebhookError) as error:
        verify_challenge(settings, "subscribe", "x", "ok")
    assert error.value.status == 503
    assert verify_challenge(meta_settings, "subscribe", "challenge-secret", "abc") == "abc"
    for mode, token, challenge in (
        ("other", "challenge-secret", "abc"),
        ("subscribe", None, "abc"),
        ("subscribe", "wrong", "abc"),
        ("subscribe", "challenge-secret", None),
    ):
        with pytest.raises(MetaWebhookError) as error:
            verify_challenge(meta_settings, mode, token, challenge)
        assert error.value.status == 403
    body = json.dumps(payload()).encode()
    verify_signature(meta_settings, body, signed(body))
    for config, raw, header, status in (
        (settings, body, signed(body), 503),
        (meta_settings, b"x" * 262145, signed(body), 413),
        (meta_settings, body, None, 403),
        (meta_settings, body, "sha256=wrong", 403),
    ):
        with pytest.raises(MetaWebhookError) as error:
            verify_signature(config, raw, header)
        assert error.value.status == status


@pytest.mark.parametrize(
    "changes",
    [
        {"meta_app_secret": None},
        {"meta_database_url": None},
        {"meta_encryption_key": "invalid"},
    ],
)
def test_active_webhook_requires_valid_configuration(settings, meta_settings, changes):
    with pytest.raises(ValidationError):
        type(settings)(_env_file=None, **{**settings.model_dump(), **meta_settings.model_dump(), **changes})


def test_extract_messages_status_transitions_and_ignore_foreign_or_unsupported(meta_settings):
    raw = json.dumps(payload()).encode()
    events = extract_events(meta_settings, raw)
    assert len(events) == 2
    assert [kind for _, kind, _ in events] == ["message", "status"]
    assert events == extract_events(meta_settings, raw)
    second = payload()
    second["entry"][0]["changes"][0]["value"]["statuses"][0]["status"] = "read"
    assert extract_events(meta_settings, json.dumps(second).encode())[1][0] != events[1][0]
    assert extract_events(meta_settings, json.dumps(payload(entry={"id": "other"})).encode()) == []
    assert (
        extract_events(
            meta_settings,
            json.dumps(
                payload(
                    entry={
                        "id": "waba-1",
                        "changes": [
                            {"field": "other"},
                            {"field": "messages", "value": {"metadata": {"phone_number_id": "other"}}},
                        ],
                    }
                )
            ).encode(),
        )
        == []
    )


@pytest.mark.parametrize(
    "raw",
    [
        b"{",
        b"[]",
        b"{}",
        b'{"object":"whatsapp_business_account"}',
        b'{"object":"whatsapp_business_account","entry":{}}',
    ],
)
def test_invalid_envelopes_are_rejected(meta_settings, raw):
    with pytest.raises(MetaWebhookError) as error:
        extract_events(meta_settings, raw)
    assert error.value.code == "INVALID_WEBHOOK_PAYLOAD"


def test_malformed_subevents_are_skipped_without_crashing(meta_settings):
    envelope = payload(
        entry={
            "id": "waba-1",
            "changes": [
                None,
                {"field": "messages", "value": None},
                {"field": "messages", "value": {"metadata": {}, "messages": []}},
                {
                    "field": "messages",
                    "value": {
                        "metadata": {"phone_number_id": "phone-1"},
                        "messages": [None, {}, {"id": ""}],
                        "statuses": {},
                    },
                },
            ],
        }
    )
    assert extract_events(meta_settings, json.dumps(envelope).encode()) == []
    envelope["entry"].extend([None, {"id": "waba-1", "changes": None}])
    assert extract_events(meta_settings, json.dumps(envelope).encode()) == []


def test_route_handshake_signature_and_durable_call(settings, meta_settings, fake_database, monkeypatch):
    save = AsyncMock()
    monkeypatch.setattr("app.api.v1.whatsapp.save_events", save)
    raw = json.dumps(payload()).encode()
    with TestClient(create_app(settings, fake_database, fake_database)) as client:
        assert client.get("/api/v1/webhooks/whatsapp").status_code == 503
        assert client.post("/api/v1/webhooks/whatsapp", content=raw).status_code == 503
    with TestClient(create_app(meta_settings, fake_database, fake_database, meta_database=fake_database)) as client:
        endpoint = "/api/v1/webhooks/whatsapp"
        params = {"hub.mode": "subscribe", "hub.verify_token": "challenge-secret", "hub.challenge": "1234"}
        assert client.get(endpoint, params=params).text == "1234"
        assert client.get(endpoint, params={**params, "hub.verify_token": "wrong"}).status_code == 403
        assert client.post(endpoint, content=raw).status_code == 403
        assert client.post(endpoint, content=raw, headers={"x-hub-signature-256": signed(raw)}).json() == {
            "status": "accepted"
        }
        assert (
            client.post(endpoint, content=b"x" * 262145, headers={"x-hub-signature-256": signed(raw)}).status_code
            == 413
        )
        assert client.post(endpoint, content=b"{", headers={"x-hub-signature-256": signed(b"{")}).status_code == 400
    assert save.await_count == 1


def test_route_has_no_storage_without_configured_database(meta_settings, fake_database):
    raw = json.dumps(payload()).encode()
    with TestClient(create_app(meta_settings, fake_database, fake_database, meta_database=fake_database)) as client:
        client.app.state.meta_database = None
        response = client.post("/api/v1/webhooks/whatsapp", content=raw, headers={"x-hub-signature-256": signed(raw)})
    assert response.status_code == 503


def test_storage_failure_does_not_acknowledge_callback(meta_settings, fake_database, monkeypatch):
    private_text = "synthetic private payload must not leak"
    monkeypatch.setattr("app.api.v1.whatsapp.save_events", AsyncMock(side_effect=RuntimeError(private_text)))
    raw = json.dumps(payload()).encode()
    app = create_app(meta_settings, fake_database, fake_database, meta_database=fake_database)
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/api/v1/webhooks/whatsapp", content=raw, headers={"x-hub-signature-256": signed(raw)})
    assert response.status_code == 500
    assert private_text not in response.text


@pytest.mark.asyncio
async def test_empty_event_batch_does_not_open_a_transaction(meta_settings, fake_database):
    await save_events(fake_database, meta_settings, [])
    fake_database.sessions.assert_not_called()


def test_app_owns_and_closes_configured_meta_database(meta_settings, fake_database, monkeypatch):
    monkeypatch.setattr("app.main.Database", lambda *args, **kwargs: fake_database)
    with TestClient(create_app(meta_settings, fake_database, fake_database)) as client:
        assert client.get("/health/ready").status_code == 200
    fake_database.close.assert_awaited_once()
