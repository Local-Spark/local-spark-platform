"""Immutable private versions and owner decisions; approving never publishes."""

import hashlib
import hmac
import json
from dataclasses import asdict, dataclass
from typing import Any
from uuid import UUID, uuid5

from cryptography.fernet import Fernet
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.material_media import FetchedMedia, MaterialStore, inspect_media
from app.core.config import Settings
from app.db.session import Database
from app.schemas.content_pieces import (
    PieceArtifactRead,
    PieceDecision,
    PieceDecisionRead,
    PieceFormat,
    PieceFromPreview,
    PieceRead,
    PieceVersionRead,
)
from app.services.auth import AuthError
from app.services.media_previews import MediaPreviewService
from app.services.whatsapp_materials import WhatsAppMaterialsService


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


@dataclass(frozen=True)
class PieceArtifact:
    """Server-only metadata of an already verified, immutable private object."""

    id: UUID
    object_key: str
    sha256: str
    mime_type: str
    size_bytes: int


async def _event(
    session: AsyncSession,
    tenant: UUID,
    business: UUID,
    actor: UUID,
    operation: UUID,
    action: str,
    *,
    event_id: UUID | None = None,
) -> None:
    params = {"tenant": tenant, "business": business, "actor": actor, "operation": operation, "action": action}
    await session.execute(
        text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(:tenant,:actor,:operation,:action,:business)"""),
        {**params, "operation": event_id if event_id is not None else operation},
    )
    await session.execute(
        text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
          VALUES(:id,:tenant,:action,CAST(:payload AS jsonb))"""),
        {
            **params,
            "id": event_id if event_id is not None else uuid5(operation, action),
            "payload": _json({"business_id": business, "actor_id": actor, "operation_id": operation}),
        },
    )


