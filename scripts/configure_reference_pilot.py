"""Prepare one local USD 5 pilot; never reset spending or enable provider flags.

Run with --apply only after reviewing the default JSON plan. Credentials are read
from the environment and never included in output. This is an administrator
operation, not an API available to customers or workers.
"""

import argparse
import asyncio
import json
import os
import re
from dataclasses import asdict, dataclass
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from app.adapters.google_geocoding import GEOCODING_FIELD_MASK
from app.adapters.google_places import PLACES_FIELD_MASK
from app.core.config import get_settings

PILOT_ID = uuid5(NAMESPACE_URL, "meu-braco-direito/reference-pilot/2026-11-04/usd-5")
POLICY_ID = uuid5(PILOT_ID, "policy-v2")
PREVIOUS_POLICY_ID = uuid5(PILOT_ID, "policy-v1")
CAP = 5_000_000
PROVIDER_LIMITS = {"google": (150_000, 500_000), "jev": (250_000, 500_000), "apify": (800_000, 4_000_000)}


@dataclass(frozen=True)
class Tariff:
    version: str
    provider: str
    field_mask: str
    reserve: int


def tariffs(contacts_build: str, feed_build: str) -> tuple[Tariff, ...]:
    if any(
        re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value) is None or len(value) > 24
        for value in (contacts_build, feed_build)
    ):
        raise ValueError("REFERENCE_PILOT_BUILD_INVALID")
    return (
        Tariff("pilot-20261104-google-nearby", "google", PLACES_FIELD_MASK, 35_000),
        Tariff("pilot-20261104-google-geocode", "google", "geocode-v4:" + GEOCODING_FIELD_MASK, 5_000),
        Tariff("pilot-20261104-jev-1.14", "jev", "jev-model:jev-1.14.0", 3_000),
        Tariff(f"pilot-20261104-contacts-{contacts_build}", "apify", f"apify-place-contacts:{contacts_build}", 500_000),
        Tariff(f"pilot-20261104-feed-{feed_build}", "apify", f"apify-instagram-feed:{feed_build}", 100_000),
    )


def validate_local_database(environment: str, admin_url: str, runtime_url: str) -> None:
    admin, runtime = make_url(admin_url), make_url(runtime_url)
    if environment not in {"development", "testing"} or admin.host not in {"localhost", "127.0.0.1"}:
        raise ValueError("REFERENCE_PILOT_LOCAL_ONLY")
    if (
        admin.drivername != "postgresql+asyncpg"
        or not admin.database
        or (admin.host, admin.port, admin.database) != (runtime.host, runtime.port, runtime.database)
    ):
        raise ValueError("REFERENCE_PILOT_DATABASE_MISMATCH")
    if admin.username == runtime.username:
        raise ValueError("REFERENCE_PILOT_ADMIN_ROLE_REQUIRED")
    if environment == "testing" and not admin.database.endswith("_test"):
        raise ValueError("REFERENCE_PILOT_TEST_DATABASE_REQUIRED")


