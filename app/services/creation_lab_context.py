"""Read the selected business without owner impersonation or customer writes."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.session import Database
from app.services.auth import AuthError
from app.services.brand_kits import BrandKitService
from app.services.creation_lab_access import require_lab_access
from app.services.creation_lab_drafts import ZERO
from app.services.editorial_context import EditorialContextService
from app.services.motion_context import MotionContext
from app.services.visual_consent_gate import VisualConsentGate


class CreationLabContext:
    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings, self.database = settings, database

    @asynccontextmanager
    async def scope(self, actor: UUID, run: UUID, action: str) -> AsyncIterator[tuple[AsyncSession, dict[str, Any]]]:
        async with self.database.transaction(ZERO, actor) as session:
            await require_lab_access(session, self.settings, actor, action)
            row = (
                (
                    await session.execute(
                        text("SELECT id,tenant_id,business_id,actor_id FROM creation_lab_runs WHERE id=:run"),
                        {"run": run},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise AuthError("CREATION_LAB_RUN_NOT_FOUND", 404)
            # Scope comes solely from the authenticated persisted run. Both GUCs
            # are local to this transaction and disappear before pool reuse.
            await session.execute(
                text("""SELECT set_config('app.tenant_id',:tenant,true),
                  set_config('app.creation_lab_run_id',:run,true)"""),
                {"tenant": str(row["tenant_id"]), "run": str(run)},
            )
            yield session, dict(row)

    async def read(self, actor: UUID, run: UUID, after: UUID | None = None) -> dict[str, Any]:
        async with self.scope(actor, run, "admin.creation_lab.context.read") as (session, row):
            tenant, business = row["tenant_id"], row["business_id"]
            kit = await BrandKitService._state(session, tenant, business)
            context = EditorialContextService._present(
                await EditorialContextService._version(session, tenant, business)
            )
            consent = await VisualConsentGate(self.database, self.settings)._state(session, tenant, business)
            today = await session.scalar(
                text("""SELECT (clock_timestamp() AT TIME ZONE timezone)::date
                  FROM businesses WHERE tenant_id=:tenant AND id=:business"""),
                {"tenant": tenant, "business": business},
            )
            facts = [
                item.model_dump(mode="json", exclude={"source_detail"})
                for item in context.facts
                if item.valid_until is None or item.valid_until >= today
            ]
            photos = (
                (
                    await session.execute(
                        text("""SELECT id,version,title,mime_type,size_bytes FROM business_collection_photos
                  WHERE tenant_id=:tenant AND business_id=:business AND state='ready' AND status='active'
                    AND rights_scope='business_collection_confirmed' AND delete_owner IS NULL
                    AND delete_lease_until IS NULL AND (CAST(:after AS uuid) IS NULL OR id>CAST(:after AS uuid)) ORDER BY id LIMIT 51"""),
                        {"tenant": tenant, "business": business, "after": after},
                    )
                )
                .mappings()
                .all()
            )
            selected = await session.scalar(
                text("SELECT selection_ciphertext FROM creation_lab_collection_choices WHERE run_id=:run"), {"run": run}
            )
            selection = MotionContext(self.settings).open(selected)["photos"] if selected else []
            return {
                "run_id": run,
                "business_id": business,
                "context_version": context.version,
                "confirmed_facts": facts,
                "preferences": context.preferences.model_dump(mode="json", exclude={"reference_search"}),
                "confirmed_kit": kit.confirmed.model_dump(mode="json") if kit.confirmed else None,
                "ai_consent": consent,
                "collection_photos": [dict(item) for item in photos[:50]],
                "has_more_photos": len(photos) > 50,
                "selected_photos": [
                    {"id": item["id"], "version": item["version"], "title": item["title"]} for item in selection
                ],
                "generation_authorized": False,
            }
