"""CI only: verify migration downgrade in its own disposable database."""

import asyncio
import os
import subprocess
from uuid import uuid4

from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import create_async_engine


async def main() -> None:
    if os.getenv("CI") != "true":
        raise SystemExit("This command is restricted to CI")
    admin = make_url(os.environ["TEST_ADMIN_DATABASE_URL"])
    if admin.host not in {"127.0.0.1", "localhost"} or not (admin.database or "").endswith("_test"):
        raise SystemExit("Refusing to create rollback database outside the local test server")
    database = f"mbd_rollback_{uuid4().hex}_test"
    admin_engine = create_async_engine(admin.set(database="postgres"), isolation_level="AUTOCOMMIT")
    migration_env = os.environ.copy()
    migration_env["MEU_BRACO_DIREITO_MIGRATION_DATABASE_URL"] = admin.set(database=database).render_as_string(
        hide_password=False
    )
    created = False
    try:
        async with admin_engine.connect() as connection:
            await connection.execute(text(f'CREATE DATABASE "{database}"'))
        created = True
        for target in ("head", "base", "head"):
            command = "downgrade" if target == "base" else "upgrade"
            await asyncio.to_thread(subprocess.run, ["alembic", command, target], env=migration_env, check=True)
    finally:
        if created:
            async with admin_engine.connect() as connection:
                await connection.execute(text(f'DROP DATABASE "{database}"'))
        await admin_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
