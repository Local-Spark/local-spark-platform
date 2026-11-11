"""Durable owner changes serialized with visual admissions, for the simulated flow."""

import json
from typing import Any
from uuid import UUID

from sqlalchemy import text

from app.services.auth import AuthError


class VisualPendingChanges:
    @staticmethod
    async def require_change_author_in_session(
        session: Any, tenant: UUID, business: UUID, actor: UUID, resource_key: str
    ) -> None:
        """Never transfer an unresolved command to another owner's identity.

        Owner RLS cannot inspect another user's account or membership. Keep that
        command blocked for restricted staff recovery rather than guessing that
        its author still has access.
        """
        author = await session.scalar(
            text("""SELECT actor_id FROM business_visual_pending_changes
              WHERE tenant_id=:tenant AND business_id=:business AND resource_key=:resource
                AND state IN ('pending','failed')"""),
            {"tenant": tenant, "business": business, "resource": resource_key},
        )
        if author not in (None, actor):
            raise AuthError("VISUAL_CHANGE_STAFF_REQUIRED", 409)

    @staticmethod
    async def has_pending_in_session(session: Any, tenant: UUID, business: UUID) -> bool:
        return bool(
            await session.scalar(
                text("""SELECT 1 FROM business_visual_pending_changes
          WHERE tenant_id=:tenant AND business_id=:business AND state IN ('pending','failed') LIMIT 1"""),
                {"tenant": tenant, "business": business},
            )
        )

    @staticmethod
    async def status_in_session(session: Any, tenant: UUID, business: UUID, resource_key: str) -> dict[str, Any] | None:
        row = (
            (
                await session.execute(
                    text("""SELECT operation_id,state,error_code FROM business_visual_pending_changes
              WHERE tenant_id=:tenant AND business_id=:business AND resource_key=:resource
                AND state IN ('pending','failed')"""),
                    {"tenant": tenant, "business": business, "resource": resource_key},
                )
            )
            .mappings()
            .one_or_none()
        )
        return (
            {"operation_id": row["operation_id"], "status": row["state"], "error_code": row["error_code"]}
            if row
            else None
        )

    @staticmethod
    async def enqueue_in_session(
        session: Any,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        operation: UUID,
        kind: str,
        resource_key: str,
        digest: str,
        payload: dict[str, Any],
        *,
        reserve: bool = False,
    ) -> bool:
        from app.services.visual_consent_gate import VisualConsentGate

        await VisualConsentGate._lock(session, tenant, business, actor)
        params = {
            "tenant": tenant,
            "business": business,
            "actor": actor,
            "operation": operation,
            "kind": kind,
            "resource": resource_key,
            "digest": digest,
        }
        old = (
            (
                await session.execute(
                    text("""SELECT actor_id,kind,resource_key,request_hash,state FROM business_visual_pending_changes
              WHERE tenant_id=:tenant AND business_id=:business AND operation_id=:operation"""),
                    params,
                )
            )
            .mappings()
            .one_or_none()
        )
        if old:
            if (old["actor_id"], old["kind"], old["resource_key"], old["request_hash"]) != (
                actor,
                kind,
                resource_key,
                digest,
            ):
                raise AuthError("VISUAL_CHANGE_OPERATION_CONFLICT", 409)
            if old["state"] in {"failed", "cancelled"}:
                raise AuthError("VISUAL_CHANGE_FAILED", 409)
            return bool(old["state"] == "pending")
        status = await VisualPendingChanges.status_in_session(session, tenant, business, resource_key)
        if status and status["status"] == "pending":
            raise AuthError("VISUAL_CHANGE_ALREADY_PENDING", 409)
        if status:
            await VisualPendingChanges.require_change_author_in_session(session, tenant, business, actor, resource_key)
            await session.execute(
                text("""UPDATE business_visual_pending_changes
              SET state='cancelled',finished_at=clock_timestamp()
              WHERE tenant_id=:tenant AND business_id=:business AND resource_key=:resource AND state='failed'"""),
                params,
            )
            await VisualConsentGate._audit(session, tenant, business, actor, "visual.change_superseded")
        count = await session.scalar(
            text("""SELECT count(*) FROM creative_active_runs
          WHERE tenant_id=:tenant AND business_id=:business AND state='in_flight'"""),
            params,
        )
        deferred = reserve or bool(count)
        await session.execute(
            text("""INSERT INTO business_visual_pending_changes
          (tenant_id,business_id,actor_id,operation_id,kind,resource_key,request_hash,payload,state,finished_at)
          VALUES(:tenant,:business,:actor,:operation,:kind,:resource,:digest,CAST(:payload AS jsonb),
            :state,CASE WHEN :deferred THEN NULL ELSE clock_timestamp() END)"""),
            {
                **params,
                "payload": json.dumps(payload, ensure_ascii=False),
                "state": "pending" if deferred else "completed",
                "deferred": deferred,
            },
        )
        await VisualConsentGate._audit(session, tenant, business, actor, "visual.change_requested")
        return deferred

    @staticmethod
    async def apply_pending_in_session(session: Any, tenant: UUID, business: UUID) -> None:
        """Apply the validated commands in order within the last run's transaction."""
        from app.services.visual_consent_gate import VisualConsentGate

        params = {"tenant": tenant, "business": business}
        active = await session.scalar(
            text("""SELECT count(*) FROM creative_active_runs
          WHERE tenant_id=:tenant AND business_id=:business AND state='in_flight'"""),
            params,
        )
        if active:
            return
        rows = (
            (
                await session.execute(
                    text("""SELECT * FROM business_visual_pending_changes
          WHERE tenant_id=:tenant AND business_id=:business AND state='pending'
          ORDER BY requested_at,operation_id FOR UPDATE"""),
                    params,
                )
            )
            .mappings()
            .all()
        )
        for row in rows:
            if row["kind"] in {"script_edit", "script_review"}:
                # Script application locks proposal before visual in a separate
                # transaction. Never invert that order from this visual gate.
                break
            if row["kind"] == "photo_create":
                photo = await session.scalar(
                    text("""SELECT version FROM business_collection_photos WHERE tenant_id=:tenant
                      AND business_id=:business AND id=:photo AND state='pending'"""),
                    {**params, "photo": UUID(row["payload"]["photo_id"])},
                )
                if photo == 0:
                    # The upload still runs outside this transaction. Preserve command order.
                    break
            try:
                async with session.begin_nested():
                    from app.services.whatsapp_materials import WhatsAppMaterialsService

                    await WhatsAppMaterialsService._require_owner(session, tenant, business, row["actor_id"])
                    if row["kind"] in {"context_update", "context_restore"}:
                        from app.services.editorial_context import EditorialContextService

                        await EditorialContextService.apply_pending_in_session(session, tenant, business, row)
                    elif row["kind"] == "catalog_update":
                        from app.services.business_catalog import BusinessCatalogService

                        await BusinessCatalogService.apply_pending_in_session(session, tenant, business, row)
                    elif row["kind"] in {"kit_confirm", "photo_create", "photo_delete", "photo_update"}:
                        from app.services.visual_pending_media import (
                            apply_kit_pending_in_session,
                            apply_photo_pending_in_session,
                        )

                        handler = (
                            apply_kit_pending_in_session
                            if row["kind"] == "kit_confirm"
                            else apply_photo_pending_in_session
                        )
                        await handler(session, tenant, business, row["actor_id"], row["kind"], row["payload"])
                    else:
                        raise AuthError("VISUAL_CHANGE_KIND_INVALID", 409)
            except AuthError as exc:
                await session.execute(
                    text("""UPDATE business_visual_pending_changes SET state='failed',
                  error_code=:error,finished_at=clock_timestamp() WHERE tenant_id=:tenant AND business_id=:business
                  AND operation_id=:operation AND state='pending'"""),
                    {**params, "operation": row["operation_id"], "error": exc.code},
                )
                await VisualConsentGate._audit(session, tenant, business, row["actor_id"], "visual.change_failed")
                continue
            await session.execute(
                text("""UPDATE business_visual_pending_changes SET state='completed',
              finished_at=clock_timestamp() WHERE tenant_id=:tenant AND business_id=:business
              AND operation_id=:operation AND state='pending'"""),
                {**params, "operation": row["operation_id"]},
            )
            await VisualConsentGate._audit(session, tenant, business, row["actor_id"], "visual.change_applied")
