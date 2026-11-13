"""Bounded private media preparation, with real sampled frames and preserved audio."""

import hashlib
import io
import math
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PIL import Image, ImageOps, UnidentifiedImageError

from app.adapters.material_media import FetchedMedia, MaterialStore
from app.adapters.motion_html_renderer import RenderAsset, RenderedFrame
from app.adapters.motion_media import _command, inspect_and_extract_motion_audio, inspect_supplemental_audio
from app.schemas.motion_production import MotionDucking, MotionSoundEvent
from app.services.auth import AuthError
from app.services.motion_audio import compile_soundtrack
from app.services.motion_preparation import additional_source_times
from app.services.motion_repertoire import RepertoireImage, load_repertoire_images
from app.services.motion_sound_analysis import prepare_sound_assessment
from app.services.motion_sound_library import load_sound_library
from app.services.motion_speech import speech_context

if TYPE_CHECKING:
    from app.services.motion_context import MotionContext

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
    soundtrack: dict[str, Any] | None = None
    baseline_frames: tuple[RenderedFrame, ...] = ()


def _asset(name: str, mime: str, data: bytes) -> RenderAsset:
    return RenderAsset(name, mime, data, hashlib.sha256(data).hexdigest())


async def baseline_video_frames(data: bytes, times: tuple[int, ...]) -> tuple[RenderedFrame, ...]:
    """Decode specific frames of an existing MP4; never execute a composition or render a new piece."""
    if not 2 <= len(times) <= 20 or tuple(sorted(set(times))) != times or any(not 0 <= t < 60000 for t in times):
        raise AuthError("MOTION_EVOLUTION_SAMPLE_TIMES_INVALID", 409)
    frames = []
    with tempfile.TemporaryDirectory(prefix="motion-baseline-") as folder:
        path = Path(folder) / "baseline.mp4"
        path.write_bytes(data)
        for ms in times:
            index = ms * 30 // 1000
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
                "-i",
                str(path),
                "-vf",
                f"select=eq(n\\,{index}),scale=360:640",
                "-frames:v",
                "1",
                "-f",
                "image2pipe",
                "-vcodec",
                "png",
                "pipe:1",
                output_limit=4 * 1024 * 1024,
            )
            if not png.startswith(b"\x89PNG\r\n\x1a\n"):
                raise AuthError("MOTION_EVOLUTION_EVIDENCE_INVALID", 409)
            frames.append(RenderedFrame(round(index * 1000 / 30), png, hashlib.sha256(png).hexdigest(), index))
    return tuple(frames)


async def source_frames(
    data: bytes, duration_ms: int, *, extra_times: tuple[int, ...] = ()
) -> tuple[RenderedFrame, ...]:
    samples = tuple(
        sorted({0, *(duration_ms * index // 5 for index in range(1, 5)), max(0, duration_ms - 100), *extra_times})
    )
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
    def __init__(self, store: MaterialStore, context: "MotionContext | None" = None):
        self.store, self.context = store, context

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
        assets.extend(load_sound_library(snapshot))
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
        request = snapshot.get("request", {})
        events = tuple(MotionSoundEvent.model_validate(event) for event in request.get("sound_events", []))
        duck_raw = request.get("music_ducking")
        ducking = MotionDucking.model_validate(duck_raw) if duck_raw is not None else None
        captured_audio = snapshot.get("audio_materials", [])
        ids = [str(item["id"]) for item in captured_audio]
        if len(ids) != len(set(ids)) or set(ids) != {str(event.asset_id) for event in events}:
            raise AuthError("MOTION_AUDIO_MATERIAL_CHANGED", 409)
        audio_catalog: dict[str, dict[str, Any]] = {}
        audio_public = []
        extensions = {"audio/ogg": "ogg", "audio/mpeg": "mp3", "audio/wav": "wav"}
        for material in captured_audio:
            raw = await self.store.get_audio(material["object_key"])
            if (
                not 0 < len(raw) <= 16 * 1024 * 1024
                or len(raw) != material["size_bytes"]
                or hashlib.sha256(raw).hexdigest() != material["sha256"]
                or material["mime_type"] not in extensions
            ):
                raise AuthError("MOTION_AUDIO_MATERIAL_CHANGED", 409)
            identifier = str(material["id"])
            available_seconds = await inspect_supplemental_audio(
                FetchedMedia(raw, material["mime_type"], material["sha256"])
            )
            if any(
                event.trim_end_ms > available_seconds * 1000 + 1
                for event in events
                if str(event.asset_id) == identifier
            ):
                raise AuthError("MOTION_AUDIO_MATERIAL_TOO_SHORT", 409)
            asset_id = f"assets/audio-{identifier}.{extensions[material['mime_type']]}"
            asset = _asset(asset_id, material["mime_type"], raw)
            assets.append(asset)
            audio_catalog[identifier] = {"asset_id": asset_id, "sha256": asset.sha256}
            audio_public.append(
                {"asset_id": asset_id, "sha256": asset.sha256, "rights": "owner_confirmed", "origin": "owner_material"}
            )
        source_duration = int(info.duration_seconds * 1000)
        extra = additional_source_times(snapshot, source_duration)
        frames = (
            await source_frames(data, source_duration, extra_times=extra)
            if extra
            else await source_frames(data, source_duration)
        )
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
            if key
            not in {
                "tenant_id",
                "business_id",
                "source",
                "logo",
                "references",
                "execution",
                "collection_photos",
                "audio_materials",
            }
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
        soundtrack = compile_soundtrack(audio, events, ducking, audio_catalog, duration_ms)
        if soundtrack is not None:
            context["authorized_soundtrack"] = soundtrack
            context["available_audio"] = audio_public
        context["output"] = {"width": 720, "height": 1280, "fps": 30, "duration_ms": duration_ms}
        context["transcript"] = speech_context(context, context["source"])
        context["limitations"] = [
            "Owner-reviewed timing supplied, not automatic listening; preserve the entire original audio."
            if context["transcript"] is not None
            else "No transcript or audio listening supplied; preserve the entire original audio.",
            "Source sampling does not show continuous movement.",
        ]
        prepared = PreparedMotionInput(
            context, tuple(assets), frames, duration_ms, audio, tuple(previews), reference_images, soundtrack
        )
        prepared = await prepare_sound_assessment(prepared)
        if snapshot.get("evolution") is not None:
            from app.services.motion_evolution_inputs import load_evolution

            if self.context is None:
                raise AuthError("MOTION_EVOLUTION_RESOLVER_REQUIRED", 409)
            return await load_evolution(prepared, snapshot["evolution"], self.context, self.store)
        return prepared
