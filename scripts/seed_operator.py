"""Seed only the two local demo accounts; preserve their IDs and existing passwords/MFA."""

import asyncio
import os

from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.core.identity import actor_for_subject
from app.core.passwords import Passwords


async def main():
    settings = get_settings()
    url = os.environ["LOCAL_SPARK_MIGRATION_DATABASE_URL"]
    parsed, runtime = make_url(url), make_url(settings.database_url.get_secret_value())
    if settings.environment != "development" or parsed.host not in {"localhost", "127.0.0.1"}:
        raise SystemExit("Local development database required")
    if (parsed.host, parsed.port, parsed.database) != (runtime.host, runtime.port, runtime.database):
        raise SystemExit("Migration and runtime databases must match")
    passwords = Passwords()
    engine = create_async_engine(url, hide_parameters=True)
    async with engine.begin() as connection:
        await connection.execute(
            text("""
DO $$ BEGIN
IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='local_spark_identity') THEN
CREATE ROLE local_spark_identity LOGIN PASSWORD 'local-spark-auth-password'
NOSUPERUSER NOBYPASSRLS;
END IF;
IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='local_spark_payments') THEN
CREATE ROLE local_spark_payments LOGIN PASSWORD 'local-spark-billing-password' NOSUPERUSER NOBYPASSRLS;
END IF; END $$
""")
        )
        await connection.execute(text("GRANT local_spark_auth TO local_spark_identity"))
        await connection.execute(text("GRANT local_spark_billing TO local_spark_payments"))
        await connection.execute(text("GRANT SELECT ON alembic_version TO local_spark_auth"))
        for sub, email, name, password in (
            (
                "11111111-1111-4111-8111-111111111111",
                "operator@local-spark.local",
                "Equipe Local Spark",
                "LocalSpark-Operator-2026!",
            ),
            (
                "22222222-2222-4222-8222-222222222222",
                "cliente@local-spark.local",
                "Cliente Local Spark",
                "LocalSpark-Client-2026!",
            ),
        ):
            actor = actor_for_subject("http://localhost:8081/realms/local-spark", sub)
            await connection.execute(
                text("""
INSERT INTO user_accounts(id,issuer,subject,display_name,email,email_verified)
VALUES (:id,'local-spark',:subject,:name,:email,true) ON CONFLICT(id) DO NOTHING
"""),
                {"id": actor, "subject": str(actor), "name": name, "email": email},
            )
            hashed = await passwords.hash(password)
            await connection.execute(
                text("""
INSERT INTO auth_credentials(user_id,email,password_hash) VALUES (:id,:email,:hash)
ON CONFLICT(user_id) DO UPDATE SET password_hash=excluded.password_hash
WHERE auth_credentials.password_hash IS NULL
"""),
                {"id": actor, "email": email, "hash": hashed},
            )
            if sub.startswith("1111"):
                await connection.execute(
                    text("INSERT INTO platform_staff(actor_id) VALUES (:id) ON CONFLICT DO NOTHING"), {"id": actor}
                )
    await engine.dispose()
    print("Local demo identities ready. Existing IDs, passwords and MFA are preserved.")


if __name__ == "__main__":
    asyncio.run(main())
