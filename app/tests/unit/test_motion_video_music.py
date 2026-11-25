"""Video music shares elevenlabs-music-v1 gates with photo; cache-only when unpaid."""

import base64
from dataclasses import replace

import pytest

from app.services.auth import AuthError
from app.services.motion_photos import music_soundtrack
from app.tests.unit.test_motion_music import case, configured  # noqa: F401
from app.tests.unit.test_motion_video_capabilities import prepared


async def test_video_cache_hit_never_dispatches_when_unconfigured(case):  # noqa: F811
    c = case
    c.effects.requests.settings.elevenlabs_music_execution_enabled = False
    p = prepared()
    p = replace(p, context={**p.context, "request": {"instruction": "cafe jazz"}})
    result = {"status": "ready", "data": base64.b64encode(c.media.data).decode(), "sha256": c.media.sha256}
    c.service.cache.select.return_value = (result, False)
    out = await c.service.prepare(c.row, c.token, p)
    assert out.context["video_music_status"] == "existing_cache_ready"
    assert out.assets[0].id == "assets/video-music.mp3"
    assert c.service.cache.select.await_args.kwargs["existing_only"] is True
    assert c.service.cache.select.await_args.args[4] == 0
    assert await c.service.prepare(c.row, c.token, p, restore=True) == out
    c.provider.generate.assert_not_awaited()
    c.effects.reserve_submission.assert_not_awaited()
    c.inspect.return_value = 1
    with pytest.raises(AuthError, match="TOO_SHORT"):
        await c.service.prepare(c.row, c.token, p)
    result["sha256"] = "b" * 64
    with pytest.raises(AuthError, match="CACHE_CHANGED"):
        await c.service.prepare(c.row, c.token, p)


@pytest.mark.parametrize("selected", [None, {"status": "no_eligible_music"}])
async def test_empty_cache_without_credentials_stays_explicit(case, selected):  # noqa: F811
    c = case
    c.effects.requests.settings.elevenlabs_music_execution_enabled = False
    p = prepared()
    p = replace(p, context={**p.context, "request": {"instruction": "cafe"}})
    c.service.cache.select.return_value = (selected, False)
    out = await c.service.prepare(c.row, c.token, p)
    assert out.context["video_music_status"] == "music_not_configured"
    c.provider.generate.assert_not_awaited()


async def test_video_generates_with_same_gates_as_photo(case):  # noqa: F811
    c = case
    c.effects.requests.settings = configured(c.effects.requests.settings)
    p = prepared()
    p = replace(p, context={**p.context, "request": {"instruction": "cafe jazz"}, "confirmed_facts": []})
    c.service.cache.select.return_value = (None, True)
    out = await c.service.prepare(c.row, c.token, p)
    assert out.context["video_music_status"] == "ready"
    assert out.assets[0].id == "assets/video-music.mp3"
    assert out.soundtrack["tracks"][0]["role"] == "music"
    c.provider.generate.assert_awaited_once()
    c.effects.reserve_submission.assert_awaited_once()
    assert c.service.cache.select.await_args.kwargs.get("existing_only", False) is False
    assert c.service.cache.select.await_args.args[4] > 0
    payload = c.provider.generate.call_args.args[0]
    assert payload["model_id"] == "music_v2_5" and payload["force_instrumental"] is True


async def test_video_budget_shortage_is_explicit_not_forbidden(case):  # noqa: F811
    c = case
    c.effects.requests.settings = configured(c.effects.requests.settings)
    p = prepared()
    p = replace(p, context={**p.context, "request": {"instruction": "cafe"}})
    c.effects.capacity.return_value = False
    c.service.cache.select.return_value = (None, True)
    out = await c.service.prepare(c.row, c.token, p)
    assert out.context["video_music_status"] == "music_budget_unavailable"
    c.provider.generate.assert_not_awaited()
    c.service.cache.save.assert_awaited_once()


async def test_requested_silence_and_explicit_selection(case):  # noqa: F811
    c = case
    p = prepared()
    p = replace(p, context={**p.context, "request": {"instruction": "sem música"}})
    out = await c.service.prepare(c.row, c.token, p)
    assert out.context["video_music_status"] == "requested_silence"
    c.service.cache.select.assert_not_awaited()
    p = replace(p, soundtrack=music_soundtrack("assets/authorized.mp3", 6000))
    out = await c.service.prepare(c.row, c.token, p)
    assert out.context["video_audio_base"] == p.soundtrack
    c.provider.generate.assert_not_awaited()
