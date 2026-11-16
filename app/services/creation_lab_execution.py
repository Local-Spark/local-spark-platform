"""Fenced, separately funded effects and private diagnostic evidence for lab runs."""

import json
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID, uuid5

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.session import Database
from app.services.auth import AuthError
from app.services.content_pieces import _event
from app.services.creation_lab_access import require_lab_access
from app.services.creation_lab_drafts import ZERO
from app.services.motion_context import MotionContext, digest


class CreationLabExecution:
    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings, self.database = settings, database
        self.cipher = MotionContext(settings)

    async def guard(self, session: AsyncSession, actor: UUID, run: UUID, action: str) -> Any:
        await session.execute(text("SELECT set_config('app.creation_lab_run_id',:run,true)"), {"run": str(run)})
        await session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key,120))"), {"key": str(run)})
        row = (
            (await session.execute(text("SELECT * FROM creation_lab_runs WHERE id=:run"), {"run": run}))
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise AuthError("CREATION_LAB_RUN_NOT_FOUND", 404)
        if row["origin"] == "lab":
            await require_lab_access(session, self.settings, actor, action)
        else:
            from app.services.whatsapp_materials import WhatsAppMaterialsService

            await session.execute(
                text("SELECT set_config('app.tenant_id',:tenant,true)"), {"tenant": str(row["tenant_id"])}
            )
            await WhatsAppMaterialsService._require_owner(session, row["tenant_id"], row["business_id"], actor)
        return row

    @staticmethod
    async def event(session: AsyncSession, run: UUID, event: UUID, kind: str, trace: UUID | None = None) -> None:
        await session.execute(
            text("""INSERT INTO creation_lab_events(run_id,sequence,event_id,kind,trace_id)
              SELECT :run,coalesce(max(sequence),0)+1,:event,:kind,:trace
              FROM creation_lab_events WHERE run_id=:run"""),
            {"run": run, "event": event, "kind": kind, "trace": trace},
        )

    @staticmethod
    def fence(row: Any, token: UUID) -> None:
        if row["state"] != "running" or row["execution_token"] != token:
            raise AuthError("CREATION_LAB_EXECUTION_FENCED", 409)

    async def budget(self, actor: UUID) -> dict[str, Any]:
        async with self.database.transaction(ZERO, actor) as session:
            await require_lab_access(session, self.settings, actor, "admin.creation_lab.budget.read")
            committed = int(
                await session.scalar(
                    text(
                        "SELECT coalesce(sum(committed_usd_micros),0) FROM creation_lab_runs WHERE actor_id=:actor AND origin='lab'"
                    ),
                    {"actor": actor},
                )
                or 0
            )
            ceiling = self.settings.creation_lab_budget_usd_micros
            return {
                "ceiling_usd_micros": ceiling,
                "committed_usd_micros": committed,
                "available_usd_micros": max(0, ceiling - committed) if ceiling else None,
                "execution_enabled": self.settings.creation_lab_execution_enabled,
            }

    async def claim(
        self,
        actor: UUID,
        run: UUID,
        token: UUID,
        operation: UUID,
        kind: str,
        payload: object,
        *,
        reserve: int = 0,
        provider: str | None = None,
        model: str | None = None,
        authorize: Callable[[AsyncSession], Awaitable[Any]] | None = None,
    ) -> None:
        if type(reserve) is not int or reserve < 0:
            raise AuthError("CREATION_LAB_RESERVATION_INVALID", 422)
        # Bound diagnostic bytes before encryption. Callers must pass provider
        # request bodies, never authorization headers or client credentials.
        if len(json.dumps(payload, default=str).encode()) > 48 * 1024 * 1024:
            raise AuthError("CREATION_LAB_TRACE_TOO_LARGE", 409)
        ciphertext, fingerprint = self.cipher.seal({"value": payload}), digest(payload)
        async with self.database.transaction(ZERO, actor) as session:
            # One administrator-wide lock prevents concurrent runs exhausting
            # the same budget. Customer billing/quota tables are never touched.
            await session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key,123))"), {"key": str(actor)})
            row = await self.guard(session, actor, run, "admin.creation_lab.effect.claim")
            self.fence(row, token)
            if authorize is not None:
                await authorize(session)
            if await session.scalar(text("SELECT 1 FROM creation_lab_effects WHERE id=:id"), {"id": operation}):
                raise AuthError("CREATION_LAB_EFFECT_ALREADY_CLAIMED", 409)
            total = int(
                await session.scalar(
                    text(
                        "SELECT coalesce(sum(committed_usd_micros),0) FROM creation_lab_runs WHERE actor_id=:actor AND origin='lab'"
                    ),
                    {"actor": actor},
                )
                or 0
            )
            if row["committed_usd_micros"] + reserve > row["budget_usd_micros"]:
                raise AuthError("CREATION_LAB_RUN_BUDGET_EXCEEDED", 409)
            if reserve and row["origin"] == "lab" and not self.settings.creation_lab_execution_enabled:
                raise AuthError("CREATION_LAB_EXECUTION_DISABLED", 409)
            if (
                reserve
                and row["origin"] == "lab"
                and self.settings.creation_lab_budget_usd_micros
                and total + reserve > self.settings.creation_lab_budget_usd_micros
            ):
                raise AuthError("CREATION_LAB_ADMIN_BUDGET_EXCEEDED", 409)
            commercial = None
            if row["origin"] == "whatsapp" and reserve:
                from app.services.message_creation import MessageCreation

                await MessageCreation(self.settings, self.database, run).authorize(session, row)
                from app.services.visual_cost_ledger import VisualCostLedger

                reservation = await VisualCostLedger(self.settings, self.database).reserve_in_transaction(
                    session,
                    row["tenant_id"],
                    row["business_id"],
                    actor,
                    operation,
                    provider,
                    model,
                    fingerprint,
                    reserve,
                )
                if not reservation.created:
                    raise AuthError("MESSAGE_EFFECT_ALREADY_RESERVED", 409)
                commercial = reservation.id
                if provider == "jev":
                    from app.services.intent_usage import reserve_intent

                    if not await reserve_intent(
                        session,
                        tenant=row["tenant_id"],
                        business=row["business_id"],
                        actor=actor,
                        operation=operation,
                        request_hash=fingerprint,
                        model=model,
                        input_rate=self.settings.intent_ai_input_rate_usd_micros,
                        output_rate=0,
                        max_input_tokens=64000,
                        max_output_tokens=0,
                        daily_limit=self.settings.intent_ai_daily_budget_usd_micros,
                    ):
                        raise AuthError("INTENT_ALREADY_SUBMITTED", 409)
            await session.execute(
                text("""INSERT INTO creation_lab_effects
              (id,run_id,kind,request_hash,state,provider,model,reserved_usd_micros,commercial_reservation_id,commercial_tenant_id)
              VALUES(:id,:run,:kind,:hash,'claimed',:provider,:model,:reserve,:commercial,:commercial_tenant)"""),
                {
                    "id": operation,
                    "run": run,
                    "kind": kind,
                    "hash": fingerprint,
                    "provider": provider,
                    "model": model,
                    "reserve": reserve,
                    "commercial": commercial,
                    "commercial_tenant": row["tenant_id"] if commercial else None,
                },
            )
            await session.execute(
                text("UPDATE creation_lab_runs SET committed_usd_micros=committed_usd_micros+:reserve WHERE id=:run"),
                {"run": run, "reserve": reserve},
            )
            trace = uuid5(operation, "request")
            await session.execute(
                text("""INSERT INTO creation_lab_trace(id,run_id,effect_id,stage,slot,payload_ciphertext)
              VALUES(:id,:run,:effect,:stage,'request',:payload)"""),
                {"id": trace, "run": run, "effect": operation, "stage": kind, "payload": ciphertext},
            )
            await self.event(session, run, uuid5(operation, "claimed"), f"effect.{kind}_claimed", trace)

    async def submitted(self, actor: UUID, run: UUID, token: UUID, operation: UUID) -> None:
        async with self.database.transaction(ZERO, actor) as session:
            row = await self.guard(session, actor, run, "admin.creation_lab.effect.submit")
            self.fence(row, token)
            kind = await session.scalar(
                text("""UPDATE creation_lab_effects SET state='submitted'
              WHERE id=:id AND run_id=:run AND state='claimed' RETURNING kind"""),
                {"id": operation, "run": run},
            )
            if not kind:
                raise AuthError("CREATION_LAB_EFFECT_FENCED", 409)
            await self.event(session, run, uuid5(operation, "submitted"), f"effect.{kind}_submitted")

    async def received(
        self, actor: UUID, run: UUID, token: UUID, operation: UUID, payload: object, estimate: int | None = None
    ) -> None:
        if estimate is not None and (type(estimate) is not int or estimate < 0):
            raise AuthError("CREATION_LAB_COST_INVALID", 422)
        if len(json.dumps(payload, default=str).encode()) > 48 * 1024 * 1024:
            raise AuthError("CREATION_LAB_TRACE_TOO_LARGE", 409)
        ciphertext = self.cipher.seal({"value": payload})
        async with self.database.transaction(ZERO, actor) as session:
            row = await self.guard(session, actor, run, "admin.creation_lab.effect.receive")
            self.fence(row, token)
            reserved = await session.scalar(
                text("SELECT reserved_usd_micros FROM creation_lab_effects WHERE id=:id AND run_id=:run"),
                {"id": operation, "run": run},
            )
            if reserved is not None and estimate is not None and estimate > reserved:
                # Preserve observed liability even if the provider exceeds its configured reservation.
                await session.execute(
                    text("UPDATE creation_lab_runs SET committed_usd_micros=committed_usd_micros+:extra WHERE id=:run"),
                    {"run": run, "extra": estimate - reserved},
                )
            effect = (
                await session.execute(
                    text("""UPDATE creation_lab_effects
              SET state='received',estimated_usd_micros=:estimate,finished_at=clock_timestamp()
              WHERE id=:id AND run_id=:run AND state IN ('claimed','submitted') RETURNING kind"""),
                    {"id": operation, "run": run, "estimate": estimate},
                )
            ).scalar_one_or_none()
            if effect is None:
                raise AuthError("CREATION_LAB_EFFECT_FENCED", 409)
            trace = uuid5(operation, "response")
            await session.execute(
                text("""INSERT INTO creation_lab_trace(id,run_id,effect_id,stage,slot,payload_ciphertext)
              VALUES(:id,:run,:effect,:stage,'response',:payload)"""),
                {"id": trace, "run": run, "effect": operation, "stage": effect, "payload": ciphertext},
            )
            await self.event(session, run, uuid5(operation, "received"), f"effect.{effect}_received", trace)

            commercial = await session.scalar(
                text("SELECT commercial_reservation_id FROM creation_lab_effects WHERE id=:id"), {"id": operation}
            )
            if commercial:
                from app.services.visual_cost_ledger import _event as cost_event

                await session.execute(
                    text("SELECT pg_advisory_xact_lock(hashtextextended(:key,31))"), {"key": str(row["tenant_id"])}
                )
                reservation = (
                    (
                        await session.execute(
                            text("SELECT * FROM visual_cost_reservations WHERE id=:id FOR UPDATE"), {"id": commercial}
                        )
                    )
                    .mappings()
                    .one()
                )
                old_hold = max(reservation["reserved_usd_micros"], reservation["estimated_usd_micros"] or 0)
                new_hold = max(old_hold, estimate or 0)
                if reservation["provider"] == "openai" and new_hold > old_hold:
                    await session.execute(
                        text("""UPDATE visual_global_monthly_budget SET committed_usd_micros=committed_usd_micros+:delta,updated_at=now()
                      WHERE month=date_trunc('month',CAST(:created AS timestamptz) AT TIME ZONE 'UTC')::date"""),
                        {"delta": new_hold - old_hold, "created": reservation["created_at"]},
                    )
                await session.execute(
                    text(
                        "UPDATE visual_cost_reservations SET state='uncertain',estimated_usd_micros=:estimate,updated_at=now() WHERE id=:id"
                    ),
                    {"id": commercial, "estimate": estimate},
                )
                if new_hold > reservation["reserved_usd_micros"]:
                    await cost_event(session, row["tenant_id"], actor, commercial, "over_reservation")
                await cost_event(session, row["tenant_id"], actor, commercial, "uncertain")
                if isinstance(payload, dict) and effect == "catalog":
                    from app.services.intent_usage import finish_intent

                    await finish_intent(
                        session,
                        tenant=row["tenant_id"],
                        operation=operation,
                        input_tokens=payload.get("input_tokens"),
                        output_tokens=payload.get("output_tokens"),
                        input_rate=self.settings.intent_ai_input_rate_usd_micros,
                        output_rate=0,
                    )
                if effect == "transcription":
                    await session.execute(
                        text("UPDATE audio_transcription_usage SET state='completed' WHERE event_id=:source"),
                        {"source": row["source_event_id"]},
                    )

    async def trace(self, actor: UUID, run: UUID, identifier: UUID) -> dict[str, Any]:
        async with self.database.transaction(ZERO, actor) as session:
            await self.guard(session, actor, run, "admin.creation_lab.trace.read")
            row = (
                (
                    await session.execute(
                        text("""SELECT t.*,
              r.trace_expires_at,
              (r.trace_expires_at IS NOT NULL AND r.trace_expires_at<=clock_timestamp()) AS expired
              FROM creation_lab_trace t JOIN creation_lab_runs r ON r.id=t.run_id
              WHERE t.run_id=:run AND t.id=:id"""),
                        {"run": run, "id": identifier},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise AuthError("CREATION_LAB_TRACE_NOT_FOUND", 404)
            if row["expired"] or row["payload_ciphertext"] is None:
                raise AuthError("CREATION_LAB_TRACE_EXPIRED", 410)
            return {
                "id": identifier,
                "stage": row["stage"],
                "slot": row["slot"],
                "created_at": row["created_at"],
                "payload": self.cipher.open(row["payload_ciphertext"])["value"],
                "expires_at": row["trace_expires_at"],
            }

    async def finish(self, actor: UUID, run: UUID, token: UUID, state: str, failure_code: str | None = None) -> None:
        if state not in {"completed", "failed", "uncertain", "cancelled"}:
            raise AuthError("CREATION_LAB_TERMINAL_STATE_INVALID", 422)
        if failure_code is not None and (not failure_code.isupper() or len(failure_code) > 100):
            raise AuthError("CREATION_LAB_FAILURE_CODE_INVALID", 422)
        async with self.database.transaction(ZERO, actor) as session:
            row = await self.guard(session, actor, run, "admin.creation_lab.run.finish")
            if row["finished_at"] is not None and row["execution_token"] == token:
                return
            self.fence(row, token)
            await self.finish_locked(session, row, state, failure_code)

    async def finish_locked(self, session: AsyncSession, row: Any, state: str, failure_code: str | None = None) -> None:
        actor, run = row["actor_id"], row["id"]
        unresolved = await session.scalar(
            text("""SELECT 1 FROM creation_lab_effects WHERE run_id=:run
          AND (state IN ('submitted','uncertain') OR (state='claimed' AND kind='upload')) LIMIT 1"""),
            {"run": run},
        )
        if unresolved:
            state = "uncertain"
        if row["origin"] == "whatsapp" and state == "completed":
            from app.services.message_creation_delivery import persist_product_result

            await persist_product_result(session, row, self.cipher)
        await session.execute(
            text("""UPDATE creation_lab_runs SET state=:state,failure_code=:code,
          finished_at=clock_timestamp(),trace_expires_at=clock_timestamp()+interval '7 days' WHERE id=:run"""),
            {"run": run, "state": state, "code": failure_code},
        )
        await self.event(session, run, uuid5(run, "terminal"), f"run.{state}")
        await session.execute(
            text("SELECT set_config('app.tenant_id',:tenant,true)"), {"tenant": str(row["tenant_id"])}
        )
        await _event(session, row["tenant_id"], row["business_id"], actor, run, "creation_lab.trace_cleanup_requested")

    async def evidence(
        self,
        actor: UUID,
        run: UUID,
        token: UUID,
        identifier: UUID,
        stage: str,
        value: object,
        *,
        slot: str = "evidence",
        effect: UUID | None = None,
    ) -> None:
        if slot not in {"evidence", "partial"}:
            raise AuthError("CREATION_LAB_TRACE_SLOT_INVALID", 422)
        if len(json.dumps(value, default=str).encode()) > 48 * 1024 * 1024:
            raise AuthError("CREATION_LAB_TRACE_TOO_LARGE", 409)
        async with self.database.transaction(ZERO, actor) as session:
            row = await self.guard(session, actor, run, "admin.creation_lab.trace.record")
            self.fence(row, token)
            await session.execute(
                text("""INSERT INTO creation_lab_trace(id,run_id,stage,slot,effect_id,payload_ciphertext)
              VALUES(:id,:run,:stage,:slot,:effect,:payload)"""),
                {
                    "id": identifier,
                    "run": run,
                    "stage": stage,
                    "slot": slot,
                    "effect": effect,
                    "payload": self.cipher.seal({"value": value}),
                },
            )
            await self.event(
                session,
                run,
                uuid5(identifier, "recorded"),
                "trace.partial" if slot == "partial" else "trace.recorded",
                identifier,
            )
