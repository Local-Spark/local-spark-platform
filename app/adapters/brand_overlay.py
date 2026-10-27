"""Experimental brand finish for a generated scene, not a creative template.

The caller must independently verify the kit, the fact and CTA, and the logo
bytes and their rights before use. A finished piece always needs human review.
"""

import hashlib
import io
from pathlib import Path
from typing import Literal

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from app.adapters.material_media import FetchedMedia
from app.schemas.brand_kits import BrandKitOverrides

_FONT_DIR = Path(__file__).resolve().parents[2] / "catalog/kits/cafe-pausas/v1/fonts"
_FONTS = {"DejaVu Sans": "DejaVuSans.ttf", "DejaVu Serif": "DejaVuSerif.ttf"}
_MAX_SCENE_BYTES = 15 * 1024 * 1024
_MAX_LOGO_BYTES = 4 * 1024 * 1024


class BrandOverlayError(Exception):
    """Stable errors never include the customer's text or private asset bytes."""


def _image(media: FetchedMedia, *, logo: bool) -> Image.Image:
    limit = _MAX_LOGO_BYTES if logo else _MAX_SCENE_BYTES
    if not 0 < len(media.data) <= limit or hashlib.sha256(media.data).hexdigest() != media.sha256:
        raise BrandOverlayError("BRAND_IMAGE_INVALID")
    if media.mime_type not in ({"image/png"} if logo else {"image/png", "image/jpeg"}):
        raise BrandOverlayError("BRAND_IMAGE_INVALID")
    try:
        with Image.open(io.BytesIO(media.data)) as image:
            if (
                image.format != {"image/png": "PNG", "image/jpeg": "JPEG"}[media.mime_type]
                or image.width * image.height > 12_000_000
                or image.width > 4096
                or image.height > 4096
            ):
                raise BrandOverlayError("BRAND_IMAGE_INVALID")
            image.load()
            return image.convert("RGBA")
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise BrandOverlayError("BRAND_IMAGE_INVALID") from exc


