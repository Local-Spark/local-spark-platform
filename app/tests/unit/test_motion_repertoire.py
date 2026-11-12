"""Curated references reach the counted input, never the render asset list."""

import base64
import hashlib
import json
import shutil
from dataclasses import replace
from unittest.mock import AsyncMock

import httpx
import pytest
from pydantic import ValidationError

from app.adapters import motion_inputs
from app.adapters.motion_html_renderer import RenderAsset
from app.schemas.motion_production import MotionRequest
from app.services import motion_repertoire as repertoire
from app.services.auth import AuthError
from app.services.motion_creative import motion_creative_contract
from app.tests.unit.test_motion_ai import frame, provider, request
from app.tests.unit.test_motion_inputs import source_snapshot, video_info


def context():
    return {
        "creative_contract": motion_creative_contract(),
        "repertoire": repertoire.capture_repertoire("business-reel-v1"),
    }


def test_v2_reference_cards_and_pixels_reach_product_payload_with_explicit_provenance():
    ctx = {
        "creative_contract": motion_creative_contract(),
        "repertoire": repertoire.capture_repertoire("business-reel-v2"),
    }
    descriptor = ctx["repertoire"]
    images = repertoire.load_repertoire_images(ctx)
    payload = provider().build_request(replace(request(), context=ctx, reference_images=images))
    content = payload["input"][0]["content"]
    serialized = json.loads(content[0]["text"])["authorized_context"]["repertoire"]
    assert serialized == descriptor
    assert len(images) == 5
    assert {card["id"] for card in serialized["reference_cards"]} == {
        "maestros-acao-com-consequencia", "lucas-hierarquia-espacial"
    }
    assert all(
        card["before"] and card["action"] and card["after"] and card["adaptation"]
        for card in serialized["reference_cards"]
    )
    assert {image_id for card in serialized["reference_cards"] for image_id in card["reference_image_ids"]} == {
        image.id for image in images
    }
    for index, image in enumerate(images):
        metadata = json.loads(content[1 + index * 2]["text"])["finish_reference"]
        assert metadata == descriptor["reference_images"][index]
        assert metadata["role"] == "finish_reference_only"
        assert base64.b64decode(content[2 + index * 2]["image_url"].split(",")[1]) == image.data
    assert json.loads(content[0]["text"])["assets"] == []


def test_v2_rejects_altered_card_under_the_pinned_capture():
    ctx = {
        "creative_contract": motion_creative_contract(),
        "repertoire": repertoire.capture_repertoire("business-reel-v2"),
    }
    images = repertoire.load_repertoire_images(ctx)
    ctx["repertoire"]["reference_cards"][0]["adaptation"] = "changed"
    with pytest.raises(AuthError, match="MOTION_REPERTOIRE_CHANGED"):
        repertoire.validate_repertoire_images(ctx, images)


async def test_full_repertoire_enters_same_counted_payload_without_becoming_assets():
    ctx = context()
    images = repertoire.load_repertoire_images(ctx)
    calls = []

    def transport(sent):
        calls.append(json.loads(sent.content))
        return httpx.Response(200, json={"object": "response.input_tokens", "input_tokens": 12000})

    model = provider(transport)
    job = replace(request(), context=ctx, reference_images=images, source_frames=(frame(),))
    payload = model.build_request(job)
    assert await model.count_input_tokens(job, payload) == 12000
    assert len(calls) == 1
    assert calls[0] == {key: payload[key] for key in ("model", "input", "instructions", "text", "reasoning")}
    content = payload["input"][0]["content"]
    assert sum(part["type"] == "input_image" for part in content) == 7
    data = json.loads(content[0]["text"])
    assert data["assets"] == []
    assert {source["id"] for source in data["authorized_context"]["repertoire"]["sources"]} == {
        "maestro",
        "finalizador",
        "claude-video",
        "felipe-borges",
        "lucas-leite",
    }
    for i, image in enumerate(images):
        metadata = json.loads(content[1 + i * 2]["text"])["finish_reference"]
        assert metadata == ctx["repertoire"]["reference_images"][i]
        assert metadata["role"] == "finish_reference_only" and metadata["at_ms"] > 0
        assert base64.b64decode(content[2 + i * 2]["image_url"].split(",")[1]) == image.data
    for example in data["authorized_context"]["repertoire"]["examples"]:
        assert hashlib.sha256(example["content"].encode()).hexdigest() == example["sha256"]
        assert example["entrypoint"] in example["content"]
    assert "Não são assets autorizados" in payload["instructions"]
    assert "test-only" not in json.dumps(payload) and "object_key" not in json.dumps(payload)


async def test_loader_preserves_reference_labels_but_keeps_bytes_out_of_render_assets(monkeypatch):
    snapshot = {**source_snapshot(), **context()}
    store = AsyncMock()
    store.get_video.return_value = b"original recording"
    monkeypatch.setattr(motion_inputs, "inspect_and_extract_motion_audio", AsyncMock(return_value=(video_info(), None)))
    monkeypatch.setattr(motion_inputs, "source_frames", AsyncMock(return_value=(frame(),)))
    prepared = await motion_inputs.MotionInputLoader(store).prepare(snapshot)
    assert len(prepared.reference_images) == 6
    assert prepared.context["repertoire"] == snapshot["repertoire"]
    assert not {a.sha256 for a in prepared.assets} & {r.sha256 for r in prepared.reference_images}
    assert len(prepared.assets) == 3  # Source and two authorized local fonts only.
    assert repertoire.load_repertoire_images({}) == ()
    assert repertoire.validate_repertoire_images({}, ()) == []


