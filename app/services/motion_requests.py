"""Motion request admission and current-source guards; no provider or storage IO."""

from typing import Any
from uuid import UUID, uuid4, uuid5

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.session import Database
from app.schemas.motion_production import MotionRequest, MotionRequestRead
from app.services.auth import AuthError
from app.services.billing import lock_commercial_change
from app.services.content_pieces import _event
from app.services.editorial_proposals import _access_sql
from app.services.motion_context import MotionContext, digest
from app.services.visual_consent_gate import VisualConsentGate
from app.services.visual_pending_changes import VisualPendingChanges
from app.services.whatsapp_materials import WhatsAppMaterialsService


class MotionRequestService:
    def __init__(self, settings: Settings, database: Database):
        self.settings, self.database = settings, database
        self.context = MotionContext(settings)
        self.gate = VisualConsentGate(database, settings)

    async def list(self, tenant: UUID, business: UUID, actor: UUID) -> list[MotionRequestRead]:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            rows = (
                (
                    await session.execute(
                        text("""SELECT id,operation_id,format,state,piece_id,failure_code
              FROM motion_requests WHERE tenant_id=:tenant AND business_id=:business
              ORDER BY created_at DESC,id DESC LIMIT 30"""),
                        {"tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .all()
            )
            return [MotionRequestRead.model_validate(dict(row)) for row in rows]

    async def get(self, tenant: UUID, business: UUID, actor: UUID, request_id: UUID) -> MotionRequestRead:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            row = await self.row(session, tenant, business, request_id)
            return MotionRequestRead.model_validate({key: row[key] for key in MotionRequestRead.model_fields})

    @staticmethod
    async def row(session: AsyncSession, tenant: UUID, business: UUID, request_id: UUID) -> Any:
        row = (
            (
                await session.execute(
                    text("""SELECT * FROM motion_requests
          WHERE tenant_id=:tenant AND business_id=:business AND id=:id FOR UPDATE"""),
                    {"tenant": tenant, "business": business, "id": request_id},
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise AuthError("MOTION_REQUEST_NOT_FOUND", 404)
        return row

    async def create(self, tenant: UUID, business: UUID, actor: UUID, body: MotionRequest) -> MotionRequestRead:
        self.context.require_qualification(business, body.source_asset_id)
        request_id = uuid5(body.operation_id, f"motion-request:{tenant}:{business}")
        request_hash = digest([tenant, business, actor, body.model_dump(mode="json")])
        async with self.database.transaction(tenant, actor) as session:
            await self.gate._lock(session, tenant, business, actor)
            existing = (
                (
                    await session.execute(
                        text("""SELECT * FROM motion_requests
              WHERE tenant_id=:tenant AND operation_id=:operation"""),
                        {"tenant": tenant, "operation": body.operation_id},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if existing is not None:
                if existing["request_hash"] != request_hash:
                    raise AuthError("MOTION_OPERATION_CONFLICT", 409)
                return MotionRequestRead.model_validate({key: existing[key] for key in MotionRequestRead.model_fields})
            await self._admission(session, tenant, business)
            snapshot = await self.context.capture(session, tenant, business, body)
            await session.execute(
                text("""INSERT INTO motion_requests
              (tenant_id,business_id,id,actor_id,operation_id,request_hash,source_asset_id,format,state,
               snapshot_ciphertext,source_fingerprint,budget_usd_micros,max_corrections)
              VALUES(:tenant,:business,:id,:actor,:operation,:hash,:source,:format,'queued',:snapshot,:fingerprint,
                :budget,:corrections)"""),
                {
                    "tenant": tenant,
                    "business": business,
                    "id": request_id,
                    "actor": actor,
                    "operation": body.operation_id,
                    "hash": request_hash,
                    "source": body.source_asset_id,
                    "format": body.format,
                    "snapshot": self.context.seal(snapshot),
                    "fingerprint": self.context.fingerprint(snapshot),
                    "budget": self.settings.motion_request_budget_usd_micros,
                    "corrections": self.settings.motion_max_corrections,
                },
            )
            await session.execute(
                text("""INSERT INTO motion_request_assets(tenant_id,business_id,request_id,asset_id)
              VALUES(:tenant,:business,:id,:source)"""),
                {"tenant": tenant, "business": business, "id": request_id, "source": body.source_asset_id},
            )
            await _event(session, tenant, business, actor, body.operation_id, "motion.requested")
            row = await self.row(session, tenant, business, request_id)
            return MotionRequestRead.model_validate({key: row[key] for key in MotionRequestRead.model_fields})

    async def _admission(self, session: AsyncSession, tenant: UUID, business: UUID) -> None:
        if not self.settings.motion_execution_ready():
            raise AuthError("MOTION_EXECUTION_NOT_CONFIGURED", 409)
        await lock_commercial_change(session, tenant)
        if not await session.scalar(
            text(_access_sql().replace("now()", "clock_timestamp()")), {"tenant": tenant, "live": False}
        ):
            raise AuthError("PLAN_REQUIRED", 403)
        if await self.gate._state(session, tenant, business) != "active":
            raise AuthError("VISUAL_AI_CONSENT_REQUIRED", 409)
        if await VisualPendingChanges.has_pending_in_session(session, tenant, business):
            raise AuthError("VISUAL_CHANGE_PENDING", 409)

    async def begin(
        self, tenant: UUID, business: UUID, actor: UUID, operation: UUID, event_id: UUID
    ) -> tuple[dict[str, Any], UUID] | None:
        request_id = uuid5(operation, f"motion-request:{tenant}:{business}")
        async with self.database.transaction(tenant, actor) as session:
            await self.gate._lock(session, tenant, business, actor)
            event = await session.scalar(
                text("""SELECT 1 FROM outbox_events WHERE tenant_id=:tenant
              AND id=:event AND event_type='motion.requested' AND payload->>'business_id'=:business
              AND payload->>'actor_id'=:actor AND payload->>'operation_id'=:operation"""),
                {
                    "tenant": tenant,
                    "event": event_id,
                    "business": str(business),
                    "actor": str(actor),
                    "operation": str(operation),
                },
            )
            if event_id != uuid5(operation, "motion.requested") or not event:
                raise AuthError("MOTION_EVENT_MISMATCH", 409)
            row = await self.row(session, tenant, business, request_id)
            if row["actor_id"] != actor:
                raise AuthError("MOTION_OWNER_CHANGED", 409)
            if row["state"] != "queued":
                return None  # Never restart a running/unknown external effect.
            failure = None
            try:
                self.context.require_qualification(business, row["source_asset_id"])
                await self._admission(session, tenant, business)
                await self.current(session, row)
            except AuthError as exc:
                failure = exc
                await session.execute(
                    text("""UPDATE motion_requests SET state='failed',failure_code=:code,
                  finished_at=clock_timestamp() WHERE tenant_id=:tenant AND business_id=:business AND id=:id"""),
                    {"tenant": tenant, "business": business, "id": request_id, "code": exc.code},
                )
                await _event(session, tenant, business, actor, operation, "motion.failed")
            if failure is None:
                token = uuid4()
                await session.execute(
                    text("""UPDATE motion_requests SET state='running',execution_token=:token,
                  admitted_at=clock_timestamp() WHERE tenant_id=:tenant AND business_id=:business AND id=:id"""),
                    {"tenant": tenant, "business": business, "id": request_id, "token": token},
                )
                return dict(row), token
        raise failure

    async def current(self, session: AsyncSession, row: Any) -> None:
        self.context.require_qualification(row["business_id"], row["source_asset_id"])
        snapshot = self.context.open(row["snapshot_ciphertext"])
        current = await self.context.capture(
            session,
            row["tenant_id"],
            row["business_id"],
            MotionRequest.model_validate(snapshot["request"]),
            previous=snapshot,
        )
        if self.context.fingerprint(current) != row["source_fingerprint"]:
            raise AuthError("MOTION_CONTEXT_CHANGED", 409)
        blocked = await session.scalar(
            text("""SELECT EXISTS(SELECT 1 FROM billing_accounts
          WHERE tenant_id=:tenant AND blocked) OR EXISTS(SELECT 1 FROM billing_sponsorships
          WHERE tenant_id=:tenant AND revoked_at IS NOT NULL AND revoked_at>=:admitted)"""),
            {"tenant": row["tenant_id"], "admitted": row["admitted_at"]},
        )
        if blocked:
            raise AuthError("MOTION_ACCESS_REVOKED", 409)

    async def locked_running(self, session: AsyncSession, row: dict[str, Any], token: UUID) -> Any:
        await self.gate._lock(session, row["tenant_id"], row["business_id"], row["actor_id"])
        current = await self.row(session, row["tenant_id"], row["business_id"], row["id"])
        if current["state"] != "running" or current["execution_token"] != token:
            raise AuthError("MOTION_EXECUTION_FENCED", 409)
        await lock_commercial_change(session, row["tenant_id"])
        await self.current(session, current)
        return current
