"""Durable address geocoding: request in API, one charged attempt in Temporal."""

import hmac
import json
from typing import Any
from uuid import UUID, uuid4, uuid5

import httpx
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.adapters.google_geocoding import (
    GEOCODING_FIELD_MASK,
    GeocodingChargeableRequest,
    GeocodingError,
    GoogleGeocoding,
)
from app.core.config import Settings
from app.db.session import Database
from app.schemas.business_address import ShopAddress
from app.schemas.business_geocoding import GeocodeConfirmation, GeocodeRead, GeocodeRequest, LocationCandidate
from app.services.auth import AuthError
from app.services.business_address import BusinessAddressService
from app.services.business_location_resolution import automatic_location_candidate
from app.services.business_shop_geocode_mac import (
    ShopGeocodeBinding,
    shop_geocode_address_text,
    shop_geocode_binding_mac,
)
from app.services.reference_geocoding_budget_guard import DatabaseGeocodingBudgetGuard, GeocodingGuardContext
from app.workflows.contracts import BusinessEvent


def _request(address: ShopAddress, key: SecretStr) -> GeocodingChargeableRequest:
    request = httpx.Request(
        "GET",
        "https://geocode.googleapis.com/v4/geocode/address",
        params={
            "address.addressLines": shop_geocode_address_text(address),
            "address.regionCode": "BR",
            "languageCode": "pt-BR",
        },
    )
    return GeocodingChargeableRequest("GET", str(request.url), GEOCODING_FIELD_MASK, key)


def _binding(
    context: GeocodingGuardContext, address_version: int, address: ShopAddress, credential: SecretStr
) -> ShopGeocodeBinding:
    return shop_geocode_binding_mac(
        context.key,
        key_version=context.key_version,
        tariff_version=context.tariff_version,
        credential_version=context.credential_version,
        tenant=context.tenant,
        business=context.business,
        actor=context.actor,
        address_version=address_version,
        origin=context.origin,
        effect=context.effect,
        pilot=context.pilot,
        context_version=context.context_version,
        reserved_usd_micros=context.reserved_usd_micros,
        address=address,
        request=_request(address, credential),
    )


_KNOWN_ERRORS = {
    "BUSINESS_OWNER_REQUIRED": 403,
    "BUSINESS_ADDRESS_VERSION_CONFLICT": 409,
    "BUSINESS_ADDRESS_OPERATION_CONFLICT": 409,
    "BUSINESS_ADDRESS_CONTEXT_REQUIRED": 409,
    "BUSINESS_ADDRESS_GEOCODE_EVENT_INVALID": 409,
    "BUSINESS_ADDRESS_GEOCODE_CONFIRMATION_INVALID": 409,
}


def _translate(error: DBAPIError) -> AuthError:
    for code, status in _KNOWN_ERRORS.items():
        if code in str(error.orig):
            return AuthError(code, status)
    return AuthError("BUSINESS_ADDRESS_GEOCODE_UNAVAILABLE", 503)


