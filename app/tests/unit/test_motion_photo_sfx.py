"""A5a: optional editorial SFX, explicit omissions and an untouched Music branch."""

from dataclasses import replace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.motion_production import MotionConstructionPlan, MotionRequest
from app.services.auth import AuthError
from app.services.motion_context import capture_motion_guidance
from app.services.motion_photos import PHOTO_MOTION_RULES, music_soundtrack, planned_photo_request
from app.services.motion_sound_library import PHOTO_SFX_RULES, apply_planned_sound, load_sound_library
from app.tests.unit.test_motion_audiovisual import sound_data
from app.tests.unit.test_motion_photo_planning import photo_case


@pytest.mark.parametrize("human", [True, False])
@pytest.mark.parametrize("message", ["Reel do café", "Reel sem som", "Reel silencioso", "Reel sem música"])
def test_library_is_only_available_in_authorized_planning_path(human, message):
    base = MotionRequest(operation_id=uuid4(), source_asset_id=None, photo_duration_ms=15000, instruction=message)
    assert "sound_library" not in capture_motion_guidance(base)
    assert load_sound_library(capture_motion_guidance(base)) == ()
    request = planned_photo_request(base, [{"id": uuid4()}], human_review=human)
    context = capture_motion_guidance(request)
    if message == "Reel do café":
        assert request.sound_library_id == "public-cc0-v1"
        assert len(load_sound_library(context)) == 2
        assert PHOTO_SFX_RULES in context["photo_motion"]["rules"]
        assert context["creative_contract"]["media_visibility_policy"] == context["photo_motion"]["rules"]
    else:
        assert request.sound_library_id is None
        assert load_sound_library(context) == ()
    assert request.review_checkpoints == human
    assert request.automatic_plan != human


def test_historical_photo_snapshot_does_not_gain_sfx_rules_or_assets():
    body, prepared, _ = photo_case()
    old_body = body.model_copy(update={"sound_library_id": None})
    old = capture_motion_guidance(old_body)
    old["photo_motion"]["rules"] = PHOTO_MOTION_RULES
    restored = capture_motion_guidance(old_body, previous=old)
    assert restored["photo_motion"]["rules"] == PHOTO_MOTION_RULES
    assert "sound_library" not in restored
    assert prepared.context["photo_motion"]["music_policy"] == "elevenlabs-music-v1"


@pytest.mark.parametrize("candidate", ["coffee-pour", "cup-contact"])
@pytest.mark.parametrize("music", [False, True])
@pytest.mark.parametrize("select", [False, True])
def test_omission_and_justified_effects_preserve_music_exactly(music, select, candidate):
    _, prepared, plan = photo_case()
    if music:
        soundtrack = music_soundtrack("assets/photo-music.mp3", 15000)
        prepared = replace(
            prepared, soundtrack=soundtrack, context={**prepared.context, "authorized_soundtrack": soundtrack}
        )
    if select:
        data = plan.model_dump(mode="json")
        item = next(item for item in prepared.context["sound_library"]["items"] if item["id"] == candidate)
        data["audiovisual"]["sounds"] = [
            {
                **sound_data(),
                "candidate_id": candidate,
                "candidate_sha256": item["sha256"],
                "purpose": "Sonorização editorial da representação de servir"
                if candidate == "coffee-pour"
                else "Acentuar apoio editorial",
            }
        ]
        data["audiovisual"]["omitted_sounds"] = [
            item for item in data["audiovisual"]["omitted_sounds"] if item["candidate_id"] != candidate
        ]
        plan = MotionConstructionPlan.model_validate(data)
    result = apply_planned_sound(prepared, plan)
    if not select:
        assert result is prepared
    else:
        tracks = result.soundtrack["tracks"]
        assert [t for t in tracks if t["role"] == "music"] == (prepared.soundtrack["tracks"] if music else [])
        assert tracks[-1]["role"] == "effect"
        assert tracks[-1]["asset_id"] == f"assets/sfx-{candidate}.mp3"
        assert result.audio == prepared.audio


@pytest.mark.parametrize("failure", ["unaccounted", "unjustified", "no_action", "foreign", "bytes"])
def test_selection_requires_justification_action_authorization_and_verified_bytes(failure):
    _, prepared, plan = photo_case()
    data = plan.model_dump(mode="json")
    sound = sound_data()
    data["audiovisual"]["sounds"] = [sound]
    data["audiovisual"]["omitted_sounds"] = [data["audiovisual"]["omitted_sounds"][0]]
    if failure == "unaccounted":
        data["audiovisual"]["omitted_sounds"] = []
    elif failure == "unjustified":
        sound["purpose"] = " "
    elif failure == "no_action":
        sound["element_id"] = "missing"
    elif failure == "foreign":
        sound["candidate_id"] = "foreign"
    else:
        prepared = replace(prepared, assets=())
    with pytest.raises((AuthError, ValidationError)):
        apply_planned_sound(prepared, MotionConstructionPlan.model_validate(data))