async def configure(connection: AsyncConnection, prices: tuple[Tariff, ...]) -> None:
    """Caller owns the transaction; all validations roll back the entire setup."""
    await connection.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('reference-cost-guard',70))"))
    existing = (
        await connection.execute(text("SELECT id,cap_usd_micros FROM reference_provider_pilots FOR UPDATE"))
    ).first()
    if existing is not None and tuple(existing) != (PILOT_ID, CAP):
        raise ValueError("REFERENCE_PILOT_EXISTING_CONFIGURATION")
    head = await connection.scalar(text("SELECT policy_id FROM reference_cost_policy_head FOR UPDATE"))
    if head is not None and head not in {POLICY_ID, PREVIOUS_POLICY_ID}:
        raise ValueError("REFERENCE_PILOT_EXISTING_POLICY")
    if head == PREVIOUS_POLICY_ID:
        previous = (
            await connection.execute(
                text("SELECT timezone,per_search,monthly_total FROM reference_cost_policies WHERE id=:id"),
                {"id": PREVIOUS_POLICY_ID},
            )
        ).one()
        providers = (
            await connection.execute(
                text(
                    "SELECT provider,per_search,monthly_total FROM reference_cost_policy_providers WHERE policy_id=:id"
                ),
                {"id": PREVIOUS_POLICY_ID},
            )
        ).all()
        if tuple(previous) != ("UTC", 1_000_000, CAP) or {row[0]: tuple(row[1:]) for row in providers} != {
            "google": (150_000, 500_000),
            "jev": (50_000, 250_000),
            "apify": (800_000, 4_250_000),
        }:
            raise ValueError("REFERENCE_PILOT_PREVIOUS_POLICY_CONFLICT")
    await connection.execute(
        text("""INSERT INTO reference_cost_policies(id,timezone,per_search,monthly_total)
      VALUES(:id,'UTC',1000000,:cap) ON CONFLICT(id) DO NOTHING"""),
        {"id": POLICY_ID, "cap": CAP},
    )
    policy = (
        await connection.execute(
            text("""SELECT timezone,per_search,monthly_total
      FROM reference_cost_policies WHERE id=:id"""),
            {"id": POLICY_ID},
        )
    ).one()
    if tuple(policy) != ("UTC", 1_000_000, CAP):
        raise ValueError("REFERENCE_PILOT_POLICY_CONFLICT")
    for provider, (search, monthly) in PROVIDER_LIMITS.items():
        values = {"id": POLICY_ID, "provider": provider, "search": search, "monthly": monthly}
        await connection.execute(
            text("""INSERT INTO reference_cost_policy_providers
          (policy_id,provider,per_search,monthly_total) SELECT :id,:provider,:search,:monthly
          WHERE NOT EXISTS(SELECT 1 FROM reference_cost_policy_providers
            WHERE policy_id=:id AND provider=:provider)"""),
            values,
        )
        row = (
            await connection.execute(
                text("""SELECT per_search,monthly_total FROM reference_cost_policy_providers
          WHERE policy_id=:id AND provider=:provider"""),
                values,
            )
        ).one()
        if tuple(row) != (search, monthly):
            raise ValueError("REFERENCE_PILOT_POLICY_CONFLICT")
    for price in prices:
        values = asdict(price)
        await connection.execute(
            text("""INSERT INTO reference_provider_tariffs
          (version,provider,field_mask,minimum_reserved_usd_micros,active)
          VALUES(:version,:provider,:field_mask,:reserve,true) ON CONFLICT(version) DO NOTHING"""),
            values,
        )
        row = (
            await connection.execute(
                text("""SELECT provider,field_mask,minimum_reserved_usd_micros
          FROM reference_provider_tariffs WHERE version=:version"""),
                values,
            )
        ).one()
        if tuple(row) != (price.provider, price.field_mask, price.reserve):
            raise ValueError("REFERENCE_PILOT_TARIFF_CONFLICT")
        await connection.execute(
            text("UPDATE reference_provider_tariffs SET active=true WHERE version=:version"), values
        )
    await connection.execute(
        text("""INSERT INTO reference_provider_pilots(id,cap_usd_micros,active)
      VALUES(:id,:cap,true) ON CONFLICT(singleton) DO UPDATE SET active=true"""),
        {"id": PILOT_ID, "cap": CAP},
    )
    await connection.execute(
        text("UPDATE reference_cost_policy_head SET policy_id=:id WHERE singleton"), {"id": POLICY_ID}
    )


def plan(prices: tuple[Tariff, ...]) -> dict[str, object]:
    return {
        "pilot_id": str(PILOT_ID),
        "policy_id": str(POLICY_ID),
        "total_cap_usd_micros": CAP,
        "per_search_usd_micros": 1_000_000,
        "provider_limits_usd_micros": PROVIDER_LIMITS,
        "tariffs": [asdict(price) for price in prices],
        "provider_flags_enabled": False,
    }


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contacts-build", required=True)
    parser.add_argument("--feed-build", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    prices = tariffs(args.contacts_build, args.feed_build)
    if args.apply:
        settings = get_settings()
        url = os.environ["MEU_BRACO_DIREITO_MIGRATION_DATABASE_URL"]
        validate_local_database(settings.environment, url, settings.database_url.get_secret_value())
        engine = create_async_engine(url, hide_parameters=True)
        try:
            async with engine.begin() as connection:
                await configure(connection, prices)
        finally:
            await engine.dispose()
    print(json.dumps({**plan(prices), "applied": args.apply}, indent=2))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        raise SystemExit("Reference pilot setup failed; no credentials or database details were printed.") from None
