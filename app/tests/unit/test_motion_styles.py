"""Style catalogue integrity and selection boundaries, without choosing a style."""

import hashlib
import json
from dataclasses import FrozenInstanceError

import pytest

from app.services.auth import AuthError
from app.services.motion_styles import list_motion_styles, resolve_motion_style


def test_complete_catalogue_is_deterministic_immutable_and_self_identifying():
    first = list_motion_styles()
    assert first == list_motion_styles()
    assert [style.id for style in first] == [
        "editorial-janela-v1",
        "tipografia-em-ritmo-v1",
        "clareza-neutra-v1",
    ]
    for style in first:
        content = json.loads(style.content)
        assert style.version == content["version"] == 1
        assert style.id == content["id"]
        assert hashlib.sha256(style.content.encode()).hexdigest() == style.sha256
        assert set(content["formats"]) == {"reel", "story_video", "carousel_motion"}
        assert content["abilities"] and content["grid_hypothesis"] and content["timing_hypothesis_ms"]
        assert "/Users/" not in style.content and "/private/" not in style.content and ".local/" not in style.content
        assert resolve_motion_style(style.id, style.version, style.sha256) == style
    with pytest.raises(FrozenInstanceError):
        first[0].id = "other"


@pytest.mark.parametrize("case", ["unknown", "path", "version", "boolean_version", "hash"])
def test_unknown_or_mismatched_choice_fails_closed(case):
    style = list_motion_styles()[0]
    style_id, version, digest = style.id, style.version, style.sha256
    if case == "unknown":
        style_id = "unknown"
    elif case == "path":
        style_id = "../../style"
    elif case == "version":
        version = 2
    elif case == "boolean_version":
        version = True
    else:
        digest = "0" * 64
    with pytest.raises(AuthError, match="MOTION_STYLE_CHANGED"):
        resolve_motion_style(style_id, version, digest)


def test_missing_changed_or_oversized_snapshot_is_not_loaded(monkeypatch, tmp_path):
    import app.services.motion_styles as module

    style = list_motion_styles()[0]
    monkeypatch.setattr(module, "_ASSETS", tmp_path)
    with pytest.raises(AuthError, match="MOTION_STYLE_CHANGED"):
        resolve_motion_style(style.id, style.version, style.sha256)
    path = tmp_path / f"{style.id}.json"
    path.write_text("changed")
    with pytest.raises(AuthError, match="MOTION_STYLE_CHANGED"):
        resolve_motion_style(style.id, style.version, style.sha256)
    path.write_bytes(b"x" * (module._MAX_BYTES + 1))
    with pytest.raises(AuthError, match="MOTION_STYLE_CHANGED"):
        resolve_motion_style(style.id, style.version, style.sha256)
    with pytest.raises(AuthError, match="MOTION_STYLE_CHANGED"):
        list_motion_styles()


@pytest.mark.parametrize(
    "source",
    [
        b"\xff",
        b"not-json",
        b"[]",
        b'{"id":"other","version":1}',
        b'{"id":"test-v1","version":true}',
        b'{"id":"test-v1","version":2}',
    ],
)
def test_invalid_or_misidentified_snapshot_fails_even_with_matching_hash(monkeypatch, tmp_path, source):
    import app.services.motion_styles as module

    digest = hashlib.sha256(source).hexdigest()
    monkeypatch.setattr(module, "_ASSETS", tmp_path)
    monkeypatch.setattr(module, "_STYLES", {"test-v1": (1, digest)})
    (tmp_path / "test-v1.json").write_bytes(source)
    with pytest.raises(AuthError, match="MOTION_STYLE_CHANGED"):
        resolve_motion_style("test-v1", 1, digest)
