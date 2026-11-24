"""New video scene runtime pins, legacy identity and tamper rejection."""

from copy import deepcopy

import pytest

from app.services import motion_video_scene_visibility as scope
from app.services.auth import AuthError
from app.services.motion_context import capture_motion_guidance
from app.services.motion_video_reel import guarded_video_scene_init
from app.tests.unit.test_motion_audiovisual import natural_body
from app.tests.unit.test_motion_video_reel import CTX, artifact


def test_capture_and_replay_never_promote_historical_or_photo_snapshots():
    assert scope.capture_scene_visibility(video=False, previous=None) == {}
    assert scope.capture_scene_visibility(video=True, previous={}) == {}
    new = capture_motion_guidance(natural_body(repertoire_id=None))
    assert new["video_scene_visibility_contract"] == scope.CONTRACT
    body = natural_body(repertoire_id=None)
    current = capture_motion_guidance(body)
    assert capture_motion_guidance(body, previous=current) == current
    old = deepcopy(current)
    old.pop("video_scene_visibility_contract")
    assert capture_motion_guidance(body, previous=old) == old


def test_executor_wraps_model_before_unchanged_guard_and_preserves_legacy_bytes():
    comp = artifact()
    old = guarded_video_scene_init(comp, CTX, comp.scene_init)
    assert scope.scoped_video_scene_init(comp, CTX, comp.scene_init) == comp.scene_init
    context = {**CTX, "video_scene_visibility_contract": scope.CONTRACT}
    scoped = scope.scoped_video_scene_init(comp, context, comp.scene_init)
    result = guarded_video_scene_init(comp, context, scoped)
    assert result.startswith(comp.scene_init)
    assert result.index("installVideoSceneVisibilityV1") < result.index("installVideoReelV1")
    assert old == guarded_video_scene_init(comp, CTX, scope.scoped_video_scene_init(comp, CTX, comp.scene_init))


@pytest.mark.parametrize(
    "context",
    [
        {**CTX, "video_scene_visibility_contract": {}},
        {"video_scene_visibility_contract": scope.CONTRACT},
    ],
)
def test_changed_or_unbound_contract_rejected(context):
    with pytest.raises(AuthError, match="MOTION_VIDEO_SCENE_CONTRACT_CHANGED"):
        scope.scoped_video_scene_init(artifact(), context, "source")


def test_missing_plan_or_runtime_bytes_rejected(tmp_path, monkeypatch):
    context = {**CTX, "video_scene_visibility_contract": scope.CONTRACT}
    with pytest.raises(AuthError, match="MOTION_VIDEO_PLAN_REQUIRED"):
        scope.scoped_video_scene_init(artifact().model_copy(update={"motion_plan": None}), context, "source")
    missing = tmp_path / "missing.js"
    monkeypatch.setattr(scope, "SOURCE", missing)
    with pytest.raises(AuthError, match="MOTION_VIDEO_SCENE_RUNTIME_CHANGED"):
        scope.scoped_video_scene_init(artifact(), context, "source")
    missing.write_text("changed")
    with pytest.raises(AuthError, match="MOTION_VIDEO_SCENE_RUNTIME_CHANGED"):
        scope.scoped_video_scene_init(artifact(), context, "source")
