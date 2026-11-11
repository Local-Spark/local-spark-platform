"""Bounded private media preparation, with real sampled frames and preserved audio."""

import hashlib
import io
import math
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps, UnidentifiedImageError

from app.adapters.material_media import FetchedMedia, MaterialStore
from app.adapters.motion_html_renderer import RenderAsset, RenderedFrame
from app.adapters.motion_media import _command, inspect_and_extract_motion_audio
from app.services.auth import AuthError
from app.services.motion_repertoire import RepertoireImage, load_repertoire_images
from app.services.motion_speech import speech_context

FONTS = Path(__file__).resolve().parents[2] / "catalog/kits/cafe-pausas/v1/fonts"


@dataclass(frozen=True)
class PreparedMotionInput:
    context: dict[str, Any]
    assets: tuple[RenderAsset, ...]
    source_frames: tuple[RenderedFrame, ...]
    duration_ms: int
    audio: dict[str, Any]
    asset_previews: tuple[tuple[str, RenderedFrame], ...] = ()
    reference_images: tuple[RepertoireImage, ...] = ()


def _asset(name: str, mime: str, data: bytes) -> RenderAsset:
    return RenderAsset(name, mime, data, hashlib.sha256(data).hexdigest())


async def source_frames(data: bytes, duration_ms: int) -> tuple[RenderedFrame, ...]:
    samples = tuple(sorted({0, *(duration_ms * index // 5 for index in range(1, 5)), max(0, duration_ms - 100)}))
    frames = []
    with tempfile.TemporaryDirectory(prefix="motion-source-") as folder:
        path = Path(folder) / "source.mp4"
        path.write_bytes(data)
        for ms in samples:
            png = await _command(
                "ffmpeg",
                "-nostdin",
                "-v",
                "error",
                "-xerror",
                "-protocol_whitelist",
                "file,pipe",
                "-f",
                "mov",
                "-enable_drefs",
                "0",
                "-ss",
                str(ms / 1000),
                "-i",
                str(path),
                "-frames:v",
                "1",
                "-vf",
                "scale=360:640:force_original_aspect_ratio=decrease",
                "-f",
                "image2pipe",
                "-c:v",
                "png",
                "pipe:1",
                output_limit=4 * 1024 * 1024,
            )
            if not png.startswith(b"\x89PNG\r\n\x1a\n"):
                raise AuthError("MOTION_SOURCE_FRAME_INVALID", 409)
            frames.append(RenderedFrame(ms, png, hashlib.sha256(png).hexdigest()))
    return tuple(frames)


class MotionInputLoader:
    def __init__(self, store: MaterialStore):
        self.store = store

    async def prepare(self, snapshot: dict[str, Any]) -> PreparedMotionInput:
        reference_images = load_repertoire_images(snapshot)
        source = snapshot["source"]
        data = await self.store.get_video(source["object_key"])
        if len(data) != source["size_bytes"] or hashlib.sha256(data).hexdigest() != source["sha256"]:
            raise AuthError("MOTION_SOURCE_BYTES_CHANGED", 409)
        info, _ = await inspect_and_extract_motion_audio(
            FetchedMedia(data, "video/mp4", source["sha256"]), extract_audio=False
        )
        # Round up to an exact output-frame boundary, retaining the entire recording.
        duration_ms = math.ceil(math.ceil(info.duration_seconds * 30) * 1000 / 30)
        if duration_ms > 60000:
            raise AuthError("MOTION_SOURCE_TOO_LONG", 409)
        assets = [_asset("assets/source.mp4", "video/mp4", data)]
        audio: dict[str, Any] = {"mode": "silent", "tracks": []}
        if info.audio_codec is not None:
            audio = {
                "mode": "mix",
                "tracks": [
                    {
                        "asset_id": "assets/source.mp4",
                        "offset_ms": 0,
                        "trim_start_ms": 0,
                        "trim_end_ms": math.floor(info.duration_seconds * 1000),
                        "volume": 1.0,
                    }
                ],
            }
        for filename in ("DejaVuSans.ttf", "DejaVuSerif.ttf"):
            assets.append(_asset(f"assets/{filename}", "font/ttf", (FONTS / filename).read_bytes()))
        logo = snapshot["logo"]
        if logo is not None:
            png = await self.store.get_image(logo["object_key"])
            if len(png) != logo["size_bytes"] or hashlib.sha256(png).hexdigest() != logo["sha256"]:
                raise AuthError("MOTION_LOGO_BYTES_CHANGED", 409)
            assets.append(_asset("assets/logo.png", "image/png", png))
        frames = await source_frames(data, int(info.duration_seconds * 1000))
        previews = []
        materials = []
        if len(snapshot.get("collection_photos", [])) > 4:
            raise AuthError("MOTION_COLLECTION_PHOTO_LIMIT", 409)
        for photo in snapshot.get("collection_photos", []):
            raw = await self.store.get_image(photo["object_key"])
            if (
                not 0 < len(raw) <= 8 * 1024 * 1024
                or len(raw) != photo["size_bytes"]
                or hashlib.sha256(raw).hexdigest() != photo["sha256"]
            ):
                raise AuthError("MOTION_COLLECTION_PHOTO_CHANGED", 409)
            asset_id = f"assets/photo-{photo['id']}.png"
            try:
                with Image.open(io.BytesIO(raw)) as source_image:
                    if source_image.format != "PNG" or source_image.width * source_image.height > 16_000_000:
                        raise AuthError("MOTION_COLLECTION_PHOTO_INVALID", 409)
                    preview = ImageOps.exif_transpose(source_image).convert("RGBA")
                    preview.thumbnail((512, 512))
                    preview.info.clear()
                    output = io.BytesIO()
                    preview.save(output, format="PNG")
                    png = output.getvalue()
            except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
                raise AuthError("MOTION_COLLECTION_PHOTO_INVALID", 409) from exc
            assets.append(_asset(asset_id, "image/png", raw))
            previews.append((asset_id, RenderedFrame(0, png, hashlib.sha256(png).hexdigest())))
            materials.append(
                {
                    "asset_id": asset_id,
                    "title": photo["title"],
                    "sha256": photo["sha256"],
                    "version": photo["version"],
                    "role": "product" if photo["item_id"] else "business_space",
                    "identity_rule": "Material real autorizado; preserve aparência, não invente atributos comerciais.",
                }
            )
        context = {
            key: value
            for key, value in snapshot.items()
            if key not in {"tenant_id", "business_id", "source", "logo", "references", "execution", "collection_photos"}
        }
        if materials:
            context["available_materials"] = materials
        context["source"] = {
            "asset_id": "assets/source.mp4",
            "sha256": source["sha256"],
            "duration_ms": math.floor(info.duration_seconds * 1000),
            "width": info.width,
            "height": info.height,
            "rotation": info.rotation,
            "has_audio": info.audio_codec is not None,
        }
        context["authorized_audio"] = audio
        context["output"] = {"width": 720, "height": 1280, "fps": 30, "duration_ms": duration_ms}
        context["transcript"] = speech_context(context, context["source"])
        context["limitations"] = [
            "Owner-reviewed timing supplied, not automatic listening; preserve the entire original audio."
            if context["transcript"] is not None
            else "No transcript or audio listening supplied; preserve the entire original audio.",
            "Source sampling does not show continuous movement.",
        ]
        return PreparedMotionInput(
            context, tuple(assets), frames, duration_ms, audio, tuple(previews), reference_images
        )
