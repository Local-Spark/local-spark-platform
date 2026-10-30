from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.media_previews import PreviewRequest
from app.services.auth import AuthError
from app.services.visual_skills import load_visual_skill, select_visual_skill


def test_skill_contract_requires_visual_ai():
    with pytest.raises(ValidationError, match="VISUAL_SKILL_REQUIRES_AI"):
        PreviewRequest(
            operation_id=uuid4(), proposal_id=uuid4(), generation_mode="local", visual_skill_id="instagram-feed-v1"
        )


@pytest.mark.parametrize("skill,format", [("instagram-feed-v1", "photo"), ("instagram-story-v1", "story")])
def test_skill_is_opt_in_versioned_and_format_bound(settings, skill, format):
    with pytest.raises(AuthError, match="VISUAL_SKILL_DISABLED"):
        select_visual_skill(settings, skill, format)
    enabled = settings.model_copy(update={"visual_skill_experiment_enabled": True})
    sha = select_visual_skill(enabled, skill, format)
    assert len(sha) == 64 and "##" in load_visual_skill(skill, sha, format)
    with pytest.raises(AuthError, match="VISUAL_SKILL_FORMAT_INVALID"):
        select_visual_skill(enabled, skill, "invalid")
    with pytest.raises(AuthError, match="VISUAL_SKILL_CHANGED"):
        load_visual_skill(skill, "0" * 64, format)
    enabled.environment = "production"
    with pytest.raises(AuthError, match="VISUAL_SKILL_DISABLED"):
        select_visual_skill(enabled, skill, format)


def test_changed_missing_or_invalid_skill_snapshot_is_refused(settings, monkeypatch, tmp_path):
    import app.services.visual_skills as module

    enabled = settings.model_copy(update={"visual_skill_experiment_enabled": True})
    sha = select_visual_skill(enabled, "instagram-feed-v1", "photo")
    monkeypatch.setattr(module, "_ASSETS", tmp_path)
    with pytest.raises(AuthError, match="VISUAL_SKILL_CHANGED"):
        load_visual_skill("instagram-feed-v1", sha, "photo")
    Path(tmp_path / "instagram-feed-v1.md").write_text("alterado")
    with pytest.raises(AuthError, match="VISUAL_SKILL_CHANGED"):
        load_visual_skill("instagram-feed-v1", sha, "photo")
    with pytest.raises(AuthError, match="VISUAL_SKILL_FORMAT_INVALID"):
        select_visual_skill(enabled, "unknown", "photo")
    with pytest.raises(AuthError, match="VISUAL_SKILL_CHANGED"):
        load_visual_skill("unknown", sha, "photo")
