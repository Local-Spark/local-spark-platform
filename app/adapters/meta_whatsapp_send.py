"""Cloud API text reply adapter; the caller owns durable attempt state."""

import httpx

from app.core.config import Settings


async def send_text(settings: Settings, recipient: str, body: str, client: httpx.AsyncClient) -> str:
    response = await client.post(
        f"https://graph.facebook.com/{settings.meta_graph_version}/{settings.meta_phone_number_id}/messages",
        headers={"Authorization": f"Bearer {settings.meta_access_token.get_secret_value()}"},  # type: ignore[union-attr]
        json={"messaging_product": "whatsapp", "to": recipient, "type": "text", "text": {"body": body}},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    message_id = payload.get("messages", [{}])[0].get("id") if isinstance(payload, dict) else None
    if not isinstance(message_id, str) or not message_id:
        raise ValueError("META_MESSAGE_ID_MISSING")
    return message_id
