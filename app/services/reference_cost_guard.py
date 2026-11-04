"""Private accounting for future discovery effects; no provider is enabled here.

The database policy has no active version initially. Claims and reconciliation
are atomic database functions; only a freshly committed claim permits dispatch.
The month assigned to a claim does not establish the provider's billing month.
"""

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Literal, NoReturn
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db.session import Database

Provider = Literal["google", "apify", "jev"]
_PROVIDERS = frozenset(("google", "apify", "jev"))
_MAX = 1_000_000_000_000
_ERROR_CODES = (
    "REFERENCE_EFFECT_CONFLICT",
    "REFERENCE_OWNER_INACTIVE",
    "REFERENCE_DISCOVERY_NOT_PENDING",
    "REFERENCE_BUDGET_DISABLED",
    "REFERENCE_SEARCH_PROVIDER_BUDGET_EXCEEDED",
    "REFERENCE_SEARCH_BUDGET_EXCEEDED",
    "REFERENCE_MONTHLY_PROVIDER_BUDGET_EXCEEDED",
    "REFERENCE_MONTHLY_BUDGET_EXCEEDED",
    "REFERENCE_RESERVATION_NOT_FOUND",
    "REFERENCE_OUTCOME_CONFLICT",
    "REFERENCE_MONTHLY_INCONSISTENT",
    "REFERENCE_EVIDENCE_REQUIRED",
    "INVALID_CLAIM",
    "INVALID_ACTUAL_COST",
)


class ReferenceCostError(Exception):
    pass


@dataclass(frozen=True)
class ReferenceCostClaim:
    id: UUID
    state: str
    created: bool
    reserved_usd_micros: int
    actual_usd_micros: int | None


def _claim(row: Any) -> ReferenceCostClaim:
    return ReferenceCostClaim(
        UUID(row["id"]), row["state"], row["created"], row["reserved_usd_micros"], row["actual_usd_micros"]
    )


def _digest(business: UUID, actor: UUID, discovery: UUID, provider: str, request_hash: str, amount: int) -> str:
    if provider not in _PROVIDERS:
        raise ReferenceCostError("INVALID_PROVIDER")
    if (
        len(request_hash) != 64
        or any(c not in "0123456789abcdef" for c in request_hash)
        or type(amount) is not int
        or not 0 < amount <= _MAX
    ):
        raise ReferenceCostError("INVALID_CLAIM")
    return hashlib.sha256(
        json.dumps(
            [str(business), str(actor), str(discovery), provider, request_hash, amount], separators=(",", ":")
        ).encode()
    ).hexdigest()


def _translate_error(error: DBAPIError) -> NoReturn:
    # Only these stable codes may leave the service; never log SQL parameters.
    for code in _ERROR_CODES:
        if code in str(error.orig):
            raise ReferenceCostError(code) from None
    raise error


class ReferenceCostGuard:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def claim(
        self,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        discovery: UUID,
        effect: UUID,
        provider: Provider,
        request_hash: str,
        reserved_usd_micros: int,
    ) -> ReferenceCostClaim:
        digest = _digest(business, actor, discovery, provider, request_hash, reserved_usd_micros)
        try:
            async with self.database.transaction(tenant, actor) as session:
                row = await session.scalar(
                    text("SELECT public.reference_cost_claim(:business,:discovery,:effect,:provider,:hash,:amount)"),
                    {
                        "business": business,
                        "discovery": discovery,
                        "effect": effect,
                        "provider": provider,
                        "hash": digest,
                        "amount": reserved_usd_micros,
                    },
                )
                return _claim(row)
        except DBAPIError as error:
            _translate_error(error)

    async def finish(
        self, tenant: UUID, actor: UUID, reservation: UUID, *, actual_usd_micros: int | None
    ) -> ReferenceCostClaim:
        if actual_usd_micros is not None and (type(actual_usd_micros) is not int or not 0 <= actual_usd_micros <= _MAX):
            raise ReferenceCostError("INVALID_ACTUAL_COST")
        try:
            async with self.database.transaction(tenant, actor) as session:
                row = await session.scalar(
                    text("SELECT public.reference_cost_finish(:id,:actual)"),
                    {"id": reservation, "actual": actual_usd_micros},
                )
                return _claim(row)
        except DBAPIError as error:
            _translate_error(error)
