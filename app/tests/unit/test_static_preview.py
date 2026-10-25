"""The first media recipe preserves claims and has bounded, deterministic output."""

import io
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image, ImageDraw, ImageFont

from app.adapters.static_preview import PreviewRenderError, _fit, _ink, _lines, render_static_preview


def _photo() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (80, 120), "#ffaa33").save(buffer, format="PNG")
    return buffer.getvalue()


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
    assert _ink("#ffffff") == "#172036"
    assert _ink("#000000") == "#ffffff"


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
