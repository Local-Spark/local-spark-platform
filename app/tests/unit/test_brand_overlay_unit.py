"""Brand finishing preserves the generated scene and fails closed on invalid inputs."""

import hashlib
import io
from uuid import uuid4

import pytest
from PIL import Image

from app.adapters.brand_overlay import BrandOverlayError, _font, render_brand_overlay
from app.adapters.material_media import FetchedMedia
from app.schemas.brand_kits import BrandKitOverrides


def _media(size=(1024, 1280), mode="RGB", color="#aabece", format="PNG"):
    image = Image.new(mode, size, color)
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    data = buffer.getvalue()
    return FetchedMedia(data, "image/png" if format == "PNG" else "image/jpeg", hashlib.sha256(data).hexdigest())


@pytest.fixture
def kit():
    return BrandKitOverrides.model_validate(
        {
            "palette": {"primary": "#244739", "background": "#F5F0E7", "accent": "#BB7A48"},
            "heading_font": "DejaVu Serif",
            "body_font": "DejaVu Sans",
            "brand_name": "Café do Cedro",
            "tagline": "Pausas com sabor",
            "cta": "Venha conhecer",
            "formats": {
                "feed": {"layout": "photo_focus", "image_position": "center"},
                "story": {"layout": "photo_focus", "image_position": "center"},
                "reel_cover": {"layout": "photo_focus", "image_position": "center"},
            },
        }
    )


@pytest.mark.parametrize("format,size", [("photo", (1024, 1280)), ("story", (1152, 2048))])
def test_finish_preserves_scene_area_and_dimensions_and_is_deterministic(kit, format, size):
    source = _media(size=size)
    result = render_brand_overlay(
        source, kit=kit, format=format, statement="Café feito com carinho.", cta="Venha hoje."
    )
    again = render_brand_overlay(source, kit=kit, format=format, statement="Café feito com carinho.", cta="Venha hoje.")
    assert result.mime_type == "image/png"
    assert result.sha256 == hashlib.sha256(result.data).hexdigest() == again.sha256
    with Image.open(io.BytesIO(result.data)) as image:
        assert image.size == size
        assert image.getpixel((size[0] // 2, size[1] // 3)) == (170, 190, 206)
        assert image.getpixel((size[0] // 2, size[1] - 1)) != (170, 190, 206)


def test_logo_is_placed_only_when_chosen_and_expected(kit):
    source = _media()
    chosen = kit.model_copy(update={"logo_asset_id": uuid4()})
    logo = _media((40, 20), "RGBA", "#ff0000")
    result = render_brand_overlay(
        source, kit=chosen, format="photo", statement="Café especial.", cta="Peça aqui", logo=logo
    )
    with Image.open(io.BytesIO(result.data)) as image:
        assert image.getpixel((1024 - 1024 // 20 - 1024 // 20, 1280 * 3 // 100 + 1024 // 20)) == (255, 0, 0)
    with pytest.raises(BrandOverlayError, match="BRAND_LOGO_REQUIRED"):
        render_brand_overlay(source, kit=chosen, format="photo", statement="Café especial.", cta="Peça aqui")
    with pytest.raises(BrandOverlayError, match="BRAND_LOGO_REQUIRED"):
        render_brand_overlay(source, kit=kit, format="photo", statement="Café especial.", cta="Peça aqui", logo=logo)


@pytest.mark.parametrize("value", ["", " preço", "preço ", "dois  espaços", "duas\nlinhas", "tab\tx"])
def test_copy_is_not_silently_changed(kit, value):
    with pytest.raises(BrandOverlayError, match="BRAND_COPY_INVALID"):
        render_brand_overlay(_media(), kit=kit, format="photo", statement=value, cta="Peça aqui")


def test_long_copy_is_rejected_instead_of_truncated(kit):
    with pytest.raises(BrandOverlayError, match="BRAND_COPY_TOO_LONG"):
        render_brand_overlay(_media(), kit=kit, format="photo", statement="a" * 200, cta="Peça aqui")


def test_multiple_words_wrap_without_truncating(kit):
    result = render_brand_overlay(
        _media(),
        kit=kit,
        format="photo",
        statement="Uma pausa especial para o seu café da manhã",
        cta="Venha conhecer nosso espaço",
    )
    assert result.data


@pytest.mark.parametrize("size,format", [((500, 625), "photo"), ((1024, 1280), "story"), ((1152, 2048), "photo")])
def test_rejects_wrong_dimensions(kit, size, format):
    with pytest.raises(BrandOverlayError, match="BRAND_DIMENSIONS_INVALID"):
        render_brand_overlay(_media(size), kit=kit, format=format, statement="Café especial.", cta="Peça aqui")


def test_rejects_other_format_and_unavailable_font(kit):
    with pytest.raises(BrandOverlayError, match="BRAND_FORMAT_UNSUPPORTED"):
        render_brand_overlay(_media(), kit=kit, format="video", statement="Café especial.", cta="Peça aqui")
    with pytest.raises(BrandOverlayError, match="BRAND_FONT_UNAVAILABLE"):
        _font("not a licensed kit font", 30)


@pytest.mark.parametrize("kind", ["hash", "mime", "wrong_type", "corrupt", "empty", "oversized", "oversized_pixels"])
def test_corrupt_or_untrusted_image_is_rejected(kit, kind):
    source = _media()
    if kind == "hash":
        source = FetchedMedia(source.data, source.mime_type, "0" * 64)
    elif kind == "mime":
        source = FetchedMedia(source.data, "image/webp", source.sha256)
    elif kind == "wrong_type":
        source = FetchedMedia(source.data, "image/jpeg", source.sha256)
    elif kind == "corrupt":
        data = b"not an image"
        source = FetchedMedia(data, "image/png", hashlib.sha256(data).hexdigest())
    elif kind == "empty":
        source = FetchedMedia(b"", "image/png", hashlib.sha256(b"").hexdigest())
    elif kind == "oversized":
        data = b"x" * (15 * 1024 * 1024 + 1)
        source = FetchedMedia(data, "image/png", hashlib.sha256(data).hexdigest())
    else:
        source = _media((4097, 1))
    with pytest.raises(BrandOverlayError, match="BRAND_IMAGE_INVALID"):
        render_brand_overlay(source, kit=kit, format="photo", statement="Café especial.", cta="Peça aqui")


def test_alternate_layout_and_font_are_supported(kit):
    edited = kit.model_copy(deep=True)
    edited.formats.feed.layout = "offer_focus"
    edited.formats.story.layout = "text_focus"
    edited.heading_font = "DejaVu Sans"
    edited.tagline = ""
    for format, size in [("photo", (1024, 1280)), ("story", (1152, 2048))]:
        result = render_brand_overlay(
            _media(size), kit=edited, format=format, statement="Uma pausa gostosa.", cta="Experimente"
        )
        assert result.data
