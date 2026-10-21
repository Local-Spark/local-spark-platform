"""Short, explicit units of work; no session state survives pool reuse."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings


class Database:
    def __init__(self, settings: Settings, *, relay: bool = False, auth: bool = False, billing: bool = False) -> None:
        url = (
            settings.billing_database_url
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
                    "application_name": "local-spark-billing"
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
            result = await session.execute(text("SELECT 1 FROM alembic_version LIMIT 1"))
            return result.scalar_one_or_none() == 1

    async def close(self) -> None:
        await self.engine.dispose()
