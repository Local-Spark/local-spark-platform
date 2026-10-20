"""Explicit local-only identity bootstrap; never an HTTP authentication shortcut."""

import asyncio
import json
import os
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings


async def main():
    settings = get_settings()
    url = os.environ["LOCAL_SPARK_MIGRATION_DATABASE_URL"]
    parsed = make_url(url)
    if settings.environment != "development" or parsed.host not in {"localhost", "127.0.0.1"}:
        raise SystemExit("Development bootstrap requires development mode and a loopback database")
    runtime = make_url(settings.database_url.get_secret_value())
    if (parsed.host, parsed.port, parsed.database) != (runtime.host, runtime.port, runtime.database):
        raise SystemExit("Runtime and migration database targets must match")
    # Stable demo identities survive repository and deployment renames.
    tenant = UUID("255de89d-66b6-53b7-bffc-f63a049e63a1")
    actor = UUID("c4b041b8-4cf8-5c8f-b407-0d99b1733ea2")
    engine = create_async_engine(url)
    async with engine.begin() as connection:
        await connection.execute(
            text("INSERT INTO tenants(id,name) VALUES (:id,'Local demonstration') ON CONFLICT DO NOTHING"),
            {"id": tenant},
        )
        await connection.execute(
            text(
                "INSERT INTO memberships(tenant_id,actor_id,role) "
                "VALUES (:tenant,:actor,'owner') ON CONFLICT DO NOTHING"
            ),
            {"tenant": tenant, "actor": actor},
        )
    await engine.dispose()
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": str(actor),
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "iat": now,
            "exp": now + timedelta(hours=1),
        },
        settings.jwt_secret.get_secret_value(),
        algorithm="HS256",
    )
    print(json.dumps({"tenant_id": str(tenant), "actor_id": str(actor), "access_token": token}))


if __name__ == "__main__":
    asyncio.run(main())