class BusinessGeocodingService:
    def __init__(self, database: Database, settings: Settings):
        self.database, self.settings = database, settings

    async def _read(self, session: Any, tenant: UUID, business: UUID, *, geocode: UUID | None = None) -> GeocodeRead:
        row = (
            (
                await session.execute(
                    text("""SELECT coalesce(g.address_version,h.version) AS version,g.id,g.status,
              g.candidates,g.chosen_candidate
          FROM business_address_heads h LEFT JOIN business_address_geocodes g
            ON g.tenant_id=h.tenant_id AND g.business_id=h.business_id AND
              ((CAST(:id AS uuid) IS NULL AND g.address_version=h.version) OR g.id=CAST(:id AS uuid))
          WHERE h.tenant_id=:tenant AND h.business_id=:business"""),
                    {"tenant": tenant, "business": business, "id": geocode},
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None or row["id"] is None:
            return GeocodeRead(
                enabled=self.settings.reference_geocoding_ready(),
                address_version=row["version"] if row else 0,
                status="unrequested",
            )
        candidates = [LocationCandidate.model_validate(item) for item in row["candidates"]]
        selected = next((item for item in candidates if item.id == row["chosen_candidate"]), None)
        return GeocodeRead(
            enabled=self.settings.reference_geocoding_ready(),
            address_version=row["version"],
            geocode_id=row["id"],
            status=row["status"],
            coordinates=selected,
            candidates=candidates if row["status"] == "confirmation_required" else [],
        )

    async def read(self, tenant: UUID, business: UUID, actor: UUID) -> GeocodeRead:
        async with self.database.transaction(tenant, actor) as session:
            await BusinessAddressService._authorize(session, tenant, business)
            return await self._read(session, tenant, business)

    async def request(self, tenant: UUID, business: UUID, actor: UUID, payload: GeocodeRequest) -> GeocodeRead:
        async with self.database.transaction(tenant, actor) as session:
            await BusinessAddressService._authorize(session, tenant, business)
            if not self.settings.reference_geocoding_ready():
                raise AuthError("BUSINESS_ADDRESS_GEOCODE_DISABLED", 503)
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key,100))"),
                {"key": f"business-address:{tenant}:{business}"},
            )
            row = (
                (
                    await session.execute(
                        text("""SELECT v.address,h.version FROM business_address_heads h
              JOIN business_address_versions v USING(tenant_id,business_id,version)
              WHERE h.tenant_id=:tenant AND h.business_id=:business"""),
                        {"tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None or row["version"] != payload.address_version:
                raise AuthError("BUSINESS_ADDRESS_VERSION_CONFLICT", 409)
            version = await session.scalar(
                text("SELECT version FROM business_context_heads WHERE tenant_id=:tenant AND business_id=:business"),
                {"tenant": tenant, "business": business},
            )
            if version is None:
                raise AuthError("BUSINESS_ADDRESS_CONTEXT_REQUIRED", 409)
            s = self.settings
            assert s.reference_provider_hmac_key and s.reference_google_api_key and s.reference_provider_pilot_id
            job = uuid5(payload.operation_id, f"business-address-geocode-v1:{tenant}:{business}")
            context = GeocodingGuardContext(
                tenant=tenant,
                business=business,
                actor=actor,
                origin=uuid5(job, "origin"),
                effect=uuid5(job, "effect"),
                event=uuid4(),
                pilot=s.reference_provider_pilot_id,
                context_version=version,
                key=s.reference_provider_hmac_key,
                key_version=s.reference_provider_key_version,
                tariff_version=s.reference_geocoding_tariff_version,
                credential_version=s.reference_google_credential_version,
                reserved_usd_micros=s.reference_geocoding_reserved_usd_micros,
            )
            binding = _binding(
                context, payload.address_version, ShopAddress.model_validate(row["address"]), s.reference_google_api_key
            )
            try:
                ident = await session.scalar(
                    text("""SELECT public.business_address_geocode_request(
                  :business,:operation,:address,:context,:id,:origin,:effect,:event,:pilot,:mac,:binding,:key,
                  :tariff,:credential,:class,:amount)"""),
                    {
                        "business": business,
                        "operation": payload.operation_id,
                        "address": payload.address_version,
                        "context": version,
                        "id": job,
                        "origin": context.origin,
                        "effect": context.effect,
                        "event": context.event,
                        "pilot": context.pilot,
                        "mac": binding.request_mac,
                        "binding": binding.shop_mac,
                        "key": context.key_version,
                        "tariff": context.tariff_version,
                        "credential": context.credential_version,
                        "class": "geocode-v4:" + GEOCODING_FIELD_MASK,
                        "amount": context.reserved_usd_micros,
                    },
                )
            except DBAPIError as error:
                raise _translate(error) from None
            return await self._read(session, tenant, business, geocode=ident)

    async def confirm(self, tenant: UUID, business: UUID, actor: UUID, payload: GeocodeConfirmation) -> GeocodeRead:
        async with self.database.transaction(tenant, actor) as session:
            await BusinessAddressService._authorize(session, tenant, business)
            try:
                await session.execute(
                    text(
                        "SELECT public.business_address_geocode_confirm(:business,:id,:operation,:candidate,:address)"
                    ),
                    {
                        "business": business,
                        "id": payload.geocode_id,
                        "operation": payload.operation_id,
                        "candidate": payload.candidate_id,
                        "address": payload.address_version,
                    },
                )
            except DBAPIError as error:
                raise _translate(error) from None
            return await self._read(session, tenant, business, geocode=payload.geocode_id)


class BusinessGeocodingRunner:
    def __init__(self, database: Database, settings: Settings, *, transport: httpx.AsyncBaseTransport | None = None):
        self.database, self.settings, self.transport = database, settings, transport

    async def run(self, event: BusinessEvent) -> str:
        if not self.settings.reference_geocoding_ready():
            raise GeocodingError("GEOCODING_DISABLED")
        tenant, business, actor, job, event_id = map(
            UUID, (event.tenant_id, event.business_id, event.actor_id, event.operation_id, event.event_id)
        )
        async with self.database.transaction(tenant, actor) as session:
            row = await session.scalar(
                text("SELECT public.business_address_geocode_load(:business,:id,:event)"),
                {"business": business, "id": job, "event": event_id},
            )
        if row["status"] != "pending":
            return str(row["status"])
        if row["effect_state"] != "pending":
            # A lost response is not evidence that the provider was never called.
            async with self.database.transaction(tenant, actor) as session:
                await session.execute(
                    text("SELECT public.business_address_geocode_uncertain(:effect,:token)"),
                    {"effect": UUID(row["effect_id"]), "token": UUID(row["executor_token"])},
                )
            return "uncertain"
        s = self.settings
        assert s.reference_provider_hmac_key and s.reference_google_api_key
        if (
            row["key_version"] != s.reference_provider_key_version
            or row["credential_version"] != s.reference_google_credential_version
        ):
            raise GeocodingError("GEOCODING_CONFIGURATION_CHANGED")
        context = GeocodingGuardContext(
            tenant=tenant,
            business=business,
            actor=actor,
            origin=UUID(row["origin_id"]),
            effect=UUID(row["effect_id"]),
            event=UUID(row["effect_event_id"]),
            pilot=UUID(row["pilot_id"]),
            context_version=row["context_version"],
            key=s.reference_provider_hmac_key,
            key_version=row["key_version"],
            tariff_version=row["tariff_version"],
            credential_version=row["credential_version"],
            reserved_usd_micros=row["reserved_usd_micros"],
        )
        address = ShopAddress.model_validate(row["address"])
        binding = _binding(context, row["address_version"], address, s.reference_google_api_key)
        if not hmac.compare_digest(binding.request_mac, row["request_mac"]) or not hmac.compare_digest(
            binding.shop_mac, row["binding_mac"]
        ):
            raise GeocodingError("GEOCODING_BINDING_INVALID")
        guard = DatabaseGeocodingBudgetGuard(self.database, context, shop_address=True)
        provider = GoogleGeocoding(key=s.reference_google_api_key, guard=guard, enabled=True, transport=self.transport)
        try:
            results = await provider.geocode(shop_geocode_address_text(address), context.effect)
        except GeocodingError as error:
            if str(error) == "GEOCODING_RESULT_UNCERTAIN":
                return "uncertain"
            raise
        automatic = automatic_location_candidate(address, results)
        options = [
            {"id": str(uuid5(job, f"candidate:{index}")), "latitude": item.latitude, "longitude": item.longitude}
            for index, item in enumerate(results)
        ]
        chosen = next(
            (UUID(str(option["id"])) for option, item in zip(options, results, strict=True) if item is automatic), None
        )
        async with self.database.transaction(tenant, actor) as session:
            return str(
                await session.scalar(
                    text(
                        "SELECT public.business_address_geocode_complete("
                        ":business,:id,:token,CAST(:candidates AS jsonb),:chosen)"
                    ),
                    {
                        "business": business,
                        "id": job,
                        "token": guard.executor_token,
                        "candidates": json.dumps(options),
                        "chosen": chosen,
                    },
                )
            )
