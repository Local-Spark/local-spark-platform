"""Reserve per-tenant speech budget before an at-most-once provider submission."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from cryptography.fernet import Fernet
from sqlalchemy import text

from app.adapters.audio_transcription import OpenAIAudioTranscriber, normalize_audio
from app.adapters.material_media import MaterialError
from app.db.session import Database
from app.services.whatsapp_processing import MaterialProcessor


async def reconcile_stale_audio(database: Database, limit: int = 100) -> int:
    """A lost one-shot activity becomes uncertain, never an automatic paid retry."""
    async with database.sessions() as session, session.begin():
        rows = (
            (
                await session.execute(
                    text("""WITH due AS (
                  SELECT event_id FROM audio_transcription_usage
                  WHERE state='submitted' AND created_at<now()-interval '5 minutes'
                  ORDER BY created_at,event_id LIMIT :limit FOR UPDATE SKIP LOCKED)
                  UPDATE audio_transcription_usage u SET state='uncertain'
                  FROM due WHERE u.event_id=due.event_id
                  RETURNING u.event_id,u.tenant_id,u.business_id"""),
                    {"limit": limit},
                )
            )
            .mappings()
            .all()
        )
        for row in rows:
            await session.execute(
                text("""UPDATE whatsapp_material_assets SET transcription_state='uncertain',
                  transcription_error='AUDIO_RESULT_UNCERTAIN'
                  WHERE id=:event AND transcription_state='submitted'"""),
                {"event": row["event_id"]},
            )
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
                  VALUES(:tenant,:actor,:operation,'whatsapp.audio_uncertain',:event)"""),
                {"tenant": row["tenant_id"], "actor": UUID(int=0), "operation": uuid4(), "event": row["event_id"]},
            )
        return len(rows)


