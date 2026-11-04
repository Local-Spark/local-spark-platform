"""Fenced geocoding guard; shop mode consumes durable saved-address intents."""

from dataclasses import dataclass
from uuid import UUID

from pydantic import SecretStr
from sqlalchemy import text

from app.adapters.google_geocoding import GeocodingChargeableRequest
from app.db.session import Database
from app.services.reference_geocoding_request_mac import geocoding_request_mac


class GeocodingGuardError(Exception):
    """Stable code without an address, coordinates or provider output."""


@dataclass(frozen=True, repr=False)
class GeocodingGuardContext:
    tenant: UUID
    business: UUID
    actor: UUID
    origin: UUID
    effect: UUID
    event: UUID
    pilot: UUID
    context_version: int
    key: SecretStr
    key_version: str
    tariff_version: str
    credential_version: str
    reserved_usd_micros: int


class DatabaseGeocodingBudgetGuard:
    def __init__(self, database: Database, context: GeocodingGuardContext, *, shop_address: bool = False) -> None:
        self._shop_address = shop_address
        self._database = database
        self._context = context
        self._attempted = False
        self._token: UUID | None = None

    async def claim(self, operation_id: UUID, request: GeocodingChargeableRequest) -> bool:
        if self._attempted or operation_id != self._context.effect:
            return False
        self._attempted = True
        c = self._context
        mac = geocoding_request_mac(
            c.key,
            key_version=c.key_version,
            tariff_version=c.tariff_version,
            credential_version=c.credential_version,
            tenant=c.tenant,
            business=c.business,
            actor=c.actor,
            origin=c.origin,
            effect=c.effect,
            pilot=c.pilot,
            context_version=c.context_version,
            reserved_usd_micros=c.reserved_usd_micros,
            request=request,
        )
        async with self._database.transaction(c.tenant, c.actor) as session:
            result = await session.scalar(
                text(
                    (
                        """SELECT public.reference_geocode_claim(
              :business,:effect,:event,:origin,:pilot,:mac,:key,:tariff,:credential,:class,:amount,:context)"""
                    ).replace(
                        "reference_geocode_claim",
                        "business_address_geocode_claim" if self._shop_address else "reference_geocode_claim",
                    )
                ),
                {
                    "business": c.business,
                    "effect": c.effect,
                    "event": c.event,
                    "origin": c.origin,
                    "pilot": c.pilot,
                    "mac": mac,
                    "key": c.key_version,
                    "tariff": c.tariff_version,
                    "credential": c.credential_version,
                    "class": "geocode-v4:" + request.field_mask,
                    "amount": c.reserved_usd_micros,
                    "context": c.context_version,
                },
            )
        if result["created"] is not True:
            return False
        self._token = UUID(result["executor_token"])
        return True

    @property
    def executor_token(self) -> UUID:
        if self._token is None:
            raise GeocodingGuardError("GEOCODING_EXECUTOR_NOT_CLAIMED")
        return self._token

    async def uncertain(self) -> None:
        if self._token is None:
            raise GeocodingGuardError("GEOCODING_EXECUTOR_NOT_CLAIMED")
        c = self._context
        async with self._database.transaction(c.tenant, c.actor) as session:
            await session.execute(
                text(
                    "SELECT public."
                    + ("business_address_geocode_uncertain" if self._shop_address else "reference_geocode_uncertain")
                    + "(:effect,:token)"
                ),
                {"effect": c.effect, "token": self._token},
            )
