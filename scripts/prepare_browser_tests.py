"""Seed/reset only bundled identities in a loopback database explicitly ending in _test."""

import asyncio
import os
from uuid import UUID

from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from scripts.seed_operator import main as seed


async def main():
    settings = get_settings()
    url = os.environ["MEU_BRACO_DIREITO_MIGRATION_DATABASE_URL"]
    parsed = make_url(url)
    if not (parsed.database or "").endswith("_test") or parsed.host not in {"localhost", "127.0.0.1"}:
        raise SystemExit("Browser setup requires an isolated loopback _test database")
    for name, login in (("Authentication", settings.auth_database_url), ("Billing", settings.billing_database_url)):
        if login is None:
            raise SystemExit(f"{name} test database URL is required")
        other = make_url(login.get_secret_value())
        if (other.host, other.port, other.database) != (parsed.host, parsed.port, parsed.database):
            raise SystemExit(f"{name} must use the same test database")
    await seed()
    engine = create_async_engine(url, hide_parameters=True)
    async with engine.begin() as db:
        for sub in ("11111111-1111-4111-8111-111111111111", "22222222-2222-4222-8222-222222222222"):
            actor = {
                "11111111-1111-4111-8111-111111111111": UUID("428f23bf-7d6b-55be-9150-792093ef0a4c"),
                "22222222-2222-4222-8222-222222222222": UUID("5cdbeb2a-4fe3-50a0-a292-c8a8a238e49c"),
            }[sub]
            await db.execute(
                text("UPDATE auth_credentials SET mfa_secret=NULL,mfa_step=-1,recovery_hashes='[]' WHERE user_id=:id"),
                {"id": actor},
            )
            await db.execute(text("UPDATE auth_sessions SET revoked=true WHERE user_id=:id"), {"id": actor})
        await db.execute(text("DELETE FROM auth_limits"))
    await engine.dispose()
    print("Isolated browser fixtures prepared; main application database untouched.")


if __name__ == "__main__":
    asyncio.run(main())
