"""Commit sanitized outputs of a trusted provider activity, never HTTP input.

The caller validates/parses each provider response and keeps raw observations
in memory. Existing effect tokens fence that caller; they do not independently
prove a provider response. Scores, Place IDs and positions are read from the
already stored batch/shortlist, never accepted as publication input.
"""

import json
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import text

from app.db.session import Database
from app.schemas.owner_references import instagram_handle
from app.services.reference_filtered_commit import FilteredCommitContext


class CompletedEffect(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    effect_id: UUID
    event_id: UUID
    executor_token: UUID


class CompletedRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    effect: CompletedEffect
    candidate_ids: tuple[UUID, ...] = Field(default=(), max_length=3)

    @model_validator(mode="after")
    def distinct_candidates(self) -> "CompletedRecommendation":
        if len(set(self.candidate_ids)) != len(self.candidate_ids):
            raise ValueError("Repeated recommended candidate")
        return self


class CompletedContacts(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: UUID
    effect: CompletedEffect
    handles: tuple[str, ...] = Field(default=(), max_length=100)
    primary_handle: str | None = None

    @field_validator("handles")
    @classmethod
    def normalize_handles(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(instagram_handle(value) for value in values)

    @field_validator("primary_handle")
    @classmethod
    def normalize_primary(cls, value: str | None) -> str | None:
        return instagram_handle(value) if value is not None else None

    @model_validator(mode="after")
    def valid_options(self) -> "CompletedContacts":
        if len(set(self.handles)) != len(self.handles):
            raise ValueError("Repeated Instagram option")
        if self.primary_handle is not None and self.primary_handle not in self.handles:
            raise ValueError("Primary profile must be one of the options")
        return self


class PublicationProjection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operation_id: UUID
    recommendation: CompletedRecommendation | None = None
    contacts: tuple[CompletedContacts, ...] = Field(default=(), max_length=10)

    @model_validator(mode="after")
    def distinct_contacts(self) -> "PublicationProjection":
        if len({item.candidate_id for item in self.contacts}) != len(self.contacts):
            raise ValueError("Repeated contact candidate")
        if len({item.effect.effect_id for item in self.contacts}) != len(self.contacts):
            raise ValueError("Repeated contact effect")
        return self


async def publish_reference_shortlist(
    database: Database, context: FilteredCommitContext, projection: PublicationProjection
) -> UUID:
    """Called by the trusted activity after source responses have been parsed."""
    async with database.transaction(context.tenant, context.actor) as session:
        value = await session.scalar(
            text("""SELECT public.reference_publish_shortlist(
              :business,:search,:batch,:google,:google_event,:google_token,
              :jev,:jev_event,:jev_token,:source,CAST(:projection AS jsonb))"""),
            {
                "business": context.business,
                "search": context.search,
                "batch": context.batch,
                "google": context.google_effect,
                "google_event": context.google_event,
                "google_token": context.google_token,
                "jev": context.jev_effect,
                "jev_event": context.jev_event,
                "jev_token": context.jev_token,
                "source": context.source_batch_mac,
                "projection": json.dumps(projection.model_dump(mode="json"), separators=(",", ":")),
            },
        )
    return UUID(str(value))
