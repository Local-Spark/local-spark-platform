"""Informative photo measurements and required soundtrack integrity before storage."""

import io
import math
from dataclasses import replace
from typing import Any

from PIL import Image, ImageChops, ImageStat

from app.adapters.motion_html_renderer import RenderedMotion
from app.adapters.motion_inputs import PreparedMotionInput
from app.schemas.motion_production import HTMLMotionComposition
from app.services.auth import AuthError


def diagnose_render(
    rendered: RenderedMotion, prepared: PreparedMotionInput, composition: HTMLMotionComposition
) -> RenderedMotion:
    """Never use visual measurements as acceptance/rejection criteria."""
    soundtrack = prepared.context.get("authorized_soundtrack") or {}
    music = [track for track in soundtrack.get("tracks", []) if track.get("role") == "music"]
    if music:
        integrity = rendered.diagnostics.get("music_integrity") or {}
        measurements = rendered.diagnostics.get("audio_measurements") or {}
        if not isinstance(integrity, dict) or not isinstance(measurements, dict):
            raise AuthError("MOTION_RENDER_MUSIC_INVALID", 409)
        duration = integrity.get("audio_duration_ms")
        peak = measurements.get("sample_peak_dbfs")
        required = max(t["offset_ms"] + t["trim_end_ms"] - t["trim_start_ms"] for t in music)
        if (
            integrity.get("source") != "decoded_output"
            or not isinstance(duration, (int, float))
            or isinstance(duration, bool)
            or not math.isfinite(duration)
            or duration <= 0
            or duration + 25 < required
            or integrity.get("required_end_ms") != required
            or measurements.get("source") != "decoded_output"
            or not isinstance(peak, (int, float))
            or isinstance(peak, bool)
            or not math.isfinite(peak)
        ):
            raise AuthError("MOTION_RENDER_MUSIC_INVALID", 409)
    if (prepared.context.get("source") or {}).get("kind") != "photos":
        return rendered
    samples = sorted(rendered.evidence, key=lambda frame: frame.ms)
    differences = []
    for left, right in zip(samples, samples[1:], strict=False):
        with Image.open(io.BytesIO(left.png)) as a, Image.open(io.BytesIO(right.png)) as b:
            delta = ImageChops.difference(a.convert("RGB").resize((64, 64)), b.convert("RGB").resize((64, 64)))
            differences.append(sum(ImageStat.Stat(delta).mean) / (3 * 255))
    plan = composition.motion_plan
    transitions = [scene.transition_to_next.strip().casefold() for scene in plan.scenes[:-1]] if plan else []
    report: dict[str, Any] = {
        "version": "motion-photo-diagnostics-v1",
        "mode": "informative_only",
        "source": "sampled_output_frames",
        "sample_count": len(samples),
        "sample_times_ms": [frame.ms for frame in samples],
        "movement": {"mean_normalized_pixel_difference": sum(differences) / len(differences) if differences else None},
        "near_static": {
            "sample_pair_percent": 100 * sum(d < 0.01 for d in differences) / len(differences) if differences else None,
            "descriptive_difference_threshold": 0.01,
        },
        "transitions": {
            "source": "declared_plan",
            "count": len(transitions),
            "distinct_descriptions": len(set(transitions)),
        },
        "narrative_strength": {
            "status": "requires_human_calibration",
            "score": None,
            "declared_moments": len(composition.staging.moments) if composition.staging else 0,
        },
        "limitations": (
            "Diferença de pixels entre amostras não mede movimento contínuo nem qualidade; "
            "mudanças de texto/cena também alteram pixels. Percentual refere-se a pares amostrados, "
            "não à duração do vídeo. Descrições distintas não comprovam variedade visual. "
            "Nenhuma destas métricas rejeita a peça."
        ),
    }
    return replace(rendered, diagnostics={**rendered.diagnostics, "photo_metrics": report})
