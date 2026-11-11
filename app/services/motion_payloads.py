"""Encrypted large motion evidence in private storage; SQL retains bounded references."""

import hashlib
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.adapters.material_media import FetchedMedia, MaterialStore
from app.services.auth import AuthError
from app.services.motion_context import MotionContext, digest

INLINE_BYTES = 64 * 1024
MAX_PAYLOAD_BYTES = 64 * 1024 * 1024
SCHEMA = "motion-private-payload-v1"


@dataclass(frozen=True)
class PreparedPayload:
    ciphertext: str = field(repr=False)
    manifest: dict[str, Any] | None = None
    data: bytes | None = field(default=None, repr=False)


class MotionPayloads:
    def __init__(self, context: MotionContext, store: MaterialStore):
        self.context, self.store = context, store

    @staticmethod
    def prefix(row: dict[str, Any]) -> str:
        return f"motion-payloads/{row['tenant_id']}/{row['business_id']}/{row['id']}/"

    def prepare(self, row: dict[str, Any], operation: UUID, value: object) -> PreparedPayload:
        ciphertext = self.context.seal(value)
        if len(ciphertext) <= INLINE_BYTES:
            return PreparedPayload(ciphertext)
        data = ciphertext.encode()
        if len(data) > MAX_PAYLOAD_BYTES:
            raise AuthError("MOTION_PAYLOAD_TOO_LARGE", 409)
        manifest = {
            "storage_schema": SCHEMA,
            "operation_id": str(operation),
            "object_key": self.prefix(row) + str(operation) + ".fernet",
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "payload_sha256": digest(value),
        }
        return PreparedPayload(self.context.seal(manifest), manifest, data)

    async def upload(self, prepared: PreparedPayload) -> None:
        assert prepared.manifest is not None and prepared.data is not None
        if getattr(self.store, "single_attempt_put", False) is not True:
            raise AuthError("MOTION_STORAGE_SINGLE_ATTEMPT_REQUIRED", 409)
        manifest = prepared.manifest
        await self.store.put(
            manifest["object_key"],
            FetchedMedia(prepared.data, "application/octet-stream", manifest["sha256"]),
        )
        await self._download(manifest)

    async def _download(self, manifest: dict[str, Any]) -> bytes:
        data = await self.store.get_motion_payload(manifest["object_key"])
        if len(data) != manifest["size_bytes"] or hashlib.sha256(data).hexdigest() != manifest["sha256"]:
            raise AuthError("MOTION_PAYLOAD_BYTES_CHANGED", 409)
        return data

    async def open(self, row: dict[str, Any], ciphertext: str) -> dict[str, Any]:
        """Caller obtains the reference under RLS, then calls outside its transaction."""
        value = self.context.open(ciphertext)
        if value.get("storage_schema") != SCHEMA:
            return value  # Historical and small inline records remain readable.
        try:
            operation = UUID(value["operation_id"])
            if (
                value["object_key"] != self.prefix(row) + str(operation) + ".fernet"
                or type(value["size_bytes"]) is not int
                or not 0 < value["size_bytes"] <= MAX_PAYLOAD_BYTES
            ):
                raise ValueError
            for name in ("sha256", "payload_sha256"):
                if len(value[name]) != 64 or any(c not in "0123456789abcdef" for c in value[name]):
                    raise ValueError
        except (KeyError, TypeError, ValueError, AttributeError):
            raise AuthError("MOTION_PAYLOAD_REFERENCE_INVALID", 409) from None
        data = await self._download(value)
        try:
            opened = self.context.open(data.decode())
        except UnicodeDecodeError:
            raise AuthError("MOTION_PAYLOAD_REFERENCE_INVALID", 409) from None
        if digest(opened) != value["payload_sha256"]:
            raise AuthError("MOTION_PAYLOAD_BYTES_CHANGED", 409)
        return opened