def _font(name: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(str(_FONT_DIR / _FONTS[name]), size=size)
    except (OSError, KeyError) as exc:
        raise BrandOverlayError("BRAND_FONT_UNAVAILABLE") from exc


def _fit(
    draw: ImageDraw.ImageDraw, value: str, font_name: str, max_width: int, max_height: int, start_size: int
) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
    # Reject control characters rather than silently normalizing marketing copy.
    if (
        not value
        or value != value.strip()
        or "  " in value
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        raise BrandOverlayError("BRAND_COPY_INVALID")
    for size in range(start_size, max(16, start_size // 2) - 1, -2):
        font = _font(font_name, size)
        lines: list[str] = []
        current = ""
        for word in value.split(" "):
            candidate = f"{current} {word}" if current else word
            if draw.textlength(candidate, font=font) > max_width and current:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
        leading = int(size * 1.25)
        if (
            lines
            and len(lines) * leading <= max_height
            and all(draw.textlength(line, font=font) <= max_width for line in lines)
        ):
            return font, lines, leading
    raise BrandOverlayError("BRAND_COPY_TOO_LONG")


def _draw_text(
    draw: ImageDraw.ImageDraw, x: int, y: int, font: ImageFont.FreeTypeFont, lines: list[str], leading: int, color: str
) -> None:
    for line in lines:
        draw.text((x, y), line, font=font, fill=color)
        y += leading


def render_brand_overlay(
    scene: FetchedMedia,
    *,
    kit: BrandKitOverrides,
    format: Literal["photo", "story"],
    statement: str,
    cta: str,
    logo: FetchedMedia | None = None,
) -> FetchedMedia:
    """Add validated copy and original logo to an AI-generated, text-free scene.

    The caller must supply an authorized, verified logo when the kit has one;
    no logo is fabricated or silently substituted. Output is a private draft.
    """
    if format not in {"photo", "story"}:
        raise BrandOverlayError("BRAND_FORMAT_UNSUPPORTED")
    if bool(kit.logo_asset_id) != bool(logo):
        raise BrandOverlayError("BRAND_LOGO_REQUIRED")
    canvas = _image(scene, logo=False)
    width, height = canvas.size
    if width < 768 or height < 960 or (format == "story" and height * 9 != width * 16):
        raise BrandOverlayError("BRAND_DIMENSIONS_INVALID")
    if format == "photo" and width * 5 != height * 4:
        raise BrandOverlayError("BRAND_DIMENSIONS_INVALID")
    draw = ImageDraw.Draw(canvas)
    margin = width // 20
    top = height * (7 if format == "story" else 3) // 100
    bottom = height * (88 if format == "story" else 96) // 100
    focus_text = (format == "photo" and kit.formats.feed.layout == "offer_focus") or (
        format == "story" and kit.formats.story.layout == "text_focus"
    )
    panel_height = height * (25 if focus_text else 21) // 100
    panel_top = bottom - panel_height
    fade_top = max(top + width // 8, panel_top - height // 10)
    gradient = Image.linear_gradient("L").resize((1, height - fade_top)).point(lambda value: min(235, value * 2))
    band = Image.new("RGBA", (width, height - fade_top), kit.palette.primary)
    band.putalpha(gradient.resize((width, height - fade_top)))
    canvas.alpha_composite(band, (0, fade_top))
    draw = ImageDraw.Draw(canvas)
    # Keep the scene visible, using a compact brand badge and a soft lower fade.
    mark_size = width // 10
    name_font, name_lines, name_leading = _fit(
        draw, kit.brand_name, kit.body_font, width * 3 // 5, mark_size, width // 34
    )
    tagline_lines: list[str] = []
    tagline_font = name_font
    tagline_leading = 0
    if kit.tagline:
        tagline_font, tagline_lines, tagline_leading = _fit(
            draw, kit.tagline, kit.body_font, width * 3 // 5, mark_size, width // 45
        )
    widths = [draw.textlength(line, font=name_font) for line in name_lines]
    widths.extend(draw.textlength(line, font=tagline_font) for line in tagline_lines)
    badge_width = int(max(widths)) + margin
    badge_height = len(name_lines) * name_leading + len(tagline_lines) * tagline_leading + margin // 2
    draw.rounded_rectangle(
        (margin, top, margin + badge_width, top + badge_height), radius=width // 90, fill=kit.palette.primary
    )
    _draw_text(
        draw, margin + margin // 2, top + margin // 5, name_font, name_lines, name_leading, kit.palette.background
    )
    if tagline_lines:
        _draw_text(
            draw,
            margin + margin // 2,
            top + margin // 5 + len(name_lines) * name_leading,
            tagline_font,
            tagline_lines,
            tagline_leading,
            kit.palette.background,
        )
    if logo is not None:
        mark = _image(logo, logo=True)
        mark.thumbnail((mark_size, mark_size), Image.Resampling.LANCZOS)
        x = width - margin - mark_size
        draw.rounded_rectangle(
            (x - margin // 4, top - margin // 4, x + mark_size + margin // 4, top + mark_size + margin // 4),
            radius=width // 80,
            fill=kit.palette.background,
        )
        canvas.alpha_composite(mark, (x + (mark_size - mark.width) // 2, top + (mark_size - mark.height) // 2))
    inner = width - margin * 2
    title_font, title_lines, title_leading = _fit(
        draw, statement, kit.heading_font, inner, panel_height * 55 // 100, width // 19
    )
    cta_font, cta_lines, cta_leading = _fit(draw, cta, kit.body_font, inner, panel_height * 25 // 100, width // 33)
    _draw_text(
        draw, margin, panel_top + panel_height // 9, title_font, title_lines, title_leading, kit.palette.background
    )
    _draw_text(draw, margin, bottom - panel_height * 3 // 10, cta_font, cta_lines, cta_leading, kit.palette.background)
    output = io.BytesIO()
    canvas.convert("RGB").save(output, format="PNG", optimize=True)
    data = output.getvalue()
    return FetchedMedia(data=data, mime_type="image/png", sha256=hashlib.sha256(data).hexdigest())
