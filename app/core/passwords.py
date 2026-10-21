"""Bounded password work outside the event loop; no home-grown password cryptography."""

import secrets
from functools import partial

import anyio
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError


class Passwords:
    def __init__(self, concurrency: int = 4) -> None:
        self.hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)
        self.limiter = anyio.CapacityLimiter(concurrency)
        self.dummy = self.hasher.hash(secrets.token_urlsafe(32))

    async def hash(self, password: str) -> str:
        return await anyio.to_thread.run_sync(self.hasher.hash, password, limiter=self.limiter)

    async def verify(self, password: str, digest: str | None) -> bool:
        try:
            result = await anyio.to_thread.run_sync(
                partial(self.hasher.verify, digest or self.dummy, password), limiter=self.limiter
            )
        except (VerificationError, InvalidHashError):
            return False
        return result and digest is not None
