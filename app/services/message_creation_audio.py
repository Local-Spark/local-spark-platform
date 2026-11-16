"""Shared bounded audio normalization and one-shot transcription."""

from uuid import uuid5

from app.adapters.audio_transcription import OpenAIAudioTranscriber, normalize_audio
from app.adapters.material_media import MaterialStore
from app.services.audio_costs import TARIFF_VERSION, TRANSCRIPTION_MODEL, transcription_cost
from app.services.auth import AuthError


async def transcribe_message(coordinator, row, token, material, authorize):
    settings = coordinator.settings
    if settings.audio_transcription_mode != "openai" or not settings.openai_api_key:
        raise AuthError("AUDIO_TRANSCRIPTION_NOT_CONFIGURED", 409)
    audio, seconds = await normalize_audio(await MaterialStore(settings).get_audio(material["object_key"]))
    reserve, estimate = transcription_cost(seconds)
    operation = uuid5(row["id"], "message-transcription")

    async def admission(session):
        await authorize(session)
        if row["origin"] == "whatsapp":
            from sqlalchemy import text

            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:tenant,0))"), {"tenant": str(row["tenant_id"])}
            )
            used = await session.scalar(
                text("""SELECT coalesce(sum(reserved_seconds),0) FROM audio_transcription_usage
              WHERE tenant_id=:tenant AND created_at>=date_trunc('day',now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'"""),
                {"tenant": row["tenant_id"]},
            )
            if used + seconds > settings.audio_daily_seconds_limit:
                raise AuthError("AUDIO_BUDGET_EXCEEDED", 409)
            await session.execute(
                text("""INSERT INTO audio_transcription_usage(event_id,tenant_id,business_id,reserved_seconds,state)
              VALUES(:source,:tenant,:business,:seconds,'submitted')"""),
                {
                    "source": row["source_event_id"],
                    "tenant": row["tenant_id"],
                    "business": row["business_id"],
                    "seconds": seconds,
                },
            )

    await coordinator.execution.claim(
        row["actor_id"],
        row["id"],
        token,
        operation,
        "transcription",
        {
            "model": TRANSCRIPTION_MODEL,
            "tariff_version": TARIFF_VERSION,
            "sha256": material["sha256"],
            "seconds": seconds,
        },
        reserve=reserve,
        provider="openai",
        model=TRANSCRIPTION_MODEL,
        authorize=admission,
    )
    await coordinator.execution.submitted(row["actor_id"], row["id"], token, operation)
    message = await OpenAIAudioTranscriber(settings).transcribe(audio, operation)
    await coordinator.execution.received(
        row["actor_id"], row["id"], token, operation, {"transcript": message}, estimate
    )
    if len(message) > 4000:
        raise AuthError("MESSAGE_TRANSCRIPT_TOO_LONG", 422)
    return message