@pytest.mark.parametrize("change", ["missing", "duplicate", "id", "sha", "bytes", "as_asset", "unexpected"])
def test_incomplete_or_misassociated_references_fail_before_transport(change):
    ctx = context()
    images = repertoire.load_repertoire_images(ctx)
    assets = ()
    if change == "missing":
        images = images[:-1]
    elif change == "duplicate":
        images = (images[0], images[0], *images[2:])
    elif change == "id":
        images = (replace(images[0], id="another-reference"), *images[1:])
    elif change == "sha":
        images = (replace(images[0], sha256="0" * 64), *images[1:])
    elif change == "bytes":
        images = (replace(images[0], data=b"changed"), *images[1:])
    elif change == "as_asset":
        assets = (RenderAsset("assets/forbidden.jpg", "image/jpeg", images[0].data, images[0].sha256),)
    else:
        ctx = {}
    with pytest.raises(AuthError, match="MOTION_REPERTOIRE_"):
        provider().build_request(replace(request(), context=ctx, reference_images=images, assets=assets))


@pytest.mark.parametrize(
    "limit,value", [("MAX_IMAGES", 5), ("MAX_IMAGE_BYTES", 1), ("MAX_IMAGE_TOTAL_BYTES", 1), ("MAX_TEXT_BYTES", 1)]
)
def test_attachment_limits_apply_before_serialization(monkeypatch, limit, value):
    ctx = context()
    images = repertoire.load_repertoire_images(ctx)
    monkeypatch.setattr(repertoire, limit, value)
    with pytest.raises(AuthError, match="MOTION_REPERTOIRE_"):
        provider().build_request(replace(request(), context=ctx, reference_images=images))


@pytest.mark.parametrize("change", ["id", "manifest", "source", "not_object"])
def test_context_cannot_change_source_or_license_under_an_existing_hash(change):
    ctx = context()
    images = repertoire.load_repertoire_images(ctx)
    if change == "id":
        ctx["repertoire"]["id"] = "unknown"
    elif change == "manifest":
        ctx["repertoire"]["manifest_sha256"] = "0" * 64
    elif change == "source":
        ctx["repertoire"]["sources"][0]["permission"] = "changed"
    else:
        ctx["repertoire"] = "invalid"
    with pytest.raises(AuthError, match="MOTION_REPERTOIRE_CHANGED"):
        repertoire.validate_repertoire_images(ctx, images)
    with pytest.raises(AuthError, match="MOTION_REPERTOIRE_CHANGED|MOTION_REPERTOIRE_UNAVAILABLE"):
        repertoire.load_repertoire_images(ctx)


@pytest.mark.parametrize("change", ["missing", "changed"])
def test_examples_require_the_actual_versioned_runtimes(change):
    ctx = context()
    if change == "missing":
        ctx.pop("creative_contract")
    else:
        ctx["creative_contract"]["element_library"]["sha256"] = "0" * 64
    with pytest.raises(AuthError, match="MOTION_REPERTOIRE_RUNTIME_REQUIRED"):
        repertoire.load_repertoire_images(ctx)


@pytest.mark.parametrize(
    "file,change",
    [
        ("manifest.json", "missing"),
        ("examples/route-action.js", "changed"),
        ("references/lucas-orbit-03.jpg", "changed"),
    ],
)
def test_missing_or_changed_library_files_fail_closed(tmp_path, monkeypatch, file, change):
    ctx = context()
    target = tmp_path / "business-reel-v1"
    shutil.copytree(repertoire.ROOT / "business-reel-v1", target)
    path = target / file
    if change == "missing":
        path.unlink()
    else:
        path.write_bytes(b"changed")
    monkeypatch.setattr(repertoire, "ROOT", tmp_path)
    with pytest.raises(AuthError, match="MOTION_REPERTOIRE_FILE_CHANGED"):
        repertoire.load_repertoire_images(ctx)


def test_bounded_read_rejects_path_escape_and_oversize_without_exposing_content(tmp_path, monkeypatch):
    secret = tmp_path / "outside"
    secret.write_bytes(b"private")
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(AuthError, match="^MOTION_REPERTOIRE_FILE_CHANGED$"):
        repertoire._read(root, "../outside", hashlib.sha256(b"private").hexdigest(), 100)
    with pytest.raises(AuthError, match="FILE_CHANGED"):
        repertoire._read(tmp_path, "outside", hashlib.sha256(b"private").hexdigest(), 1)
    with pytest.raises(AuthError, match="UNAVAILABLE"):
        repertoire.capture_repertoire("../outside")
    monkeypatch.setattr(repertoire, "MAX_TEXT_BYTES", 15000)
    with pytest.raises(AuthError, match="TEXT_LIMIT"):
        repertoire.capture_repertoire("business-reel-v1")


def test_selection_is_explicit_and_legacy_request_serialization_is_unchanged():
    from uuid import uuid4

    data = {"operation_id": uuid4(), "source_asset_id": uuid4(), "instruction": "Fictício"}
    assert "repertoire_id" not in MotionRequest(**data).model_dump()
    assert MotionRequest(**data, repertoire_id="business-reel-v1").model_dump()["repertoire_id"] == "business-reel-v1"
    with pytest.raises(ValidationError):
        MotionRequest(**data, repertoire_id="unknown")
