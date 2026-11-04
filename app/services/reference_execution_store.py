"""Private activity state, never returned by a customer API or workflow."""

import json
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from sqlalchemy import text

from app.db.session import Database
from app.schemas.reference_filtered_batch import FilteredBatchCandidate
from app.services.reference_filtered_commit import FilteredCommitContext


class ExecutionCandidate(FilteredBatchCandidate):
    similarity_level: Literal["high", "medium", "low", "unknown"]
    source_position: int
    contacts_cache: Literal["none", "pending", "completed"] = "none"


class ExecutionEffect(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID
    event: UUID
    provider: str
    purpose: str
    state: str
    token: UUID | None
    output: dict[str, Any] | None
    candidate_id: UUID | None = None
    attempt_no: int | None = None


class ExecutionState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    state: str
    execution_status: str = "pending"
    cycle_id: UUID
    context_version: int
    request_mac: str
    batch_id: UUID | None
    source_batch_mac: str | None
    effects: tuple[ExecutionEffect, ...]
    candidates: tuple[ExecutionCandidate, ...]

    def effect(self, provider: str, purpose: str) -> ExecutionEffect | None:
        return next((e for e in self.effects if e.provider == provider and e.purpose == purpose), None)

    def commit_context(self, tenant: UUID, business: UUID, actor: UUID, search: UUID) -> FilteredCommitContext:
        google, jev = self.effect("google", "discovery"), self.effect("jev", "discovery")
        if (
            self.batch_id is None
            or self.source_batch_mac is None
            or google is None
            or jev is None
            or google.token is None
            or jev.token is None
        ):
            raise ValueError("REFERENCE_EXECUTION_INCOMPLETE")
        return FilteredCommitContext(
            tenant,
            business,
            actor,
            search,
            self.batch_id,
            google.id,
            google.event,
            google.token,
            jev.id,
            jev.event,
            jev.token,
            self.source_batch_mac,
            self.context_version,
        )


def ranked_candidates(
    candidates: tuple[ExecutionCandidate, ...], excluded_place: str | None
) -> tuple[ExecutionCandidate, ...]:
    """Own score first, Jev similarity for ties, then the declared source order."""
    levels = {"high": 3, "medium": 2, "low": 1, "unknown": 0}
    return tuple(
        sorted(
            (c for c in candidates if c.place_id != excluded_place),
            key=lambda c: (-Decimal(c.reputation_score), -levels[c.similarity_level], c.source_position),
        )[:10]
    )


async def load_execution(
    database: Database, tenant: UUID, business: UUID, actor: UUID, search: UUID, event: UUID
) -> ExecutionState:
    async with database.transaction(tenant, actor) as session:
        value = await session.scalar(
            text("SELECT public.reference_execution_state(:business,:search,:event)"),
            {"business": business, "search": search, "event": event},
        )
    return ExecutionState.model_validate(value)


async def record_output(
    database: Database,
    tenant: UUID,
    business: UUID,
    actor: UUID,
    effect: UUID,
    token: UUID,
    kind: str,
    output: dict[str, Any],
) -> None:
    async with database.transaction(tenant, actor) as session:
        await session.scalar(
            text("SELECT public.reference_record_output(:business,:effect,:token,:kind,CAST(:output AS jsonb))"),
            {"business": business, "effect": effect, "token": token, "kind": kind, "output": json.dumps(output)},
        )
