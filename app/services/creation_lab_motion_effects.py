"""Administrative persistence for the existing motion effect and cost-bound algorithms."""

import json
from typing import Any
from uuid import UUID, uuid5

from sqlalchemy import text

from app.core.config import Settings
from app.db.session import Database
from app.services.auth import AuthError
from app.services.creation_lab_drafts import ZERO
from app.services.creation_lab_execution import CreationLabExecution
from app.services.motion_effects import MotionEffects
from app.services.motion_requests import MotionRequestService
from app.services.visual_cost_ledger import VisualCostLedger, VisualReservation


class LabMotionLedger(VisualCostLedger):
    """An unknown invoice keeps its hold; generation success is a distinct state."""

    def __init__(self, settings: Settings, database: Database, run: UUID) -> None:
        super().__init__(settings, database)
        self.run = run
        self.execution = CreationLabExecution(settings, database)

    async def finish(
        self, tenant: UUID, actor: UUID, reservation: UUID, *, actual_usd_micros: int | None
    ) -> VisualReservation:
        async with self.database.transaction(ZERO, actor) as session:
            await self.execution.guard(session, actor, self.run, "admin.creation_lab.cost.finish")
            effect = (
                (
                    await session.execute(
                        text("""SELECT * FROM creation_lab_effects
              WHERE id=:id AND run_id=:run"""),
                        {"id": reservation, "run": self.run},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if effect is None or (
                actual_usd_micros is not None and (actual_usd_micros != 0 or effect["provider"] != "fake")
            ):
                raise AuthError("CREATION_LAB_COST_OUTCOME_INVALID", 409)
            if effect["state"] == "submitted":
                await session.execute(
                    text("UPDATE creation_lab_effects SET state='uncertain' WHERE id=:id"), {"id": reservation}
                )
            return VisualReservation(
                reservation,
                "completed" if actual_usd_micros == 0 else "uncertain",
                effect["reserved_usd_micros"],
                actual_usd_micros,
                False,
            )


class LabMotionEffects(MotionEffects):
    """Reuse MotionEffects.model, tariffs, token bounds, parsing and correction capacity.

    Only persistence and funding differ. No customer ledger or motion table is
    written by this adapter; all operations must belong to its fenced lab run.
    """

    def __init__(self, requests: MotionRequestService, run: UUID) -> None:
        self.requests = requests
        self.run = run
        self.execution = CreationLabExecution(requests.settings, requests.database)
        self.ledger = LabMotionLedger(requests.settings, requests.database, run)

    async def model(self, row, token, provider, request):
        from app.adapters.motion_ai import OpenAIMotionProvider

        if not isinstance(provider, OpenAIMotionProvider):
            return await super().model(row, token, provider, request)
        sequence = 0

        async def observe(operation, delta):
            nonlocal sequence
            sequence += 1
            await self.execution.evidence(
                row["actor_id"],
                self.bound_run(row),
                token,
                uuid5(operation, f"partial:{sequence}"),
                request.kind,
                {"text": delta, "partial": True, "operation_id": str(operation)},
                slot="partial",
                effect=operation,
            )

        previous = provider.delta_observer
        provider.delta_observer = observe
        try:
            return await super().model(row, token, provider, request)
        finally:
            provider.delta_observer = previous

    def bound_run(self, row: dict[str, Any]) -> UUID:
        if row["id"] != self.run:
            raise AuthError("CREATION_LAB_RUN_MISMATCH", 409)
        return self.run

    async def persist_payload(self, row: dict[str, Any], token: UUID, operation: UUID, slot: str, value: object) -> str:
        self.bound_run(row)
        if len(json.dumps(value, default=str).encode()) > 48 * 1024 * 1024:
            raise AuthError("CREATION_LAB_TRACE_TOO_LARGE", 409)
        # Evidence is stored in expiring DB trace records by the output adapter;
        # never offload diagnostic blobs to non-expiring material storage.
        return self.requests.context.seal(value)

    async def capacity(self, row: dict[str, Any], token: UUID, amount: int) -> bool:
        run = self.bound_run(row)
        if type(amount) is not int or amount < 0:
            return False
        async with self.requests.database.transaction(ZERO, row["actor_id"]) as session:
            current = await self.execution.guard(session, row["actor_id"], run, "admin.creation_lab.cost.capacity")
            self.execution.fence(current, token)
            total = int(
                await session.scalar(
                    text("SELECT coalesce(sum(committed_usd_micros),0) FROM creation_lab_runs WHERE actor_id=:actor"),
                    {"actor": row["actor_id"]},
                )
                or 0
            )
            return bool(
                current["committed_usd_micros"] + amount <= current["budget_usd_micros"]
                and (
                    not self.requests.settings.creation_lab_budget_usd_micros
                    or total + amount <= self.requests.settings.creation_lab_budget_usd_micros
                )
            )

    async def claim(
        self, row: dict[str, Any], token: UUID, operation: UUID, kind: str, payload: object, reserved: int = 0
    ) -> None:
        await self.execution.claim(
            row["actor_id"],
            self.bound_run(row),
            token,
            operation,
            kind,
            payload,
            reserve=reserved,
            authorize=lambda session: self.requests.locked_running(session, row, token),
        )

    async def received(
        self, row: dict[str, Any], token: UUID, operation: UUID, result: object, estimate: int | None = None
    ) -> None:
        await self.execution.received(row["actor_id"], self.bound_run(row), token, operation, result, estimate)

    async def reserve_submission(
        self,
        row: dict[str, Any],
        token: UUID,
        operation: UUID,
        kind: str,
        signed: object,
        reserve: int,
        provider: str,
        model: str,
    ) -> VisualReservation:
        run = self.bound_run(row)
        committed = 0 if provider == "fake" else reserve
        await self.execution.claim(
            row["actor_id"],
            run,
            token,
            operation,
            kind,
            signed,
            reserve=committed,
            provider=provider,
            model=model,
            authorize=lambda session: self.requests.locked_running(session, row, token),
        )
        await self.execution.submitted(row["actor_id"], run, token, operation)
        return VisualReservation(operation, "submitted", committed, None, True)

    async def quarantine(self, row: dict[str, Any], token: UUID, *, failure_event_id: UUID | None = None) -> None:
        await self.execution.finish(
            row["actor_id"], self.bound_run(row), token, "uncertain", "MOTION_OUTCOME_UNCERTAIN"
        )
