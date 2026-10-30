"""Encrypted owner-scoped snapshot of the exact visual request, never a log."""

import json
from typing import Any
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import text

from app.adapters.visual_ai import visual_request_http_parts
from app.core.config import Settings
from app.db.session import Database
from app.services.auth import AuthError
from app.services.visual_requests import PreparedVisualRequest
from app.services.whatsapp_materials import WhatsAppMaterialsService


def encrypt_visual_trace(settings: Settings, prepared: PreparedVisualRequest) -> str:
    key = settings.meta_encryption_key
    if key is None:
        raise AuthError("VISUAL_TRACE_KEY_REQUIRED", 409)
    request = prepared.request
    if len(prepared.sources) != len(request.references):
        raise AuthError("VISUAL_TRACE_INVALID", 409)
    if (prepared.skill_id is None) != (prepared.skill_sha256 is None):
        raise AuthError("VISUAL_TRACE_INVALID", 409)
    path, body = visual_request_http_parts(request)
    payload = {
        "version": 1,
        "prompt": request.prompt,
        "model": request.model,
        "quality": request.quality,
        "size": request.size,
        "output_format": request.output_format,
        "client_request_id": str(request.request_id),
        "http": {
            "method": "POST",
            "path": path,
            "json_without_images": body,
            "images_field": "images" if request.references else None,
            "references_note": "Para reproduzir, recupere as referências autorizadas e normalize-as novamente.",
        },
        "skill_id": prepared.skill_id,
        "skill_sha256": prepared.skill_sha256,
        "context": {
            "proposal_id": str(prepared.context.proposal_id),
            "briefing_id": str(prepared.context.briefing_id),
            "context_version": prepared.context.context_version,
            "script_version": prepared.context.script_version,
            "brand_kit_version": prepared.context.brand_kit_version,
        },
        "references": [
            {
                "kind": source.kind,
                "id": str(source.id),
                "version": source.version,
                "source_sha256": source.source_sha256,
                "normalized_sha256": source.normalized_sha256,
                "mime_type": reference.mime_type,
                **(
                    {"catalog_id": source.catalog_id, "asset_path": source.asset_path}
                    if source.catalog_id is not None and source.asset_path is not None
                    else {}
                ),
            }
            for source, reference in zip(prepared.sources, request.references, strict=True)
        ],
    }
    try:
        return (
            Fernet(key.get_secret_value().encode())
            .encrypt(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode())
            .decode()
        )
    except (TypeError, ValueError) as exc:
        raise AuthError("VISUAL_TRACE_KEY_INVALID", 409) from exc


def decrypt_visual_trace(settings: Settings, ciphertext: str) -> dict[str, Any]:
    key = settings.meta_encryption_key
    if key is None:
        raise AuthError("VISUAL_TRACE_KEY_REQUIRED", 409)
    try:
        value = json.loads(Fernet(key.get_secret_value().encode()).decrypt(ciphertext.encode()))
    except (InvalidToken, ValueError, UnicodeDecodeError, TypeError) as exc:
        raise AuthError("VISUAL_TRACE_UNAVAILABLE", 409) from exc
    if not isinstance(value, dict) or value.get("version") != 1:
        raise AuthError("VISUAL_TRACE_UNAVAILABLE", 409)
    return value


class VisualRequestTraceService:
    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings, self.database = settings, database

    async def read(self, tenant: UUID, business: UUID, actor: UUID, preview: UUID) -> dict[str, object]:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            row = (
                (
                    await session.execute(
                        text("""SELECT t.operation_id,t.request_hash,t.ciphertext,t.created_at,p.sha256,
                          p.state AS preview_state,p.error_code AS preview_error_code
                          FROM visual_request_traces t JOIN media_previews p
                            ON p.id=t.preview_id AND p.tenant_id=t.tenant_id AND p.business_id=t.business_id
                          WHERE t.tenant_id=:tenant AND t.business_id=:business AND t.preview_id=:preview"""),
                        {"tenant": tenant, "business": business, "preview": preview},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise AuthError("VISUAL_TRACE_NOT_FOUND", 404)
            return {
                "preview_id": str(preview),
                "operation_id": str(row["operation_id"]),
                "request_hash": row["request_hash"],
                "output_sha256": row["sha256"],
                "trace_status": "prepared",
                "preview_state": row["preview_state"],
                "preview_error_code": row["preview_error_code"],
                "created_at": row["created_at"],
                "request": decrypt_visual_trace(self.settings, row["ciphertext"]),
            }
