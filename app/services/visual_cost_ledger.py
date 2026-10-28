"""Internal visual cost reservations; no provider calls or retry decisions.

USD amounts are integer millionths. The UTC calendar-month ceiling is an
operational guard, not a commercial plan or a complete measure of COGS.
The separate aggregate OpenAI ceiling covers only reservations in this ledger;
actual charges and calls made elsewhere can exceed it.
Only a freshly created and committed reservation grants permission to dispatch
an effect; a reservation inside an uncommitted transaction is not authorization.
"""

import hashlib
import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.session import Database


class VisualCostError(Exception):
    pass


@dataclass(frozen=True)
class VisualReservation:
    id: UUID
    state: str
    reserved_usd_micros: int
    actual_usd_micros: int | None
    created: bool


def _result(row: Any, created: bool) -> VisualReservation:
    return VisualReservation(row["id"], row["state"], row["reserved_usd_micros"], row["actual_usd_micros"], created)


async def _event(session: Any, tenant: UUID, actor: UUID, reservation: UUID, action: str) -> None:
    await session.execute(
        text("""INSERT INTO visual_cost_events(id,tenant_id,reservation_id,actor_id,action)
      VALUES(:id,:tenant,:reservation,:actor,:action)"""),
        {"id": uuid4(), "tenant": tenant, "reservation": reservation, "actor": actor, "action": action},
    )


def _reservation_digest(
    business: UUID,
    actor: UUID,
    provider: str,
    model: str,
    request_hash: str,
    reserved_usd_micros: int,
) -> str:
    if (
        not provider
        or len(provider) > 80
        or not model
        or len(model) > 120
        or len(request_hash) != 64
        or any(ch not in "0123456789abcdef" for ch in request_hash)
        or not 0 < reserved_usd_micros <= 1_000_000_000_000
    ):
        raise VisualCostError("INVALID_RESERVATION")
    # Hash the entire billing-relevant identity; never persist prompt or source data.
    return hashlib.sha256(
        json.dumps(
            [str(business), str(actor), provider, model, request_hash, reserved_usd_micros], separators=(",", ":")
        ).encode()
    ).hexdigest()