class AudioTranscriptionService:
    def __init__(self, processor: MaterialProcessor, provider: OpenAIAudioTranscriber) -> None:
        self.processor, self.provider = processor, provider

    async def _row(self, session, event: UUID):  # type: ignore[no-untyped-def]
        return (
            (
                await session.execute(
                    text("""SELECT a.id,a.tenant_id,a.business_id,a.kind,a.object_key,
                  a.transcription_state,a.delete_requested_at,a.expires_at,
                  e.sender_hash,e.created_at,e.expires_at AS event_expires
                  FROM whatsapp_material_assets a JOIN whatsapp_material_events e ON e.id=a.id
                  WHERE a.id=:event FOR UPDATE OF a"""),
                    {"event": event},
                )
            )
            .mappings()
            .one_or_none()
        )

    async def _eligible(self, session, row) -> bool:  # type: ignore[no-untyped-def]
        base = bool(
            row["delete_requested_at"] is None
            and row["expires_at"] > datetime.now(UTC)
            and await self.processor._eligible(
                session,
                {
                    "tenant_id": row["tenant_id"],
                    "business_id": row["business_id"],
                    "sender_hash": row["sender_hash"],
                    "created_at": row["created_at"],
                    "expires_at": row["event_expires"],
                },
            )
        )
        if not base:
            return False
        return bool(
            await session.scalar(
                text("""SELECT audio_transcription_accepted_at IS NOT NULL
          FROM whatsapp_processing_consents WHERE tenant_id=:tenant AND business_id=:business
            AND revoked_at IS NULL"""),
                {"tenant": row["tenant_id"], "business": row["business_id"]},
            )
        )

    @staticmethod
    async def _audit(session, row, event: UUID, action: str) -> None:  # type: ignore[no-untyped-def]
        await session.execute(
            text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
              VALUES(:tenant,:actor,:operation,:action,:event)"""),
            {"tenant": row["tenant_id"], "actor": UUID(int=0), "operation": uuid4(), "action": action, "event": event},
        )

    async def _reject(self, event: UUID, code: str) -> str:
        async with self.processor.database.sessions() as session, session.begin():
            row = await self._row(session, event)
            if row is None or row["transcription_state"] is not None:
                return "skipped"
            await session.execute(
                text("""UPDATE whatsapp_material_assets SET transcription_state='rejected',
                  transcription_error=:code WHERE id=:event"""),
                {"event": event, "code": code},
            )
            await self._audit(session, row, event, "whatsapp.audio_rejected")
        return "rejected"

    async def run(self, event: UUID) -> str:
        settings = self.processor.settings
        if settings.audio_transcription_mode != "openai":
            return "disabled"
        async with self.processor.database.sessions() as session, session.begin():
            row = await self._row(session, event)
            if row is None or row["kind"] != "audio" or row["transcription_state"] is not None:
                return "skipped"
            if not await self._eligible(session, row):
                return "skipped"
            key = row["object_key"]
        if not key:
            return await self._reject(event, "AUDIO_MISSING")
        try:
            audio, seconds = await normalize_audio(await self.processor.store.get_audio(key))
        except MaterialError as exc:
            if exc.retryable:
                raise
            return await self._reject(event, exc.code)

        async with self.processor.database.sessions() as session, session.begin():
            row = await self._row(session, event)
            if row is None or row["transcription_state"] is not None:
                return "skipped"
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 48))"),
                {"key": f"visual-consent:{row['tenant_id']}:{row['business_id']}"},
            )
            if not await self._eligible(session, row):
                return "skipped"
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:tenant,0))"),
                {"tenant": str(row["tenant_id"])},
            )
            used = await session.scalar(
                text("""SELECT coalesce(sum(reserved_seconds),0) FROM audio_transcription_usage
                  WHERE tenant_id=:tenant
                    AND created_at>=date_trunc('day',now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'"""),
                {"tenant": row["tenant_id"]},
            )
            if used + seconds > settings.audio_daily_seconds_limit:
                await session.execute(
                    text("""UPDATE whatsapp_material_assets SET transcription_state='budget_exceeded',
                      transcription_error='AUDIO_BUDGET_EXCEEDED' WHERE id=:event"""),
                    {"event": event},
                )
                await self._audit(session, row, event, "whatsapp.audio_budget_exceeded")
                return "budget_exceeded"
            await session.execute(
                text("""INSERT INTO audio_transcription_usage
                  (event_id,tenant_id,business_id,reserved_seconds,state)
                  VALUES(:event,:tenant,:business,:seconds,'submitted')"""),
                {"event": event, "tenant": row["tenant_id"], "business": row["business_id"], "seconds": seconds},
            )
            await session.execute(
                text("UPDATE whatsapp_material_assets SET transcription_state='submitted' WHERE id=:event"),
                {"event": event},
            )
            await self._audit(session, row, event, "whatsapp.audio_submitted")
        try:
            transcript = await self.provider.transcribe(audio, event)
        except MaterialError:
            transcript = None
        async with self.processor.database.sessions() as session, session.begin():
            row = await self._row(session, event)
            if row is None or row["transcription_state"] != "submitted":
                return "uncertain"
            allowed = bool(transcript and await self._eligible(session, row))
            status = "completed" if allowed else "uncertain"
            ciphertext = None
            if allowed:
                assert transcript is not None and settings.meta_encryption_key is not None
                ciphertext = (
                    Fernet(settings.meta_encryption_key.get_secret_value().encode())
                    .encrypt(transcript.encode())
                    .decode()
                )
            await session.execute(
                text("""UPDATE whatsapp_material_assets SET transcription_state=:state,
                  transcript_ciphertext=:ciphertext,
                  transcription_error=CASE WHEN :state='uncertain' THEN 'AUDIO_RESULT_UNCERTAIN' ELSE NULL END
                  WHERE id=:event"""),
                {"event": event, "state": status, "ciphertext": ciphertext},
            )
            await session.execute(
                text("UPDATE audio_transcription_usage SET state=:state WHERE event_id=:event"),
                {"event": event, "state": status},
            )
            await self._audit(session, row, event, f"whatsapp.audio_{status}")
            return status
