"""Enable providers only inside the administrative adapter, with its own ledger."""

from app.core.config import Settings


def lab_settings(settings: Settings) -> Settings:
    if not settings.creation_lab_execution_enabled:
        return settings
    # Commercial settings/dispatchers remain unchanged. Private admission still
    # checks credentials, consent, explicit rates and both administrative caps.
    return settings.model_copy(
        update={
            "visual_ai_mode": "openai",
            "visual_ai_execution_enabled": True,
            "editorial_ai_mode": "openai",
            "intent_ai_mode": "jev",
            "motion_ai_mode": "openai",
            "motion_execution_enabled": True,
        }
    )
