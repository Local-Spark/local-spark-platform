"""Seed only the two local demo accounts; preserve their IDs and existing passwords/MFA."""

import asyncio
import os
from uuid import UUID

from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.core.passwords import Passwords


async def main():
    settings = get_settings()
    url = os.environ["MEU_BRACO_DIREITO_MIGRATION_DATABASE_URL"]
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
IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_identity') THEN
CREATE ROLE meu_braco_direito_identity LOGIN PASSWORD 'meu-braco-direito-auth-password'
NOSUPERUSER NOBYPASSRLS;
END IF;
IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='meu_braco_direito_payments') THEN
CREATE ROLE meu_braco_direito_payments LOGIN PASSWORD 'meu-braco-direito-billing-password' NOSUPERUSER NOBYPASSRLS;
END IF; END $$
""")
        )
        await connection.execute(text("GRANT meu_braco_direito_auth TO meu_braco_direito_identity"))
        await connection.execute(text("GRANT meu_braco_direito_billing TO meu_braco_direito_payments"))
        await connection.execute(text("GRANT SELECT ON alembic_version TO meu_braco_direito_auth"))
        for sub, email, name, password in (
            (
                "11111111-1111-4111-8111-111111111111",
                "operator@meu-braco-direito.local",
                "Equipe Meu Braço Direito",
                "MeuBracoDireito-Operator-2026!",
            ),
            (
                "22222222-2222-4222-8222-222222222222",
                "cliente@meu-braco-direito.local",
                "Cliente Meu Braço Direito",
                "MeuBracoDireito-Client-2026!",
            ),
        ):
            actor = {
                "11111111-1111-4111-8111-111111111111": UUID("428f23bf-7d6b-55be-9150-792093ef0a4c"),
                "22222222-2222-4222-8222-222222222222": UUID("5cdbeb2a-4fe3-50a0-a292-c8a8a238e49c"),
            }[sub]
            await connection.execute(
                text("""
INSERT INTO user_accounts(id,issuer,subject,display_name,email,email_verified)
VALUES (:id,'meu-braco-direito',:subject,:name,:email,true) ON CONFLICT(id) DO NOTHING
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
