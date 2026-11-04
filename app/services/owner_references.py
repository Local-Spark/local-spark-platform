"""Record owner indications without fetching or endorsing external content."""

import hashlib
import json
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text

from app.db.session import Database
from app.schemas.owner_references import ReferenceCreate, ReferenceRead
from app.services.auth import AuthError
from app.services.whatsapp_materials import WhatsAppMaterialsService


def _request_hash(action: str, values: dict[str, Any]) -> str:
    data = json.dumps({"action": action, **values}, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(data.encode()).hexdigest()


def _present(row: Any) -> ReferenceRead:
    handle = row["instagram_handle"]
    return ReferenceRead(
        id=row["id"],
        instagram_handle=handle,
        instagram_url=f"https://www.instagram.com/{handle}/",
        note=row["note"],
        created_at=row["created_at"],
    )


class OwnerReferencesService:
    def __init__(self, database: Database) -> None:
        self.database = database

    @staticmethod
    async def _claim(session: Any, tenant: UUID, business: UUID, operation: UUID, reference: UUID, digest: str) -> bool:
        created = await session.scalar(
            text("""INSERT INTO owner_reference_operations
          (tenant_id,business_id,operation_id,reference_id,request_hash)
          VALUES(:tenant,:business,:operation,:reference,:digest)
          ON CONFLICT DO NOTHING RETURNING operation_id"""),
            {"tenant": tenant, "business": business, "operation": operation, "reference": reference, "digest": digest},
        )
        if created is not None:
            return True
        existing = (
            (
                await session.execute(
                    text("""SELECT reference_id,request_hash FROM owner_reference_operations
          WHERE tenant_id=:tenant AND business_id=:business AND operation_id=:operation"""),
                    {"tenant": tenant, "business": business, "operation": operation},
                )
            )
            .mappings()
            .one()
        )
        if existing["request_hash"] != digest:
            raise AuthError("REFERENCE_OPERATION_CONFLICT", 409)
        return False

    async def list(self, tenant: UUID, business: UUID, actor: UUID) -> list[ReferenceRead]:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            rows = (
                (
                    await session.execute(
                        text("""SELECT id,instagram_handle,note,created_at FROM owner_references
              WHERE tenant_id=:tenant AND business_id=:business AND removed_at IS NULL
              ORDER BY created_at,id"""),
                        {"tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .all()
            )
            return [_present(row) for row in rows]

    async def create(self, tenant: UUID, business: UUID, actor: UUID, payload: ReferenceCreate) -> ReferenceRead:
        digest = _request_hash("create", {"instagram": payload.instagram, "note": payload.note})
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            await session.scalar(
                text("SELECT public.reference_learning_selection_lock(:business)"), {"business": business}
            )
            reference = uuid4()
            if not await self._claim(session, tenant, business, payload.operation_id, reference, digest):
                replay_row = (
                    (
                        await session.execute(
                            text("""SELECT r.id,r.instagram_handle,r.note,r.created_at
                  FROM owner_reference_operations o JOIN owner_references r
                    ON (r.tenant_id,r.business_id,r.id)=(o.tenant_id,o.business_id,o.reference_id)
                  WHERE o.tenant_id=:tenant AND o.business_id=:business AND o.operation_id=:operation"""),
                            {"tenant": tenant, "business": business, "operation": payload.operation_id},
                        )
                    )
                    .mappings()
                    .one()
                )
                return _present(replay_row)
            row = (
                (
                    await session.execute(
                        text("""INSERT INTO owner_references
              (id,tenant_id,business_id,actor_id,instagram_handle,note)
              VALUES(:id,:tenant,:business,:actor,:handle,:note)
              ON CONFLICT (tenant_id,business_id,instagram_handle) WHERE removed_at IS NULL DO NOTHING
              RETURNING id,instagram_handle,note,created_at"""),
                        {
                            "id": reference,
                            "tenant": tenant,
                            "business": business,
                            "actor": actor,
                            "handle": payload.instagram,
                            "note": payload.note,
                        },
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise AuthError("REFERENCE_ALREADY_EXISTS", 409)
            await self._audit(session, tenant, business, actor, payload.operation_id, reference, "reference.created")
            await session.scalar(
                text("SELECT public.reference_sync_learning_selection(:business,:operation)"),
                {"business": business, "operation": payload.operation_id},
            )
            return _present(row)

    async def remove(self, tenant: UUID, business: UUID, actor: UUID, reference: UUID, operation: UUID) -> None:
        digest = _request_hash("remove", {"reference_id": str(reference)})
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            await session.scalar(
                text("SELECT public.reference_learning_selection_lock(:business)"), {"business": business}
            )
            if not await self._claim(session, tenant, business, operation, reference, digest):
                return
            deleted = await session.scalar(
                text("""UPDATE owner_references SET removed_at=now()
              WHERE tenant_id=:tenant AND business_id=:business AND id=:reference AND removed_at IS NULL
              RETURNING id"""),
                {"tenant": tenant, "business": business, "reference": reference},
            )
            if deleted is None:
                raise AuthError("REFERENCE_NOT_FOUND", 404)
            await self._audit(session, tenant, business, actor, operation, reference, "reference.removed")
            await session.scalar(
                text("SELECT public.reference_sync_learning_selection(:business,:operation)"),
                {"business": business, "operation": operation},
            )

    @staticmethod
    async def _audit(
        session: Any, tenant: UUID, business: UUID, actor: UUID, operation: UUID, reference: UUID, action: str
    ) -> None:
        await session.execute(
            text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(:tenant,:actor,:operation,:action,:reference)"""),
            {"tenant": tenant, "actor": actor, "operation": operation, "action": action, "reference": reference},
        )
        # Events are intentionally held pending until an explicit reference consumer exists.
        await session.execute(
            text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
              VALUES(:id,:tenant,:action,CAST(:payload AS jsonb))"""),
            {
                "id": uuid4(),
                "tenant": tenant,
                "action": action,
                "payload": json.dumps(
                    {
                        "business_id": str(business),
                        "actor_id": str(actor),
                        "operation_id": str(operation),
                        "reference_id": str(reference),
                    }
                ),
            },
        )
