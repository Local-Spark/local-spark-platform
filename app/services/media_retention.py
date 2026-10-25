"""Lease expired or source-revoked previews and erase their private objects."""

import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text

from app.adapters.material_media import MaterialError, MaterialStore
from app.db.session import Database
from app.services.editorial_proposals import _audit

logger = logging.getLogger("meu_braco_direito.media_retention")


@dataclass(frozen=True)
class PreviewPurgeClaim:
    id: UUID
    owner: UUID
    fence: int
    object_key: str


async def claim_expired_previews(database: Database, owner: UUID, limit: int = 50) -> list[PreviewPurgeClaim]:
    async with database.sessions() as session, session.begin():
        rows = (
            (
                await session.execute(
                    text("""WITH due AS (
                      SELECT p.id FROM media_previews p WHERE
                        (p.expires_at<=now() OR
                          NOT EXISTS(SELECT 1 FROM editorial_proposals e WHERE e.id=p.proposal_id) OR
                          (p.source_asset_id IS NOT NULL AND NOT EXISTS(
                            SELECT 1 FROM whatsapp_material_assets a WHERE a.id=p.source_asset_id
                              AND a.delete_requested_at IS NULL AND a.expires_at>now())))
                        AND (p.state NOT IN ('rendering','purging') OR p.dispatch_lease_until<now())
                      ORDER BY p.expires_at,p.id LIMIT :limit FOR UPDATE SKIP LOCKED)
                      UPDATE media_previews p SET state='purging',dispatch_owner=:owner,
                        dispatch_lease_until=now()+interval '3 minutes',
                        dispatch_fence=p.dispatch_fence+1,updated_at=now()
                      FROM due WHERE p.id=due.id
                      RETURNING p.id,p.tenant_id,p.business_id,p.render_key,p.mime_type,p.dispatch_fence"""),
                    {"owner": owner, "limit": limit},
                )
            )
            .mappings()
            .all()
        )
        return [
            PreviewPurgeClaim(
                row["id"],
                owner,
                row["dispatch_fence"],
                f"previews/{row['tenant_id']}/{row['business_id']}/{row['id']}/{row['render_key']}"
                f".{'mp4' if row['mime_type'] == 'video/mp4' else 'jpg'}",
            )
            for row in rows
        ]


async def finish_preview_purge(database: Database, claim: PreviewPurgeClaim) -> bool:
    async with database.sessions() as session, session.begin():
        row = (
            (
                await session.execute(
                    text("""DELETE FROM media_previews WHERE id=:id AND state='purging'
                      AND dispatch_owner=:owner AND dispatch_fence=:fence RETURNING *"""),
                    {"id": claim.id, "owner": claim.owner, "fence": claim.fence},
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            return False
        await _audit(session, row, "media.preview_purged")
        return True


async def purge_expired_previews(database: Database, store: MaterialStore, owner: UUID, limit: int = 50) -> int:
    claims = await claim_expired_previews(database, owner, limit)
    purged = 0
    for claim in claims:
        try:
            await store.delete(claim.object_key)
            if await finish_preview_purge(database, claim):
                purged += 1
        except MaterialError:
            logger.warning("media.preview_purge_retry", extra={"preview_id": str(claim.id)})
    return purged
