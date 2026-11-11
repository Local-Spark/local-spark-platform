"""Translate a verified v2 direction to the experimental visual compiler subset.

The caller must construct the snapshot from authorized, hash-verified kit,
style and media records scoped to the business. This service does not authorize
access, inspect files, render media, or prove that a transcript is correct.
No user-provided text is interpreted as code or a filesystem path.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID, uuid5

from pydantic import ValidationError
from pydantic_core import PydanticSerializationError

from app.schemas.motion import (
    AudioSegment,
    Caption,
    MotionDirection,
    MotionPage,
    Typography,
    VisualKeyframe,
    VisualSegment,
)
from app.services.auth import AuthError
from app.services.motion_skills import load_motion_skill

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MAX_COMPILER_LAYERS = 64


@dataclass(frozen=True)
class MotionCompositionCapabilities:
    # Plan data is supported; the current visual executor does not mix it.
    audio_plan: bool = True
    audio: bool = False
    variable_playback: bool = False
    captions_as_text: bool = True
    independent_fade: bool = True


EXPERIMENTAL_MOTION_CAPABILITIES = MotionCompositionCapabilities()


@dataclass(frozen=True)
class VerifiedMotionSource:
    """An authorized source and digest; speech evidence is supplied by caller."""

    id: UUID
    kind: str
    origin: str
    duration_ms: int | None
    has_audio: bool | None
    has_speech: bool | None
    derived_from_source_id: UUID | None
    sha256: str


@dataclass(frozen=True)
class VerifiedMotionSnapshot:
    """Business-scoped input built by the trusted caller, never by the model."""

    kit_id: str
    kit_sha256: str
    style_id: str
    style_sha256: str
    font_faces: frozenset[tuple[str, int]]
    sources: tuple[VerifiedMotionSource, ...]


@dataclass(frozen=True)
class MotionComposition:
    """Intermediate scenes and trust bindings; caller must guard against mutation."""

    scenes: tuple[dict[str, Any], ...]
    audio_plans: tuple["MotionAudioPlan", ...]
    kit_id: str
    kit_sha256: str
    style_id: str
    style_sha256: str
    source_hashes: tuple[tuple[UUID, str], ...]


@dataclass(frozen=True)
class MotionAudioTrack:
    """Only declarative, validated fields; no path, shell or filter expressions."""

    id: str
    source_id: str
    sha256: str
    source_kind: str
    source_has_speech: bool | None
    source_derived_from_id: str | None
    role: str
    trim_start_ms: int
    trim_end_ms: int
    timeline_start_ms: int
    timeline_end_ms: int
    gain_mdb: int
    fade_in_ms: int
    fade_out_ms: int
    rate_numerator: int
    rate_denominator: int


@dataclass(frozen=True)
class MotionAudioPlan:
    page_id: str
    duration_ms: int
    mode: str
    speech: str
    omission_reason: str | None
    # Metadata/trim validation alone does not establish semantic fidelity.
    speech_semantics_verified: bool
    tracks: tuple[MotionAudioTrack, ...]


def _unsupported() -> AuthError:
    return AuthError("MOTION_COMPOSITION_UNSUPPORTED", 409)


def _validate_sources(direction: MotionDirection, snapshot: VerifiedMotionSnapshot) -> tuple[tuple[UUID, str], ...]:
    trusted = {source.id: source for source in snapshot.sources}
    if len(trusted) != len(snapshot.sources):
        raise AuthError("MOTION_COMPOSITION_SNAPSHOT_INVALID", 409)
    result = []
    for source in direction.sources:
        expected = trusted.get(source.id)
        if expected is None or not _SHA256.fullmatch(expected.sha256):
            raise AuthError("MOTION_COMPOSITION_SOURCE_CHANGED", 409)
        if (expected.has_speech is not None and type(expected.has_speech) is not bool) or (
            expected.has_speech is True
            and (
                expected.kind not in {"video", "audio"} or (expected.kind == "video" and expected.has_audio is not True)
            )
        ):
            raise AuthError("MOTION_COMPOSITION_SNAPSHOT_INVALID", 409)
        if (
            source.kind,
            source.origin,
            source.duration_ms,
            source.has_audio,
            source.derived_from_source_id,
        ) != (
            expected.kind,
            expected.origin,
            expected.duration_ms,
            expected.has_audio,
            expected.derived_from_source_id,
        ):
            raise AuthError("MOTION_COMPOSITION_SOURCE_CHANGED", 409)
        if source.kind == "video" and (source.duration_ms is None or source.duration_ms > 60000):
            raise _unsupported()
        result.append((source.id, expected.sha256))
    return tuple(result)


def _validate_speech(page: MotionPage, trusted: dict[UUID, VerifiedMotionSource]) -> None:
    videos = [trusted[cast(UUID, layer.source_id)] for layer in page.visual if layer.kind == "video"]
    if any(source.has_speech is None for source in videos):
        raise AuthError("MOTION_COMPOSITION_SPEECH_UNVERIFIED", 409)
    if page.audio.speech == "not_present" and any(source.has_speech is True for source in videos):
        raise AuthError("MOTION_COMPOSITION_SPEECH_CHANGED", 409)
    if page.audio.speech == "omit" and not any(source.has_speech is True for source in videos):
        raise AuthError("MOTION_COMPOSITION_SPEECH_CHANGED", 409)
    for track in page.audio.tracks:
        source = trusted[track.source_id]
        if track.role == "recorded_voice":
            if source.has_speech is None:
                raise AuthError("MOTION_COMPOSITION_SPEECH_UNVERIFIED", 409)
            if source.has_speech is not True:
                raise AuthError("MOTION_COMPOSITION_SPEECH_CHANGED", 409)
            if source.derived_from_source_id is not None:
                parent = trusted[source.derived_from_source_id]
                if parent.has_speech is None:
                    raise AuthError("MOTION_COMPOSITION_SPEECH_UNVERIFIED", 409)
                if parent.has_speech is not True:
                    raise AuthError("MOTION_COMPOSITION_SPEECH_CHANGED", 409)
        if page.audio.speech in {"omit", "not_present"}:
            if source.has_speech is None:
                raise AuthError("MOTION_COMPOSITION_SPEECH_UNVERIFIED", 409)
            if source.has_speech is True:
                raise AuthError("MOTION_COMPOSITION_SPEECH_CHANGED", 409)


def _audio_track(page_id: UUID, index: int, track: AudioSegment, source: VerifiedMotionSource) -> MotionAudioTrack:
    if track.playback_rate.numerator != track.playback_rate.denominator or track.gain_mdb > 0:
        raise AuthError("MOTION_COMPOSITION_AUDIO_UNSUPPORTED", 409)
    return MotionAudioTrack(
        id=str(uuid5(page_id, f"motion-v2:audio:{index}")),
        source_id=str(track.source_id),
        sha256=source.sha256,
        source_kind=source.kind,
        source_has_speech=source.has_speech,
        source_derived_from_id=str(source.derived_from_source_id)
        if source.derived_from_source_id is not None
        else None,
        role=track.role,
        trim_start_ms=track.source_trim.start_ms,
        trim_end_ms=track.source_trim.end_ms,
        timeline_start_ms=track.timeline.start_ms,
        timeline_end_ms=track.timeline.end_ms,
        gain_mdb=track.gain_mdb,
        fade_in_ms=track.fade_in_ms,
        fade_out_ms=track.fade_out_ms,
        rate_numerator=track.playback_rate.numerator,
        rate_denominator=track.playback_rate.denominator,
    )


def _audio_plan(page: MotionPage, trusted: dict[UUID, VerifiedMotionSource]) -> MotionAudioPlan:
    _validate_speech(page, trusted)
    return MotionAudioPlan(
        page_id=str(page.id),
        duration_ms=page.duration_ms,
        mode=page.audio.mode,
        speech=page.audio.speech,
        omission_reason=page.audio.omission_reason,
        speech_semantics_verified=False,
        tracks=tuple(
            _audio_track(page.id, i, track, trusted[track.source_id]) for i, track in enumerate(page.audio.tracks)
        ),
    )


def _frame(keyframe: VisualKeyframe) -> dict[str, Any]:
    result = keyframe.state.model_dump()
    result["time_ms"] = keyframe.at_ms
    # The terminal frame has no outgoing interval; WAAPI requires an easing key.
    result["easing"] = keyframe.easing_to_next or "linear"
    return result


def _text_layer(layer: dict[str, Any], text: str, typography: Typography, snapshot: VerifiedMotionSnapshot) -> None:
    if (typography.font_id, typography.weight) not in snapshot.font_faces:
        raise AuthError("MOTION_COMPOSITION_FONT_UNAUTHORIZED", 409)
    code_units = len(text.encode("utf-16-le")) // 2
    if code_units > 500:
        raise _unsupported()
    layer.update(kind="text", text=text, **typography.model_dump())


def _base_layer(page_id: UUID, kind: str, index: int, item: VisualSegment | Caption) -> dict[str, Any]:
    return {
        "id": str(uuid5(page_id, f"motion-v2:{kind}:{index}")),
        "start_ms": item.timeline.start_ms,
        "end_ms": item.timeline.end_ms,
        "frames": [_frame(frame) for frame in item.keyframes],
        "enter": item.enter.model_dump(),
        "exit": item.exit.model_dump(),
    }


def _visual_layer(page_id: UUID, index: int, item: VisualSegment, snapshot: VerifiedMotionSnapshot) -> dict[str, Any]:
    layer = _base_layer(page_id, "visual", index, item)
    if item.kind == "graphic":
        graphic = item.graphic
        assert graphic is not None
        if graphic.kind == "text":
            assert graphic.text is not None and graphic.typography is not None
            _text_layer(layer, graphic.text, graphic.typography, snapshot)
        else:
            if graphic.corner_radius not in (None, 0):
                raise _unsupported()
            layer.update(kind=graphic.kind, color=graphic.fill)
        return layer
    assert item.placement is not None and item.source_id is not None
    layer.update(
        kind=item.kind,
        source_id=str(item.source_id),
        fit=item.placement.fit,
        focus={"x": item.placement.focus_x, "y": item.placement.focus_y},
    )
    if item.kind == "video":
        assert item.playback_rate is not None and item.source_trim is not None
        if item.playback_rate.numerator != item.playback_rate.denominator:
            raise _unsupported()
        layer.update(trim_start_ms=item.source_trim.start_ms, trim_end_ms=item.source_trim.end_ms)
    return layer


def compile_motion_composition(document: Mapping[str, Any], *, snapshot: VerifiedMotionSnapshot) -> MotionComposition:
    """Validate inputs and return visual scenes and declarative audio plans.

    Caller is responsible for trusted snapshot construction and must supply a
    separately validated render profile and isolated compiler/media registry.
    Audio planning is not audio rendering; a driver must independently enforce
    its capabilities and reverify trusted files before producing output.
    """
    try:
        candidate = MotionDirection.model_validate(document)
        # Revalidate serialized data: callers may supply existing Pydantic
        # instances that were mutated or created with validation bypassed.
        direction = MotionDirection.model_validate_json(candidate.model_dump_json(warnings="error"))
    except (ValidationError, PydanticSerializationError, UnicodeEncodeError):
        raise AuthError("MOTION_COMPOSITION_INVALID", 409) from None
    if not snapshot.kit_id.strip() or not _SHA256.fullmatch(snapshot.kit_sha256):
        raise AuthError("MOTION_COMPOSITION_SNAPSHOT_INVALID", 409)
    if (direction.style.id, direction.style.sha256) != (snapshot.style_id, snapshot.style_sha256):
        raise AuthError("MOTION_COMPOSITION_STYLE_CHANGED", 409)
    load_motion_skill(direction.skill.id, direction.skill.sha256, direction.format)
    source_hashes = _validate_sources(direction, snapshot)
    trusted_sources = {source.id: source for source in snapshot.sources}
    scenes: list[dict[str, Any]] = []
    audio_plans: list[MotionAudioPlan] = []
    for page in direction.pages:
        if len(page.visual) + len(page.captions) > _MAX_COMPILER_LAYERS:
            raise _unsupported()
        audio_plans.append(_audio_plan(page, trusted_sources))
        layers = [_visual_layer(page.id, index, layer, snapshot) for index, layer in enumerate(page.visual)]
        for index, caption in enumerate(page.captions):
            layer = _base_layer(page.id, "caption", index, caption)
            _text_layer(layer, caption.text, caption.typography, snapshot)
            layers.append(layer)
        scenes.append(
            {
                "format": direction.format,
                "duration_ms": page.duration_ms,
                "background": page.background,
                "layers": layers,
            }
        )
    return MotionComposition(
        scenes=tuple(scenes),
        audio_plans=tuple(audio_plans),
        kit_id=snapshot.kit_id,
        kit_sha256=snapshot.kit_sha256,
        style_id=snapshot.style_id,
        style_sha256=snapshot.style_sha256,
        source_hashes=source_hashes,
    )
