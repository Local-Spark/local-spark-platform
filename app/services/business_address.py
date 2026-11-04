"""Version and retain the shop address explicitly supplied by an active owner."""

import hashlib
import json
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text

from app.db.session import Database
from app.schemas.business_address import BusinessAddressRead, BusinessAddressWrite
from app.services.auth import AuthError


def _present(row: Any) -> BusinessAddressRead:
    if row is None:
        return BusinessAddressRead(version=0, address=None, updated_at=None)
    return BusinessAddressRead(version=row["version"], address=row["address"], updated_at=row["created_at"])


class BusinessAddressService:
    def __init__(self, database: Database) -> None:
        self.database = database

    @staticmethod
    async def _authorize(session: Any, tenant: UUID, business: UUID) -> None:
        active = await session.scalar(text("SELECT public.lock_reference_cost_owner()"))
        found = await session.scalar(
            text("SELECT 1 FROM business_profiles WHERE tenant_id=:tenant AND business_id=:business"),
            {"tenant": tenant, "business": business},
        )
        if not active or found is None:
            raise AuthError("BUSINESS_OWNER_REQUIRED", 403)

    async def read(self, tenant: UUID, business: UUID, actor: UUID) -> BusinessAddressRead:
        async with self.database.transaction(tenant, actor) as session:
            await self._authorize(session, tenant, business)
            row = (
                (
                    await session.execute(
                        text("""SELECT v.version,v.address,v.created_at FROM business_address_heads h
                      JOIN business_address_versions v USING(tenant_id,business_id,version)
                      WHERE h.tenant_id=:tenant AND h.business_id=:business"""),
                        {"tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .one_or_none()
            )
            return _present(row)

    async def save(
        self, tenant: UUID, business: UUID, actor: UUID, payload: BusinessAddressWrite
    ) -> BusinessAddressRead:
        address = payload.address.model_dump(mode="json", exclude_none=True)
        canonical = json.dumps(
            {"expected_version": payload.expected_version, "address": address},
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(canonical.encode("ascii")).hexdigest()
        params = {"tenant": tenant, "business": business, "actor": actor, "operation": payload.operation_id}
        async with self.database.transaction(tenant, actor) as session:
            await self._authorize(session, tenant, business)
            # One lock also serializes the first save, before a head row exists.
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key,100))"),
                {"key": f"business-address:{tenant}:{business}"},
            )
            prior = (
                (
                    await session.execute(
                        text("""SELECT o.actor_id,o.request_hash,v.version,v.address,v.created_at
                      FROM business_address_operations o JOIN business_address_versions v
                        USING(tenant_id,business_id,version)
                      WHERE o.tenant_id=:tenant AND o.business_id=:business AND o.operation_id=:operation"""),
                        params,
                    )
                )
                .mappings()
                .one_or_none()
            )
            if prior is not None:
                if prior["actor_id"] != actor or prior["request_hash"] != digest:
                    raise AuthError("BUSINESS_ADDRESS_OPERATION_CONFLICT", 409)
                return _present(prior)
            current = (
                (
                    await session.execute(
                        text("""SELECT v.version,v.address,v.created_at FROM business_address_heads h
                      JOIN business_address_versions v USING(tenant_id,business_id,version)
                      WHERE h.tenant_id=:tenant AND h.business_id=:business"""),
                        params,
                    )
                )
                .mappings()
                .one_or_none()
            )
            version = current["version"] if current is not None else 0
            if version != payload.expected_version:
                raise AuthError("BUSINESS_ADDRESS_VERSION_CONFLICT", 409)
            event = uuid4()
            if current is None or current["address"] != address:
                version += 1
                current = (
                    (
                        await session.execute(
                            text("""INSERT INTO business_address_versions
                          (tenant_id,business_id,version,address,actor_id,operation_id)
                          VALUES(:tenant,:business,:version,CAST(:address AS jsonb),:actor,:operation)
                          RETURNING version,address,created_at"""),
                            {**params, "version": version, "address": json.dumps(address, ensure_ascii=True)},
                        )
                    )
                    .mappings()
                    .one()
                )
                await session.execute(
                    text("""INSERT INTO business_address_heads(tenant_id,business_id,version)
                      VALUES(:tenant,:business,:version) ON CONFLICT(tenant_id,business_id)
                      DO UPDATE SET version=excluded.version"""),
                    {**params, "version": version},
                )
            await session.execute(
                text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
                  VALUES(:event,:tenant,'business.address_saved',CAST(:payload AS jsonb))"""),
                {
                    "event": event,
                    "tenant": tenant,
                    "payload": json.dumps(
                        {
                            "business_id": str(business),
                            "actor_id": str(actor),
                            "operation_id": str(payload.operation_id),
                            "address_version": version,
                        }
                    ),
                },
            )
            await session.execute(
                text("""INSERT INTO business_address_operations
                  (tenant_id,business_id,operation_id,actor_id,request_hash,version,event_id)
                  VALUES(:tenant,:business,:operation,:actor,:hash,:version,:event)"""),
                {**params, "hash": digest, "version": version, "event": event},
            )
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                  VALUES(:tenant,:actor,:operation,'business.address_saved',:business)"""),
                params,
            )
            return _present(current)
