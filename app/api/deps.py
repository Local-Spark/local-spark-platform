from collections.abc import AsyncIterator
from typing import Annotated, cast
from uuid import UUID

import jwt
from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.identity import Identity
from app.db.session import Database

bearer = HTTPBearer(auto_error=False)


async def get_actor(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> UUID:
    if credentials is None:
        raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})
    try:
        identity = await request.app.state.identity_verifier.authenticate(credentials.credentials)
        request.state.identity = identity
        return cast(UUID, identity.actor_id)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(401, "Invalid access token", headers={"WWW-Authenticate": "Bearer"}) from exc


Actor = Annotated[UUID, Depends(get_actor)]
Tenant = Annotated[UUID, Header(alias="X-Tenant-ID")]


async def get_session(request: Request, actor: Actor, x_tenant_id: Tenant) -> AsyncIterator[AsyncSession]:
    database = cast(Database, request.app.state.database)
    async with database.transaction(x_tenant_id, actor) as session:
        yield session


Session = Annotated[AsyncSession, Depends(get_session, scope="function")]


async def get_identity(request: Request, actor: Actor) -> Identity:
    return cast(Identity, request.state.identity)


Principal = Annotated[Identity, Depends(get_identity)]


async def get_actor_session(request: Request, actor: Actor) -> AsyncIterator[AsyncSession]:
    database = cast(Database, request.app.state.database)
    async with database.transaction(UUID(int=0), actor) as session:
        yield session


ActorSession = Annotated[AsyncSession, Depends(get_actor_session, scope="function")]
