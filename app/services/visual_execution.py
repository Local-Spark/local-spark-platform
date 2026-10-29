"""Explicit opt-in for the wired visual path, independent of isolated adapters."""

from app.core.config import Settings
from app.services.auth import AuthError


def require_visual_execution(settings: Settings) -> None:
    # Recheck at the effect boundary too: a model_copy or injected dependency is
    # not proof that the startup validator ran. No secrets enter the error code.
    if not settings.visual_execution_ready():
        raise AuthError("VISUAL_EXECUTION_DISABLED", 409)