async def write_version(
    session: AsyncSession,
    tenant: UUID,
    business: UUID,
    actor: UUID,
    piece_id: UUID,
    operation_id: UUID,
    format: PieceFormat,
    artifacts: tuple[PieceArtifact, ...],
    *,
    parent_id: UUID | None = None,
    source_preview_id: UUID | None = None,
    select_current: bool = True,
    simulated: bool = False,
) -> UUID:
    """Commit a complete version inside the producer's authorized transaction.

    The producer verifies every object's bytes and storage result BEFORE calling
    this function, and revalidates its context/fence in the same transaction.
    Nothing supplied by a public request may become an object key here.
    Original/corrected versions may be retained without selecting the newest.
    """
    await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
    if not artifacts or len(artifacts) > 20 or (format != "carousel_motion" and len(artifacts) != 1):
        raise AuthError("PIECE_ARTIFACT_SET_INVALID", 409)
    if len({item.id for item in artifacts}) != len(artifacts):
        raise AuthError("PIECE_ARTIFACT_SET_INVALID", 409)
    allowed_mime = {"image/png", "image/jpeg"} if format in {"photo", "story"} else {"video/mp4"}
    for position, item in enumerate(artifacts):
        PieceArtifactRead.model_validate(
            {**{k: v for k, v in asdict(item).items() if k != "object_key"}, "position": position}
        )
        if not item.object_key or item.mime_type not in allowed_mime or item.size_bytes > 50 * 1024 * 1024:
            raise AuthError("PIECE_ARTIFACT_SET_INVALID", 409)
    params = {"tenant": tenant, "business": business, "piece": piece_id, "operation": operation_id}
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 58))"), {"key": f"{tenant}:{operation_id}"}
    )
    # Serializes initial insertion as well as later version/decision races.
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 57))"), {"key": f"{tenant}:{piece_id}"}
    )
    digest = hashlib.sha256(
        _json(
            [
                business,
                piece_id,
                format,
                parent_id,
                source_preview_id,
                select_current,
                simulated,
                [asdict(a) for a in artifacts],
            ]
        ).encode()
    ).hexdigest()
    replay = (
        (
            await session.execute(
                text(
                    "SELECT id,request_hash FROM content_piece_versions "
                    "WHERE tenant_id=:tenant AND operation_id=:operation"
                ),
                params,
            )
        )
        .mappings()
        .one_or_none()
    )
    if replay is not None:
        if replay["request_hash"] != digest:
            raise AuthError("PIECE_OPERATION_CONFLICT", 409)
        return UUID(str(replay["id"]))
    current = (
        (
            await session.execute(
                text(
                    "SELECT * FROM content_pieces "
                    "WHERE tenant_id=:tenant AND business_id=:business AND id=:piece FOR UPDATE"
                ),
                params,
            )
        )
        .mappings()
        .one_or_none()
    )
    version = uuid5(operation_id, f"piece-version:{tenant}:{piece_id}")
    if current is None:
        if parent_id is not None or not select_current:
            raise AuthError("PIECE_PARENT_INVALID", 409)
        await session.execute(
            text("""INSERT INTO content_pieces
              (tenant_id,business_id,id,actor_id,format,current_version_id,state,source_preview_id,simulated)
              VALUES(:tenant,:business,:piece,:actor,:format,:version,'ready_for_review',:preview,:simulated)"""),
            {
                **params,
                "actor": actor,
                "format": format,
                "version": version,
                "preview": source_preview_id,
                "simulated": simulated,
            },
        )
    elif (
        current["format"] != format
        or current["source_preview_id"] != source_preview_id
        or current["simulated"] != simulated
    ):
        raise AuthError("PIECE_SOURCE_CHANGED", 409)
    elif parent_id is None or not await session.scalar(
        text("""SELECT 1 FROM content_piece_versions WHERE tenant_id=:tenant AND business_id=:business
          AND piece_id=:piece AND id=:parent"""),
        {**params, "parent": parent_id},
    ):
        raise AuthError("PIECE_PARENT_INVALID", 409)
    await session.execute(
        text("""INSERT INTO content_piece_versions
          (tenant_id,business_id,piece_id,id,number,parent_id,operation_id,request_hash)
          SELECT :tenant,:business,:piece,:version,coalesce(max(number),0)+1,:parent,:operation,:hash
          FROM content_piece_versions WHERE tenant_id=:tenant AND business_id=:business AND piece_id=:piece"""),
        {**params, "version": version, "parent": parent_id, "hash": digest},
    )
    for position, item in enumerate(artifacts):
        await session.execute(
            text("""INSERT INTO content_piece_artifacts
              (tenant_id,business_id,piece_id,version_id,id,position,object_key,sha256,mime_type,size_bytes)
              VALUES(:tenant,:business,:piece,:version,:id,:position,:object_key,:sha256,:mime_type,:size_bytes)"""),
            {**params, "version": version, "position": position, **asdict(item)},
        )
    if select_current:
        await session.execute(
            text("""UPDATE content_pieces SET current_version_id=:version,state='ready_for_review',updated_at=now()
              WHERE tenant_id=:tenant AND business_id=:business AND id=:piece"""),
            {**params, "version": version},
        )
    await _event(session, tenant, business, actor, operation_id, "content.piece_ready")
    return version


