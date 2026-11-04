"""Prepare durable provider intents and reserve costs before each HTTP send."""

import json
from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

from pydantic import SecretStr
from sqlalchemy import text

from app.adapters.google_places import PlacesChargeableRequest
from app.adapters.jev_reference_recommendations import RecommendationRequest
from app.adapters.jev_reference_similarity import JevChargeableRequest
from app.db.session import Database
from app.schemas.reference_contacts_effect import ContactsChargeableRequest
from app.schemas.reference_filtered_batch import FilteredBatch
from app.services.reference_contacts_budget_guard import ContactsGuardContext, DatabaseContactsBudgetGuard
from app.services.reference_google_intent import create_google_intent, google_effect_id
from app.services.reference_jev_request_mac import jev_request_mac
from app.services.reference_places_budget_guard import DatabasePlacesBudgetGuard, PlacesGuardContext
from app.services.reference_recommendation_mac import recommendation_request_mac


class IntentPlacesGuard:
    def __init__(self, database: Database, context: PlacesGuardContext) -> None:
        self.database, self.context = database, context
        self.guard: DatabasePlacesBudgetGuard | None = None

    async def claim(self, operation_id: UUID, request: PlacesChargeableRequest) -> bool | Literal["completed_empty"]:
        self.context = await create_google_intent(self.database, self.context, request)
        self.guard = DatabasePlacesBudgetGuard(self.database, self.context)
        return await self.guard.claim(operation_id, request)

    async def complete_empty(self) -> None:
        if self.guard is None:
            raise ValueError("PLACES_EXECUTOR_NOT_CLAIMED")
        await self.guard.complete_empty()

    async def uncertain(self) -> None:
        if self.guard is None:
            raise ValueError("PLACES_EXECUTOR_NOT_CLAIMED")
        await self.guard.uncertain()

    def execution_token(self) -> UUID:
        if self.guard is None:
            raise ValueError("PLACES_EXECUTOR_NOT_CLAIMED")
        return self.guard.execution_token()


@dataclass(frozen=True, repr=False)
class StageContext:
    tenant: UUID
    business: UUID
    actor: UUID
    search: UUID
    effect: UUID
    event: UUID
    pilot: UUID
    context_version: int
    key: SecretStr
    key_version: str
    tariff_version: str
    credential_version: str
    reserved_usd_micros: int
    source_mac: str
    batch: UUID | None = None
    similarity_effect: UUID | None = None
    shortlist: FilteredBatch | None = None


async def stage_claim(
    database: Database, context: StageContext, kind: str, mac: str, charge: str, **extra: Any
) -> dict[str, Any]:
    c = context
    value = {
        "effect": str(c.effect),
        "event": str(c.event),
        "pilot": str(c.pilot),
        "mac": mac,
        "amount": c.reserved_usd_micros,
        "charge": charge,
        "key": c.key_version,
        "tariff": c.tariff_version,
        "credential": c.credential_version,
        "batch": str(c.batch) if c.batch else None,
        **extra,
    }
    async with database.transaction(c.tenant, c.actor) as session:
        result = await session.scalar(
            text("SELECT public.reference_stage_claim(:business,:search,:kind,CAST(:intent AS jsonb))"),
            {"business": c.business, "search": c.search, "kind": kind, "intent": json.dumps(value)},
        )
    return dict(result)


class JevStageGuard:
    def __init__(self, database: Database, context: StageContext, kind: Literal["mapping", "recommendation"]) -> None:
        self.database, self.context, self.kind = database, context, kind
        self.token: UUID | None = None
        self.attempted = False

    async def claim(self, operation_id: UUID, request: JevChargeableRequest | RecommendationRequest) -> bool:
        c = self.context
        if self.attempted or operation_id != c.effect:
            return False
        self.attempted = True
        if self.kind == "mapping":
            if not isinstance(request, JevChargeableRequest):
                raise ValueError("REFERENCE_STAGE_INVALID")
            mac = jev_request_mac(
                c.key,
                key_version=c.key_version,
                tariff_version=c.tariff_version,
                credential_version=c.credential_version,
                tenant=c.tenant,
                business=c.business,
                actor=c.actor,
                search=c.search,
                effect=c.effect,
                pilot=c.pilot,
                parent_google_effect=google_effect_id(c.search),
                source_batch_mac=c.source_mac,
                context_version=c.context_version,
                reserved_usd_micros=c.reserved_usd_micros,
                request=request,
            )
        else:
            if (
                not isinstance(request, RecommendationRequest)
                or c.batch is None
                or c.similarity_effect is None
                or c.shortlist is None
            ):
                raise ValueError("REFERENCE_STAGE_INVALID")
            mac = recommendation_request_mac(
                c.key,
                key_version=c.key_version,
                tariff_version=c.tariff_version,
                credential_version=c.credential_version,
                tenant=c.tenant,
                business=c.business,
                actor=c.actor,
                search=c.search,
                effect=c.effect,
                pilot=c.pilot,
                google_effect=google_effect_id(c.search),
                similarity_effect=c.similarity_effect,
                batch_id=c.batch,
                context_version=c.context_version,
                source_batch_mac=c.source_mac,
                reserved_usd_micros=c.reserved_usd_micros,
                shortlist=c.shortlist,
                request=request,
            )
        result = await stage_claim(self.database, c, self.kind, mac, "jev-model:" + request.model)
        if result["created"] is not True:
            return False
        self.token = UUID(result["executor_token"])
        return True

    def execution_token(self) -> UUID:
        if self.token is None:
            raise ValueError("REFERENCE_STAGE_NOT_CLAIMED")
        return self.token

    async def uncertain(self) -> None:
        async with self.database.transaction(self.context.tenant, self.context.actor) as session:
            await session.scalar(
                text("SELECT public.reference_provider_uncertain(:effect,:token)"),
                {"effect": self.context.effect, "token": self.execution_token()},
            )


class IntentContactsGuard(DatabaseContactsBudgetGuard):
    def __init__(self, database: Database, context: ContactsGuardContext, search: UUID, source: str) -> None:
        super().__init__(database, context)
        self.search, self.source = search, source

    async def claim_submission(self, operation_id: UUID, request: ContactsChargeableRequest) -> bool:
        c = self._context
        if self._attempted or operation_id != c.effect:
            return False
        self._attempted = True
        mac = self._request_mac(request)
        stage = StageContext(
            c.tenant,
            c.business,
            c.actor,
            self.search,
            c.effect,
            c.event,
            c.pilot,
            c.context_version,
            c.key,
            c.key_version,
            c.tariff_version,
            c.credential_version,
            c.reserved_usd_micros,
            self.source,
            c.batch,
        )
        result = await stage_claim(
            self._database,
            stage,
            "contacts",
            mac,
            "apify-place-contacts:" + c.build,
            lookup=str(c.lookup),
            candidate=str(c.candidate),
        )
        if result["created"] is not True:
            return False
        self._token, self._mac = UUID(result["executor_token"]), mac
        return True
