"""Local editorial conversation simulator contracts."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class SimulateMessage(BaseModel):
    operation_id: UUID
    text: str = Field(min_length=1, max_length=1000)


class DecideMessage(BaseModel):
    confirmed: bool


class ConversationDecision(BaseModel):
    id: UUID
    state: Literal["awaiting_confirmation", "needs_review", "confirmed", "discarded"]
    intent: Literal["price", "availability", "unknown"]
    summary: str | None
    reply: str
