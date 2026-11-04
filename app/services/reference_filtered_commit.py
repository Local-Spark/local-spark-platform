"""Internal commit call for a filtered batch produced by one trusted activity.

This service does not prove that supplied observations came from providers. It
must only receive a batch derived from the bound in-memory Google/Jev inputs.
The database separately verifies and fences their durable intents. There is no
route, live provider configuration, or Temporal payload in this module.
"""

import json
import re
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text

from app.db.session import Database
from app.schemas.reference_filtered_batch import FilteredBatch


class FilteredCommitError(ValueError):
    """A stable pre-dispatch failure without sensitive input in its message."""


@dataclass(frozen=True, repr=False)
class FilteredCommitContext:
    tenant: UUID
    business: UUID
    actor: UUID
    search: UUID
    batch: UUID
    google_effect: UUID
    google_event: UUID
    google_token: UUID
    jev_effect: UUID
    jev_event: UUID
    jev_token: UUID
    source_batch_mac: str
    context_version: int


async def commit_filtered_batch(database: Database, context: FilteredCommitContext, batch: FilteredBatch) -> UUID:
    """Commit only the allowlisted data; repeat with the same identity for replay."""
    if (
        not isinstance(context, FilteredCommitContext)
        or not isinstance(batch, FilteredBatch)
        or any(
            not isinstance(value, UUID)
            for value in (
                context.tenant,
                context.business,
                context.actor,
                context.search,
                context.batch,
                context.google_effect,
                context.google_event,
                context.google_token,
                context.jev_effect,
                context.jev_event,
                context.jev_token,
            )
        )
        or context.google_effect == context.jev_effect
        or not isinstance(context.source_batch_mac, str)
        or re.fullmatch(r"[0-9a-f]{64}", context.source_batch_mac) is None
        or type(context.context_version) is not int
        or not 0 < context.context_version <= 9_223_372_036_854_775_807
    ):
        raise FilteredCommitError("REFERENCE_FILTERED_INPUT_INVALID")
    async with database.transaction(context.tenant, context.actor) as session:
        result = await session.scalar(
            text("""SELECT public.reference_filtered_commit(
          :business,:search,:batch,:google,:google_event,:google_token,:jev,:jev_event,:jev_token,
          :source,:context,CAST(:candidates AS jsonb))"""),
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
                "context": context.context_version,
                "candidates": json.dumps(batch.model_dump(mode="json")["candidates"], separators=(",", ":")),
            },
        )
    if result != context.batch:
        raise FilteredCommitError("REFERENCE_FILTERED_RESULT_INVALID")
    return context.batch
