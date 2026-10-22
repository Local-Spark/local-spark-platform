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
          IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='local_spark_runtime') THEN
            CREATE ROLE local_spark_runtime LOGIN PASSWORD 'local-spark-app-password' NOSUPERUSER NOBYPASSRLS;
          END IF;
          IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='local_spark_delivery') THEN
            CREATE ROLE local_spark_delivery LOGIN PASSWORD 'local-spark-relay-password' NOSUPERUSER NOBYPASSRLS;
          END IF;
          IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='local_spark_identity') THEN
            CREATE ROLE local_spark_identity LOGIN PASSWORD 'local-spark-auth-password' NOSUPERUSER NOBYPASSRLS;
          END IF;
          IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='local_spark_payments') THEN
            CREATE ROLE local_spark_payments LOGIN PASSWORD 'local-spark-billing-password' NOSUPERUSER NOBYPASSRLS;
          END IF;
          IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='local_spark_ingest') THEN
            CREATE ROLE local_spark_ingest LOGIN PASSWORD 'local-spark-meta-password' NOSUPERUSER NOBYPASSRLS;
          END IF;
        END $$""")
        )
        await connection.execute(text("GRANT local_spark_app TO local_spark_runtime"))
        await connection.execute(text("GRANT local_spark_relay TO local_spark_delivery"))
        await connection.execute(text("GRANT local_spark_auth TO local_spark_identity"))
        await connection.execute(text("GRANT local_spark_billing TO local_spark_payments"))
        await connection.execute(text("GRANT local_spark_meta TO local_spark_ingest"))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
