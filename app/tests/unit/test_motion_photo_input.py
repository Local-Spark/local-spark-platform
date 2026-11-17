"""Photo reels use real authorized images, never a fabricated source recording."""

import hashlib
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.adapters import motion_inputs
from app.schemas.motion_production import MotionRequest
from app.services.auth import AuthError
from app.services.creation_lab_motion_context import LabMotionContext
from app.services.motion_context import MotionContext
from app.services.motion_photos import photo_duration_ms
from app.tests.unit.test_motion_ai import frame


@pytest.mark.parametrize(
    "message,expected",
    [
        ("Quero um reel aconchegante usando nossas fotos", 15000),
        ("Reel de 20 segundos", 20000),
        ("Um reel de 5s", 5000),
        ("Reel de 60 segundos", 60000),
        ("Reel de 90 segundos\nResposta do solicitante:\nPode fazer com 15 segundos", 15000),
    ],
)
def test_photo_duration(message, expected):
    assert photo_duration_ms(message) == expected


@pytest.mark.parametrize("message", ["Reel de 90 segundos", "Reel de 0 segundos", "10 segundos ou 20 segundos"])
def test_unbounded_or_ambiguous_duration_needs_reply(message):
    with pytest.raises(AuthError, match="MOTION_PHOTO_DURATION_REQUIRED"):
        photo_duration_ms(message)


@pytest.mark.parametrize("source,duration", [(None, None), (uuid4(), 15000), (None, 1000)])
def test_video_and_photo_sources_cannot_be_confused(source, duration):
    with pytest.raises(ValidationError):
        MotionRequest(operation_id=uuid4(), instruction="Reel", source_asset_id=source, photo_duration_ms=duration)


async def test_photo_loader_keeps_private_keys_out_and_never_fetches_video(monkeypatch):
    png = frame().png
    identifier = str(uuid4())
    snapshot = {
        "source": None,
        "logo": None,
        "request": MotionRequest(
            operation_id=uuid4(), instruction="Reel com fotos", source_asset_id=None, photo_duration_ms=15000
        ).model_dump(mode="json"),
        "collection_photos": [
            {
                "id": identifier,
                "title": "Interior",
                "version": 1,
                "item_id": None,
                "object_key": "private/interior.png",
                "size_bytes": len(png),
                "sha256": hashlib.sha256(png).hexdigest(),
            }
        ],
    }
    store = SimpleNamespace(get_video=AsyncMock(), get_image=AsyncMock(return_value=png))
    inspect = AsyncMock(side_effect=AssertionError("A photograph is not a recording"))
    monkeypatch.setattr(motion_inputs, "inspect_and_extract_motion_audio", inspect)
    prepared = await motion_inputs.MotionInputLoader(store).prepare(snapshot)
    assert prepared.duration_ms == 15000
    assert prepared.source_frames == ()
    assert prepared.audio == {"mode": "silent", "tracks": []}
    assert prepared.context["transcript"] is None
    assert prepared.context["source"] == {"kind": "photos", "has_audio": False, "duration_ms": 15000}
    assert prepared.asset_previews[0][0] == f"assets/photo-{identifier}.png"
    assert all(asset.id != "assets/source.mp4" for asset in prepared.assets)
    assert "private/interior.png" not in str(prepared.context)
    store.get_video.assert_not_awaited()
    inspect.assert_not_awaited()
    snapshot["collection_photos"] = []
    with pytest.raises(AuthError, match="MOTION_PHOTOS_REQUIRED"):
        await motion_inputs.MotionInputLoader(store).prepare(snapshot)


@pytest.mark.parametrize("has_photo", [False, True])
async def test_shared_message_context_requires_photos_only_when_no_video(monkeypatch, settings, has_photo):
    capture = AsyncMock(return_value={"source": None, "collection_photos": [{"id": "photo"}] if has_photo else []})
    monkeypatch.setattr(MotionContext, "capture", capture)
    session = SimpleNamespace(
        execute=AsyncMock(return_value=SimpleNamespace(mappings=lambda: SimpleNamespace(all=lambda: [])))
    )
    context = LabMotionContext(settings, uuid4())
    request = MotionRequest(
        operation_id=uuid4(), instruction="Reel com fotos", source_asset_id=None, photo_duration_ms=15000
    )
    if has_photo:
        result = await context.capture(session, uuid4(), uuid4(), request)
        assert result["collection_photos"] == [{"id": "photo"}]
    else:
        with pytest.raises(AuthError, match="MOTION_PHOTOS_REQUIRED"):
            await context.capture(session, uuid4(), uuid4(), request)


