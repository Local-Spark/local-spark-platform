"""Bounded, declarative motion plan; this module performs no rendering or IO.

Prose and media metadata are untrusted. Services must revalidate origin, actual
media duration and audio, ownership, rights, kit fonts, speech, hashes and costs.
An executor must reject any capability it cannot implement; it must not execute
or silently ignore fields from this document.
"""

from itertools import pairwise
from typing import Annotated, Literal, Self, cast
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

Milliseconds = Annotated[int, Field(strict=True, ge=0)]
PositiveMilliseconds = Annotated[int, Field(strict=True, gt=0)]
Description = Annotated[str, Field(min_length=1, max_length=1000)]
ContentText = Annotated[str, Field(min_length=1, max_length=500)]
FontId = Annotated[str, Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")]
HexColor = Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")]
_KEYFRAME_SEQUENCE_DESCRIPTION = (
    "Tempos relativos ao início da própria camada, não ao início da página: "
    "primeiro at_ms=0, último at_ms=timeline.end_ms-timeline.start_ms e os demais "
    "estritamente crescentes. Exemplo: para timeline 2000–5000 ms, use primeiro "
    "at_ms=0 e último at_ms=3000. Todos os quadros até o penúltimo exigem "
    "easing_to_next permitido e não nulo; o último exige null."
)


class MotionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class VersionSnapshot(MotionModel):
    id: str = Field(min_length=1, max_length=120)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class MediaSource(MotionModel):
    id: UUID
    kind: Literal["video", "image", "audio"]
    origin: Literal["customer_recording", "asset"]
    duration_ms: PositiveMilliseconds | None = None
    # Probe-derived at the service boundary, never inferred from a model answer.
    has_audio: bool | None = None
    derived_from_source_id: UUID | None = None

    @model_validator(mode="after")
    def validate_media(self) -> Self:
        if self.kind == "image":
            if self.duration_ms is not None or self.has_audio is not None:
                raise ValueError("Image cannot declare source duration or audio")
        elif self.duration_ms is None:
            raise ValueError("Time-based sources need a duration")
        if self.kind != "video" and self.has_audio is not None:
            raise ValueError("Only video sources declare has_audio")
        if self.origin == "customer_recording" and (
            self.kind != "video" or self.duration_ms is None or self.duration_ms > 60000
        ):
            raise ValueError("Customer recording must be video of at most 60000 ms")
        if self.derived_from_source_id is not None and (self.kind != "audio" or self.origin != "asset"):
            raise ValueError("Only audio assets may declare a source video")
        return self


class TimeRange(MotionModel):
    start_ms: Milliseconds
    end_ms: PositiveMilliseconds

    @model_validator(mode="after")
    def validate_interval(self) -> Self:
        if self.end_ms <= self.start_ms:
            raise ValueError("End must follow start")
        return self


class PlaybackRate(MotionModel):
    """Exact source-time / output-time ratio; 1/16..16, no implicit speed."""

    numerator: int = Field(strict=True, ge=1, le=60000)
    denominator: int = Field(strict=True, ge=1, le=60000)

    @model_validator(mode="after")
    def validate_rate(self) -> Self:
        if self.numerator > 16 * self.denominator or self.denominator > 16 * self.numerator:
            raise ValueError("Playback rate outside executor bounds")
        return self


class ClipInsets(MotionModel):
    """Inset from each layer edge in basis points, with positive visible area."""

    top: int = Field(strict=True, ge=0, le=9999)
    right: int = Field(strict=True, ge=0, le=9999)
    bottom: int = Field(strict=True, ge=0, le=9999)
    left: int = Field(strict=True, ge=0, le=9999)

    @model_validator(mode="after")
    def validate_visible_area(self) -> Self:
        if self.top + self.bottom >= 10000 or self.left + self.right >= 10000:
            raise ValueError("Clip insets must leave a positive area")
        return self


class VisualState(MotionModel):
    """Frame-relative x/y/w/h and layer-relative scale/opacity in basis points.

    x/y identify the upper-left box corner, permitting bounded off-canvas entry;
    Scale and rotation use the box center; rotation is in centidegrees.
    Clip applies inside the box.
    """

    x: int = Field(strict=True, ge=-20000, le=30000)
    y: int = Field(strict=True, ge=-20000, le=30000)
    width: int = Field(strict=True, ge=1, le=30000)
    height: int = Field(strict=True, ge=1, le=30000)
    scale: int = Field(strict=True, ge=1, le=40000)
    opacity: int = Field(strict=True, ge=0, le=10000)
    rotation: int = Field(strict=True, ge=-360000, le=360000)
    clip: ClipInsets


class VisualKeyframe(MotionModel):
    """Time is relative to layer start; easing applies to the next keyframe."""

    at_ms: Milliseconds = Field(description="Milissegundos desde o início da camada, não desde a página.")
    state: VisualState
    easing_to_next: Literal["linear", "ease_in", "ease_out", "ease_in_out"] | None = Field(
        description=(
            "Interpolação até o próximo quadro: valor permitido e não nulo até o penúltimo, "
            "inclusive quando estados são iguais; no último quadro, null."
        )
    )


class Transition(MotionModel):
    """Entry/exit fade multiplies keyframed opacity; cut is instantaneous."""

    kind: Literal["cut", "fade"]
    duration_ms: Milliseconds

    @model_validator(mode="after")
    def validate_duration(self) -> Self:
        if (self.kind == "cut") != (self.duration_ms == 0):
            raise ValueError("A cut is instantaneous; a fade needs positive duration")
        return self


class Typography(MotionModel):
    # The compiler must resolve this ID against an authorized kit allowlist.
    font_id: FontId
    font_size: int = Field(
        strict=True,
        ge=1,
        le=10000,
        description=(
            "Tamanho em pontos-base da altura do quadro, não pixels: 10000 = 100% da altura. "
            "Exemplo: em um quadro de 1280 px de altura, 250 = 32 px."
        ),
    )
    weight: Literal[400, 700]
    align: Literal["left", "center", "right"]
    vertical_align: Literal["top", "center", "bottom"]
    color: HexColor
    line_height: int = Field(
        strict=True,
        ge=5000,
        le=30000,
        description="Entrelinha em pontos-base do tamanho da fonte: 10000 equivale a 1,0 vez o tamanho.",
    )
    letter_spacing: int = Field(
        strict=True,
        ge=-5000,
        le=5000,
        description="Espaçamento em pontos-base do tamanho da fonte: 500 equivale a 0,05 em; 0 é sem acréscimo.",
    )


class GraphicSpec(MotionModel):
    kind: Literal["text", "rectangle", "circle"]
    text: ContentText | None = None
    typography: Typography | None = None
    fill: HexColor | None = None
    corner_radius: int | None = Field(default=None, strict=True, ge=0, le=5000)

    @model_validator(mode="after")
    def validate_graphic(self) -> Self:
        if self.kind == "text":
            if self.text is None or self.typography is None or self.fill is not None or self.corner_radius is not None:
                raise ValueError("Text requires text and typography only")
        elif self.text is not None or self.typography is not None or self.fill is None:
            raise ValueError("Shapes require fill and cannot contain text")
        elif self.kind == "circle" and self.corner_radius is not None:
            raise ValueError("Circle does not accept corner radius")
        return self


class MediaPlacement(MotionModel):
    fit: Literal["cover", "contain"]
    focus_x: int = Field(strict=True, ge=0, le=10000)
    focus_y: int = Field(strict=True, ge=0, le=10000)


class VisualSegment(MotionModel):
    """One layer. Later entries overlay earlier entries on the page."""

    kind: Literal["video", "image", "graphic"]
    timeline: TimeRange
    source_id: UUID | None = None
    source_trim: TimeRange | None = None
    playback_rate: PlaybackRate | None = None
    placement: MediaPlacement | None = None
    graphic: GraphicSpec | None = None
    keyframes: list[VisualKeyframe] = Field(min_length=2, max_length=32, description=_KEYFRAME_SEQUENCE_DESCRIPTION)
    enter: Transition
    exit: Transition
    direction: Description

    @model_validator(mode="after")
    def validate_layer(self) -> Self:
        duration = self.timeline.end_ms - self.timeline.start_ms
        _keyframes_and_transitions(self.keyframes, self.enter, self.exit, duration)
        if self.kind == "graphic":
            if any(
                v is not None
                for v in (
                    self.source_id,
                    self.source_trim,
                    self.playback_rate,
                    self.placement,
                )
            ):
                raise ValueError("Graphic cannot reference media")
            if self.graphic is None:
                raise ValueError("Graphic specification required")
        else:
            if self.source_id is None or self.placement is None or self.graphic is not None:
                raise ValueError("Media needs source and placement, without graphic")
            if self.kind == "video":
                if self.source_trim is None or self.playback_rate is None:
                    raise ValueError("Video needs source trim and playback rate")
                _check_rate(self.source_trim, self.timeline, self.playback_rate)
            elif self.source_trim is not None or self.playback_rate is not None:
                raise ValueError("Image cannot have source trim or playback rate")
        return self


class AudioSegment(MotionModel):
    """Gain uses millidecibels; fade ramps are linear in amplitude."""

    source_id: UUID
    source_trim: TimeRange
    timeline: TimeRange
    playback_rate: PlaybackRate
    role: Literal["recorded_voice", "original_sound", "music", "effect"]
    # millidecibels; an actual mute must use the explicit silent mode instead.
    gain_mdb: int = Field(strict=True, ge=-60000, le=12000)
    fade_in_ms: Milliseconds
    fade_out_ms: Milliseconds
    direction: Description

    @model_validator(mode="after")
    def validate_track(self) -> Self:
        duration = self.timeline.end_ms - self.timeline.start_ms
        if self.fade_in_ms + self.fade_out_ms > duration:
            raise ValueError("Audio fades exceed track duration")
        _check_rate(self.source_trim, self.timeline, self.playback_rate)
        return self


class AudioPlan(MotionModel):
    mode: Literal["mix", "silent"]
    speech: Literal["preserve", "not_present", "omit"]
    omission_reason: Description | None = Field(
        default=None,
        description=(
            "Razão não vazia somente quando speech='omit'; para speech='preserve' ou 'not_present', deve ser null."
        ),
    )
    tracks: list[AudioSegment] = Field(max_length=16)

    @model_validator(mode="after")
    def validate_plan(self) -> Self:
        if (self.mode == "mix") != bool(self.tracks):
            raise ValueError("Audio mode must agree with track presence")
        if (self.speech == "omit") != (self.omission_reason is not None):
            raise ValueError("Omitted speech requires a reason")
        if self.speech == "preserve" and not any(track.role == "recorded_voice" for track in self.tracks):
            raise ValueError("Preserved speech requires an explicit voice track")
        if self.speech != "preserve" and any(track.role == "recorded_voice" for track in self.tracks):
            raise ValueError("Voice track conflicts with the declared speech policy")
        return self


class Caption(MotionModel):
    """Caption uses the same complete geometry and animation as a text layer."""

    timeline: TimeRange
    text: ContentText
    typography: Typography
    keyframes: list[VisualKeyframe] = Field(min_length=2, max_length=32, description=_KEYFRAME_SEQUENCE_DESCRIPTION)
    enter: Transition
    exit: Transition
    direction: Description | None = None

    @model_validator(mode="after")
    def validate_caption(self) -> Self:
        _keyframes_and_transitions(
            self.keyframes,
            self.enter,
            self.exit,
            self.timeline.end_ms - self.timeline.start_ms,
        )
        return self


class MotionPage(MotionModel):
    id: UUID
    duration_ms: PositiveMilliseconds = Field(le=60000)
    background: HexColor
    visual: list[VisualSegment] = Field(min_length=1, max_length=64)
    audio: AudioPlan
    captions: list[Caption] = Field(max_length=128)


class MotionDirection(MotionModel):
    schema_version: Literal["motion-direction-v2"]
    format: Literal["reel", "story_video", "carousel_motion"]
    skill: VersionSnapshot
    style: VersionSnapshot
    sources: list[MediaSource] = Field(max_length=32)
    pages: list[MotionPage] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def validate_direction(self) -> Self:
        sources = {source.id: source for source in self.sources}
        if len(sources) != len(self.sources):
            raise ValueError("Source IDs must be unique")
        recordings = [source for source in self.sources if source.origin == "customer_recording"]
        if len(recordings) > 1:
            raise ValueError("At most one customer recording is allowed")
        for source in self.sources:
            if source.derived_from_source_id is not None:
                original = sources.get(source.derived_from_source_id)
                if original is None or original.kind != "video" or original.id == source.id:
                    raise ValueError("Derived audio must reference a video source")
        if self.format == "carousel_motion":
            if len(self.pages) < 3 or any(not 5000 <= page.duration_ms <= 8000 for page in self.pages):
                raise ValueError("Carousel needs 3 to 5 pages of 5000 to 8000 ms")
        elif len(self.pages) != 1 or len(recordings) != 1:
            raise ValueError("Reel and video story need one page and one customer recording")
        if len({page.id for page in self.pages}) != len(self.pages):
            raise ValueError("Page IDs must be unique")
        used_visual_sources: set[UUID] = set()
        for page in self.pages:
            for visual in page.visual:
                _within_timeline(visual.timeline, page.duration_ms)
                if visual.kind == "graphic":
                    continue
                visual_source = sources.get(cast(UUID, visual.source_id))
                if visual_source is None or visual_source.kind != visual.kind:
                    raise ValueError("Visual source missing or type mismatch")
                if visual_source.kind == "video":
                    _source_trim(visual.source_trim, visual_source)
                used_visual_sources.add(visual_source.id)
            for track in page.audio.tracks:
                _within_timeline(track.timeline, page.duration_ms)
                audio_source = sources.get(track.source_id)
                if audio_source is None or audio_source.kind not in {"video", "audio"}:
                    raise ValueError("Audio source missing or not time-based")
                if audio_source.kind == "video" and audio_source.has_audio is not True:
                    raise ValueError("Video audio must be verified before use")
                _source_trim(track.source_trim, audio_source)
                if track.role == "recorded_voice" and not any(
                    r.has_audio is True and (audio_source.id == r.id or audio_source.derived_from_source_id == r.id)
                    for r in recordings
                ):
                    raise ValueError("Recorded voice must belong to a recording with verified audio")
            for caption in page.captions:
                _within_timeline(caption.timeline, page.duration_ms)
        if self.format != "carousel_motion" and recordings[0].id not in used_visual_sources:
            raise ValueError("Customer recording must appear in video")
        return self


def _keyframes_and_transitions(
    keyframes: list[VisualKeyframe], enter: Transition, exit: Transition, duration: int
) -> None:
    if keyframes[0].at_ms != 0 or keyframes[-1].at_ms != duration:
        raise ValueError("Keyframes must span the entire layer")
    if any(a.at_ms >= b.at_ms for a, b in pairwise(keyframes)):
        raise ValueError("Keyframes must be strictly ordered")
    if any(frame.easing_to_next is None for frame in keyframes[:-1]) or keyframes[-1].easing_to_next is not None:
        raise ValueError("Easing is required only when a next keyframe exists")
    if enter.duration_ms + exit.duration_ms > duration:
        raise ValueError("Transitions exceed layer duration")


def _check_rate(source: TimeRange, timeline: TimeRange, rate: PlaybackRate) -> None:
    if (source.end_ms - source.start_ms) * rate.denominator != (timeline.end_ms - timeline.start_ms) * rate.numerator:
        raise ValueError("Source trim, timeline and playback rate disagree")


def _within_timeline(interval: TimeRange, duration_ms: int) -> None:
    if interval.end_ms > duration_ms:
        raise ValueError("Segment exceeds output duration")


def _source_trim(interval: TimeRange | None, source: MediaSource) -> None:
    if interval is None or source.duration_ms is None or interval.end_ms > source.duration_ms:
        raise ValueError("Source trim missing or exceeds source duration")


class MotionRenderProfile(MotionModel):
    """Trusted executor configuration, chosen separately from the creative plan.

    A caller must restrict profiles to tested capabilities and resource limits;
    this class does not establish a product-wide aspect ratio or channel spec.
    """

    width_px: int = Field(strict=True, ge=1, le=4096)
    height_px: int = Field(strict=True, ge=1, le=4096)
    fps: int = Field(strict=True, ge=1, le=60)

    @model_validator(mode="after")
    def validate_pixel_budget(self) -> Self:
        if self.width_px * self.height_px > 8294400:
            raise ValueError("Frame exceeds renderer pixel budget")
        return self
