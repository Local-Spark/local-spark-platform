"""Bounded, retryable removal of WhatsApp source events and stored materials."""

import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text

from app.adapters.material_media import MaterialError, MaterialStore
from app.db.session import Database

logger = logging.getLogger("meu_braco_direito.whatsapp_retention")


@dataclass(frozen=True)
class PurgeClaim:
    id: UUID
    tenant_id: UUID
    business_id: UUID
    object_key: str | None
    fencing_token: int


async def claim_expired_assets(database: Database, owner: UUID, limit: int = 100) -> list[PurgeClaim]:
    async with database.sessions() as session, session.begin():
        rows = (
            (
                await session.execute(
                    text("""WITH candidates AS (
                      SELECT id FROM whatsapp_material_assets
                      WHERE (expires_at<=now() OR delete_requested_at IS NOT NULL)
                        AND (delete_lease_until IS NULL OR delete_lease_until<now())
                      ORDER BY expires_at,id LIMIT :limit FOR UPDATE SKIP LOCKED)
                      UPDATE whatsapp_material_assets a SET delete_owner=:owner,
                        delete_lease_until=now()+interval '60 seconds',
                        delete_fencing_token=a.delete_fencing_token+1
                      FROM candidates c WHERE a.id=c.id
                      RETURNING a.id,a.tenant_id,a.business_id,a.object_key,a.delete_fencing_token"""),
                    {"owner": owner, "limit": limit},
                )
            )
            .mappings()
            .all()
        )
        return [
            PurgeClaim(row["id"], row["tenant_id"], row["business_id"], row["object_key"], row["delete_fencing_token"])
            for row in rows
        ]


async def finish_purge(database: Database, owner: UUID, claim: PurgeClaim) -> bool:
    async with database.sessions() as session, session.begin():
        row = (
            await session.execute(
                text("""SELECT id FROM whatsapp_material_assets
                      WHERE id=:id AND delete_owner=:owner AND delete_fencing_token=:token
                        AND (expires_at<=now() OR delete_requested_at IS NOT NULL)
                      FOR UPDATE"""),
                {"id": claim.id, "owner": owner, "token": claim.fencing_token},
            )
        ).one_or_none()
        if row is None:
            return False
        # The inbox and routed payload contain the same original material. Erase them
        # together with the asset record after object deletion has been acknowledged.
        await session.execute(text("DELETE FROM whatsapp_inbox WHERE id=:id"), {"id": claim.id})
        await session.execute(text("DELETE FROM whatsapp_material_events WHERE id=:id"), {"id": claim.id})
        await session.execute(text("DELETE FROM whatsapp_material_assets WHERE id=:id"), {"id": claim.id})
        await session.execute(
            text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
              VALUES(:tenant,:actor,:id,'whatsapp.material_purged',:business)"""),
            {"tenant": claim.tenant_id, "actor": UUID(int=0), "id": claim.id, "business": claim.business_id},
        )
        return True


async def purge_expired_raw(database: Database, limit: int = 1000) -> None:
    async with database.sessions() as session, session.begin():
        await session.execute(
            text("""DELETE FROM whatsapp_material_events WHERE id IN (
              SELECT id FROM whatsapp_material_events WHERE expires_at<now()
              ORDER BY expires_at,id LIMIT :limit FOR UPDATE SKIP LOCKED)"""),
            {"limit": limit},
        )
        await session.execute(
            text("""DELETE FROM whatsapp_inbox WHERE id IN (
              SELECT id FROM whatsapp_inbox WHERE expires_at<now()
              ORDER BY expires_at,id LIMIT :limit FOR UPDATE SKIP LOCKED)"""),
            {"limit": limit},
        )


async def purge_once(database: Database, store: MaterialStore, owner: UUID, limit: int = 100) -> int:
    await purge_expired_raw(database)
    claims = await claim_expired_assets(database, owner, limit)
    purged = 0
    for claim in claims:
        try:
            if claim.object_key:
                await store.delete(claim.object_key)
            if await finish_purge(database, owner, claim):
                purged += 1
        except MaterialError:
            # The lease expires and another worker can retry. Keep the DB record
            # until the object store acknowledges deletion.
            logger.warning("whatsapp.material_purge_retry", extra={"event_id": str(claim.id)})
    return purged
