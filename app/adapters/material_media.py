"""Bounded Meta download, local inspection and private object storage."""

import asyncio
import base64
import binascii
import hashlib
import io
import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast
from urllib.parse import urlsplit

import boto3  # type: ignore[import-untyped]
import httpx
from botocore.config import Config  # type: ignore[import-untyped]
from PIL import Image, UnidentifiedImageError

from app.core.config import Settings

MAX_BYTES = {"image": 5 * 1024 * 1024, "audio": 16 * 1024 * 1024, "video": 50 * 1024 * 1024}
MIME_TYPES = {
    "image": frozenset({"image/jpeg", "image/png"}),
    "audio": frozenset({"audio/aac", "audio/amr", "audio/mpeg", "audio/mp4", "audio/ogg"}),
    "video": frozenset({"video/mp4", "video/3gpp"}),
}


class MaterialError(Exception):
    def __init__(self, code: str, *, retryable: bool = False) -> None:
        self.code, self.retryable = code, retryable
        super().__init__(code)


@dataclass(frozen=True)
class FetchedMedia:
    data: bytes
    mime_type: str
    sha256: str


def safe_meta_url(value: str) -> bool:
    try:
        url = urlsplit(value)
        host = (url.hostname or "").lower()
        port = url.port
    except ValueError:
        return False
    return (
        url.scheme == "https"
        and port in {None, 443}
        and url.username is None
        and url.password is None
        and (
            host in {"lookaside.fbsbx.com", "lookaside.facebook.com", "graph.facebook.com"}
            or host.endswith(".fbcdn.net")
        )
    )


def _check_hash(actual: str, expected: str) -> bool:
    if re.fullmatch(r"[0-9a-fA-F]{64}", expected):
        return actual.lower() == expected.lower()
    try:
        return bytes.fromhex(actual) == base64.b64decode(expected, validate=True)
    except (ValueError, binascii.Error):
        return False


