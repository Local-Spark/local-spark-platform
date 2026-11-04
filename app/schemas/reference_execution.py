"""Start the currently configured local search; providers remain server-owned."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReferenceSearchStart(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operation_id: UUID


class ReferenceSearchStarted(BaseModel):
    search_id: UUID
    cycle_id: UUID
    state: str


class ReferenceSearchRetried(BaseModel):
    search_id: UUID
    state: str
