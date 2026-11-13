"""Deterministic, bounded audio measurements; semantic suitability still requires listening."""

import hashlib
import math
import sys
from array import array
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from app.adapters.material_media import FetchedMedia
from app.adapters.motion_media import decode_analysis_pcm
from app.services.auth import AuthError

if TYPE_CHECKING:
    from app.adapters.motion_inputs import PreparedMotionInput

ANALYSIS_CONTRACT = {
    "version": "motion-sound-analysis-v1",
    "scope": "Decoded mono 16 kHz PCM measurements, not listening or loudness normalization.",
    "rules": (
        "audio_assessment registra duração decodificada, RMS/pico de amostra e intervalos de energia. "
        "Intervalos são candidatos técnicos de trecho; não identificam o significado do som nem seu sincronismo. "
        "Não confunda RMS com LUFS ou pico de amostra com true peak. Não alegue escuta, ausência de duplicação "
        "semântica ou inteligibilidade da mistura. Observe avaliações humanas explicitamente identificadas "
        "quando presentes, sem inventar aprovação. Escolha eventos apenas para ações justificadas no plano."
    ),
}


def pcm_measurements(pcm: bytes) -> dict[str, Any]:
    if not pcm or len(pcm) % 2 or len(pcm) > 60 * 16000 * 2:
        raise AuthError("MOTION_AUDIO_ANALYSIS_PCM_INVALID", 409)
    samples = array("h")
    samples.frombytes(pcm)
    if sys.byteorder != "little":
        samples.byteswap()
    peak = max(abs(s) for s in samples)
    squares = sum(s * s for s in samples)
    window_size = 160  # 10 ms, including a possible final partial window.
    rms_windows = [
        math.sqrt(sum(s * s for s in samples[i : i + window_size]) / len(samples[i : i + window_size]))
        for i in range(0, len(samples), window_size)
    ]
    maximum = max(rms_windows)
    threshold = max(32768 * 10 ** (-50 / 20), maximum * 10 ** (-30 / 20))
    active = [i for i, rms in enumerate(rms_windows) if rms >= threshold]
    intervals: list[list[int]] = []
    duration_ms = (len(samples) * 1000 + 15999) // 16000
    for i in active:
        start, end = i * 10, min((i + 1) * 10, duration_ms)
        if intervals and start - intervals[-1][1] <= 100:
            intervals[-1][1] = end
        else:
            intervals.append([start, end])

    def db(value: float) -> float | None:
        return round(20 * math.log10(value / 32768), 3) if value else None

    return {
        "decoded_duration_ms": duration_ms,
        "pcm_sha256": hashlib.sha256(pcm).hexdigest(),
        "rms_dbfs": db(math.sqrt(squares / len(samples))),
        "sample_peak_dbfs": db(peak),
        "peak_at_ms": next(i for i, s in enumerate(samples) if abs(s) == peak) * 1000 // 16000,
        "samples_at_full_scale": sum(abs(s) >= 32767 for s in samples),
        "activity_threshold_dbfs": db(threshold),
        "active_intervals_ms": intervals[:16],
        "omitted_active_intervals": max(0, len(intervals) - 16),
        "listening_status": "not_listened",
        "suitability": "requires_listening",
        "source_duplication": "requires_listening",
        "voice_intelligibility": "requires_listening",
    }


async def prepare_sound_assessment(prepared: "PreparedMotionInput") -> "PreparedMotionInput":
    contract = prepared.context.get("audio_analysis_contract")
    if contract is None:
        return prepared
    if contract != ANALYSIS_CONTRACT:
        raise AuthError("MOTION_AUDIO_ANALYSIS_CONTRACT_CHANGED", 409)
    source = prepared.context["source"]
    expected = {
        f"assets/sfx-{item['id']}.mp3": item["sha256"]
        for item in prepared.context.get("sound_library", {}).get("items", [])
    }
    if source["has_audio"]:
        expected[source["asset_id"]] = source["sha256"]
    selected = [a for a in prepared.assets if a.id in expected]
    assets = {a.id: a for a in selected}
    if set(assets) != set(expected):
        raise AuthError("MOTION_AUDIO_ANALYSIS_ASSET_MISSING", 409)
    if len(selected) != len(assets) or any(a.sha256 != expected[a.id] for a in selected):
        raise AuthError("MOTION_AUDIO_ANALYSIS_ASSET_CHANGED", 409)
    measurements = []
    for identifier in sorted(assets):
        asset = assets[identifier]
        pcm = await decode_analysis_pcm(FetchedMedia(asset.data, asset.mime_type, asset.sha256))
        measurements.append({"asset_id": identifier, "sha256": asset.sha256, **pcm_measurements(pcm)})
    return replace(
        prepared,
        context={
            **prepared.context,
            "audio_assessment": {
                "version": ANALYSIS_CONTRACT["version"],
                "measurements": measurements,
                "limitations": (
                    "Energy measurements do not establish perceptual quality, "
                    "semantic duplication or mix intelligibility."
                ),
            },
        },
    )
