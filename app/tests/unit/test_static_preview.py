"""The first media recipe preserves claims and has bounded, deterministic output."""

import io
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image, ImageDraw, ImageFont

from app.adapters.static_preview import (
    TEMPLATE_VERSION,
    PreviewRenderError,
    _fit,
    _font,
    _ink,
    _lines,
    render_static_preview,
)


def _photo() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (80, 120), "#ffaa33").save(buffer, format="PNG")
    return buffer.getvalue()


def test_bundled_font_has_portuguese_glyphs():
    font = _font(48)
    assert font.getmask("õ").size != font.getmask("□").size


def test_static_recipe_is_deterministic_with_and_without_source():
    inputs = dict(business_name="Lanches da Ana", statement="X-tudo por R$ 20.", brand_color="#6557ed", format="photo")
    card = render_static_preview(**inputs, source_image=None)
    assert card == render_static_preview(**inputs, source_image=None)
    with Image.open(io.BytesIO(card.data)) as picture:
        assert picture.size == (1080, 1350)
        assert picture.format == "JPEG"
    assert card.mime_type == "image/jpeg"
    with_image = render_static_preview(**inputs, source_image=_photo())
    assert with_image.sha256 != card.sha256
    with Image.open(io.BytesIO(with_image.data)) as picture:
        assert picture.getpixel((200, 300))[0] > 100
    story = render_static_preview(**{**inputs, "format": "story", "brand_color": "#ffffff"}, source_image=None)
    with Image.open(io.BytesIO(story.data)) as picture:
        assert picture.size == (1080, 1920)
    assert _ink("#ffffff") == "#182137"
    assert _ink("#000000") == "#ffffff"
    assert _ink("#777777") == "#ffffff"
    assert _ink("#bbbbbb") == "#182137"
    assert TEMPLATE_VERSION == 4


def test_visual_adjustments_keep_the_same_fact_and_source():
    values = dict(
        business_name="Ateliê Ana",
        statement="Manicure clássica disponível.",
        brand_color="#6557ed",
        format="photo",
        source_image=_photo(),
    )
    balanced = render_static_preview(**values)
    photo = render_static_preview(**values, emphasis="photo")
    text = render_static_preview(**values, emphasis="text")
    assert len({balanced.sha256, photo.sha256, text.sha256}) == 3
    with Image.open(io.BytesIO(text.data)) as picture:
        assert max(picture.getpixel((300, 1000))) < 80
    with Image.open(io.BytesIO(photo.data)) as picture:
        assert picture.getpixel((540, 400))[0] > 100
    with pytest.raises(PreviewRenderError, match="PREVIEW_EMPHASIS_UNSUPPORTED"):
        render_static_preview(**values, emphasis="invented")


@pytest.mark.parametrize("dimensions", [(900, 120), (120, 900)])
def test_source_ends_remain_visible_at_extreme_aspect_ratios(dimensions):
    source = Image.new("RGB", dimensions, "#22bb44")
    source_draw = ImageDraw.Draw(source)
    width, height = dimensions
    if width > height:
        source_draw.rectangle((0, 0, width // 4, height), fill="#dd2222")
        source_draw.rectangle((3 * width // 4, 0, width, height), fill="#2222dd")
    else:
        source_draw.rectangle((0, 0, width, height // 4), fill="#dd2222")
        source_draw.rectangle((0, 3 * height // 4, width, height), fill="#2222dd")
    source_bytes = io.BytesIO()
    source.save(source_bytes, "PNG")
    preview = render_static_preview(
        business_name="Ateliê Ana",
        statement="Manicure clássica disponível.",
        brand_color="#6557ed",
        format="photo",
        source_image=source_bytes.getvalue(),
    )
    with Image.open(io.BytesIO(preview.data)) as picture:
        sample_points = ((120, 539), (960, 539)) if width > height else ((540, 260), (540, 820))
        first, last = (picture.getpixel(point) for point in sample_points)
        assert first[0] > first[1] * 2 and first[0] > first[2] * 2
        assert last[2] > last[0] * 2 and last[2] > last[1] * 2
        assert min(picture.getpixel((300, 990))) > 245  # factual copy stays on an opaque card


@pytest.mark.parametrize(
    ("change", "error"),
    [
        ({"format": "short_video"}, "PREVIEW_FORMAT_UNSUPPORTED"),
        ({"brand_color": "red"}, "PREVIEW_BRAND_INVALID"),
        ({"statement": "x" * 500}, "PREVIEW_TEXT_OVERFLOW"),
        ({"source_image": b"bad"}, "PREVIEW_SOURCE_INVALID"),
        ({"source_image": b"x" * (5 * 1024 * 1024 + 1)}, "PREVIEW_SOURCE_TOO_LARGE"),
    ],
)
def test_static_recipe_rejects_unsafe_or_unreadable_input(change, error):
    data = dict(
        business_name="Lanches da Ana",
        statement="X-tudo por R$ 20.",
        brand_color="#6557ed",
        format="photo",
        source_image=None,
    )
    with pytest.raises(PreviewRenderError, match=error):
        render_static_preview(**{**data, **change})


def test_oversized_image_dimensions_and_text_fit_errors():
    raw = MagicMock()
    raw.__enter__.return_value.width = 6000
    raw.__enter__.return_value.height = 5000
    with patch("app.adapters.static_preview.Image.open", return_value=raw):
        with pytest.raises(PreviewRenderError, match="PREVIEW_SOURCE_TOO_LARGE"):
            render_static_preview(
                business_name="Ana",
                statement="Serviço confirmado",
                brand_color="#000000",
                format="photo",
                source_image=b"image",
            )
    draw = ImageDraw.Draw(Image.new("RGB", (100, 100)))
    font = ImageFont.load_default(size=40)
    assert _lines(draw, "", font, 100) == []
    assert len(_lines(draw, "duas palavras", font, 100)) == 2
    with pytest.raises(PreviewRenderError, match="PREVIEW_TEXT_OVERFLOW"):
        _fit(draw, "", 100, 100, 40)
