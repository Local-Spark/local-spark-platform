"""Deterministic, bounded Pillow recipe for a first private static preview."""

import hashlib
import io
import re

from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError

from app.adapters.material_media import FetchedMedia

TEMPLATE_VERSION = 1
Font = ImageFont.ImageFont | ImageFont.FreeTypeFont


class PreviewRenderError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _ink(color: str) -> str:
    red, green, blue = (int(color[index : index + 2], 16) / 255 for index in (1, 3, 5))
    brightness = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    return "#172036" if brightness > 0.65 else "#ffffff"


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
        font = ImageFont.load_default(size=size)
        lines = _lines(draw, value, font, width)
        leading = int(size * 1.2)
        if (
            lines
            and len(lines) * leading <= height
            and all(draw.textlength(line, font=font) <= width for line in lines)
        ):
            return lines, font, leading
    raise PreviewRenderError("PREVIEW_TEXT_OVERFLOW")


def render_static_preview(
    *, business_name: str, statement: str, brand_color: str, format: str, source_image: bytes | None
) -> FetchedMedia:
    if format not in {"photo", "story"}:
        raise PreviewRenderError("PREVIEW_FORMAT_UNSUPPORTED")
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", brand_color):
        raise PreviewRenderError("PREVIEW_BRAND_INVALID")
    height = 1920 if format == "story" else 1350
    canvas = Image.new("RGB", (1080, height), "#f5f4f9")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, 1080, 160), fill=brand_color)
    title_lines, title_font, title_leading = _fit(draw, business_name, 930, 114, 52)
    for index, line in enumerate(title_lines):
        draw.text((68, 27 + index * title_leading), line, font=title_font, fill=_ink(brand_color))

    card_top = 185
    card_bottom = height - 72
    draw.rounded_rectangle((44, card_top, 1036, card_bottom), radius=30, fill="#ffffff")
    fact_top = height - 500
    if source_image is not None:
        if len(source_image) > 5 * 1024 * 1024:
            raise PreviewRenderError("PREVIEW_SOURCE_TOO_LARGE")
        try:
            with Image.open(io.BytesIO(source_image)) as raw:
                if raw.width * raw.height > 24_000_000:
                    raise PreviewRenderError("PREVIEW_SOURCE_TOO_LARGE")
                photo = ImageOps.fit(ImageOps.exif_transpose(raw).convert("RGB"), (992, fact_top - card_top - 24))
        except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
            raise PreviewRenderError("PREVIEW_SOURCE_INVALID") from exc
        canvas.paste(photo, (44, card_top))
        draw = ImageDraw.Draw(canvas)
    else:
        draw.rounded_rectangle((72, card_top + 30, 1008, fact_top - 26), radius=24, fill=brand_color)
        label = "O QUE FAZEMOS"
        label_font = ImageFont.load_default(size=38)
        draw.text((112, card_top + 76), label, font=label_font, fill=_ink(brand_color))

    draw.rectangle((44, fact_top, 1036, card_bottom), fill="#ffffff")
    draw.rectangle((80, fact_top + 48, 94, fact_top + 102), fill=brand_color)
    lines, font, leading = _fit(draw, statement, 820, 300, 64)
    for index, line in enumerate(lines):
        draw.text((118, fact_top + 50 + index * leading), line, font=font, fill="#172036")
    draw.text(
        (86, card_bottom - 84), "Entre em contato para saber mais", font=ImageFont.load_default(size=31), fill="#4c5369"
    )
    output = io.BytesIO()
    canvas.save(output, format="JPEG", quality=88, subsampling=0, optimize=True)
    data = output.getvalue()
    return FetchedMedia(data=data, mime_type="image/jpeg", sha256=hashlib.sha256(data).hexdigest())
