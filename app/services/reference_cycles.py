"""Simulated-only selection cycles. No provider calls or real profiles."""

import hashlib
import json
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import text

from app.core.config import Settings
from app.db.session import Database
from app.schemas.reference_discovery import FixtureSelectionRead, FixtureSelectionRequest, FixtureSelectionState
from app.services.auth import AuthError
from app.services.whatsapp_materials import WhatsAppMaterialsService


async def lock_reference_head(session: Any, tenant: UUID, business: UUID) -> Any:
    await session.execute(
        text("""INSERT INTO reference_search_heads(tenant_id,business_id) VALUES(:tenant,:business)
          ON CONFLICT DO NOTHING"""),
        {"tenant": tenant, "business": business},
    )
    return (
        (
            await session.execute(
                text("""SELECT cycle_id FROM reference_search_heads
                  WHERE tenant_id=:tenant AND business_id=:business FOR UPDATE"""),
                {"tenant": tenant, "business": business},
            )
        )
        .mappings()
        .one()
    )


async def reserve_simulated_radius(session: Any, tenant: UUID, business: UUID, radius: int) -> UUID:
    head = await lock_reference_head(session, tenant, business)
    cycle = head["cycle_id"]
    if cycle is not None:
        row = (
            (
                await session.execute(
                    text("""SELECT locked_until,locked_until > clock_timestamp() AS locked FROM reference_search_cycles
                      WHERE tenant_id=:tenant AND business_id=:business AND id=:cycle"""),
                    {"tenant": tenant, "business": business, "cycle": cycle},
                )
            )
            .mappings()
            .one()
        )
        # A confirmation starts a shared six-month cycle; previously unused
        # radii remain available until the original deadline expires.
        if row["locked_until"] is not None and not row["locked"]:
            cycle = None
    if cycle is None:
        cycle = uuid4()
        await session.execute(
            text("""INSERT INTO reference_search_cycles(id,tenant_id,business_id) VALUES(:id,:tenant,:business)"""),
            {"id": cycle, "tenant": tenant, "business": business},
        )
        await session.execute(
            text(
                """UPDATE reference_search_heads SET cycle_id=:cycle
                  WHERE tenant_id=:tenant AND business_id=:business"""
            ),
            {"cycle": cycle, "tenant": tenant, "business": business},
        )
    used = await session.scalar(
        text("""SELECT 1 FROM reference_discoveries WHERE tenant_id=:tenant AND business_id=:business
          AND cycle_id=:cycle AND radius_km=:radius AND state IN ('pending','simulated')"""),
        {"tenant": tenant, "business": business, "cycle": cycle, "radius": radius},
    )
    if used is not None:
        raise AuthError("REFERENCE_RADIUS_ALREADY_SEARCHED", 409)
    return cast(UUID, cycle)


