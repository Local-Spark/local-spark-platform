"""Fictitious effect intent; never accepts real identifiers or calls a provider."""

import hashlib
import hmac
import json
from uuid import UUID, uuid5

from sqlalchemy import text

from app.core.config import Settings
from app.db.session import Database
from app.services.auth import AuthError
from app.services.whatsapp_materials import WhatsAppMaterialsService

# Closed fixture set prevents real place IDs and social accounts entering this simulation.
FIXTURES = {"fixture_place_1": "google", "fixture_profile_1": "apify", "fixture_jev_1": "jev"}
FIXTURE_RESERVATION = 1


def fixture_mac(
    settings: Settings,
    tenant: UUID,
    business: UUID,
    actor: UUID,
    discovery: UUID,
    effect: UUID,
    fixture: str,
    provider: str,
    amount: int,
) -> str:
    if settings.reference_discovery_mode != "fake" or settings.environment not in {"development", "testing"}:
        raise AuthError("REFERENCE_FIXTURE_DISABLED", 503)
    key = settings.reference_fixture_hmac_key
    if key is None or len(key.get_secret_value().encode()) < 32:
        raise AuthError("REFERENCE_FIXTURE_KEY_REQUIRED", 503)
    if FIXTURES.get(fixture) != provider or amount != FIXTURE_RESERVATION:
        raise AuthError("REFERENCE_FIXTURE_INVALID", 422)
    payload = json.dumps(
        [
            "reference-fixture-v1",
            str(tenant),
            str(business),
            str(actor),
            str(discovery),
            str(effect),
            fixture,
            provider,
            amount,
        ],
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hmac.new(key.get_secret_value().encode(), payload.encode(), hashlib.sha256).hexdigest()


class ReferenceEffectSimulationService:
    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings, self.database = settings, database

    async def request(self, tenant: UUID, business: UUID, actor: UUID, discovery: UUID, fixture: str) -> UUID:
        provider = FIXTURES.get(fixture)
        if provider is None:
            raise AuthError("REFERENCE_FIXTURE_INVALID", 422)
        effect = uuid5(discovery, f"reference-fixture-v1:{fixture}")
        mac = fixture_mac(
            self.settings, tenant, business, actor, discovery, effect, fixture, provider, FIXTURE_RESERVATION
        )
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            exists = await session.scalar(
                text("""SELECT 1 FROM reference_discoveries
              WHERE tenant_id=:tenant AND business_id=:business AND actor_id=:actor AND id=:discovery
                AND state IN ('pending','simulated') FOR SHARE"""),
                {"tenant": tenant, "business": business, "actor": actor, "discovery": discovery},
            )
            if exists is None:
                raise AuthError("REFERENCE_DISCOVERY_NOT_PENDING", 409)
            row = (
                await session.execute(
                    text("""INSERT INTO reference_simulated_effects
              (id,tenant_id,business_id,actor_id,discovery_id,fixture,provider,reserved_usd_micros,request_mac,state)
              VALUES(:id,:tenant,:business,:actor,:discovery,:fixture,:provider,:amount,:mac,'pending')
              ON CONFLICT(tenant_id,id) DO NOTHING RETURNING id"""),
                    {
                        "id": effect,
                        "tenant": tenant,
                        "business": business,
                        "actor": actor,
                        "discovery": discovery,
                        "fixture": fixture,
                        "provider": provider,
                        "amount": FIXTURE_RESERVATION,
                        "mac": mac,
                    },
                )
            ).scalar_one_or_none()
            if row is None:
                existing = await session.scalar(
                    text("""SELECT request_mac FROM reference_simulated_effects
                  WHERE tenant_id=:tenant AND actor_id=:actor AND id=:id"""),
                    {"tenant": tenant, "actor": actor, "id": effect},
                )
                if existing is None or not hmac.compare_digest(existing, mac):
                    raise AuthError("REFERENCE_EFFECT_CONFLICT", 409)
                return effect
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
              VALUES(:tenant,:actor,:effect,'reference.effect_requested',:business)"""),
                {"tenant": tenant, "actor": actor, "effect": effect, "business": business},
            )
            await session.execute(
                text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
              VALUES(gen_random_uuid(),:tenant,'reference.effect_requested',CAST(:payload AS jsonb))"""),
                {
                    "tenant": tenant,
                    "payload": json.dumps(
                        {"business_id": str(business), "actor_id": str(actor), "operation_id": str(effect)}
                    ),
                },
            )
            return effect
