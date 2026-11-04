"""Two-transaction contract for future editorial catalog resolution.

The caller supplies an interpreter and enforces consent, budget and durable
idempotency before any external call. Lexical candidates are never automatically
selected.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, Protocol, cast
from uuid import UUID

from app.db.session import Database
from app.services.auth import AuthError
from app.services.creative_catalog import catalog_candidates, selected_catalog_snapshot
from app.services.editorial_conversation import NEGATION


@dataclass(frozen=True)
class CatalogIntent:
    """The interpreter must explicitly select, abstain, or request clarification."""

    decision: Literal["selected", "none", "clarify"]
    offering_id: UUID | None = None
    intent: Literal["content_request", "price", "availability", "question", "other"] | None = None
    format: Literal["photo", "carousel", "short_video", "story"] | None = None


class CatalogInterpreter(Protocol):
    async def interpret(self, message: str, candidates: list[dict[str, str]]) -> CatalogIntent: ...


class CatalogInterpreterUnavailable(Exception):
    """A provider was unavailable; this does not imply a business decision."""


class CatalogInterpreterBudgetBlocked(CatalogInterpreterUnavailable):
    """A paid request was denied before submission and may be retried safely."""


@dataclass(frozen=True)
class CatalogResolution:
    status: Literal[
        "resolved",
        "no_text",
        "not_found",
        "catalog_too_large",
        "too_many_matches",
        "none",
        "clarify",
        "interpreter_unavailable",
        "budget_blocked",
        "invalid_decision",
        "context_changed",
    ]
    snapshot: dict[str, object] | None = None
    intent: Literal["content_request", "price", "availability", "question", "other"] | None = None
    format: Literal["photo", "carousel", "short_video", "story"] | None = None


async def resolve_catalog_context(
    database: Database,
    tenant: UUID,
    business: UUID,
    actor: UUID,
    message: str,
    interpreter: CatalogInterpreter,
    *,
    interpret_unmatched: bool = False,
) -> CatalogResolution:
    """Resolve for an authorized owner without holding a lock during interpretation.

    Both transactions repeat owner authorization and the second checks the
    catalog version. Returned snapshots are transient; callers must persist
    atomically, revalidate for effects, and handle clarification explicitly.
    """
    bounded_message = message[:4000]
    async with database.transaction(tenant, actor) as session:
        result = await catalog_candidates(session, tenant, business, actor, bounded_message)
    status = result["status"]
    if status != "needs_selection" and not (interpret_unmatched and status == "not_found"):
        if status not in {"no_text", "not_found", "catalog_too_large", "too_many_matches"}:
            return CatalogResolution("invalid_decision")
        return CatalogResolution(cast(Literal["no_text", "not_found", "catalog_too_large", "too_many_matches"], status))
    # The lexical candidate is never an affirmative instruction. Negation is
    # conservatively routed to clarification, including benign "sem glúten".
    if NEGATION.search(bounded_message):
        return CatalogResolution("clarify")
    choices = cast(list[dict[str, str]], result["candidates"])
    version = cast(int, result["catalog_version"])
    # A provider can receive only the bounded text and candidate names/IDs, not
    # source photos, prices, storage paths, tenant identifiers or credentials.
    try:
        intent = await interpreter.interpret(bounded_message, [choice.copy() for choice in choices])
    except CatalogInterpreterBudgetBlocked:
        return CatalogResolution("budget_blocked")
    except CatalogInterpreterUnavailable:
        return CatalogResolution("interpreter_unavailable")
    if not isinstance(intent, CatalogIntent):
        return CatalogResolution("invalid_decision")
    if intent.intent not in {None, "content_request", "price", "availability", "question", "other"}:
        return CatalogResolution("invalid_decision")
    if intent.format not in {None, "photo", "carousel", "short_video", "story"}:
        return CatalogResolution("invalid_decision")
    if intent.decision == "none" and intent.offering_id is None:
        return CatalogResolution("none", intent=intent.intent, format=intent.format)
    if intent.decision == "clarify" and intent.offering_id is None:
        return CatalogResolution("clarify", intent=intent.intent, format=intent.format)
    if (
        intent.decision != "selected"
        or not isinstance(intent.offering_id, UUID)
        or str(intent.offering_id) not in {choice["id"] for choice in choices}
    ):
        return CatalogResolution("invalid_decision")
    try:
        async with database.transaction(tenant, actor) as session:
            snapshot = await selected_catalog_snapshot(
                session,
                tenant,
                business,
                actor,
                bounded_message,
                intent.offering_id,
                version,
                datetime.now(UTC),
                promotion_policy="request_only",
            )
    except AuthError as exc:
        if exc.code == "COLLECTION_CONTEXT_CHANGED":
            return CatalogResolution("context_changed")
        raise
    return CatalogResolution("resolved", snapshot, intent=intent.intent, format=intent.format)