async def inspect_media(media: FetchedMedia, kind: str) -> None:
    if kind == "image":
        try:
            with Image.open(io.BytesIO(media.data)) as picture:
                if picture.width * picture.height > 24_000_000:
                    raise MaterialError("MEDIA_DIMENSIONS_EXCEEDED")
                picture.verify()
                if media.mime_type != Image.MIME.get(picture.format or ""):
                    raise MaterialError("MEDIA_TYPE_MISMATCH")
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
            raise MaterialError("MEDIA_INVALID") from exc
        return
    with tempfile.TemporaryDirectory(prefix="material-") as folder:
        path = Path(folder) / "input"
        path.write_bytes(media.data)
        try:
            proc = await asyncio.create_subprocess_exec(
                "ffprobe",
                "-v",
                "error",
                "-protocol_whitelist",
                "file,pipe",
                "-show_entries",
                "stream=codec_type",
                "-of",
                "json",
                str(path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=12)
        except (FileNotFoundError, TimeoutError) as exc:
            if "proc" in locals() and proc.returncode is None:
                proc.kill()
                await proc.communicate()
            raise MaterialError("MEDIA_INSPECTION_UNAVAILABLE", retryable=True) from exc
        try:
            streams = json.loads(stdout).get("streams", [])
            if not isinstance(streams, list) or not all(isinstance(item, dict) for item in streams):
                raise ValueError("Invalid stream list")
        except (ValueError, UnicodeDecodeError, AttributeError) as exc:
            raise MaterialError("MEDIA_INVALID") from exc
        expected = "video" if kind == "video" else "audio"
        if proc.returncode != 0 or not any(item.get("codec_type") == expected for item in streams):
            raise MaterialError("MEDIA_INVALID")


class MetaMediaClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def fetch(self, media_id: str, kind: str) -> FetchedMedia:
        if (
            not self.settings.meta_access_token
            or not self.settings.meta_graph_version
            or not self.settings.meta_phone_number_id
        ):
            raise MaterialError("META_MEDIA_NOT_CONFIGURED")
        if kind not in MAX_BYTES or not re.fullmatch(r"\d{1,40}", media_id):
            raise MaterialError("MEDIA_ID_INVALID")
        token = self.settings.meta_access_token.get_secret_value()
        headers = {"Authorization": f"Bearer {token}"}
        metadata_url = f"https://graph.facebook.com/{self.settings.meta_graph_version}/{media_id}"
        async with httpx.AsyncClient(timeout=20, follow_redirects=False, trust_env=False) as client:
            try:
                response = await client.get(
                    metadata_url, params={"phone_number_id": self.settings.meta_phone_number_id}, headers=headers
                )
                response.raise_for_status()
                metadata = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                raise MaterialError("META_MEDIA_UNAVAILABLE", retryable=True) from exc
            if not isinstance(metadata, dict):
                raise MaterialError("MEDIA_METADATA_INVALID")
            url = metadata.get("url")
            mime = metadata.get("mime_type")
            if not isinstance(url, str) or not safe_meta_url(url) or mime not in MIME_TYPES[kind]:
                raise MaterialError("MEDIA_METADATA_INVALID")
            if isinstance(metadata.get("file_size"), int) and metadata["file_size"] > MAX_BYTES[kind]:
                raise MaterialError("MEDIA_TOO_LARGE")
            data = bytearray()
            try:
                async with client.stream("GET", url, headers=headers) as stream:
                    stream.raise_for_status()
                    async for chunk in stream.aiter_bytes():
                        data.extend(chunk)
                        if len(data) > MAX_BYTES[kind]:
                            raise MaterialError("MEDIA_TOO_LARGE")
            except httpx.HTTPError as exc:
                raise MaterialError("META_MEDIA_UNAVAILABLE", retryable=True) from exc
        if not data:
            raise MaterialError("MEDIA_INVALID")
        checksum = hashlib.sha256(data).hexdigest()
        expected_hash = metadata.get("sha256")
        if isinstance(expected_hash, str) and not _check_hash(checksum, expected_hash):
            raise MaterialError("MEDIA_CHECKSUM_MISMATCH")
        result = FetchedMedia(bytes(data), mime, checksum)
        await inspect_media(result, kind)
        return result


class MaterialStore:
    # This adapter uses a single S3 PUT; never assume this for injected stores.
    single_attempt_put = True

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _client(self, *, public: bool = False, single_attempt: bool = False) -> Any:
        return boto3.client(
            "s3",
            region_name=self.settings.material_storage_region,
            endpoint_url=(
                self.settings.material_storage_public_endpoint if public else self.settings.material_storage_endpoint
            ),
            aws_access_key_id=self.settings.material_storage_access_key.get_secret_value()
            if self.settings.material_storage_access_key
            else None,
            aws_secret_access_key=self.settings.material_storage_secret_key.get_secret_value()
            if self.settings.material_storage_secret_key
            else None,
            config=Config(
                signature_version="s3v4",
                connect_timeout=10,
                read_timeout=60,
                retries={"total_max_attempts": 1} if single_attempt else {"max_attempts": 2},
            ),
        )

    async def put(self, key: str, media: FetchedMedia) -> None:
        if not self.settings.material_storage_bucket:
            raise MaterialError("MATERIAL_STORAGE_NOT_CONFIGURED")

        def upload() -> None:
            # A timed-out earlier retry can finish after a later success and
            # recreate a deleted object. One request makes success definitive;
            # an ambiguous failure remains quarantined instead of retried.
            self._client(single_attempt=True).put_object(
                Bucket=self.settings.material_storage_bucket,
                Key=key,
                Body=media.data,
                ContentType=media.mime_type,
                ServerSideEncryption="AES256",
                Metadata={"sha256": media.sha256},
            )

        try:
            await asyncio.to_thread(upload)
        except Exception as exc:
            raise MaterialError("MATERIAL_STORAGE_UNAVAILABLE", retryable=True) from exc

    async def get_audio(self, key: str) -> bytes:
        if not self.settings.material_storage_bucket:
            raise MaterialError("MATERIAL_STORAGE_NOT_CONFIGURED")

        def download() -> bytes:
            response = self._client().get_object(Bucket=self.settings.material_storage_bucket, Key=key)
            body = response["Body"]
            try:
                if response.get("ContentLength", 0) > MAX_BYTES["audio"]:
                    raise MaterialError("MEDIA_SIZE_EXCEEDED")
                data = cast(bytes, body.read(MAX_BYTES["audio"] + 1))
                if len(data) > MAX_BYTES["audio"]:
                    raise MaterialError("MEDIA_SIZE_EXCEEDED")
                return data
            finally:
                body.close()

        try:
            return await asyncio.to_thread(download)
        except MaterialError:
            raise
        except Exception as exc:
            raise MaterialError("MATERIAL_STORAGE_UNAVAILABLE", retryable=True) from exc

    async def get_image(self, key: str, *, max_bytes: int = MAX_BYTES["image"]) -> bytes:
        if not self.settings.material_storage_bucket:
            raise MaterialError("MATERIAL_STORAGE_NOT_CONFIGURED")
        if not 0 < max_bytes <= 8 * 1024 * 1024:
            raise MaterialError("MEDIA_SIZE_EXCEEDED")

        def download() -> bytes:
            response = self._client().get_object(Bucket=self.settings.material_storage_bucket, Key=key)
            body = response["Body"]
            try:
                if response.get("ContentLength", 0) > max_bytes:
                    raise MaterialError("MEDIA_SIZE_EXCEEDED")
                data = cast(bytes, body.read(max_bytes + 1))
                if len(data) > max_bytes:
                    raise MaterialError("MEDIA_SIZE_EXCEEDED")
                return data
            finally:
                body.close()

        try:
            return await asyncio.to_thread(download)
        except MaterialError:
            raise
        except Exception as exc:
            raise MaterialError("MATERIAL_STORAGE_UNAVAILABLE", retryable=True) from exc

    async def get_video(self, key: str) -> bytes:
        if not self.settings.material_storage_bucket:
            raise MaterialError("MATERIAL_STORAGE_NOT_CONFIGURED")

        def download() -> bytes:
            response = self._client().get_object(Bucket=self.settings.material_storage_bucket, Key=key)
            body = response["Body"]
            try:
                if response.get("ContentLength", 0) > MAX_BYTES["video"]:
                    raise MaterialError("MEDIA_SIZE_EXCEEDED")
                data = cast(bytes, body.read(MAX_BYTES["video"] + 1))
                if len(data) > MAX_BYTES["video"]:
                    raise MaterialError("MEDIA_SIZE_EXCEEDED")
                return data
            finally:
                body.close()

        try:
            return await asyncio.to_thread(download)
        except MaterialError:
            raise
        except Exception as exc:
            raise MaterialError("MATERIAL_STORAGE_UNAVAILABLE", retryable=True) from exc

    async def delete(self, key: str) -> None:
        if not self.settings.material_storage_bucket:
            raise MaterialError("MATERIAL_STORAGE_NOT_CONFIGURED")

        def remove() -> None:
            self._client().delete_object(Bucket=self.settings.material_storage_bucket, Key=key)

        try:
            await asyncio.to_thread(remove)
        except Exception as exc:
            raise MaterialError("MATERIAL_STORAGE_UNAVAILABLE", retryable=True) from exc

    async def signed_url(self, key: str, mime_type: str) -> str:
        if not self.settings.material_storage_bucket:
            raise MaterialError("MATERIAL_STORAGE_NOT_CONFIGURED")

        def sign() -> str:
            return cast(
                str,
                self._client(public=True).generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": self.settings.material_storage_bucket,
                        "Key": key,
                        "ResponseContentType": mime_type,
                    },
                    ExpiresIn=120,
                ),
            )

        try:
            return await asyncio.to_thread(sign)
        except Exception as exc:
            raise MaterialError("MATERIAL_STORAGE_UNAVAILABLE", retryable=True) from exc
