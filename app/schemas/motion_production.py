"""Private HTML motion contracts; code remains untrusted until isolated rendering."""

from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.motion_audiovisual import MotionAudiovisualDesign
from app.schemas.motion_correction import MotionCorrectionRegion
from app.schemas.motion_evolution import MotionEvolutionRequest
from app.schemas.motion_plan import MotionPlan
from app.schemas.motion_preparation import MotionPreparation
from app.schemas.motion_scene_direction import MotionSceneDirection
from app.schemas.motion_speech import MotionSpeechTiming
from app.schemas.motion_staging import MotionStaging


class MotionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class MotionSoundEvent(MotionModel):
    """An owner-selected, rights-confirmed audio event; never inferred from a prompt."""

    asset_id: UUID
    role: Literal["music", "effect"]
    rights_confirmed: bool = Field(strict=True)
    not_duplicate_of_source: bool = Field(strict=True)
    trim_start_ms: int = Field(strict=True, ge=0, le=60000)
    trim_end_ms: int = Field(strict=True, gt=0, le=60000)
    offset_ms: int = Field(strict=True, ge=0, le=60000)
    volume: float = Field(strict=True, ge=0, le=1)
    fade_in_ms: int = Field(strict=True, ge=0, le=60000)
    fade_out_ms: int = Field(strict=True, ge=0, le=60000)

    @model_validator(mode="after")
    def interval(self) -> Self:
        duration = self.trim_end_ms - self.trim_start_ms
        if (
            not self.rights_confirmed
            or not self.not_duplicate_of_source
            or duration <= 0
            or self.offset_ms + duration > 60000
        ):
            raise ValueError("Sound rights and bounded interval are required")
        if self.fade_in_ms + self.fade_out_ms > duration:
            raise ValueError("Invalid sound interval or fades")
        if not float(self.volume * 1000000).is_integer():
            raise ValueError("Volume exceeds six decimal places")
        return self


class MotionDucking(MotionModel):
    """User-selected compressor parameters; applied only to music against the source."""

    threshold: float = Field(strict=True, ge=0.00097563, le=1)
    ratio: float = Field(strict=True, ge=1, le=20)
    attack_ms: int = Field(strict=True, ge=1, le=2000)
    release_ms: int = Field(strict=True, ge=5, le=9000)


class MotionRequest(MotionModel):
    operation_id: UUID
    instruction: str = Field(min_length=1, max_length=4000, repr=False)
    source_asset_id: UUID
    format: Literal["reel"] = "reel"
    storyboard: bool = Field(default=False, exclude_if=lambda value: not value)
    collection_photo_ids: tuple[UUID, ...] = Field(default=(), max_length=4, exclude_if=lambda value: not value)
    repertoire_id: (
        Literal["business-reel-v1", "business-reel-v2", "business-reel-v3", "business-reel-v4", "business-reel-v5"]
        | None
    ) = Field(default=None, exclude_if=lambda value: value is None)
    structural_floor: Literal["motion-production-quality-v3"] | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
        description="Opt-in structural rejection. Omitted requests stay on the v2 quality contract.",
    )
    scene_direction: MotionSceneDirection | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
        repr=False,
        description="Visual direction supplied before construction; omission retains model-proposed direction.",
    )
    speech_timing: MotionSpeechTiming | None = Field(default=None, exclude_if=lambda value: value is None, repr=False)
    sound_events: tuple[MotionSoundEvent, ...] = Field(default=(), max_length=8, exclude_if=lambda value: not value)
    music_ducking: MotionDucking | None = Field(default=None, exclude_if=lambda value: value is None)
    evolution: MotionEvolutionRequest | None = Field(default=None, exclude_if=lambda value: value is None)
    preparation: MotionPreparation | None = Field(default=None, exclude_if=lambda value: value is None, repr=False)
    review_checkpoints: bool = Field(default=False, strict=True, exclude_if=lambda value: not value)
    propose_direction: bool = Field(default=False, strict=True, exclude_if=lambda value: not value)
    sound_library_id: Literal["public-cc0-v1"] | None = Field(default=None, exclude_if=lambda value: value is None)

    @model_validator(mode="after")
    def unique_photos(self) -> Self:
        if self.review_checkpoints and (
            self.preparation is None
            or (self.scene_direction is None and not self.propose_direction)
            or not self.storyboard
        ):
            raise ValueError("Checkpoints require preparation, supplied direction and storyboard")
        if self.propose_direction and (
            not self.review_checkpoints
            or self.scene_direction is not None
            or self.preparation is None
            or self.instruction != self.preparation.client_message
            or self.sound_events
            or self.music_ducking is not None
        ):
            raise ValueError(
                "Proposed direction requires the exact client message and checkpoints without fixed choices"
            )
        if self.sound_library_id is not None and not self.propose_direction:
            raise ValueError("Sound library selection belongs to proposed audiovisual planning")
        if self.preparation is not None:
            if self.scene_direction is None and not self.propose_direction:
                raise ValueError("Preparation requires a direction to bind its decisions")
            if self.scene_direction is not None and any(not item.scene_ids for item in self.preparation.evidence):
                raise ValueError("Supplied-direction evidence requires scene identifiers")
            scenes = {scene.scene_id for scene in self.scene_direction.scenes} if self.scene_direction else set()
            mentioned = {scene for item in self.preparation.decisions for scene in item.scene_ids}
            mentioned |= {scene for evidence in self.preparation.evidence for scene in evidence.scene_ids}
            if not mentioned <= scenes:
                raise ValueError("Preparation refers to an unknown scene")
            if {scene for item in self.preparation.decisions for scene in item.scene_ids} != scenes:
                raise ValueError("Every scene requires an explicit decision basis")
        if self.evolution is not None and (
            not self.storyboard
            or (self.evolution.version == "motion-evolution-v1" and self.scene_direction is None)
            or (self.evolution.version == "motion-evolution-v2" and not self.propose_direction)
        ):
            raise ValueError("Evolution requires supplied direction and storyboard")
        if self.speech_timing is not None and self.speech_timing.provenance != "owner_reviewed":
            raise ValueError("Only reviewed timing may be supplied by the caller")
        if len(set(self.collection_photo_ids)) != len(self.collection_photo_ids):
            raise ValueError("Collection photos must be distinct")
        if self.music_ducking is not None and not any(event.role == "music" for event in self.sound_events):
            raise ValueError("Ducking requires an explicitly selected music event")
        return self


