"""Durable, private requests for the non-network discovery simulation."""

import json
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text

from app.core.config import Settings
from app.db.session import Database
from app.schemas.editorial_context import ReferenceSearchPreference
from app.schemas.reference_discovery import DiscoveryFixtureRead, DiscoveryRead
from app.services.auth import AuthError
from app.services.reference_cycles import lock_reference_head, reserve_simulated_radius
from app.services.whatsapp_materials import WhatsAppMaterialsService


class ReferenceDiscoveryService:
    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings, self.database = settings, database

    def _enabled(self) -> None:
        if self.settings.reference_discovery_mode != "fake":
            raise AuthError("REFERENCE_DISCOVERY_DISABLED", 503)

    @staticmethod
    def _present(row: object) -> DiscoveryRead:
        return DiscoveryRead.model_validate(row, from_attributes=True)

    async def request(self, tenant: UUID, business: UUID, actor: UUID, operation: UUID) -> DiscoveryRead:
        self._enabled()
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            await lock_reference_head(session, tenant, business)
            old = (
                (
                    await session.execute(
                        text("""SELECT id,operation_id,state,created_at,completed_at
              FROM reference_discoveries WHERE tenant_id=:tenant AND business_id=:business
                AND operation_id=:operation"""),
                        {"tenant": tenant, "business": business, "operation": operation},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if old is not None:
                return self._present(old)
            pending_context = await session.scalar(
                text("""SELECT 1 FROM business_visual_pending_changes WHERE tenant_id=:tenant AND business_id=:business
                  AND resource_key='context' AND state='pending' LIMIT 1"""),
                {"tenant": tenant, "business": business},
            )
            if pending_context is not None:
                raise AuthError("REFERENCE_CONTEXT_CHANGE_PENDING", 409)
            current = (
                (
                    await session.execute(
                        text("""SELECT h.version,v.document,p.category
              FROM business_context_heads h JOIN business_context_versions v
                ON (v.tenant_id,v.business_id,v.version)=(h.tenant_id,h.business_id,h.version)
              JOIN business_profiles p ON (p.tenant_id,p.business_id)=(h.tenant_id,h.business_id)
              WHERE h.tenant_id=:tenant AND h.business_id=:business FOR SHARE OF h,p"""),
                        {"tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if current is None:
                raise AuthError("REFERENCE_SEARCH_PREFERENCE_REQUIRED", 409)
            preference = current["document"].get("preferences", {}).get("reference_search")
            if preference is None:
                raise AuthError("REFERENCE_SEARCH_PREFERENCE_REQUIRED", 409)
            if not current["document"].get("preferences", {}).get("business_terms", []):
                raise AuthError("REFERENCE_TERMS_REQUIRED", 409)
            parsed = ReferenceSearchPreference.model_validate(preference)
            if parsed.scope != "local" or parsed.radius_km not in {5, 20, 50}:
                raise AuthError("REFERENCE_SCOPE_NOT_SUPPORTED", 409)
            if parsed.scope == "local" and parsed.origin is not None and parsed.origin.method == "manual":
                raise AuthError("REFERENCE_ORIGIN_REQUIRES_GEOCODING", 409)
            cycle_id = await reserve_simulated_radius(session, tenant, business, int(parsed.radius_km))
            discovery = uuid4()
            row = (
                (
                    await session.execute(
                        text("""INSERT INTO reference_discoveries
              (id,tenant_id,business_id,actor_id,operation_id,context_version,category,preference,state,cycle_id,radius_km)
              VALUES(:id,:tenant,:business,:actor,:operation,:version,:category,CAST(:preference AS jsonb),'pending',
                     :cycle_id,:radius)
              ON CONFLICT(tenant_id,business_id,operation_id) DO NOTHING
              RETURNING id,operation_id,state,created_at,completed_at"""),
                        {
                            "id": discovery,
                            "tenant": tenant,
                            "business": business,
                            "actor": actor,
                            "operation": operation,
                            "version": current["version"],
                            "category": current["category"],
                            "cycle_id": cycle_id,
                            "radius": int(parsed.radius_km),
                            "preference": json.dumps(parsed.model_dump(mode="json"), ensure_ascii=False),
                        },
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                row = (
                    (
                        await session.execute(
                            text("""SELECT id,operation_id,state,created_at,completed_at
                  FROM reference_discoveries WHERE tenant_id=:tenant AND business_id=:business
                    AND operation_id=:operation"""),
                            {"tenant": tenant, "business": business, "operation": operation},
                        )
                    )
                    .mappings()
                    .one()
                )
                return self._present(row)
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
              VALUES(:tenant,:actor,:operation,'reference.search_requested',:business)"""),
                {"tenant": tenant, "actor": actor, "operation": operation, "business": business},
            )
            await session.execute(
                text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
              VALUES(:id,:tenant,'reference.search_requested',CAST(:payload AS jsonb))"""),
                {
                    "id": uuid4(),
                    "tenant": tenant,
                    "payload": json.dumps(
                        {"business_id": str(business), "actor_id": str(actor), "operation_id": str(operation)}
                    ),
                },
            )
            return self._present(row)

    async def read(self, tenant: UUID, business: UUID, actor: UUID, discovery: UUID) -> DiscoveryRead:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            row = (
                (
                    await session.execute(
                        text("""SELECT id,operation_id,state,created_at,completed_at
              FROM reference_discoveries WHERE tenant_id=:tenant AND business_id=:business AND id=:id"""),
                        {"tenant": tenant, "business": business, "id": discovery},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise AuthError("REFERENCE_DISCOVERY_NOT_FOUND", 404)
            return self._present(row)

    async def list_discoveries(self, tenant: UUID, business: UUID, actor: UUID) -> list[DiscoveryRead]:
        self._enabled()
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            rows = (
                (
                    await session.execute(
                        text("""SELECT id,operation_id,state,created_at,completed_at FROM reference_discoveries
                          WHERE tenant_id=:tenant AND business_id=:business
                          ORDER BY created_at DESC,id DESC LIMIT 100"""),
                        {"tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .all()
            )
            return [self._present(row) for row in rows]

    async def fixtures(self, tenant: UUID, business: UUID, actor: UUID, discovery: UUID) -> list[DiscoveryFixtureRead]:
        self._enabled()
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            found = await session.scalar(
                text("""SELECT id FROM reference_discoveries
                  WHERE tenant_id=:tenant AND business_id=:business AND id=:discovery"""),
                {"tenant": tenant, "business": business, "discovery": discovery},
            )
            if found is None:
                raise AuthError("REFERENCE_DISCOVERY_NOT_FOUND", 404)
            rows = (
                (
                    await session.execute(
                        text("""SELECT id,discovery_id,fixture_number,canonical_id,selected,
                          reputation_score_snapshot,reputation_formula_version,reputation_fixture_version
                          FROM reference_discovery_candidates
                          WHERE tenant_id=:tenant AND business_id=:business AND discovery_id=:discovery
                          ORDER BY fixture_number"""),
                        {"tenant": tenant, "business": business, "discovery": discovery},
                    )
                )
                .mappings()
                .all()
            )
            # Every admitted row has a score snapshot. Never reconstruct an
            # earlier score from the currently loaded fixture set or formula.
            ranked: list[tuple[Decimal, dict[str, Any]]] = []
            for row in rows:
                score = row["reputation_score_snapshot"]
                with localcontext() as context:
                    context.prec = 28
                    context.rounding = ROUND_HALF_EVEN
                    displayed = score.quantize(Decimal("0.01"))
                ranked.append(
                    (
                        score,
                        {
                            **row,
                            "fixture_version": row["reputation_fixture_version"],
                            "reputation_score": displayed,
                            "reputation_status": "scored",
                        },
                    )
                )
            # Sort on the unrounded value; stable fixture number breaks ties.
            ranked.sort(key=lambda item: item[1]["fixture_number"])
            ranked.sort(key=lambda item: item[0], reverse=True)
            return [DiscoveryFixtureRead.model_validate(item) for _, item in ranked]
