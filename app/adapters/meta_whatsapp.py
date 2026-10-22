"""Verify Meta's raw webhook bytes and normalize only supported subevents."""

import hashlib
import hmac
import json
from typing import Any

from app.core.config import Settings


class MetaWebhookError(Exception):
    def __init__(self, code: str, status: int = 400) -> None:
        self.code, self.status = code, status


def verify_challenge(settings: Settings, mode: str | None, token: str | None, challenge: str | None) -> str:
    if settings.meta_webhook_mode != "cloud":
        raise MetaWebhookError("WHATSAPP_UNAVAILABLE", 503)
    expected = settings.meta_verify_token.get_secret_value()  # type: ignore[union-attr]
    if mode != "subscribe" or token is None or challenge is None or not hmac.compare_digest(token, expected):
        raise MetaWebhookError("INVALID_WEBHOOK_CHALLENGE", 403)
    return challenge


def verify_signature(settings: Settings, body: bytes, signature: str | None) -> None:
    if settings.meta_webhook_mode != "cloud":
        raise MetaWebhookError("WHATSAPP_UNAVAILABLE", 503)
    if len(body) > 262144:
        raise MetaWebhookError("WEBHOOK_TOO_LARGE", 413)
    expected = (
        "sha256="
        + hmac.new(
            settings.meta_app_secret.get_secret_value().encode(),  # type: ignore[union-attr]
            body,
            hashlib.sha256,
        ).hexdigest()
    )
    if signature is None or not hmac.compare_digest(signature, expected):
        raise MetaWebhookError("INVALID_WEBHOOK_SIGNATURE", 403)


def extract_events(settings: Settings, body: bytes) -> list[tuple[str, str, dict[str, Any]]]:
    try:
        envelope = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MetaWebhookError("INVALID_WEBHOOK_PAYLOAD") from exc
    if not isinstance(envelope, dict) or envelope.get("object") != "whatsapp_business_account":
        raise MetaWebhookError("INVALID_WEBHOOK_PAYLOAD")
    entries = envelope.get("entry")
    if not isinstance(entries, list):
        raise MetaWebhookError("INVALID_WEBHOOK_PAYLOAD")
    events: list[tuple[str, str, dict[str, Any]]] = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("id") != settings.meta_waba_id:
            continue
        changes = entry.get("changes")
        if not isinstance(changes, list):
            continue
        for change in changes:
            if not isinstance(change, dict) or change.get("field") != "messages":
                continue
            value = change.get("value")
            if not isinstance(value, dict) or not isinstance(value.get("metadata"), dict):
                continue
            if value["metadata"].get("phone_number_id") != settings.meta_phone_number_id:
                continue
            for kind, plural in (("message", "messages"), ("status", "statuses")):
                items = value.get(plural, [])
                if not isinstance(items, list):
                    continue
                for item in items:
                    if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
                        continue
                    # Status transitions share a message ID; the state/time identify each callback.
                    identity = [settings.meta_waba_id, settings.meta_phone_number_id, kind, item["id"]]
                    if kind == "status":
                        identity.extend((str(item.get("status", "")), str(item.get("timestamp", ""))))
                    key = hashlib.sha256(json.dumps(identity, separators=(",", ":")).encode()).hexdigest()
                    events.append((key, kind, item))
    return events