class MotionAudioTrack(MotionModel):
    asset_id: str = Field(pattern=r"^assets/[A-Za-z0-9_.-]{1,80}$")
    offset_ms: int = Field(strict=True, ge=0, le=60000)
    trim_start_ms: int = Field(strict=True, ge=0, le=60000)
    trim_end_ms: int = Field(strict=True, gt=0, le=60000)
    volume: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def interval(self) -> Self:
        if self.trim_end_ms <= self.trim_start_ms:
            raise ValueError("Invalid audio interval")
        return self


class MotionAudio(MotionModel):
    mode: Literal["silent", "mix"]
    tracks: tuple[MotionAudioTrack, ...] = Field(max_length=16)

    @model_validator(mode="after")
    def track_mode(self) -> Self:
        if (self.mode == "silent") != (len(self.tracks) == 0):
            raise ValueError("Audio mode and tracks disagree")
        return self


class MotionIllustration(MotionModel):
    asset_id: str = Field(pattern=r"^assets/illustration-[a-z0-9-]{1,40}\.png$")
    description: str = Field(min_length=1, max_length=1600, pattern=r"\S")
    purpose: str = Field(min_length=1, max_length=400, pattern=r"\S")


class MotionConstructionPlan(MotionModel):
    """Complete planning artifact; deliberately has no executable code."""

    concept: str = Field(min_length=1, max_length=4000)
    source_usage: str = Field(min_length=1, max_length=4000)
    audio: MotionAudio
    motion_plan: MotionPlan
    illustrations: tuple[MotionIllustration, ...] = Field(max_length=2)
    scene_direction: MotionSceneDirection
    audiovisual: MotionAudiovisualDesign | None = Field(default=None, exclude_if=lambda value: value is None)
    staging: MotionStaging | None = Field(default=None, exclude_if=lambda value: value is None)


class HTMLMotionComposition(MotionModel):
    html: str = Field(min_length=1, max_length=2 * 1024 * 1024, repr=False)
    scene_init: str = Field(min_length=1, max_length=1024 * 1024, repr=False)
    concept: str = Field(min_length=1, max_length=4000)
    source_usage: str = Field(min_length=1, max_length=4000)
    audio: MotionAudio
    # Historical compositions remain readable; new contracts require a plan.
    motion_plan: MotionPlan | None = None
    illustrations: tuple[MotionIllustration, ...] = Field(default=(), max_length=2, exclude_if=lambda v: not v)
    scene_direction: MotionSceneDirection | None = Field(default=None, exclude_if=lambda value: value is None)
    audiovisual: MotionAudiovisualDesign | None = Field(default=None, exclude_if=lambda value: value is None)
    staging: MotionStaging | None = Field(default=None, exclude_if=lambda value: value is None)


class PlannedHTMLMotionComposition(HTMLMotionComposition):
    motion_plan: MotionPlan


class DirectedHTMLMotionComposition(PlannedHTMLMotionComposition):
    scene_direction: MotionSceneDirection


CriterionName = Literal["factuality", "brand", "legibility", "composition", "motion", "technical", "audio"]
MANDATORY_CRITERIA = frozenset({"factuality", "brand", "legibility", "technical"})


class MotionEvidenceReference(MotionModel):
    version: Literal["current", "previous", "source", "baseline"]
    at_ms: int = Field(strict=True, ge=0, lt=60000)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class MotionCriterion(MotionModel):
    name: CriterionName
    status: Literal["pass", "fail", "uncertain"]
    observation: str = Field(min_length=1, max_length=1000)
    evidence: tuple[MotionEvidenceReference, ...] = Field(max_length=32)

    @model_validator(mode="after")
    def grounded(self) -> Self:
        if self.name == "audio" and self.status != "uncertain":
            raise ValueError("Sampled images cannot certify audio")
        if self.status != "uncertain" and not any(ref.version == "current" for ref in self.evidence):
            raise ValueError("A verdict requires observed evidence from the current version")
        return self


