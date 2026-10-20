"""A complete transactional slice: membership, business, idempotency, audit and outbox."""

import hashlib
import json
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.business import BusinessCreate, BusinessCreated, BusinessPage, BusinessRead


class AccessDenied(Exception):
    pass


class IdempotencyConflict(Exception):
    pass


def fingerprint(payload: BusinessCreate) -> str:
    encoded = json.dumps(payload.model_dump(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode()).hexdigest()


async def require_member(session: AsyncSession, tenant_id: UUID, actor_id: UUID, *, write: bool = False) -> None:
    role = await session.scalar(
        text("SELECT role FROM memberships WHERE tenant_id = :tenant AND actor_id = :actor AND active"),
        {"tenant": tenant_id, "actor": actor_id},
    )
    if role is None or (write and role not in {"owner", "editor"}):
        raise AccessDenied


async def create_business(
    session: AsyncSession,
    tenant_id: UUID,
    actor_id: UUID,
    key: str,
    payload: BusinessCreate,
) -> BusinessCreated:
    await require_member(session, tenant_id, actor_id, write=True)
    operation_id, business_id, event_id = uuid4(), uuid4(), uuid4()
    scope = f"{actor_id}:POST:/api/v1/businesses"
    digest = fingerprint(payload)
    inserted = await session.scalar(
        text("""INSERT INTO idempotency_records
          (tenant_id, scope, key, request_hash, operation_id)
          VALUES (:tenant, :scope, :key, :hash, :operation)
          ON CONFLICT (tenant_id, scope, key) DO NOTHING RETURNING operation_id"""),
        {"tenant": tenant_id, "scope": scope, "key": key, "hash": digest, "operation": operation_id},
    )
    if inserted is None:
        previous = (
            (
                await session.execute(
                    text(
                        "SELECT request_hash, response FROM idempotency_records "
                        "WHERE tenant_id=:tenant AND scope=:scope AND key=:key"
                    ),
                    {"tenant": tenant_id, "scope": scope, "key": key},
                )
            )
            .mappings()
            .one()
        )
        if previous["request_hash"] != digest:
            raise IdempotencyConflict
        return BusinessCreated.model_validate({**previous["response"], "replayed": True})

    row = (
        (
            await session.execute(
                text("""INSERT INTO businesses (id, tenant_id, name, timezone)
             VALUES (:id, :tenant, :name, :timezone) RETURNING *"""),
                {"id": business_id, "tenant": tenant_id, **payload.model_dump()},
            )
        )
        .mappings()
        .one()
    )
    response = BusinessCreated(business=BusinessRead.model_validate(row), operation_id=operation_id)
    event_payload = {"business_id": str(business_id), "actor_id": str(actor_id), "operation_id": str(operation_id)}
    await session.execute(
        text("""INSERT INTO outbox_events (id, tenant_id, event_type, payload)
             VALUES (:id, :tenant, 'business.created', CAST(:payload AS jsonb))"""),
        {"id": event_id, "tenant": tenant_id, "payload": json.dumps(event_payload)},
    )
    await session.execute(
        text("""INSERT INTO audit_events (tenant_id, actor_id, operation_id, action, resource_id)
             VALUES (:tenant, :actor, :operation, 'business.created', :resource)"""),
        {"tenant": tenant_id, "actor": actor_id, "operation": operation_id, "resource": business_id},
    )
    await session.execute(
        text("""UPDATE idempotency_records SET response=CAST(:response AS jsonb)
             WHERE tenant_id=:tenant AND scope=:scope AND key=:key"""),
        {"response": response.model_dump_json(), "tenant": tenant_id, "scope": scope, "key": key},
    )
    return response


async def list_businesses(
    session: AsyncSession,
    tenant_id: UUID,
    actor_id: UUID,
    limit: int,
    after: UUID | None,
) -> BusinessPage:
    await require_member(session, tenant_id, actor_id)
    rows = (
        (
            await session.execute(
                text("""SELECT * FROM businesses WHERE tenant_id=:tenant
          AND (CAST(:after AS uuid) IS NULL OR id > CAST(:after AS uuid)) ORDER BY id LIMIT :limit"""),
                {"tenant": tenant_id, "after": after, "limit": limit + 1},
            )
        )
        .mappings()
        .all()
    )
    items = [BusinessRead.model_validate(row) for row in rows[:limit]]
    return BusinessPage(items=items, next_cursor=items[-1].id if len(rows) > limit else None)
