"""Versioned context; only explicit owner edits become confirmed facts."""

import hashlib
import json
from typing import Any
from uuid import UUID

from sqlalchemy import text

from app.db.session import Database
from app.schemas.editorial_context import ContextContent, ContextHistoryItem, ContextRead, ContextRestore, ContextUpdate
from app.services.auth import AuthError
from app.services.whatsapp_materials import WhatsAppMaterialsService


def _digest(content: ContextContent | ContextRestore) -> str:
    encoded = json.dumps(content.model_dump(mode="json"), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


class EditorialContextService:
    def __init__(self, database: Database) -> None:
        self.database = database

    @staticmethod
    async def _owner(session: Any, tenant: UUID, business: UUID, actor: UUID) -> None:
        await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)

    @staticmethod
    def _present(row: Any) -> ContextRead:
        if row is None:
            return ContextRead(version=0)
        return ContextRead.model_validate(
            {**row["document"], "version": row["version"], "updated_at": row["created_at"]}
        )

    @staticmethod
    async def _version(session: Any, tenant: UUID, business: UUID, version: int | None = None) -> Any:
        return (
            (
                await session.execute(
                    text("""SELECT version,document,created_at FROM business_context_versions
                  WHERE tenant_id=:tenant AND business_id=:business
                    AND version=coalesce(:version,(SELECT version FROM business_context_heads
                      WHERE tenant_id=:tenant AND business_id=:business))"""),
                    {"tenant": tenant, "business": business, "version": version},
                )
            )
            .mappings()
            .one_or_none()
        )

    async def read(self, tenant: UUID, business: UUID, actor: UUID, version: int | None = None) -> ContextRead:
        async with self.database.transaction(tenant, actor) as session:
            await self._owner(session, tenant, business, actor)
            row = await self._version(session, tenant, business, version)
            if version is not None and row is None:
                raise AuthError("CONTEXT_VERSION_NOT_FOUND", 404)
            return self._present(row)

    async def history(self, tenant: UUID, business: UUID, actor: UUID) -> list[ContextHistoryItem]:
        async with self.database.transaction(tenant, actor) as session:
            await self._owner(session, tenant, business, actor)
            rows = (
                (
                    await session.execute(
                        text("""SELECT version,created_at,actor_id FROM business_context_versions
                  WHERE tenant_id=:tenant AND business_id=:business ORDER BY version DESC LIMIT 20"""),
                        {"tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .all()
            )
            return [ContextHistoryItem.model_validate(row) for row in rows]

    @staticmethod
    async def _replay(session: Any, tenant: UUID, business: UUID, operation: UUID, digest: str) -> ContextRead | None:
        row = (
            (
                await session.execute(
                    text("""SELECT version,document,created_at,request_hash FROM business_context_versions
              WHERE tenant_id=:tenant AND business_id=:business AND operation_id=:operation"""),
                    {"tenant": tenant, "business": business, "operation": operation},
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        if row["request_hash"] != digest:
            raise AuthError("CONTEXT_OPERATION_CONFLICT", 409)
        return EditorialContextService._present(row)

    async def _save(
        self,
        session: Any,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        expected: int,
        operation: UUID,
        digest: str,
        content: ContextContent,
    ) -> ContextRead:
        replay = await self._replay(session, tenant, business, operation, digest)
        if replay is not None:
            return replay
        await session.execute(
            text("""INSERT INTO business_context_heads(tenant_id,business_id)
              VALUES(:tenant,:business) ON CONFLICT DO NOTHING"""),
            {"tenant": tenant, "business": business},
        )
        version = await session.scalar(
            text("""UPDATE business_context_heads SET version=version+1
              WHERE tenant_id=:tenant AND business_id=:business AND version=:expected RETURNING version"""),
            {"tenant": tenant, "business": business, "expected": expected},
        )
        if version is None:
            replay = await self._replay(session, tenant, business, operation, digest)
            if replay is not None:
                return replay
            raise AuthError("CONTEXT_VERSION_CONFLICT", 409)
        document = content.model_dump(mode="json")
        row = (
            (
                await session.execute(
                    text("""INSERT INTO business_context_versions
              (tenant_id,business_id,version,operation_id,actor_id,request_hash,document)
              VALUES(:tenant,:business,:version,:operation,:actor,:digest,CAST(:document AS jsonb))
              RETURNING version,document,created_at"""),
                    {
                        "tenant": tenant,
                        "business": business,
                        "version": version,
                        "operation": operation,
                        "actor": actor,
                        "digest": digest,
                        "document": json.dumps(document, ensure_ascii=False),
                    },
                )
            )
            .mappings()
            .one()
        )
        await session.execute(
            text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
              VALUES(:tenant,:actor,:operation,'editorial.context_updated',:business)"""),
            {"tenant": tenant, "actor": actor, "operation": operation, "business": business},
        )
        return self._present(row)

    async def update(self, tenant: UUID, business: UUID, actor: UUID, payload: ContextUpdate) -> ContextRead:
        content = ContextContent.model_validate(payload.model_dump(exclude={"expected_version", "operation_id"}))
        async with self.database.transaction(tenant, actor) as session:
            await self._owner(session, tenant, business, actor)
            return await self._save(
                session,
                tenant,
                business,
                actor,
                payload.expected_version,
                payload.operation_id,
                _digest(payload),
                content,
            )

    async def restore(self, tenant: UUID, business: UUID, actor: UUID, payload: ContextRestore) -> ContextRead:
        async with self.database.transaction(tenant, actor) as session:
            await self._owner(session, tenant, business, actor)
            replay = await self._replay(session, tenant, business, payload.operation_id, _digest(payload))
            if replay is not None:
                return replay
            source = await self._version(session, tenant, business, payload.target_version)
            if source is None:
                raise AuthError("CONTEXT_VERSION_NOT_FOUND", 404)
            content = ContextContent.model_validate(source["document"])
            return await self._save(
                session,
                tenant,
                business,
                actor,
                payload.expected_version,
                payload.operation_id,
                _digest(payload),
                content,
            )
