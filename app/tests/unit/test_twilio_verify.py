"""Twilio Verify contract and error handling without an external account."""

import httpx
import pytest
from pydantic import SecretStr

from app.adapters import twilio_verify
from app.adapters.twilio_verify import PhoneProviderError, TwilioVerify


def configured(settings):
    return settings.model_copy(
        update={
            "phone_verify_mode": "twilio",
            "twilio_verify_service_sid": "VA" + "a" * 32,
            "twilio_api_key": "SK" + "b" * 32,
            "twilio_api_secret": SecretStr("test-secret"),
        }
    )


def fake_transport(monkeypatch, handler):
    original = httpx.AsyncClient
    monkeypatch.setattr(
        twilio_verify.httpx,
        "AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs),
    )


async def test_twilio_start_and_check_use_form_and_basic_auth(settings, monkeypatch):
    paths = []

    def handler(request):
        paths.append((request.url.path, request.content.decode(), request.headers.get("authorization", "")))
        if request.url.path.endswith("VerificationCheck"):
            return httpx.Response(200, json={"status": "approved"})
        return httpx.Response(200, json={"status": "pending", "sid": "VE" + "a" * 32})

    fake_transport(monkeypatch, handler)
    provider = TwilioVerify(configured(settings))
    assert await provider.start("+5511999999999") == "VE" + "a" * 32
    assert await provider.check("VE" + "a" * 32, "123456")
    assert paths[0][0].endswith("/Verifications") and "Channel=sms" in paths[0][1]
    assert "To=%2B5511999999999" in paths[0][1]
    assert paths[1][0].endswith("/VerificationCheck") and "Code=123456" in paths[1][1]
    assert all(value.startswith("Basic ") for _, _, value in paths)
    await provider.close()


async def test_twilio_pending_check_and_invalid_start(settings, monkeypatch):
    fake_transport(monkeypatch, lambda _: httpx.Response(200, json={"status": "pending"}))
    provider = TwilioVerify(configured(settings))
    assert not await provider.check("VE", "0000")
    with pytest.raises(PhoneProviderError):
        await provider.start("+5511999999999")
    await provider.close()


@pytest.mark.parametrize(
    "response", [httpx.Response(503), httpx.Response(200, text="bad json"), httpx.Response(200, json=[])]
)
async def test_twilio_unusable_response_is_not_accepted(settings, monkeypatch, response):
    fake_transport(monkeypatch, lambda _: response)
    provider = TwilioVerify(configured(settings))
    with pytest.raises(PhoneProviderError):
        await provider.check("VE", "1234")
    await provider.close()


async def test_twilio_without_credentials_fails_closed(settings):
    provider = TwilioVerify(settings)
    with pytest.raises(PhoneProviderError):
        await provider.start("+5511999999999")
    await provider.close()
