"""Music policy and one-shot effects use synthetic bytes and fake providers only."""

import base64
import hashlib
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.adapters.material_media import FetchedMedia
from app.adapters.motion_inputs import PreparedMotionInput
from app.services import motion_music
from app.services.auth import AuthError


def configured(settings):
    return settings.model_copy(
        update={
            "elevenlabs_api_key": SecretStr("synthetic-unit-key"),
            "elevenlabs_music_execution_enabled": True,
            "elevenlabs_music_commercial_rights_confirmed": True,
            "elevenlabs_music_reservation_usd_micros": 50000,
            "elevenlabs_music_monthly_budget_usd_micros": 100000,
            "elevenlabs_music_usd_micros_per_minute": 150000,
        }
    )


def prepared(instruction="Reel cafe jazz"):
    return PreparedMotionInput(
        {"photo_motion": {"music_policy": motion_music.POLICY}, "request": {"instruction": instruction}},
        (),
        (),
        15000,
        {"mode": "silent", "tracks": []},
    )


@pytest.fixture
def case(settings, monkeypatch):
    cfg = configured(settings)
    effects = SimpleNamespace(
        requests=SimpleNamespace(settings=cfg),
        capacity=AsyncMock(return_value=True),
        reserve_submission=AsyncMock(return_value=SimpleNamespace(id=uuid4())),
        received=AsyncMock(),
        ledger=SimpleNamespace(finish=AsyncMock()),
    )
    media = FetchedMedia(b"synthetic mp3", "audio/mpeg", hashlib.sha256(b"synthetic mp3").hexdigest())
    provider = SimpleNamespace(generate=AsyncMock(return_value=media))
    service = motion_music.MotionMusic(effects, provider)
    service.cache = SimpleNamespace(select=AsyncMock(return_value=(None, True)), save=AsyncMock())
    inspect = AsyncMock(return_value=15.1)
    monkeypatch.setattr(motion_music, "inspect_supplemental_audio", inspect)
    return SimpleNamespace(
        service=service,
        effects=effects,
        provider=provider,
        media=media,
        inspect=inspect,
        row={"operation_id": uuid4(), "tenant_id": uuid4(), "actor_id": uuid4()},
        token=uuid4(),
    )


@pytest.mark.parametrize(
    "message,mood",
    [
        ("sem música", None),
        ("silêncio", None),
        ("no music", None),
        ("café jazz", "cafe"),
        ("calmo", "calm"),
        ("festa animado", "energetic"),
        ("produto", "neutral"),
    ],
)
def test_moods_are_allowlisted_and_silence_wins(message, mood):
    assert motion_music.music_mood(message) == mood


async def test_generate_mix_cache_and_restore_without_repaying(case):
    c = case
    result = await c.service.prepare(c.row, c.token, prepared())
    assert result.soundtrack["tracks"][0]["role"] == "music"
    assert result.soundtrack["tracks"][0]["trim_end_ms"] == 15000
    assert result.assets[0].data == c.media.data
    c.effects.reserve_submission.assert_awaited_once()
    c.effects.ledger.finish.assert_awaited_once()
    assert c.effects.ledger.finish.call_args.kwargs["actual_usd_micros"] is None
    payload = c.provider.generate.call_args.args[0]
    assert payload["model_id"] == "music_v2_5"
    assert c.effects.reserve_submission.call_args.args[-1] == "music_v2_5"
    assert payload["force_instrumental"] is True and payload["music_length_ms"] == 15000
    saved = c.service.cache.save.call_args.args[-1]
    c.service.cache.select.return_value = (saved, False)
    c.effects.requests.settings.elevenlabs_music_execution_enabled = False
    restored = await c.service.prepare(c.row, c.token, prepared(), restore=True)
    assert restored == result
    c.provider.generate.assert_awaited_once()


@pytest.mark.parametrize(
    "field,value",
    [
        ("elevenlabs_music_execution_enabled", False),
        ("elevenlabs_api_key", None),
        ("elevenlabs_music_commercial_rights_confirmed", False),
        ("elevenlabs_music_reservation_usd_micros", 0),
        ("elevenlabs_music_usd_micros_per_minute", 0),
        ("elevenlabs_music_usd_micros_per_minute", 1000000),
        ("elevenlabs_music_monthly_budget_usd_micros", 0),
    ],
)
async def test_disabled_credentials_rights_and_limits_never_dispatch(case, field, value):
    setattr(case.effects.requests.settings, field, value)
    result = await case.service.prepare(case.row, case.token, prepared())
    assert result.soundtrack is None
    case.service.cache.select.assert_not_awaited()
    case.provider.generate.assert_not_awaited()


