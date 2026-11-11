"""Motion instruction snapshots must remain identifiable and format-specific."""

import hashlib

import pytest

import app.services.motion_skills as motion_skills
from app.services.auth import AuthError


@pytest.mark.parametrize(
    ("format", "skill_id", "required_text"),
    [
        ("reel", "instagram-reel-v1", "gravação enviada pelo cliente"),
        ("story_video", "instagram-story-video-v1", "gravação enviada pelo cliente"),
        ("carousel_motion", "instagram-carrossel-motion-v1", "PNG de apoio é opcional"),
    ],
)
def test_resolve_snapshot_for_each_motion_format(format: str, skill_id: str, required_text: str) -> None:
    resolved_id, digest, text = motion_skills.resolve_motion_skill(format)

    assert resolved_id == skill_id
    assert digest == hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert required_text in text
    assert motion_skills.load_motion_skill(skill_id, digest, format) == text


def test_html_reel_skill_preserves_recording_and_old_snapshot() -> None:
    skill_id, digest, instructions = motion_skills.resolve_html_motion_skill("reel")

    assert skill_id == "instagram-reel-v11"
    assert digest == hashlib.sha256(instructions.encode("utf-8")).hexdigest()
    assert "preserva a gravação inteira e sua voz" in instructions
    assert "HTML/scene_init" in instructions
    assert "não invente transcrição" in instructions
    old_id, old_digest, old_instructions = motion_skills.resolve_motion_skill("reel")
    assert old_id == "instagram-reel-v1"
    assert old_digest == "4ed6a1307437b492cf423612855645752fda331e206920abfcf155c198271ec7"
    assert motion_skills.load_motion_skill(old_id, old_digest, "reel") == old_instructions


def test_html_skill_rejects_other_formats() -> None:
    with pytest.raises(AuthError, match="MOTION_SKILL_FORMAT_INVALID"):
        motion_skills.resolve_html_motion_skill("story_video")


@pytest.mark.parametrize("format", ["story", "photo", "short_video", "../reel", ""])
def test_resolve_rejects_non_motion_or_unrecognized_formats(format: str) -> None:
    with pytest.raises(AuthError, match="MOTION_SKILL_FORMAT_INVALID"):
        motion_skills.resolve_motion_skill(format)


@pytest.mark.parametrize(
    ("skill_id", "format", "digest"),
    [
        ("../instagram-reel-v1", "reel", "4ed6a1307437b492cf423612855645752fda331e206920abfcf155c198271ec7"),
        ("instagram-reel-v1", "story_video", "4ed6a1307437b492cf423612855645752fda331e206920abfcf155c198271ec7"),
        ("instagram-reel-v1", "reel", "0" * 64),
    ],
)
def test_load_rejects_unknown_id_format_or_hash(skill_id: str, format: str, digest: str) -> None:
    with pytest.raises(AuthError, match="MOTION_SKILL_CHANGED"):
        motion_skills.load_motion_skill(skill_id, digest, format)


def test_load_rejects_missing_or_modified_snapshot(tmp_path, monkeypatch) -> None:
    skill_id, digest, _ = motion_skills.resolve_motion_skill("reel")
    monkeypatch.setattr(motion_skills, "_ASSETS", tmp_path)

    with pytest.raises(AuthError, match="MOTION_SKILL_CHANGED"):
        motion_skills.load_motion_skill(skill_id, digest, "reel")

    (tmp_path / f"{skill_id}.md").write_text("modified", encoding="utf-8")
    with pytest.raises(AuthError, match="MOTION_SKILL_CHANGED"):
        motion_skills.load_motion_skill(skill_id, digest, "reel")


def test_load_rejects_invalid_utf8_even_if_digest_matches(tmp_path, monkeypatch) -> None:
    skill_id = "instagram-reel-v1"
    invalid_bytes = b"\xff"
    digest = hashlib.sha256(invalid_bytes).hexdigest()
    (tmp_path / f"{skill_id}.md").write_bytes(invalid_bytes)
    monkeypatch.setattr(motion_skills, "_ASSETS", tmp_path)
    monkeypatch.setattr(motion_skills, "_SKILLS", {skill_id: ("reel", digest)})

    with pytest.raises(AuthError, match="MOTION_SKILL_CHANGED"):
        motion_skills.load_motion_skill(skill_id, digest, "reel")


@pytest.mark.parametrize(
    "skill_id",
    [
        "instagram-reel-v2",
        "instagram-reel-v3",
        "instagram-reel-v4",
        "instagram-reel-v5",
        "instagram-reel-v6",
        "instagram-reel-v7",
        "instagram-reel-v8",
        "instagram-reel-v9",
        "instagram-reel-v10",
        "instagram-reel-v11",
    ],
)
def test_html_skill_versions_reject_modified_bytes(tmp_path, monkeypatch, skill_id):
    digest = motion_skills._SKILLS[skill_id][1]
    original = motion_skills.load_motion_skill(skill_id, digest, "reel")
    (tmp_path / f"{skill_id}.md").write_text(original + "changed", encoding="utf-8")
    monkeypatch.setattr(motion_skills, "_ASSETS", tmp_path)
    with pytest.raises(AuthError, match="MOTION_SKILL_CHANGED"):
        motion_skills.load_motion_skill(skill_id, digest, "reel")
