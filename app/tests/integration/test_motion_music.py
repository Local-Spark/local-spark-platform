"""A1 cache, funding and RLS against a dedicated restricted PostgreSQL database."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4, uuid5

import pytest
from sqlalchemy import text

from app.services.auth import AuthError
from app.services.motion_music import MotionMusic
from app.services.motion_music_cache import MusicCache
from app.tests.integration.test_motion_production import motion_case  # noqa: F401
from app.tests.unit.test_motion_music import configured, prepared

pytestmark = pytest.mark.integration


async def begin(c):
    await c.requests.create(c.tenant, c.business, c.actor, c.body)
    c.requests.settings = configured(c.cfg)
    return await c.requests.begin(c.tenant, c.business, c.actor, c.body.operation_id, UUID(c.event.event_id))


async def test_cache_reuses_bytes_pins_selection_and_fences_unknown_effect(motion_case, seeded):  # noqa: F811
    c = motion_case
    row, token = await begin(c)
    cache = MusicCache(c.runner.effects)
    operation = uuid5(row["operation_id"], "music:0")
    assert await cache.select(row, token, operation, "cafe", 50000, restore=True) == (None, False)
    assert await cache.select(row, token, operation, "cafe", 50000, restore=False) == (None, True)
    with pytest.raises(AuthError, match="OUTCOME_UNCERTAIN"):
        await cache.select(row, token, operation, "cafe", 50000, restore=False)
    result = {"status": "ready", "data": "synthetic", "sha256": "a" * 64}
    await cache.save(row, token, operation, result)
    with pytest.raises(AuthError, match="CACHE_FENCED"):
        await cache.save(row, token, operation, result)
    assert await cache.select(row, token, operation, "cafe", 50000, restore=True) == (result, False)
    assert await cache.select(row, token, uuid4(), "cafe", 50000, restore=False) == (result, False)
    async with c.database.transaction(c.tenant, c.actor) as session:
        assert await session.scalar(text("SELECT sum(reserved_usd_micros) FROM motion_music")) == 50000
        assert (
            await session.scalar(text("SELECT count(*) FROM outbox_events WHERE event_type='motion.music_ready'")) == 2
        )
        assert await session.scalar(text("SELECT count(*) FROM audit_events WHERE action='motion.music_reserved'")) == 1
    for tenant, actor in [(seeded["t2"], seeded["a2"]), (c.tenant, seeded["a2"])]:
        async with c.database.transaction(tenant, actor) as session:
            assert await session.scalar(text("SELECT count(*) FROM motion_music")) == 0


async def test_concurrent_monthly_reservations_cannot_overspend(motion_case):  # noqa: F811
    c = motion_case
    row, token = await begin(c)
    c.requests.settings.elevenlabs_music_monthly_budget_usd_micros = 50000
    cache = MusicCache(c.runner.effects)
    results = await asyncio.gather(
        *[cache.select(row, token, uuid4(), mood, 50000, restore=False) for mood in ["cafe", "calm"]]
    )
    assert sorted(generated for _, generated in results) == [False, True]


async def test_real_audio_decode_cache_and_ledger_without_external_api(motion_case, monkeypatch, tmp_path):  # noqa: F811
    import hashlib

    from app.adapters.material_media import FetchedMedia

    c = motion_case
    c.cfg = c.cfg.model_copy(update={"motion_request_budget_usd_micros": 200000})
    c.requests.settings = c.cfg
    c.requests.context.settings = c.cfg
    row, token = await begin(c)
    provider = SimpleNamespace(generate=AsyncMock())
    service = MotionMusic(c.runner.effects, provider)
    audio = tmp_path / "tone.mp3"
    process = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-v",
        "error",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=440:duration=15.1",
        "-codec:a",
        "libmp3lame",
        str(audio),
        stderr=asyncio.subprocess.PIPE,
    )
    _, error = await process.communicate()
    assert process.returncode == 0, error
    data = audio.read_bytes()
    media = FetchedMedia(data, "audio/mpeg", hashlib.sha256(data).hexdigest())
    provider.generate.return_value = media
    output = await service.prepare(row, token, prepared("relaxante"))
    assert output.soundtrack["tracks"][0]["fade_out_ms"] == 800
    assert output.assets[0].sha256 == media.sha256
    restored = await service.prepare(row, token, prepared("relaxante"), restore=True)
    assert restored == output
    provider.generate.assert_awaited_once()
    async with c.database.transaction(c.tenant, c.actor) as session:
        held = (
            (
                await session.execute(
                    text(
                        "SELECT state,provider,reserved_usd_micros FROM visual_cost_reservations "
                        "WHERE provider='elevenlabs'"
                    )
                )
            )
            .mappings()
            .one()
        )
        assert dict(held) == {"state": "uncertain", "provider": "elevenlabs", "reserved_usd_micros": 50000}
    # Exercise the production mixer with the exact A1 plan and decode the final MP4.
    import array
    import json
    import math
    from pathlib import Path

    from app.adapters.motion_media import decode_analysis_pcm

    mixer = str(Path("app/assets/motion_html_renderer/audio.cjs").resolve())
    node = await asyncio.create_subprocess_exec(
        "node",
        "-e",
        "const m=require(process.argv[1]);console.log(JSON.stringify(m.buildAudioArgs("
        "JSON.parse(process.argv[2]),new Map([['assets/photo-music.mp3',process.argv[3]]]),15000)))",
        mixer,
        json.dumps(output.soundtrack),
        str(audio),
        stdout=asyncio.subprocess.PIPE,
    )
    raw, _ = await node.communicate()
    assert node.returncode == 0
    mix = json.loads(raw)
    video = tmp_path / "synthetic-photo-reel.mp4"
    mux = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-v",
        "error",
        "-f",
        "lavfi",
        "-i",
        "color=c=black:s=64x64:r=10:d=15",
        *mix["inputs"],
        "-filter_complex",
        mix["filter"],
        *mix["mapArgs"],
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-t",
        "15",
        str(video),
        stderr=asyncio.subprocess.PIPE,
    )
    _, error = await mux.communicate()
    assert mux.returncode == 0, error
    mp4 = video.read_bytes()
    pcm = await decode_analysis_pcm(FetchedMedia(mp4, "video/mp4", hashlib.sha256(mp4).hexdigest()))
    samples = array.array("h", pcm)
    assert 15 <= len(samples) / 16000 < 15.1

    def rms(start, end):
        values = samples[int(start * 16000) : int(end * 16000)]
        return math.sqrt(sum((v / 32768) ** 2 for v in values) / len(values))

    assert rms(1, 2) > 0.001
    assert rms(0, 0.1) < rms(1, 2) / 2
    assert rms(14.9, 15) < rms(1, 2) / 2
    assert max(abs(v) for v in samples) < 32767
