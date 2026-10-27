"""Optional business catalog, with owner confirmation and immutable CAS snapshots."""

import hashlib
import json
from typing import Any
from uuid import UUID

from sqlalchemy import text

from app.db.session import Database
from app.schemas.business_catalog import CatalogContent, CatalogHistoryItem, CatalogRead, CatalogUpdate
from app.services.auth import AuthError
from app.services.whatsapp_materials import WhatsAppMaterialsService


async def require_catalog_owner(session: Any, tenant: UUID, business: UUID, actor: UUID) -> None:
    """Shared owner guard for catalog and private collection media; staff is not an owner."""
    await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)


async def audit_catalog_change(
    session: Any, tenant: UUID, business: UUID, actor: UUID, operation: UUID, action: str
) -> None:
    await session.execute(
        text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(:tenant,:actor,:operation,:action,:business)"""),
        {"tenant": tenant, "actor": actor, "operation": operation, "business": business, "action": action},
    )


def _digest(payload: CatalogUpdate) -> str:
    document = json.dumps(payload.model_dump(mode="json"), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(document.encode()).hexdigest()


class BusinessCatalogService:
    def __init__(self, database: Database) -> None:
        self.database = database

    @staticmethod
    def _present(row: Any) -> CatalogRead:
        if row is None:
            return CatalogRead(version=0)
        return CatalogRead.model_validate(
            {**row["document"], "version": row["version"], "updated_at": row["created_at"]}
        )

    @staticmethod
    async def _version(session: Any, tenant: UUID, business: UUID, version: int | None = None) -> Any:
        return (
            (
                await session.execute(
                    text("""SELECT version,document,created_at FROM business_catalog_versions
                      WHERE tenant_id=:tenant AND business_id=:business
                        AND version=coalesce(:version,(SELECT version FROM business_catalog_heads
                          WHERE tenant_id=:tenant AND business_id=:business))"""),
                    {"tenant": tenant, "business": business, "version": version},
                )
            )
            .mappings()
            .one_or_none()
        )

    async def read(self, tenant: UUID, business: UUID, actor: UUID, version: int | None = None) -> CatalogRead:
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            row = await self._version(session, tenant, business, version)
            if version is not None and row is None:
                raise AuthError("CATALOG_VERSION_NOT_FOUND", 404)
            return self._present(row)

    async def history(self, tenant: UUID, business: UUID, actor: UUID) -> list[CatalogHistoryItem]:
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            rows = (
                (
                    await session.execute(
                        text("""SELECT version,created_at,actor_id FROM business_catalog_versions
                          WHERE tenant_id=:tenant AND business_id=:business ORDER BY version DESC LIMIT 50"""),
                        {"tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .all()
            )
            return [CatalogHistoryItem.model_validate(row) for row in rows]

    @staticmethod
    async def _replay(session: Any, tenant: UUID, business: UUID, payload: CatalogUpdate) -> CatalogRead | None:
        row = (
            (
                await session.execute(
                    text("""SELECT business_id,version,document,created_at,request_hash FROM business_catalog_versions
                      WHERE tenant_id=:tenant AND operation_id=:operation"""),
                    {"tenant": tenant, "operation": payload.operation_id},
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return None
        if row["business_id"] != business or row["request_hash"] != _digest(payload):
            raise AuthError("CATALOG_OPERATION_CONFLICT", 409)
        return BusinessCatalogService._present(row)

    @staticmethod
    async def _project(session: Any, tenant: UUID, business: UUID, version: int, content: CatalogContent) -> None:
        for offering in content.offerings:
            await session.execute(
                text("""INSERT INTO business_offerings
                  (tenant_id,business_id,id,kind,state,name,description,category,aliases,position,price_minor,
                   currency,price_valid_until,duration_minutes,booking_instructions,version)
                  VALUES(:tenant,:business,:id,:kind,:state,:name,:description,:category,CAST(:aliases AS jsonb),
                    :position,:price_minor,:currency,:price_valid_until,:duration_minutes,:booking_instructions,:version)
                  ON CONFLICT(tenant_id,business_id,id) DO UPDATE SET
                    kind=EXCLUDED.kind,state=EXCLUDED.state,name=EXCLUDED.name,description=EXCLUDED.description,
                    category=EXCLUDED.category,aliases=EXCLUDED.aliases,position=EXCLUDED.position,
                    price_minor=EXCLUDED.price_minor,currency=EXCLUDED.currency,price_valid_until=EXCLUDED.price_valid_until,
                    duration_minutes=EXCLUDED.duration_minutes,booking_instructions=EXCLUDED.booking_instructions,
                    version=EXCLUDED.version"""),
                {
                    **offering.model_dump(),
                    "aliases": json.dumps(offering.aliases, ensure_ascii=False),
                    "tenant": tenant,
                    "business": business,
                    "version": version,
                },
            )
        for promotion in content.promotions:
            await session.execute(
                text("""INSERT INTO business_offering_promotions
                  (tenant_id,business_id,id,offering_id,title,description,state,price_minor,starts_at,ends_at,version)
                  VALUES(:tenant,:business,:id,:offering_id,:title,:description,:state,:price_minor,
                    :starts_at,:ends_at,:version)
                  ON CONFLICT(tenant_id,business_id,id) DO UPDATE SET
                    offering_id=EXCLUDED.offering_id,title=EXCLUDED.title,description=EXCLUDED.description,
                    state=EXCLUDED.state,price_minor=EXCLUDED.price_minor,starts_at=EXCLUDED.starts_at,
                    ends_at=EXCLUDED.ends_at,version=EXCLUDED.version"""),
                {**promotion.model_dump(), "tenant": tenant, "business": business, "version": version},
            )

    async def update(self, tenant: UUID, business: UUID, actor: UUID, payload: CatalogUpdate) -> CatalogRead:
        async with self.database.transaction(tenant, actor) as session:
            await require_catalog_owner(session, tenant, business, actor)
            replay = await self._replay(session, tenant, business, payload)
            if replay is not None:
                return replay
            # Serialize mutations even across different businesses sharing an operation id.
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key,0))"),
                {"key": f"catalog:{tenant}:{payload.operation_id}"},
            )
            replay = await self._replay(session, tenant, business, payload)
            if replay is not None:
                return replay
            await session.execute(
                text("""INSERT INTO business_catalog_heads(tenant_id,business_id)
                  VALUES(:tenant,:business) ON CONFLICT DO NOTHING"""),
                {"tenant": tenant, "business": business},
            )
            version = await session.scalar(
                text("""UPDATE business_catalog_heads SET version=version+1
                  WHERE tenant_id=:tenant AND business_id=:business AND version=:expected RETURNING version"""),
                {"tenant": tenant, "business": business, "expected": payload.expected_version},
            )
            if version is None:
                raise AuthError("CATALOG_VERSION_CONFLICT", 409)
            previous = await self._version(session, tenant, business, version - 1)
            if previous is not None:
                for key in ("offerings", "promotions"):
                    existing = {item["id"] for item in previous["document"][key]}
                    incoming = {str(item.id) for item in getattr(payload, key)}
                    if not existing <= incoming:
                        raise AuthError("CATALOG_ARCHIVE_REQUIRED", 409)
            content = CatalogContent(offerings=payload.offerings, promotions=payload.promotions)
            row = (
                (
                    await session.execute(
                        text("""INSERT INTO business_catalog_versions
                          (tenant_id,business_id,version,operation_id,actor_id,request_hash,document)
                          VALUES(:tenant,:business,:version,:operation,:actor,:digest,CAST(:document AS jsonb))
                          RETURNING version,document,created_at"""),
                        {
                            "tenant": tenant,
                            "business": business,
                            "version": version,
                            "operation": payload.operation_id,
                            "actor": actor,
                            "digest": _digest(payload),
                            "document": content.model_dump_json(),
                        },
                    )
                )
                .mappings()
                .one()
            )
            await self._project(session, tenant, business, version, content)
            await audit_catalog_change(session, tenant, business, actor, payload.operation_id, "catalog.updated")
            return self._present(row)
