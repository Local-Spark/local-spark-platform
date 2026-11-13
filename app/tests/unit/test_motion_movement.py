"""Pinned browser helpers travel through the existing isolated scene channel."""

import hashlib
from dataclasses import replace

import pytest

from app.adapters.motion_html_renderer import MotionRenderError, _prepare
from app.services.auth import AuthError
from app.services.motion_creative import alternating_creative_contract
from app.services.motion_movement import SOURCE, movement_contract, movement_hash
from app.tests.unit.test_motion_ai import provider, request
from app.tests.unit.test_motion_html_renderer import bundle


def test_captured_capabilities_are_in_the_counted_payload():
    contract = alternating_creative_contract()
    runtime = contract["movement_runtime"]
    assert runtime["sha256"] == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    context = {"creative_contract": contract}
    payload = provider().build_request(replace(request(), context=context))
    assert "MotionV1.timeline" in payload["input"][0]["content"][0]["text"]
    assert runtime["sha256"] in payload["input"][0]["content"][0]["text"]
    assert movement_hash(context) == runtime["sha256"]


@pytest.mark.parametrize("change", [{"version": "future"}, {"sha256": "f" * 64}, "invalid"])
def test_changed_or_unknown_runtime_cannot_silently_replace_snapshot(change):
    descriptor = {**movement_contract(), **change} if isinstance(change, dict) else change
    with pytest.raises(AuthError, match="MOVEMENT_VERSION_UNAVAILABLE"):
        movement_hash({"creative_contract": {"movement_runtime": descriptor}})


def test_preamble_is_hashed_with_scene_and_legacy_bytes_remain_unchanged(tmp_path):
    original = bundle()
    cfg = _prepare(original, tmp_path / "legacy")
    assert (tmp_path / "legacy/scene.js").read_bytes() == original.scene_init.encode()
    assert movement_hash({}) is None
    assert movement_hash({"creative_contract": None}) is None
    with pytest.raises(AuthError, match="MOVEMENT_VERSION_UNAVAILABLE"):
        movement_hash({"creative_contract": "invalid"})
    assert movement_hash({"creative_contract": {"version": "reel-creative-v2"}}) is None
    modern = replace(original, movement_runtime_sha256=movement_contract()["sha256"])
    new = _prepare(modern, tmp_path / "modern")
    packed = (tmp_path / "modern/scene.js").read_bytes()
    assert packed == SOURCE.read_bytes() + b"\n;\n" + original.scene_init.encode()
    assert new["scene_sha256"] == hashlib.sha256(packed).hexdigest() != cfg["scene_sha256"]
    assert new["html_sha256"] == cfg["html_sha256"]
    with pytest.raises(MotionRenderError, match="MOVEMENT_VERSION_UNAVAILABLE"):
        _prepare(replace(modern, movement_runtime_sha256="f" * 64), tmp_path / "wrong")
    with pytest.raises(MotionRenderError, match="INVALID_INPUT"):
        _prepare(replace(modern, scene_init=""), tmp_path / "empty")


def test_old_runtime_bytes_remain_renderable_and_cannot_be_mixed_with_new_version(tmp_path):
    from app.services.motion_movement import LEGACY_SOURCE

    legacy = movement_contract(legacy=True)
    assert movement_hash({"creative_contract": {"movement_runtime": legacy}}) == legacy["sha256"]
    original = bundle()
    tmp_path = tmp_path / "historical"
    _prepare(replace(original, movement_runtime_sha256=legacy["sha256"]), tmp_path)
    assert (tmp_path / "scene.js").read_bytes() == LEGACY_SOURCE.read_bytes() + b"\n;\n" + original.scene_init.encode()
    with pytest.raises(AuthError, match="MOVEMENT_VERSION_UNAVAILABLE"):
        movement_hash({"creative_contract": {"movement_runtime": {**legacy, "version": "motion-movement-v2"}}})


def test_v2_snapshot_still_resolves_and_can_use_the_registered_repertoire(tmp_path):
    from app.services.motion_movement import V2_SOURCE, movement_v2_contract
    from app.services.motion_repertoire import capture_repertoire, load_repertoire_images

    prior = movement_v2_contract()
    ctx = {
        "creative_contract": {**alternating_creative_contract(), "movement_runtime": prior},
        "repertoire": capture_repertoire("business-reel-v1"),
    }
    assert movement_hash(ctx) == prior["sha256"]
    assert len(load_repertoire_images(ctx)) == 6
    tmp_path = tmp_path / "v2"
    _prepare(replace(bundle(), movement_runtime_sha256=prior["sha256"]), tmp_path)
    assert (tmp_path / "scene.js").read_bytes().startswith(V2_SOURCE.read_bytes())
    assert movement_contract()["version"] == "motion-movement-v3"


def test_structural_runtime_is_prepended_only_when_the_scene_calls_it(tmp_path):
    from app.services.motion_structural_floor import MECHANISM_RUNTIME

    original = bundle()
    plain = _prepare(original, tmp_path / "plain")
    assert MECHANISM_RUNTIME.encode() not in (tmp_path / "plain/scene.js").read_bytes()
    marked = replace(original, scene_init=original.scene_init + "\nStructuralFloorV1.apply(ms);")
    _prepare(marked, tmp_path / "marked")
    packed = (tmp_path / "marked/scene.js").read_bytes()
    assert packed.startswith(MECHANISM_RUNTIME.encode())
    assert plain["scene_sha256"] != hashlib.sha256(packed).hexdigest()
