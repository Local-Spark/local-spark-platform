"""Versioned, bounded static-art recipe that keeps real source photos intact."""

import hashlib
import io
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, UnidentifiedImageError

from app.adapters.material_media import FetchedMedia

TEMPLATE_VERSION = 4
Font = ImageFont.ImageFont | ImageFont.FreeTypeFont
FONT_PATH = Path(__file__).parents[1] / "assets" / "DejaVuSans.ttf"
INK = "#182137"
PAPER = "#f6f5f2"


def _font(size: int) -> ImageFont.FreeTypeFont:
    """Use a bundled font so PT-BR accents render identically in worker and tests."""
    return ImageFont.truetype(str(FONT_PATH), size=size)


class PreviewRenderError(Exception):
    def __init__(self, code: str, *, retryable: bool = False) -> None:
        self.code, self.retryable = code, retryable
        super().__init__(code)


def _luminance(color: str) -> float:
    components = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in components]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _ink(color: str) -> str:
    """Choose dark/white text by WCAG relative contrast, including mid-tone brands."""
    luminance = _luminance(color)
    return INK if (luminance + 0.05) / (_luminance(INK) + 0.05) >= 1.05 / (luminance + 0.05) else "#ffffff"


def _lines(draw: ImageDraw.ImageDraw, value: str, font: Font, width: int) -> list[str]:
    words = value.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def _fit(draw: ImageDraw.ImageDraw, value: str, width: int, height: int, start: int) -> tuple[list[str], Font, int]:
    for size in range(start, 27, -4):
        font = _font(size)
        lines = _lines(draw, value, font, width)
        leading = int(size * 1.2)
        if (
            lines
            and len(lines) * leading <= height
            and all(draw.textlength(line, font=font) <= width for line in lines)
        ):
            return lines, font, leading
    raise PreviewRenderError("PREVIEW_TEXT_OVERFLOW")


def _draw_lines(
    draw: ImageDraw.ImageDraw, lines: list[str], font: Font, leading: int, x: int, y: int, fill: str
) -> None:
    for index, line in enumerate(lines):
        draw.text((x, y + index * leading), line, font=font, fill=fill)


def _source_photo(source_image: bytes, size: tuple[int, int]) -> Image.Image:
    if len(source_image) > 5 * 1024 * 1024:
        raise PreviewRenderError("PREVIEW_SOURCE_TOO_LARGE")
    try:
        with Image.open(io.BytesIO(source_image)) as raw:
            if raw.width * raw.height > 24_000_000:
                raise PreviewRenderError("PREVIEW_SOURCE_TOO_LARGE")
            # Contain preserves the complete product/result, even in a very wide photo.
            return ImageOps.contain(ImageOps.exif_transpose(raw).convert("RGB"), size, Image.Resampling.LANCZOS)
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise PreviewRenderError("PREVIEW_SOURCE_INVALID") from exc


def render_static_preview(
    *,
    business_name: str,
    statement: str,
    brand_color: str,
    format: str,
    source_image: bytes | None,
    emphasis: str = "balanced",
) -> FetchedMedia:
    if format not in {"photo", "story"}:
        raise PreviewRenderError("PREVIEW_FORMAT_UNSUPPORTED")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", brand_color):
        raise PreviewRenderError("PREVIEW_BRAND_INVALID")
    if emphasis not in {"balanced", "photo", "text"}:
        raise PreviewRenderError("PREVIEW_EMPHASIS_UNSUPPORTED")
    height = 1920 if format == "story" else 1350
    canvas = Image.new("RGB", (1080, height), PAPER)
    draw = ImageDraw.Draw(canvas)

    # The business identity is outside the photo, so it never obscures the product.
    draw.rectangle((0, 0, 1080, 18), fill=brand_color)
    title_lines, title_font, title_leading = _fit(draw, business_name, 936, 124, 52)
    _draw_lines(draw, title_lines, title_font, title_leading, 72, 58, INK)

    visual_box = (56, 205, 1024, height - 477)
    draw.rounded_rectangle(visual_box, radius=36, fill="#e9e8e5")
    if source_image is not None:
        inset = 12 if emphasis == "photo" else 28
        photo = _source_photo(
            source_image, (visual_box[2] - visual_box[0] - 2 * inset, visual_box[3] - visual_box[1] - 2 * inset)
        )
        backdrop = ImageOps.fit(photo, (912, height - 738)).filter(ImageFilter.GaussianBlur(24))
        canvas.paste(backdrop, (84, 233))
        x = (1080 - photo.width) // 2
        y = (visual_box[1] + visual_box[3] - photo.height) // 2
        canvas.paste(photo, (x, y))
    else:
        fill = brand_color if _ink(brand_color) == "#ffffff" else INK
        accent = "#ffffff" if fill == brand_color else brand_color
        draw.rounded_rectangle((84, 233, 996, height - 505), radius=28, fill=fill)
        middle = (233 + height - 505) // 2
        draw.ellipse((600, middle - 246, 1092, middle + 246), outline=accent, width=6)
        draw.ellipse((687, middle - 159, 1005, middle + 159), outline=accent, width=4)
        draw.text((130, 295), "NOSSO DESTAQUE", font=_font(35), fill=accent)

    # A separate opaque fact panel keeps price and offer legible on every photo.
    fact_top = height - 492
    text_focus = emphasis == "text"
    panel_fill = INK if text_focus else "#ffffff"
    panel_ink = "#ffffff" if text_focus else INK
    draw.rounded_rectangle((56, fact_top, 1024, height - 52), radius=32, fill=panel_fill)
    draw.rounded_rectangle((92, fact_top + 38, 106, fact_top + 96), radius=7, fill=brand_color)
    draw.text((134, fact_top + 43), "CONFIRA", font=_font(29), fill=panel_ink)
    lines, font, leading = _fit(draw, statement, 826, 225, 64)
    _draw_lines(draw, lines, font, leading, 92, fact_top + 122, panel_ink)
    draw.line((92, height - 137, 988, height - 137), fill="#777d8b" if text_focus else "#e5e5e9", width=2)
    draw.text((92, height - 114), "Saiba mais", font=_font(30), fill=panel_ink)
    draw.ellipse((927, height - 112, 967, height - 72), fill=brand_color)

    output = io.BytesIO()
    canvas.save(output, format="JPEG", quality=88, subsampling=0, optimize=True)
    data = output.getvalue()
    return FetchedMedia(data=data, mime_type="image/jpeg", sha256=hashlib.sha256(data).hexdigest())
