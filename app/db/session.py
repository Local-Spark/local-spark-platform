"""Short, explicit units of work; no session state survives pool reuse."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from uuid import UUID

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings


@lru_cache
def current_schema_head() -> str:
    root = Path(__file__).resolve().parents[2]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    head = ScriptDirectory.from_config(config).get_current_head()
    if head is None:
        raise RuntimeError("No database migration head configured")
    return head


class Database:
    def __init__(
        self, settings: Settings, *, relay: bool = False, auth: bool = False, billing: bool = False, meta: bool = False
    ) -> None:
        url = (
            settings.meta_database_url
            if meta
            else settings.billing_database_url
            if billing
            else settings.auth_database_url
            if auth
            else settings.relay_database_url
            if relay
            else settings.database_url
        )
        if url is None:
            raise ValueError("Database URL must be configured explicitly for the restricted role")
        self.engine: AsyncEngine = create_async_engine(
            url.get_secret_value(),
            pool_pre_ping=True,
            hide_parameters=True,
            pool_size=settings.pool_size,
            max_overflow=settings.max_overflow,
            connect_args={
                "server_settings": {
                    "application_name": "local-spark-meta"
                    if meta
                    else "local-spark-billing"
                    if billing
                    else "local-spark-auth"
                    if auth
                    else "local-spark-relay"
                    if relay
                    else "local-spark-api"
                }
            },
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    @asynccontextmanager
    async def transaction(self, tenant_id: UUID, actor_id: UUID) -> AsyncIterator[AsyncSession]:
        async with self.sessions() as session, session.begin():
            await session.execute(
                text("SELECT set_config('app.tenant_id', :tenant, true), set_config('app.actor_id', :actor, true)"),
                {"tenant": str(tenant_id), "actor": str(actor_id)},
            )
            await session.execute(text("SET LOCAL lock_timeout = '3s'"))
            await session.execute(text("SET LOCAL statement_timeout = '10s'"))
            yield session

    async def ready(self) -> bool:
        async with self.sessions() as session:
            result = await session.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
            return result.scalar_one_or_none() == current_schema_head()

    async def close(self) -> None:
        await self.engine.dispose()
