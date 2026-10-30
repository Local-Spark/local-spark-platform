"""Restrict a pending editorial grant to the already admitted visual attempt."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class VisualRunScope:
    tenant: UUID
    business: UUID
    actor: UUID
    operation: UUID
    fence: int
    preview: UUID | None = None
    skill_id: str | None = None
    skill_sha256: str | None = None
    visual_recipe: str = "legacy_overlay"


_scope: ContextVar[VisualRunScope | None] = ContextVar("editorial_visual_run_scope", default=None)


def current_visual_run() -> VisualRunScope | None:
    return _scope.get()


@contextmanager
def admitted_visual_run(scope: VisualRunScope) -> Iterator[None]:
    token = _scope.set(scope)
    try:
        yield
    finally:
        _scope.reset(token)
