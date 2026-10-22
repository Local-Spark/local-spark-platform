"""Create restricted local test logins after migration. Never accepts a non-test database."""

import asyncio
import os

from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import create_async_engine


async def main():
    url = os.environ["TEST_ADMIN_DATABASE_URL"]
    name = make_url(url).database or ""
    if not name.endswith("_test"):
        raise SystemExit("Refusing test setup: database name must end in _test")
    engine = create_async_engine(url)
    async with engine.begin() as connection:
        await connection.execute(
            text("""DO $$ BEGIN
          IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_runtime') THEN
            CREATE ROLE meu_braco_direito_runtime LOGIN PASSWORD 'meu-braco-direito-app-password'
            NOSUPERUSER NOBYPASSRLS;
          END IF;
          IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_delivery') THEN
            CREATE ROLE meu_braco_direito_delivery LOGIN PASSWORD 'meu-braco-direito-relay-password'
            NOSUPERUSER NOBYPASSRLS;
          END IF;
          IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_identity') THEN
            CREATE ROLE meu_braco_direito_identity LOGIN PASSWORD 'meu-braco-direito-auth-password'
            NOSUPERUSER NOBYPASSRLS;
          END IF;
          IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_payments') THEN
            CREATE ROLE meu_braco_direito_payments LOGIN PASSWORD 'meu-braco-direito-billing-password'
            NOSUPERUSER NOBYPASSRLS;
          END IF;
          IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_ingest') THEN
            CREATE ROLE meu_braco_direito_ingest LOGIN PASSWORD 'meu-braco-direito-meta-password'
            NOSUPERUSER NOBYPASSRLS;
          END IF;
          IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_router') THEN
            CREATE ROLE meu_braco_direito_router LOGIN PASSWORD 'meu-braco-direito-router-password'
            NOSUPERUSER NOBYPASSRLS;
          END IF;
        END $$""")
        )
        await connection.execute(text("GRANT meu_braco_direito_app TO meu_braco_direito_runtime"))
        await connection.execute(text("GRANT meu_braco_direito_relay TO meu_braco_direito_delivery"))
        await connection.execute(text("GRANT meu_braco_direito_auth TO meu_braco_direito_identity"))
        await connection.execute(text("GRANT meu_braco_direito_billing TO meu_braco_direito_payments"))
        await connection.execute(text("GRANT meu_braco_direito_meta TO meu_braco_direito_ingest"))
        await connection.execute(text("GRANT meu_braco_direito_correlator TO meu_braco_direito_router"))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
