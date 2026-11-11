"""Private HTML motion contracts; code remains untrusted until isolated rendering."""

from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.motion_plan import MotionPlan
from app.schemas.motion_scene_direction import MotionSceneDirection


class MotionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class MotionRequest(MotionModel):
    operation_id: UUID
    instruction: str = Field(min_length=1, max_length=4000, repr=False)
    source_asset_id: UUID
    format: Literal["reel"] = "reel"
    storyboard: bool = Field(default=False, exclude_if=lambda value: not value)
    collection_photo_ids: tuple[UUID, ...] = Field(default=(), max_length=4, exclude_if=lambda value: not value)
 
    @model_validator(mode="after")
    def unique_photos(self) -> Self:
        if len(set(self.collection_photo_ids)) != len(self.collection_photo_ids):
            raise ValueError("Collection photos must be distinct")
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


class PlannedHTMLMotionComposition(HTMLMotionComposition):
    motion_plan: MotionPlan


class DirectedHTMLMotionComposition(PlannedHTMLMotionComposition):
    scene_direction: MotionSceneDirection


CriterionName = Literal["factuality", "brand", "legibility", "composition", "motion", "technical", "audio"]
MANDATORY_CRITERIA = frozenset({"factuality", "brand", "legibility", "technical"})


class MotionEvidenceReference(MotionModel):
    version: Literal["current", "previous", "source"]
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
    event_ids: tuple[str, ...] = Field(max_length=3)
    evidence: tuple[MotionEvidenceReference, ...] = Field(max_length=32)
    issue_indices: tuple[int, ...] = Field(max_length=20)


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
