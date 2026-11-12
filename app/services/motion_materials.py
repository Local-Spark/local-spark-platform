"""Bind planned image bytes and deterministic previews before code generation."""

import hashlib
import io
from dataclasses import replace
from typing import cast

from PIL import Image, ImageOps, UnidentifiedImageError

from app.adapters.motion_html_renderer import RenderedFrame
from app.adapters.motion_inputs import PreparedMotionInput
from app.schemas.motion_production import MotionConstructionPlan
from app.services.auth import AuthError


def prepare_implementation_materials(
    plan: MotionConstructionPlan, prepared: PreparedMotionInput
) -> PreparedMotionInput:
    ids = sorted(
        {
            element.asset_id
            for scene in plan.motion_plan.scenes
            for element in scene.elements
            if element.role == "image" and element.asset_id is not None
        }
    )
    assets = {asset.id: asset for asset in prepared.assets}
    if len(assets) != len(prepared.assets):
        raise AuthError("MOTION_IMPLEMENTATION_MATERIAL_INVALID", 409)
    previews = [(identifier, preview) for identifier, preview in prepared.asset_previews if identifier not in ids]
    materials = []
    for identifier in ids:
        asset = assets.get(identifier)
        if (
            asset is None
            or asset.mime_type != "image/png"
            or not 0 < len(asset.data) <= 8 * 1024 * 1024
            or hashlib.sha256(asset.data).hexdigest() != asset.sha256
        ):
            raise AuthError("MOTION_IMPLEMENTATION_MATERIAL_INVALID", 409)
        try:
            with Image.open(io.BytesIO(asset.data)) as image:
                if image.format != "PNG" or image.width * image.height > 16_000_000:
                    raise ValueError
                rgba = ImageOps.exif_transpose(image).convert("RGBA")
                width, height = rgba.size
                lo, hi = cast(tuple[int, int], rgba.getchannel("A").getextrema())
                if hi == 0:
                    raise ValueError
                rgba.thumbnail((512, 512))
                rgba.info.clear()
                out = io.BytesIO()
                rgba.save(out, format="PNG")
                png = out.getvalue()
        except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
            raise AuthError("MOTION_IMPLEMENTATION_MATERIAL_INVALID", 409) from exc
        preview_hash = hashlib.sha256(png).hexdigest()
        previews.append((identifier, RenderedFrame(0, png, preview_hash)))
        materials.append(
            {
                "asset_id": identifier,
                "sha256": asset.sha256,
                "width": width,
                "height": height,
                "transparency": "has_transparency" if lo < 255 else "opaque",
                "preview_sha256": preview_hash,
                "limitations": "Imagem plana; não revela faces ocultas nem geometria 3D.",
            }
        )
    return replace(
        prepared, asset_previews=tuple(previews), context={**prepared.context, "implementation_materials": materials}
    )


def verify_implementation_materials(plan: MotionConstructionPlan, prepared: PreparedMotionInput) -> None:
    expected = prepare_implementation_materials(plan, prepared)
    if (
        prepared.context.get("implementation_materials") != expected.context["implementation_materials"]
        or prepared.asset_previews != expected.asset_previews
    ):
        raise AuthError("MOTION_IMPLEMENTATION_MATERIAL_CHANGED", 409)