class VisualCostLedger:
    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings, self.database = settings, database

    async def reserve(
        self,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        operation: UUID,
        provider: str,
        model: str,
        request_hash: str,
        reserved_usd_micros: int,
    ) -> VisualReservation:
        # Preserve rejection of invalid inputs before opening the database transaction.
        _reservation_digest(business, actor, provider, model, request_hash, reserved_usd_micros)
        async with self.database.transaction(tenant, actor) as session:
            return await self.reserve_in_transaction(
                session, tenant, business, actor, operation, provider, model, request_hash, reserved_usd_micros
            )

    async def reserve_in_transaction(
        self,
        session: AsyncSession,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        operation: UUID,
        provider: str,
        model: str,
        request_hash: str,
        reserved_usd_micros: int,
    ) -> VisualReservation:
        """Reserve inside the caller's active transaction without committing it.

        The caller must set tenant/actor RLS context and revalidate owner, fence,
        sources and consent in this transaction. A newly inserted reservation
        permits a provider call only after this transaction has committed. This
        method itself never makes network requests or controls transaction scope.
        """
        digest = _reservation_digest(business, actor, provider, model, request_hash, reserved_usd_micros)
        if not session.in_transaction():
            raise VisualCostError("VISUAL_TRANSACTION_REQUIRED")
        await session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 31))"), {"key": str(tenant)})
        row = (
            (
                await session.execute(
                    text("""SELECT * FROM visual_cost_reservations
              WHERE tenant_id=:tenant AND operation_id=:operation"""),
                    {"tenant": tenant, "operation": operation},
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is not None:
            if row["request_hash"] != digest:
                raise VisualCostError("RESERVATION_OPERATION_CONFLICT")
            return _result(row, False)
        if self.settings.visual_ai_monthly_budget_usd_micros <= 0:
            raise VisualCostError("VISUAL_BUDGET_DISABLED")
        used = await session.scalar(
            text("""SELECT coalesce(sum(CASE WHEN state='completed'
              THEN actual_usd_micros ELSE reserved_usd_micros END),0) FROM visual_cost_reservations
              WHERE tenant_id=:tenant AND created_at>=date_trunc('month',now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'
              AND created_at<(date_trunc('month',now() AT TIME ZONE 'UTC') + interval '1 month') AT TIME ZONE 'UTC'"""),
            {"tenant": tenant},
        )
        if used + reserved_usd_micros > self.settings.visual_ai_monthly_budget_usd_micros:
            raise VisualCostError("VISUAL_BUDGET_EXCEEDED")
        if provider == "openai":
            ceiling = self.settings.visual_ai_global_monthly_budget_usd_micros
            if ceiling <= 0:
                raise VisualCostError("VISUAL_GLOBAL_BUDGET_DISABLED")
            month = "date_trunc('month',now() AT TIME ZONE 'UTC')::date"
            await session.execute(
                text(f"INSERT INTO visual_global_monthly_budget(month) VALUES({month}) ON CONFLICT DO NOTHING")
            )
            total = await session.scalar(
                text(f"SELECT committed_usd_micros FROM visual_global_monthly_budget WHERE month={month} FOR UPDATE")
            )
            if total + reserved_usd_micros > ceiling:
                raise VisualCostError("VISUAL_GLOBAL_BUDGET_EXCEEDED")
            await session.execute(
                text(f"""UPDATE visual_global_monthly_budget SET committed_usd_micros=committed_usd_micros+:amount,
                  updated_at=now() WHERE month={month}"""),
                {"amount": reserved_usd_micros},
            )
        row = (
            (
                await session.execute(
                    text("""INSERT INTO visual_cost_reservations
              (id,tenant_id,business_id,actor_id,operation_id,request_hash,provider,model,reserved_usd_micros,state)
              VALUES(:id,:tenant,:business,:actor,:operation,:hash,:provider,:model,:reserved,'submitted')
              RETURNING *"""),
                    {
                        "id": uuid4(),
                        "tenant": tenant,
                        "business": business,
                        "actor": actor,
                        "operation": operation,
                        "hash": digest,
                        "provider": provider,
                        "model": model,
                        "reserved": reserved_usd_micros,
                    },
                )
            )
            .mappings()
            .one()
        )
        await _event(session, tenant, actor, row["id"], "reserved")
        return _result(row, True)

    async def finish(
        self, tenant: UUID, actor: UUID, reservation: UUID, *, actual_usd_micros: int | None
    ) -> VisualReservation:
        # None is an unknown outcome; it never frees the hold nor grants a retry.
        if actual_usd_micros is not None and not 0 <= actual_usd_micros <= 1_000_000_000_000:
            raise VisualCostError("INVALID_ACTUAL_COST")
        async with self.database.transaction(tenant, actor) as session:
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 31))"), {"key": str(tenant)}
            )
            row = (
                (
                    await session.execute(
                        text("SELECT * FROM visual_cost_reservations WHERE tenant_id=:tenant AND id=:id"),
                        {"tenant": tenant, "id": reservation},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise VisualCostError("RESERVATION_NOT_FOUND")
            if row["state"] == "completed":
                if actual_usd_micros != row["actual_usd_micros"]:
                    raise VisualCostError("RESERVATION_OUTCOME_CONFLICT")
                return _result(row, False)
            state = "uncertain" if actual_usd_micros is None else "completed"
            if row["state"] == "uncertain" and state == "uncertain":
                return _result(row, False)
            if row["provider"] == "openai" and actual_usd_micros is not None:
                changed = await session.scalar(
                    text("""UPDATE visual_global_monthly_budget SET
                      committed_usd_micros=committed_usd_micros+:delta, updated_at=now()
                      WHERE month=date_trunc('month',CAST(:created AS timestamptz) AT TIME ZONE 'UTC')::date
                      RETURNING 1"""),
                    {"delta": actual_usd_micros - row["reserved_usd_micros"], "created": row["created_at"]},
                )
                if changed is None:
                    raise VisualCostError("VISUAL_GLOBAL_BUDGET_INCONSISTENT")
            row = (
                (
                    await session.execute(
                        text("""UPDATE visual_cost_reservations SET state=:state,
              actual_usd_micros=:actual,updated_at=now() WHERE tenant_id=:tenant AND id=:id RETURNING *"""),
                        {"tenant": tenant, "id": reservation, "state": state, "actual": actual_usd_micros},
                    )
                )
                .mappings()
                .one()
            )
            await _event(session, tenant, actor, reservation, state)
            if actual_usd_micros is not None and actual_usd_micros > row["reserved_usd_micros"]:
                await _event(session, tenant, actor, reservation, "over_reservation")
            return _result(row, False)
