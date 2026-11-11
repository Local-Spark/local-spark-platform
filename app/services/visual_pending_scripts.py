"""Apply queued script changes after visual runs, in proposal -> visual order."""

from typing import Any
from uuid import UUID

from sqlalchemy import text

from app.core.config import Settings
from app.db.session import Database
from app.schemas.editorial_proposals import ScriptEdit, ScriptReview
from app.services.auth import AuthError


async def script_change_status(session: Any, tenant: UUID, business: UUID, proposal: UUID) -> dict[str, Any] | None:
    from app.services.visual_pending_changes import VisualPendingChanges

    return await VisualPendingChanges.status_in_session(session, tenant, business, f"script:{proposal}")


async def require_script_change_slot(
    session: Any, tenant: UUID, business: UUID, actor: UUID, proposal: UUID, operation: UUID, kind: str, digest: str
) -> None:
    """Preserve replay while refusing commands behind another pending source."""
    params = {"tenant": tenant, "business": business, "operation": operation, "resource": f"script:{proposal}"}
    previous = (
        (
            await session.execute(
                text("""SELECT actor_id,kind,resource_key,request_hash FROM business_visual_pending_changes
                  WHERE tenant_id=:tenant AND business_id=:business AND operation_id=:operation"""),
                params,
            )
        )
        .mappings()
        .one_or_none()
    )
    if previous is not None:
        if (previous["actor_id"], previous["kind"], previous["resource_key"], previous["request_hash"]) != (
            actor,
            kind,
            params["resource"],
            digest,
        ):
            raise AuthError("VISUAL_CHANGE_OPERATION_CONFLICT", 409)
        return
    if await session.scalar(
        text("""SELECT 1 FROM business_visual_pending_changes WHERE tenant_id=:tenant AND business_id=:business
          AND resource_key<>:resource AND state IN ('pending','failed') LIMIT 1"""),
        params,
    ):
        raise AuthError("VISUAL_CHANGE_PENDING", 409)


async def apply_pending_script_changes(
    settings: Settings, database: Database, tenant: UUID, business: UUID, actor: UUID
) -> None:
    """Drain this author's script commands without taking proposal after visual.

    A different author's command is preserved. Their next authorized read can
    resume application; losing access requires the separately deferred staff flow.
    Never transfer the transaction's actor identity to process another owner.
    """
    from app.services.editorial_proposals import EditorialProposalService
    from app.services.visual_consent_gate import VisualConsentGate
    from app.services.visual_pending_changes import VisualPendingChanges
    from app.services.whatsapp_materials import WhatsAppMaterialsService

    params = {"tenant": tenant, "business": business}
    while True:
        async with database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            command = (
                (
                    await session.execute(
                        text("""SELECT * FROM business_visual_pending_changes
                          WHERE tenant_id=:tenant AND business_id=:business AND state='pending'
                          ORDER BY requested_at,operation_id LIMIT 1"""),
                        params,
                    )
                )
                .mappings()
                .one_or_none()
            )
        if command is None or command["kind"] not in {"script_edit", "script_review"} or command["actor_id"] != actor:
            return
        proposal = UUID(command["payload"]["proposal_id"])
        async with database.transaction(tenant, actor) as session:
            # The proposal row is acquired before the visual gate, even when
            # this helper is called after the final run has committed its finish.
            await session.execute(
                text("""SELECT id FROM editorial_proposals WHERE tenant_id=:tenant
                  AND business_id=:business AND id=:proposal FOR UPDATE"""),
                {**params, "proposal": proposal},
            )
            await VisualConsentGate._lock(session, tenant, business, actor)
            if await session.scalar(
                text("""SELECT 1 FROM creative_active_runs WHERE tenant_id=:tenant AND business_id=:business
                  AND state='in_flight' LIMIT 1"""),
                params,
            ):
                return
            current = (
                (
                    await session.execute(
                        text("""SELECT * FROM business_visual_pending_changes
                          WHERE tenant_id=:tenant AND business_id=:business AND state='pending'
                          ORDER BY requested_at,operation_id LIMIT 1 FOR UPDATE"""),
                        params,
                    )
                )
                .mappings()
                .one_or_none()
            )
            if current is None or current["operation_id"] != command["operation_id"]:
                continue
            service = EditorialProposalService(settings, database)
            error: str | None
            try:
                async with session.begin_nested():
                    if current["kind"] == "script_edit":
                        await service._edit_script_in_session(
                            session,
                            tenant,
                            business,
                            actor,
                            proposal,
                            ScriptEdit.model_validate(current["payload"]["body"]),
                            enqueue=False,
                        )
                    else:
                        version = await session.scalar(
                            text("SELECT script_version FROM editorial_proposals WHERE id=:proposal"),
                            {"proposal": proposal},
                        )
                        if version != current["payload"]["expected_version"]:
                            raise AuthError("SCRIPT_VERSION_CONFLICT", 409)
                        await service._review_script_in_session(
                            session,
                            tenant,
                            business,
                            actor,
                            proposal,
                            ScriptReview.model_validate(current["payload"]["body"]),
                            enqueue=False,
                        )
            except AuthError as exc:
                state, error = "failed", exc.code
            else:
                state, error = "completed", None
            await session.execute(
                text("""UPDATE business_visual_pending_changes SET state=:state,error_code=:error,
                  finished_at=clock_timestamp() WHERE tenant_id=:tenant AND business_id=:business
                  AND operation_id=:operation AND state='pending'"""),
                {**params, "operation": command["operation_id"], "state": state, "error": error},
            )
            await VisualConsentGate._audit(
                session, tenant, business, actor, f"visual.change_{'applied' if error is None else 'failed'}"
            )
            # Commands that do not touch the proposal may follow this script.
            # Their dispatcher must stop again before the next script command.
            await VisualPendingChanges.apply_pending_in_session(session, tenant, business)
