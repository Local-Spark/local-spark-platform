"""Protect the last-operator invariant if another revocation wins a race."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.identity import Identity
from app.services.auth import AuthError
from app.services.staff import StaffService


@pytest.mark.parametrize("remaining", [1, 2])
async def test_concurrent_revocation_cannot_remove_last_operator(settings, remaining):
    db = AsyncMock()
    # The actor passed the initial guard, but a competing transaction revoked
    # them before the advisory lock and count are read.
    db.scalar.side_effect = [True, 1, True, remaining]

    @asynccontextmanager
    async def transaction(*_args):
        yield db

    database = AsyncMock()
    database.transaction = transaction
    if remaining == 1:
        with pytest.raises(AuthError, match="LAST_OPERATOR"):
            await StaffService(settings, database).revoke_operator(uuid4(), uuid4())
    else:
        await StaffService(settings, database).revoke_operator(uuid4(), uuid4())
    assert db.scalar.await_count == 4


async def test_accept_rechecks_invitation_after_lock(settings):
    actor, invitation = uuid4(), uuid4()
    db = AsyncMock()
    preview = MagicMock()
    preview.mappings.return_value.one_or_none.return_value = {"id": invitation, "email": "invitee@example.com"}
    locked = MagicMock()
    locked.mappings.return_value.one_or_none.return_value = None
    db.execute.side_effect = [MagicMock(), preview, locked]

    @asynccontextmanager
    async def transaction(*_args):
        yield db

    database = AsyncMock()
    database.transaction = transaction
    identity = Identity(actor, "test", str(actor), "Invitee", "invitee@example.com", True)
    with pytest.raises(AuthError, match="INVALID_INVITATION"):
        await StaffService(settings, database).accept(identity, "valid-token")
    assert db.execute.await_count == 3
