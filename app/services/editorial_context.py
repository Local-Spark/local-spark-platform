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
            current = self._present(row)
            if version is None:
                from app.services.visual_pending_changes import VisualPendingChanges

                pending = await VisualPendingChanges.status_in_session(session, tenant, business, "context")
                if pending:
                    return ContextRead.model_validate({**current.model_dump(), "pending_change": pending})
            return current

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

    @staticmethod
    async def _save(
        session: Any,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        expected: int,
        operation: UUID,
        digest: str,
        content: ContextContent,
    ) -> ContextRead:
        replay = await EditorialContextService._replay(session, tenant, business, operation, digest)
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
            replay = await EditorialContextService._replay(session, tenant, business, operation, digest)
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
        return EditorialContextService._present(row)

    @staticmethod
    async def apply_pending_in_session(session: Any, tenant: UUID, business: UUID, row: Any) -> None:
        payload: ContextUpdate | ContextRestore
        if row["kind"] == "context_update":
            payload = ContextUpdate.model_validate(row["payload"])
            content = ContextContent.model_validate(payload.model_dump(exclude={"expected_version", "operation_id"}))
        else:
            payload = ContextRestore.model_validate(row["payload"])
            source = await EditorialContextService._version(session, tenant, business, payload.target_version)
            if source is None:
                raise AuthError("CONTEXT_VERSION_NOT_FOUND", 404)
            content = ContextContent.model_validate(source["document"])
        if payload.operation_id != row["operation_id"] or _digest(payload) != row["request_hash"]:
            raise AuthError("VISUAL_CHANGE_OPERATION_CONFLICT", 409)
        await EditorialContextService._save(
            session,
            tenant,
            business,
            row["actor_id"],
            payload.expected_version,
            payload.operation_id,
            row["request_hash"],
            content,
        )

    async def _queue_or_save(
        self,
        session: Any,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        payload: ContextUpdate | ContextRestore,
        content: ContextContent,
        kind: str,
    ) -> ContextRead:
        from app.services.visual_pending_changes import VisualPendingChanges

        digest = _digest(payload)
        replay = await self._replay(session, tenant, business, payload.operation_id, digest)
        if replay is not None:
            return replay
        # This lock serializes the version check with run admission and edits.
        from app.services.visual_consent_gate import VisualConsentGate

        await VisualConsentGate._lock(session, tenant, business, actor)
        replay = await self._replay(session, tenant, business, payload.operation_id, digest)
        if replay is not None:
            return replay
        current = self._present(await self._version(session, tenant, business))
        if current.version != payload.expected_version:
            raise AuthError("CONTEXT_VERSION_CONFLICT", 409)
        deferred = await VisualPendingChanges.enqueue_in_session(
            session,
            tenant,
            business,
            actor,
            payload.operation_id,
            kind,
            "context",
            digest,
            payload.model_dump(mode="json"),
        )
        if deferred:
            return ContextRead.model_validate(
                {**current.model_dump(), "pending_change": {"operation_id": payload.operation_id, "status": "pending"}}
            )
        return await self._save(
            session, tenant, business, actor, payload.expected_version, payload.operation_id, digest, content
        )

    async def update(self, tenant: UUID, business: UUID, actor: UUID, payload: ContextUpdate) -> ContextRead:
        content = ContextContent.model_validate(payload.model_dump(exclude={"expected_version", "operation_id"}))
        async with self.database.transaction(tenant, actor) as session:
            await self._owner(session, tenant, business, actor)
            return await self._queue_or_save(session, tenant, business, actor, payload, content, "context_update")

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
            return await self._queue_or_save(session, tenant, business, actor, payload, content, "context_restore")