def test_sound_effects_are_not_substituted_for_music():
    from app.services.motion_photos import photo_music

    assert photo_music(15000) is None  # Current pinned library contains only two effects.


def test_music_requires_curated_rights_duration_and_verified_bytes(monkeypatch):
    from app.adapters.motion_html_renderer import RenderAsset
    from app.services import motion_photos

    item = {
        "id": "background",
        "role": "music",
        "default_for_photo_reels": True,
        "license": "CC0-1.0",
        "duration_ms": 20000,
        "sha256": "a" * 64,
    }
    monkeypatch.setattr(motion_photos, "capture_sound_library", lambda _: {"id": "public-cc0-v1", "items": [item]})
    selection = motion_photos.photo_music(15000)
    asset = RenderAsset("assets/sfx-background.mp3", "audio/mpeg", b"synthetic", "a" * 64)
    monkeypatch.setattr(motion_photos, "load_sound_library", lambda _: (asset,))
    loaded, track = motion_photos.load_photo_music(selection, 15000)
    assert loaded == asset
    assert track["tracks"][0]["role"] == "music"
    assert track["tracks"][0]["trim_end_ms"] == 15000
    assert motion_photos.photo_music(30000) is None
    item["license"] = "unknown"
    assert motion_photos.photo_music(15000) is None
    with pytest.raises(AuthError, match="MOTION_SOUND_LIBRARY_CHANGED"):
        motion_photos.load_photo_music(selection, 15000)


@pytest.mark.parametrize("new_contract", [False, True])
async def test_logo_inventory_and_preview_before_plan_preserve_legacy(new_contract):
    from app.services.motion_photo_intent import PHOTO_INTENT_CONTRACT, PHOTO_INTENT_CONTRACT_V2

    png = frame().png
    descriptor = {"object_key": "private/logo.png", "size_bytes": len(png), "sha256": hashlib.sha256(png).hexdigest()}
    snapshot = {
        "source": None,
        "logo": descriptor,
        "photo_intent_contract": PHOTO_INTENT_CONTRACT if new_contract else PHOTO_INTENT_CONTRACT_V2,
        "request": MotionRequest(
            operation_id=uuid4(), instruction="Fotos", source_asset_id=None, photo_duration_ms=15000
        ).model_dump(mode="json"),
        "collection_photos": [
            {**descriptor, "id": str(UUID(int=i + 1)), "title": "Foto", "version": 1, "item_id": None} for i in range(4)
        ],
    }
    store = SimpleNamespace(get_image=AsyncMock(return_value=png))
    prepared = await motion_inputs.MotionInputLoader(store).prepare(snapshot)
    assert sum(a.id == "assets/logo.png" for a in prepared.assets) == 1
    assert len(prepared.asset_previews) == 4 + int(new_contract)
    logos = [m for m in prepared.context["available_materials"] if m["role"] == "brand_logo"]
    assert bool(logos) == new_contract
    assert "private/logo.png" not in str(prepared.context)
    if new_contract:
        assert logos[0]["asset_id"] == "assets/logo.png"
        assert prepared.asset_previews[-1][0] == "assets/logo.png"

        import json
        from dataclasses import replace

        from app.tests.unit.test_motion_ai import provider, request
        from app.tests.unit.test_motion_photo_planning import photo_case

        _, base, _ = photo_case()
        job = replace(
            request(),
            context={**base.context, "available_materials": prepared.context["available_materials"]},
            assets=(*prepared.assets, *(a for a in base.assets if a.mime_type != "image/png")),
            source_frames=(),
            asset_previews=prepared.asset_previews,
            reference_images=base.reference_images,
        )
        payload = provider().build_request(job)
        content = payload["input"][0]["content"]
        labels = [json.loads(item["text"]) for item in content if item["type"] == "input_text"]
        assert any(item.get("material_asset_id") == "assets/logo.png" for item in labels)
        assert len([item for item in labels if "material_asset_id" in item]) == 5
        assert logos[0] in labels[0]["authorized_context"]["available_materials"]