async def test_silence_and_legacy_or_video_do_not_access_cache(case):
    for item in [prepared("sem trilha cafe"), replace(prepared(), context={})]:
        assert (await case.service.prepare(case.row, case.token, item)).soundtrack is None
    case.service.cache.select.assert_not_awaited()


@pytest.mark.parametrize("capacity", [False, True])
async def test_budget_shortage_stays_silent(case, capacity):
    case.effects.capacity.return_value = capacity
    if capacity:
        case.service.cache.select.return_value = (None, False)
    result = await case.service.prepare(case.row, case.token, prepared())
    assert result.soundtrack is None
    case.provider.generate.assert_not_awaited()


@pytest.mark.parametrize("failure", ["provider", "short", "corrupt", "empty", "cached_short"])
async def test_selected_audio_never_falls_back_silently(case, failure):
    if failure == "provider":
        case.provider.generate.side_effect = AuthError("PROVIDER_FAILED", 502)
    elif failure == "short":
        case.inspect.return_value = 10
    else:
        case.service.cache.select.return_value = (
            {
                "status": "ready",
                "sha256": case.media.sha256,
                "data": base64.b64encode(
                    b"" if failure == "empty" else b"wrong" if failure == "corrupt" else case.media.data
                ).decode(),
            },
            False,
        )
        if failure == "cached_short":
            case.inspect.return_value = 10
    with pytest.raises(AuthError):
        await case.service.prepare(case.row, case.token, prepared())
    if failure in {"provider", "short"}:
        case.effects.ledger.finish.assert_awaited_once()
    case.service.cache.save.assert_not_awaited()


def test_safe_defaults(settings):
    assert settings.elevenlabs_music_execution_enabled is False
    assert settings.elevenlabs_music_reservation_usd_micros == 0
    assert motion_music.MotionMusic(SimpleNamespace(requests=SimpleNamespace(settings=settings))).provider is None


@pytest.mark.parametrize("code", ["VISUAL_BUDGET_EXCEEDED", "CREATION_LAB_RUN_BUDGET_EXCEEDED", "FENCED"])
async def test_funding_rejection_never_submits_and_only_budget_errors_allow_silence(case, code):
    from app.services.visual_cost_ledger import VisualCostError

    case.effects.reserve_submission.side_effect = VisualCostError(code)
    if code == "FENCED":
        with pytest.raises(VisualCostError):
            await case.service.prepare(case.row, case.token, prepared())
    else:
        assert (await case.service.prepare(case.row, case.token, prepared())).soundtrack is None
    case.provider.generate.assert_not_awaited()


async def test_neutral_request_uses_business_facts_without_sending_customer_text(case):
    item = prepared("Mostre nossos produtos")
    item.context["confirmed_facts"] = [{"statement": "Nossa cafeteria serve café exclusivo segredo-cliente"}]
    await case.service.prepare(case.row, case.token, item)
    payload = case.provider.generate.call_args.args[0]
    assert payload["prompt"] == motion_music.MOODS["cafe"]
    assert "segredo-cliente" not in str(payload)


async def test_competing_explicit_audio_selection_cannot_be_overwritten(case):
    item = replace(prepared(), soundtrack={"mode": "mix", "tracks": [{"role": "effect"}]})
    with pytest.raises(AuthError, match="MOTION_AUDIO_SELECTION_CONFLICT"):
        await case.service.prepare(case.row, case.token, item)
    case.provider.generate.assert_not_awaited()
    case.service.cache.select.assert_not_awaited()


def test_existing_planned_sfx_preserves_the_music_branch():
    from app.services.motion_photos import music_soundtrack
    from app.services.motion_sound_library import apply_planned_sound
    from app.tests.unit.test_motion_audiovisual import natural_plan, natural_prepared

    p = natural_prepared()
    music = music_soundtrack("assets/photo-music.mp3", p.duration_ms)
    p = replace(p, soundtrack=music)
    mixed = apply_planned_sound(p, natural_plan())
    assert mixed.soundtrack["tracks"][0] == music["tracks"][0]
    assert mixed.soundtrack["tracks"][1]["role"] == "effect"