class MotionIssue(MotionModel):
    severity: Literal["blocking", "major", "minor"]
    criterion: CriterionName
    actionable: bool = Field(strict=True)
    at_ms: int = Field(strict=True, ge=0, lt=60000)
    evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    problem: str = Field(min_length=1, max_length=1000)
    correction: str = Field(min_length=1, max_length=1000)
    localization: MotionCorrectionRegion | None = Field(default=None, exclude_if=lambda value: value is None)
    repair_kind: Literal["implementation", "direction", "material", "uncertain"] | None = Field(
        default=None, exclude_if=lambda value: value is None
    )

    @model_validator(mode="after")
    def actionable_audio(self) -> Self:
        if self.criterion == "audio" and self.actionable:
            raise ValueError("Unheard audio cannot trigger a correction")
        return self


class MotionCreativeCheck(MotionModel):
    name: Literal["brief_alignment", "narrative_progression", "motion_role", "visual_development"]
    status: Literal["met", "not_met", "uncertain"]
    brief_basis: str = Field(min_length=1, max_length=1000)
    observation: str = Field(min_length=1, max_length=1500)
    evidence: tuple[MotionEvidenceReference, ...] = Field(max_length=32)


class MotionTemporalCheck(MotionModel):
    name: Literal["continuity", "overlap", "reading_time", "coordination"]
    status: Literal["pass", "fail", "uncertain"]
    observation: str = Field(min_length=1, max_length=1500)
    event_ids: tuple[str, ...] = Field(max_length=16)
    evidence: tuple[MotionEvidenceReference, ...] = Field(max_length=48)
    issue_indices: tuple[int, ...] = Field(max_length=20)


class MotionBaselineCheck(MotionModel):
    dimension: Literal["meaning", "recording", "space", "rhythm", "identity"]
    result: Literal["improved", "equivalent", "regressed", "uncertain"]
    observation: str = Field(min_length=1, max_length=1000)
    evidence: tuple[MotionEvidenceReference, ...] = Field(max_length=32)


class MotionReview(MotionModel):
    verdict: Literal["adequate", "needs_revision", "reject", "insufficient_evidence"]
    criteria: tuple[MotionCriterion, ...] = Field(min_length=7, max_length=7)
    preferred: Literal["current", "previous", "undetermined"]
    preference_reason: str = Field(min_length=1, max_length=1500)
    preference_evidence: tuple[MotionEvidenceReference, ...] = Field(max_length=32)
    issues: tuple[MotionIssue, ...] = Field(max_length=20)
    limitations: tuple[str, ...] = Field(min_length=1, max_length=12)

    # Optional only for reading historical evaluations; live v1 contracts require all four.
    creative_checks: tuple[MotionCreativeCheck, ...] = Field(default=(), max_length=4)
    temporal_checks: tuple[MotionTemporalCheck, ...] = Field(default=(), max_length=4)
    baseline_video_sha256: str | None = Field(
        default=None, pattern=r"^[a-f0-9]{64}$", exclude_if=lambda value: value is None
    )
    baseline_checks: tuple[MotionBaselineCheck, ...] = Field(
        default=(), max_length=5, exclude_if=lambda value: not value
    )

    @property
    def mandatory_pass(self) -> bool:
        return all(item.status == "pass" for item in self.criteria if item.name in MANDATORY_CRITERIA)

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if {item.name for item in self.criteria} != {
            "factuality",
            "brand",
            "legibility",
            "composition",
            "motion",
            "technical",
            "audio",
        }:
            raise ValueError("Each review criterion must appear exactly once")
        actionable = [issue for issue in self.issues if issue.actionable and issue.severity != "minor"]
        if self.verdict == "adequate" and (not self.mandatory_pass or actionable):
            raise ValueError("Adequacy requires mandatory checks and no actionable major issue")
        if self.verdict == "needs_revision" and not actionable:
            raise ValueError("Correction requires an actionable major issue")
        if self.verdict == "adequate" and any(check.status != "pass" for check in self.temporal_checks):
            raise ValueError("Adequacy cannot conceal temporal failure or uncertainty")
        if (
            self.verdict == "adequate"
            and self.creative_checks
            and (
                any(item.status == "fail" for item in self.criteria)
                or any(item.status != "met" for item in self.creative_checks)
            )
        ):
            raise ValueError("Adequacy cannot conceal a creative failure or unresolved creative check")
        statuses = {item.name: item.status for item in self.criteria}
        if any(statuses[issue.criterion] != "fail" for issue in actionable):
            raise ValueError("Actionable issues must match failed criteria")
        return self


class MotionRequestRead(MotionModel):
    id: UUID
    operation_id: UUID
    format: Literal["reel", "story_video"]
    state: Literal["queued", "running", "completed", "failed", "uncertain"]
    piece_id: UUID | None
    failure_code: str | None
