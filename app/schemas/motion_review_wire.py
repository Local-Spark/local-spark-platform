"""Bounded model response; services expand evidence IDs to the durable review schema."""

from typing import Annotated, Literal

from pydantic import Field

from app.schemas.motion_correction import MotionCorrectionRegion
from app.schemas.motion_production import CriterionName, MotionModel

EvidenceID = Annotated[str, Field(pattern=r"^(current|previous|source|baseline)-[0-9]{1,2}$")]
Observation = Annotated[str, Field(min_length=1, max_length=240, pattern=r"\S")]


class CompactCriterion(MotionModel):
    name: CriterionName
    status: Literal["pass", "fail", "uncertain"]
    observation: Observation
    evidence: tuple[EvidenceID, ...] = Field(max_length=32)


class CompactCreativeCheck(MotionModel):
    name: Literal["brief_alignment", "narrative_progression", "motion_role", "visual_development"]
    status: Literal["met", "not_met", "uncertain"]
    brief_basis: Annotated[str, Field(min_length=1, max_length=160, pattern=r"\S")]
    observation: Observation
    evidence: tuple[EvidenceID, ...] = Field(max_length=32)


class CompactTemporalCheck(MotionModel):
    name: Literal["continuity", "overlap", "reading_time", "coordination"]
    status: Literal["pass", "fail", "uncertain"]
    observation: Observation
    event_ids: tuple[str, ...] = Field(max_length=3)
    evidence: tuple[EvidenceID, ...] = Field(max_length=32)
    issue_indices: tuple[int, ...] = Field(max_length=6)


class CompactIssue(MotionModel):
    severity: Literal["blocking", "major", "minor"]
    criterion: CriterionName
    actionable: bool = Field(strict=True)
    evidence_id: EvidenceID
    problem: Observation
    correction: Annotated[str, Field(min_length=1, max_length=320, pattern=r"\S")]


class CompactMotionReview(MotionModel):
    verdict: Literal["adequate", "needs_revision", "reject", "insufficient_evidence"]
    criteria: tuple[CompactCriterion, ...] = Field(min_length=7, max_length=7)
    preferred: Literal["current", "previous", "undetermined"]
    preference_reason: Observation
    preference_evidence: tuple[EvidenceID, ...] = Field(max_length=32)
    issues: tuple[CompactIssue, ...] = Field(max_length=6)
    limitations: tuple[Observation, ...] = Field(min_length=1, max_length=4)
    creative_checks: tuple[CompactCreativeCheck, ...] = Field(max_length=4)
    temporal_checks: tuple[CompactTemporalCheck, ...] = Field(max_length=4)


class LinkedCreativeCheck(CompactCreativeCheck):
    issue_indices: tuple[Annotated[int, Field(strict=True, ge=0, le=5)], ...] = Field(
        max_length=6,
        description="Zero-based indices in issues explicitly supporting this not_met check. "
        "Their current evidence is included by the service; use [] for met/uncertain.",
    )


class LinkedMotionReview(CompactMotionReview):
    creative_checks: tuple[LinkedCreativeCheck, ...] = Field(max_length=4)


class LocalizedIssue(CompactIssue):
    localization: MotionCorrectionRegion | None


class LocalizedMotionReview(LinkedMotionReview):
    issues: tuple[LocalizedIssue, ...] = Field(max_length=6)


class StagedIssue(LocalizedIssue):
    repair_kind: Literal["implementation", "direction", "material", "uncertain"]


class StagedTemporalCheck(CompactTemporalCheck):
    event_ids: tuple[str, ...] = Field(max_length=16)
    evidence: tuple[EvidenceID, ...] = Field(max_length=48)


class StagedMotionReview(LocalizedMotionReview):
    issues: tuple[StagedIssue, ...] = Field(max_length=6)
    temporal_checks: tuple[StagedTemporalCheck, ...] = Field(max_length=4)


class CompactBaselineCheck(MotionModel):
    dimension: Literal["meaning", "recording", "space", "rhythm", "identity"]
    result: Literal["improved", "equivalent", "regressed", "uncertain"]
    observation: Observation
    evidence: tuple[EvidenceID, ...] = Field(max_length=32)


class EvolutionMotionReview(LocalizedMotionReview):
    baseline_video_sha256: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
    baseline_checks: tuple[CompactBaselineCheck, ...] = Field(min_length=5, max_length=5)
