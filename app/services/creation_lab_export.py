"""On-demand private draft archive; no persisted package or fabricated execution trace."""

import asyncio
import io
import json
from typing import Any
from uuid import UUID, uuid5
from zipfile import ZIP_STORED, ZipFile

from sqlalchemy import text

from app.core.config import Settings
from app.db.session import Database
from app.services.auth import AuthError
from app.services.creation_lab_attachments import CreationLabAttachments
from app.services.creation_lab_drafts import ZERO, CreationLabDrafts
from app.services.creation_lab_execution import CreationLabExecution
from app.services.creation_lab_results import CreationLabResults


class CreationLabExport:
    def __init__(self, settings: Settings, database: Database) -> None:
        self.drafts = CreationLabDrafts(settings, database)
        self.attachments = CreationLabAttachments(settings, database)
        self.execution = CreationLabExecution(settings, database)
        self.results = CreationLabResults(settings, database)

    async def download(self, actor: UUID, run: UUID) -> bytes:
        await self.attachments.authorize(actor, run, "admin.creation_lab.draft.export")
        # One SQL statement captures message, event cursor, selected collection
        # versions and upload states together. Later changes belong to the next ZIP.
        async with self.drafts.database.transaction(ZERO, actor) as session:
            await self.execution.guard(session, actor, run, "admin.creation_lab.export.snapshot")
            trace_bytes = await session.scalar(
                text(
                    "SELECT coalesce(sum(octet_length(payload_ciphertext)),0) FROM creation_lab_trace WHERE run_id=:run"
                ),
                {"run": run},
            )
            if trace_bytes > 256 * 1024 * 1024:
                raise AuthError("CREATION_LAB_EXPORT_TOO_LARGE", 409)
            snapshot = (
                (
                    await session.execute(
                        text("""SELECT r.*,
                  (SELECT coalesce(jsonb_agg(to_jsonb(e) ORDER BY e.sequence),'[]'::jsonb)
                   FROM (SELECT sequence,event_id,kind,trace_id,created_at FROM creation_lab_events
                     WHERE run_id=:run ORDER BY sequence LIMIT 10001) e) AS events,
                  (SELECT coalesce(jsonb_agg(to_jsonb(a) ORDER BY a.created_at,a.id),'[]'::jsonb)
                   FROM creation_lab_attachments a WHERE a.run_id=:run) AS attachments,
                  (SELECT selection_ciphertext FROM creation_lab_collection_choices WHERE run_id=:run) AS selection,
                  (SELECT coalesce(jsonb_agg(to_jsonb(v) ORDER BY v.number),'[]'::jsonb)
                   FROM (SELECT id,number,sha256,mime_type,size_bytes,selected,review_verdict,copy_ciphertext,created_at
                     FROM creation_lab_versions WHERE run_id=:run) v) AS versions,
                  (SELECT coalesce(jsonb_agg(to_jsonb(e) ORDER BY e.created_at,e.id),'[]'::jsonb)
                   FROM creation_lab_effects e WHERE e.run_id=:run) AS effects,
                  (SELECT coalesce(jsonb_agg(to_jsonb(f) ORDER BY f.created_at,f.id),'[]'::jsonb)
                   FROM creation_lab_feedback f WHERE f.run_id=:run) AS feedback,
                  (SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY t.created_at,t.id),'[]'::jsonb)
                   FROM creation_lab_trace t WHERE t.run_id=:run
                     AND (r.trace_expires_at IS NULL OR r.trace_expires_at>clock_timestamp())) AS traces,
                  r.trace_expires_at IS NOT NULL AND r.trace_expires_at<=clock_timestamp() AS trace_expired
                  FROM creation_lab_runs r WHERE r.id=:run"""),
                        {"run": run},
                    )
                )
                .mappings()
                .one()
            )
        draft = self.drafts.present(dict(snapshot))
        events = snapshot["events"]
        if len(events) > 10000:
            raise AuthError("CREATION_LAB_EXPORT_TOO_LARGE", 409)
        metadata = [self.attachments.present(item) for item in snapshot["attachments"]]
        claimed_ids = {UUID(item["event_id"]) for item in events if item["kind"] == "attachment.uploading"}
        ready_ids = {UUID(item["event_id"]) for item in events if item["kind"] == "attachment.ready"}

        files: list[tuple[str, bytes]] = []
        manifest: list[dict[str, Any]] = []
        for item in metadata:
            identifier = UUID(item["id"])
            if uuid5(identifier, "attachment.uploading") not in claimed_ids:
                continue
            entry = dict(item)
            # A ready event after the cursor is intentionally excluded.
            if item["state"] == "ready" and uuid5(identifier, "attachment.ready") in ready_ids:
                _, data = await self.attachments.download(actor, run, identifier)
                path = f"attachments/{item['id']}"
                files.append((path, data))
                entry["archive_path"] = path
            else:
                entry["archive_path"] = None
                entry["unavailable_reason"] = "upload_not_complete_at_export_cursor"
            manifest.append(entry)
        versions = []
        for version in snapshot["versions"]:
            copy = version.pop("copy_ciphertext")
            version["copy"] = self.drafts.cipher.open(copy) if copy else None
            if sum(len(data) for _, data in files) + version["size_bytes"] > 512 * 1024 * 1024:
                raise AuthError("CREATION_LAB_EXPORT_TOO_LARGE", 409)
            _, data = await self.results.download(actor, run, UUID(version["id"]))
            path = f"versions/{version['id']}"
            files.append((path, data))
            versions.append({**version, "archive_path": path})
        traces = []
        for trace in snapshot["traces"]:
            ciphertext = trace.pop("payload_ciphertext")
            traces.append({**trace, "payload": self.drafts.cipher.open(ciphertext)["value"] if ciphertext else None})
        feedback = [
            {k: v for k, v in item.items() if k != "note_ciphertext"} | self.drafts.cipher.open(item["note_ciphertext"])
            for item in snapshot["feedback"]
        ]
        document = {
            "schema": "creation-lab-execution-export-v1",
            "run": draft,
            "event_cursor": events[-1]["sequence"] if events else 0,
            "events": events,
            "attachments": manifest,
            "collection_references": self.drafts.cipher.open(snapshot["selection"])["photos"]
            if snapshot["selection"]
            else [],
            "collection_files_included": False,
            "generation_started": snapshot["snapshot_trace_id"] is not None,
            "versions": versions,
            "feedback": feedback,
            "model_trace": traces,
            "costs": {
                "committed_usd_micros": snapshot["committed_usd_micros"],
                "effects": snapshot["effects"],
                "invoice_confirmed": False,
            },
            "trace_retention": {
                "days_after_completion": 7,
                "expires_at": snapshot["trace_expires_at"],
                "status": "expired" if snapshot["trace_expired"] else "available",
            },
        }

        def archive() -> bytes:
            buffer = io.BytesIO()
            with ZipFile(buffer, "w", compression=ZIP_STORED) as package:
                package.writestr("manifest.json", json.dumps(document, ensure_ascii=False, indent=2, default=str))
                for path, data in files:
                    package.writestr(path, data)
            return buffer.getvalue()

        if sum(len(data) for _, data in files) + len(json.dumps(document, default=str).encode()) > 512 * 1024 * 1024:
            raise AuthError("CREATION_LAB_EXPORT_TOO_LARGE", 409)
        result = await asyncio.to_thread(archive)
        await self.attachments.authorize(actor, run, "admin.creation_lab.draft.export.release")
        if traces:
            async with self.drafts.database.transaction(ZERO, actor) as session:
                expired = await session.scalar(
                    text(
                        "SELECT trace_expires_at IS NOT NULL AND trace_expires_at<=clock_timestamp() FROM creation_lab_runs WHERE id=:run"
                    ),
                    {"run": run},
                )
                if expired:
                    raise AuthError("CREATION_LAB_TRACE_EXPIRED", 410)
        return result
