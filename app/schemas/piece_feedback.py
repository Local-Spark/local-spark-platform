"""Explicit notes about an approved version; never a generation command."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PieceFeedbackWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    operation_id: UUID
    version_id: UUID
    note: str = Field(min_length=1, max_length=2000)


class LabPieceApproval(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation_id: UUID
    version_id: UUID
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
