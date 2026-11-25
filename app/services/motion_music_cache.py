"""RLS-scoped encrypted cache and conservative UTC monthly Music holds."""

from typing import Any
from uuid import UUID, uuid5

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth import AuthError
from app.services.motion_effects import MotionEffects


class MusicCache:
    def __init__(self, effects: MotionEffects):
        self.effects = effects

    async def event(self, session: AsyncSession, row: dict[str, Any], operation: UUID, action: str) -> None:
        params = {
            "tenant": row["tenant_id"],
            "actor": row["actor_id"],
            "business": row["business_id"],
            "operation": operation,
            "action": "motion.music_" + action,
            "event": uuid5(operation, action),
        }
        await session.execute(
            text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(:tenant,:actor,:operation,:action,:business)"""),
            params,
        )
        await session.execute(
            text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
          VALUES(:event,:tenant,:action,jsonb_build_object('operation_id',CAST(CAST(:operation AS uuid) AS text)))"""),
            params,
        )

    async def select(
        self,
        row: dict[str, Any],
        token: UUID,
        operation: UUID,
        key: str,
        reserve: int,
        *,
        restore: bool,
        existing_only: bool = False,
    ) -> tuple[dict[str, Any] | None, bool]:
        requests = self.effects.requests
        params = {
            "tenant": row["tenant_id"],
            "business": row["business_id"],
            "actor": row["actor_id"],
            "operation": operation,
            "key": key,
            "reserve": reserve,
        }
        async with requests.database.transaction(row["tenant_id"], row["actor_id"]) as session:
            await requests.locked_running(session, row, token)
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:scope, 73))"), {"scope": str(row["tenant_id"])}
            )
            existing = (
                (
                    await session.execute(
                        text("""SELECT result_ciphertext FROM motion_music
              WHERE tenant_id=:tenant AND operation_id=:operation"""),
                        params,
                    )
                )
                .mappings()
                .one_or_none()
            )
            if existing is not None:
                if existing["result_ciphertext"] is None:
                    raise AuthError("MOTION_MUSIC_OUTCOME_UNCERTAIN", 409)
                return requests.context.open(existing["result_ciphertext"]), False
            if restore:
                return None, False
            cached = await session.scalar(
                text("""SELECT result_ciphertext FROM motion_music
              WHERE tenant_id=:tenant AND business_id=:business AND cache_key=:key
              AND ready ORDER BY created_at,operation_id LIMIT 1"""),
                params,
            )
            if cached is None and existing_only:
                cached = requests.context.seal({"status": "no_eligible_music"})
            if cached is None:
                used = await session.scalar(
                    text("""SELECT coalesce(sum(reserved_usd_micros),0) FROM motion_music
                  WHERE tenant_id=:tenant
                  AND created_at>=date_trunc('month',now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'"""),
                    params,
                )
                if used + reserve > requests.settings.elevenlabs_music_monthly_budget_usd_micros:
                    return None, False
            params.update(
                reserve=0 if cached else reserve,
                result=cached,
                ready=bool(cached and requests.context.open(cached)["status"] == "ready"),
            )
            await session.execute(
                text("""INSERT INTO motion_music
              (tenant_id,business_id,actor_id,operation_id,cache_key,reserved_usd_micros,result_ciphertext,ready)
              VALUES(:tenant,:business,:actor,:operation,:key,:reserve,:result,:ready)"""),
                params,
            )
            await self.event(session, row, operation, "ready" if cached else "reserved")
            return (requests.context.open(cached), False) if cached else (None, True)

    async def save(self, row: dict[str, Any], token: UUID, operation: UUID, result: dict[str, Any]) -> None:
        requests = self.effects.requests
        ciphertext = requests.context.seal(result)
        async with requests.database.transaction(row["tenant_id"], row["actor_id"]) as session:
            await requests.locked_running(session, row, token)
            changed = await session.scalar(
                text("""UPDATE motion_music SET result_ciphertext=:result,ready=:ready
              WHERE tenant_id=:tenant AND operation_id=:operation AND result_ciphertext IS NULL RETURNING 1"""),
                {
                    "tenant": row["tenant_id"],
                    "operation": operation,
                    "result": ciphertext,
                    "ready": result["status"] == "ready",
                },
            )
            if not changed:
                raise AuthError("MOTION_MUSIC_CACHE_FENCED", 409)
            await self.event(session, row, operation, "ready")
