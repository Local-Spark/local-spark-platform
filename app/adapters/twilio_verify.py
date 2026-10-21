"""Small, bounded Twilio Verify adapter; never logs phone numbers or codes."""

import httpx

from app.core.config import Settings


class PhoneProviderError(Exception):
    pass


class TwilioVerify:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = httpx.AsyncClient(
            timeout=5.0, limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def _post(self, path: str, payload: dict[str, str]) -> dict[str, str]:
        secret = self.settings.twilio_api_secret
        if secret is None or self.settings.twilio_api_key is None:
            raise PhoneProviderError("PHONE_VERIFY_UNAVAILABLE")
        sid = self.settings.twilio_verify_service_sid
        url = f"https://verify.twilio.com/v2/Services/{sid}/{path}"
        try:
            response = await self.client.post(
                url,
                data=payload,
                auth=(self.settings.twilio_api_key, secret.get_secret_value()),
            )
            response.raise_for_status()
            result = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise PhoneProviderError("PHONE_VERIFY_UNAVAILABLE") from exc
        if not isinstance(result, dict):
            raise PhoneProviderError("PHONE_VERIFY_UNAVAILABLE")
        return result

    async def start(self, phone: str) -> str:
        result = await self._post("Verifications", {"To": phone, "Channel": self.settings.phone_verify_channel})
        if result.get("status") != "pending" or not isinstance(result.get("sid"), str):
            raise PhoneProviderError("PHONE_VERIFY_UNAVAILABLE")
        return result["sid"]

    async def check(self, sid: str, code: str) -> bool:
        result = await self._post("VerificationCheck", {"VerificationSid": sid, "Code": code})
        return result.get("status") == "approved"