class ContentPieceService:
    def __init__(self, settings: Settings, database: Database, store: MaterialStore | None = None) -> None:
        self.settings, self.database = settings, database
        self.store = store or MaterialStore(settings)

    async def from_preview(self, tenant: UUID, business: UUID, actor: UUID, body: PieceFromPreview) -> PieceRead:
        preview_service = MediaPreviewService(self.settings, self.database, self.store)
        key = await preview_service.file_key(tenant, business, actor, body.preview_id, review=True)
        data = await self.store.get_image(key)
        sha = hashlib.sha256(data).hexdigest()
        mime = "image/png" if data.startswith(b"\x89PNG\r\n\x1a\n") else "image/jpeg"
        await inspect_media(FetchedMedia(data, mime, sha), "image")
        piece = uuid5(body.preview_id, f"piece:{tenant}:{business}")
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            row = (
                (
                    await session.execute(
                        text("""SELECT p.*,e.document->>'format' AS format FROM media_previews p
                      JOIN editorial_proposals e ON e.id=p.proposal_id
                      AND e.tenant_id=p.tenant_id AND e.business_id=p.business_id
                      WHERE p.id=:preview AND p.tenant_id=:tenant AND p.business_id=:business
                        AND p.state='completed' AND p.generation_mode IN ('visual_fake','visual_ai')"""),
                        {"preview": body.preview_id, "tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if (
                row is None
                or row["object_key"] != key
                or row["sha256"] != sha
                or row["format"] not in {"photo", "story"}
            ):
                raise AuthError("PIECE_PREVIEW_UNAVAILABLE", 409)
            await write_version(
                session,
                tenant,
                business,
                actor,
                piece,
                body.operation_id,
                row["format"],
                (PieceArtifact(uuid5(body.preview_id, "piece-artifact"), key, sha, mime, len(data)),),
                source_preview_id=body.preview_id,
                simulated=row["generation_mode"] == "visual_fake",
            )
        return await self.get(tenant, business, actor, piece)

    async def get(self, tenant: UUID, business: UUID, actor: UUID, piece: UUID) -> PieceRead:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            return await self._read(session, tenant, business, piece)

    @staticmethod
    async def _read(session: AsyncSession, tenant: UUID, business: UUID, piece: UUID) -> PieceRead:
        params = {"tenant": tenant, "business": business, "piece": piece}
        row = (
            (
                await session.execute(
                    text(
                        "SELECT * FROM content_pieces WHERE tenant_id=:tenant AND business_id=:business AND id=:piece"
                    ),
                    params,
                )
            )
            .mappings()
            .one_or_none()
        )
        if row is None:
            raise AuthError("PIECE_NOT_FOUND", 404)
        versions = (
            (
                await session.execute(
                    text(
                        "SELECT * FROM content_piece_versions WHERE tenant_id=:tenant "
                        "AND business_id=:business AND piece_id=:piece ORDER BY number"
                    ),
                    params,
                )
            )
            .mappings()
            .all()
        )
        files = (
            (
                await session.execute(
                    text(
                        "SELECT id,version_id,position,sha256,mime_type,size_bytes FROM content_piece_artifacts "
                        "WHERE tenant_id=:tenant AND business_id=:business AND piece_id=:piece ORDER BY position"
                    ),
                    params,
                )
            )
            .mappings()
            .all()
        )
        return PieceRead(
            id=piece,
            simulated=row["simulated"],
            format=row["format"],
            state=row["state"],
            current_version_id=row["current_version_id"],
            approved_version_id=row["approved_version_id"],
            created_at=row["created_at"],
            versions=[
                PieceVersionRead(
                    id=v["id"],
                    number=v["number"],
                    parent_id=v["parent_id"],
                    created_at=v["created_at"],
                    artifacts=[
                        PieceArtifactRead(**{k: x[k] for k in PieceArtifactRead.model_fields})
                        for x in files
                        if x["version_id"] == v["id"]
                    ],
                )
                for v in versions
            ],
        )

    async def list(self, tenant: UUID, business: UUID, actor: UUID) -> list[PieceRead]:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            ids = (
                await session.scalars(
                    text(
                        "SELECT id FROM content_pieces WHERE tenant_id=:tenant "
                        "AND business_id=:business ORDER BY created_at DESC,id DESC LIMIT 30"
                    ),
                    {"tenant": tenant, "business": business},
                )
            ).all()
            return [await self._read(session, tenant, business, piece) for piece in ids]

    async def decide(
        self, tenant: UUID, business: UUID, actor: UUID, piece: UUID, body: PieceDecision
    ) -> PieceDecisionRead:
        key = self.settings.meta_encryption_key
        if key is None:
            raise AuthError("PIECE_PRIVACY_KEY_REQUIRED", 409)
        request_hash = hmac.new(
            key.get_secret_value().encode(),
            _json([business, piece, body.model_dump(mode="json")]).encode(),
            hashlib.sha256,
        ).hexdigest()
        params = {"tenant": tenant, "business": business, "piece": piece, "operation": body.operation_id}
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 58))"),
                {"key": f"{tenant}:{body.operation_id}"},
            )
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 57))"), {"key": f"{tenant}:{piece}"}
            )
            replay = (
                (
                    await session.execute(
                        text(
                            "SELECT * FROM content_piece_decisions WHERE tenant_id=:tenant AND operation_id=:operation"
                        ),
                        params,
                    )
                )
                .mappings()
                .one_or_none()
            )
            if replay is not None:
                if replay["request_hash"] != request_hash:
                    raise AuthError("PIECE_OPERATION_CONFLICT", 409)
                return self._decision_read(replay)
            await session.execute(
                text(
                    "SELECT id FROM content_pieces "
                    "WHERE tenant_id=:tenant AND business_id=:business AND id=:piece FOR UPDATE"
                ),
                params,
            )
            current = await self._read(session, tenant, business, piece)
            if current.current_version_id != body.version_id:
                raise AuthError("PIECE_VERSION_CHANGED", 409)
            version = next(v for v in current.versions if v.id == body.version_id)
            if version.artifacts != body.artifacts:
                raise AuthError("PIECE_ARTIFACT_SET_CHANGED", 409)
            row = (
                (
                    await session.execute(
                        text("""INSERT INTO content_piece_decisions
                  (tenant_id,business_id,piece_id,version_id,operation_id,actor_id,
                  decision,request_hash,confirmation,note_ciphertext,page_positions)
                  VALUES(:tenant,:business,:piece,:version,:operation,:actor,:decision,:hash,
                    CAST(:confirmation AS jsonb),:note,CAST(:pages AS jsonb)) RETURNING *"""),
                        {
                            **params,
                            "version": body.version_id,
                            "actor": actor,
                            "decision": body.decision,
                            "hash": request_hash,
                            "confirmation": _json([item.model_dump() for item in body.confirmations]),
                            "note": Fernet(key.get_secret_value().encode()).encrypt(body.note.encode()).decode()
                            if body.note
                            else None,
                            "pages": _json(body.page_positions),
                        },
                    )
                )
                .mappings()
                .one()
            )
            await session.execute(
                text("""UPDATE content_pieces SET state=:state,
                  approved_version_id=CASE WHEN :approved THEN :version ELSE approved_version_id END,
                  updated_at=now() WHERE tenant_id=:tenant AND business_id=:business AND id=:piece"""),
                {
                    **params,
                    "state": "approved" if body.decision == "approve" else "changes_requested",
                    "approved": body.decision == "approve",
                    "version": body.version_id,
                },
            )
            await _event(session, tenant, business, actor, body.operation_id, "content.piece_decided")
            return self._decision_read(row)

    @staticmethod
    def _decision_read(row: Any) -> PieceDecisionRead:
        return PieceDecisionRead(**{key: row[key] for key in PieceDecisionRead.model_fields})

    async def download(
        self, tenant: UUID, business: UUID, actor: UUID, piece: UUID, version: UUID, artifact: UUID
    ) -> str:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            row = (
                (
                    await session.execute(
                        text("""SELECT a.object_key,a.mime_type,p.source_preview_id FROM content_piece_artifacts a
              JOIN content_pieces p ON p.tenant_id=a.tenant_id AND p.business_id=a.business_id AND p.id=a.piece_id
              WHERE a.tenant_id=:tenant AND a.business_id=:business AND a.piece_id=:piece
                AND a.version_id=:version AND a.id=:artifact"""),
                        {
                            "tenant": tenant,
                            "business": business,
                            "piece": piece,
                            "version": version,
                            "artifact": artifact,
                        },
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise AuthError("PIECE_ARTIFACT_NOT_FOUND", 404)
        if row["source_preview_id"] is not None:
            current_key = await MediaPreviewService(self.settings, self.database, self.store).file_key(
                tenant, business, actor, row["source_preview_id"], review=True
            )
            if current_key != row["object_key"]:
                raise AuthError("PIECE_ARTIFACT_NOT_FOUND", 404)
        return await self.store.signed_url(row["object_key"], row["mime_type"])