class FixtureSelectionService:
    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings, self.database = settings, database

    async def current(self, tenant: UUID, business: UUID, actor: UUID) -> FixtureSelectionState:
        if self.settings.reference_discovery_mode != "fake":
            raise AuthError("REFERENCE_DISCOVERY_DISABLED", 503)
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            locked_until = await session.scalar(
                text("""SELECT c.locked_until FROM reference_search_heads h
                  JOIN reference_search_cycles c
                    ON (c.tenant_id,c.business_id,c.id)=(h.tenant_id,h.business_id,h.cycle_id)
                  WHERE h.tenant_id=:tenant AND h.business_id=:business"""),
                {"tenant": tenant, "business": business},
            )
            rows = (
                (
                    await session.execute(
                        text("""SELECT id,canonical_id FROM reference_discovery_candidates
                          WHERE tenant_id=:tenant AND business_id=:business AND selected=true
                          ORDER BY created_at,id"""),
                        {"tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .all()
            )
            selected: dict[UUID, UUID] = {}
            for row in rows:
                selected.setdefault(row["canonical_id"], row["id"])
            return FixtureSelectionState(candidate_ids=list(selected.values()), locked_until=locked_until)

    async def confirm(
        self, tenant: UUID, business: UUID, actor: UUID, payload: FixtureSelectionRequest
    ) -> FixtureSelectionRead:
        if self.settings.reference_discovery_mode != "fake":
            raise AuthError("REFERENCE_DISCOVERY_DISABLED", 503)
        candidates = sorted(str(value) for value in payload.candidate_ids)
        digest = hashlib.sha256(json.dumps(candidates, separators=(",", ":")).encode()).hexdigest()
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            head = await lock_reference_head(session, tenant, business)
            previous = (
                (
                    await session.execute(
                        text("""SELECT request_hash,response FROM reference_selection_operations
                          WHERE tenant_id=:tenant AND business_id=:business AND operation_id=:operation"""),
                        {"tenant": tenant, "business": business, "operation": payload.operation_id},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if previous is not None:
                if previous["request_hash"] != digest:
                    raise AuthError("REFERENCE_SELECTION_OPERATION_CONFLICT", 409)
                return FixtureSelectionRead.model_validate(previous["response"])
            cycle = head["cycle_id"]
            if cycle is None:
                raise AuthError("REFERENCE_SELECTION_NO_CYCLE", 409)
            rows = (
                (
                    await session.execute(
                        text("""SELECT c.id,c.canonical_id FROM reference_discovery_candidates c
                          JOIN reference_discoveries d
                            ON (d.tenant_id,d.business_id,d.id)=(c.tenant_id,c.business_id,c.discovery_id)
                          WHERE c.tenant_id=:tenant AND c.business_id=:business
                            AND (d.cycle_id=:cycle OR c.selected=true)
                            AND d.state='simulated'"""),
                        {"tenant": tenant, "business": business, "cycle": cycle},
                    )
                )
                .mappings()
                .all()
            )
            identities = {row["id"]: row["canonical_id"] for row in rows}
            if not set(payload.candidate_ids).issubset(identities):
                raise AuthError("REFERENCE_SELECTION_INVALID_CANDIDATE", 409)
            canonical_ids = [identities[value] for value in payload.candidate_ids]
            if len(set(canonical_ids)) != len(canonical_ids):
                raise AuthError("REFERENCE_SELECTION_DUPLICATE_ENTITY", 409)
            await session.execute(
                text("""UPDATE reference_discovery_candidates SET selected=false
                  WHERE tenant_id=:tenant AND business_id=:business AND selected=true"""),
                {"tenant": tenant, "business": business},
            )
            await session.execute(
                text("""UPDATE reference_discovery_candidates SET selected=true
                  WHERE tenant_id=:tenant AND business_id=:business AND canonical_id=ANY(CAST(:ids AS uuid[]))"""),
                {"tenant": tenant, "business": business, "ids": canonical_ids},
            )
            locked_until = await session.scalar(
                text("""UPDATE reference_search_cycles SET confirmed_at=coalesce(confirmed_at,instant.confirmed),
                  locked_until=coalesce(locked_until,instant.confirmed+interval '6 months')
                  FROM (SELECT clock_timestamp() AS confirmed) instant
                  WHERE tenant_id=:tenant AND business_id=:business AND id=:cycle RETURNING locked_until"""),
                {"tenant": tenant, "business": business, "cycle": cycle},
            )
            response = FixtureSelectionRead(
                operation_id=payload.operation_id,
                candidate_ids=[UUID(value) for value in candidates],
                locked_until=locked_until,
            )
            await session.execute(
                text("""INSERT INTO reference_selection_operations
                  (tenant_id,business_id,operation_id,actor_id,cycle_id,request_hash,response)
                  VALUES(:tenant,:business,:operation,:actor,:cycle,:digest,CAST(:response AS jsonb))"""),
                {
                    "tenant": tenant,
                    "business": business,
                    "operation": payload.operation_id,
                    "actor": actor,
                    "cycle": cycle,
                    "digest": digest,
                    "response": response.model_dump_json(),
                },
            )
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                  VALUES(:tenant,:actor,:operation,'reference.selection_confirmed',:business)"""),
                {"tenant": tenant, "actor": actor, "operation": payload.operation_id, "business": business},
            )
            await session.execute(
                text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
                  VALUES(:id,:tenant,'reference.selection_confirmed',CAST(:payload AS jsonb))"""),
                {
                    "id": uuid4(),
                    "tenant": tenant,
                    "payload": json.dumps(
                        {
                            "business_id": str(business),
                            "actor_id": str(actor),
                            "operation_id": str(payload.operation_id),
                        }
                    ),
                },
            )
            return response
