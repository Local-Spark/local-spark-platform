"""A2: photo plans, real material relations and distinct lab/WhatsApp approval modes."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.adapters.motion_ai import _format
from app.adapters.motion_html_renderer import RenderAsset
from app.adapters.motion_inputs import PreparedMotionInput
from app.schemas.motion_generation import MotionStagedPlanningOutput
from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan, MotionRequest
from app.services.auth import AuthError
from app.services.motion_construction import implement_motion, plan_motion
from app.services.motion_context import capture_motion_guidance
from app.services.motion_generation import PHOTO_GENERATION_CONTRACT, staged_generation_enabled
from app.services.motion_illustrations import validate_declarations
from app.services.motion_photos import planned_photo_request
from app.services.motion_protocols import MotionModelResult
from app.services.motion_quality import planning_input
from app.services.motion_repertoire import load_repertoire_images
from app.services.motion_sound_library import load_sound_library
from app.services.motion_staging import PHOTO_STAGING_CONTRACT, validate_staging
from app.tests.unit.test_motion_ai import frame
from app.tests.unit.test_motion_orchestrator import unit_case  # noqa: F401
from app.tests.unit.test_motion_staging import staged_plan

PHOTO_ID = "00000000-0000-0000-0000-000000000001"
ASSET_ID = f"assets/photo-{PHOTO_ID}.png"


def photo_case(*, human_review=False):
    body = planned_photo_request(
        MotionRequest(
            operation_id=uuid4(), instruction="Um reel com fotos do café", source_asset_id=None, photo_duration_ms=15000
        ),
        [{"id": PHOTO_ID}],
        human_review=human_review,
    )
    context = {
        **capture_motion_guidance(body),
        "source": {"kind": "photos", "has_audio": False, "duration_ms": 15000},
        "output": {"width": 720, "height": 1280, "fps": 30, "duration_ms": 15000},
        "authorized_audio": {"mode": "silent", "tracks": []},
        "available_materials": [{"asset_id": ASSET_ID, "role": "business_space"}],
    }
    data = staged_plan().model_dump(mode="json")
    data["source_usage"] = "Fotografia autorizada, sem vídeo ou transcrição."
    data["motion_plan"]["style_id"] = None

    def times(value):
        if isinstance(value, dict):
            return {
                key: item * 15 if key.endswith("_ms") and type(item) is int else times(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [times(item) for item in value]
        return value

    data = times(data)
    data["motion_plan"]["scenes"][0]["elements"][0].update(role="image", asset_id=ASSET_ID)
    data["scene_direction"]["scenes"][0]["elements"][0]["construction"] = "authorized_asset"
    data["staging"]["version"] = PHOTO_STAGING_CONTRACT["version"]
    data["staging"]["moments"][0].update(media_relation="photo_dominant", material_element_ids=["title"])
    data["staging"]["moments"][0]["transition"]["end_ms"] = 13000
    closing = deepcopy(data["motion_plan"]["scenes"][0]["elements"][0])
    closing.update(id="closing-photo", related_element_ids=[])
    closing["beats"][0].update(
        phase="transform",
        start_ms=7500,
        end_ms=15000,
        start_state="scale=1.04 pan=-1%",
        end_state="scale=1.12 pan=1%",
        trajectory="Continuous Ken Burns on a full-bleed photograph",
    )
    data["motion_plan"]["scenes"][-1]["elements"].append(closing)
    direction = deepcopy(data["scene_direction"]["scenes"][0]["elements"][0])
    direction["element_id"] = "closing-photo"
    data["scene_direction"]["scenes"][-1]["elements"].append(direction)
    data["staging"]["moments"][-1].update(media_relation="integrated", material_element_ids=["closing-photo"])
    for function in data["audiovisual"]["functions"]:
        if function["function_id"] == "recording":
            function["function_id"] = "photographs"
    data["audiovisual"].update(
        sounds=[],
        omitted_sounds=[
            {"candidate_id": item["id"], "reason": "Plano contemplativo sem ação que justifique SFX."}
            for item in context["sound_library"]["items"]
        ],
    )
    for scene in data["motion_plan"]["scenes"]:
        for element in scene["elements"]:
            if element["role"] == "image":
                element["beats"] = [
                    dict(
                        element["beats"][0],
                        phase="transform",
                        start_ms=scene["start_ms"],
                        end_ms=scene["end_ms"],
                        start_state="scale=1.04 x_pct=0 y_pct=0",
                        end_state="scale=1.28 x_pct=0 y_pct=0",
                        curve={"kind": "linear", "parameters": []},
                    )
                ]
    for scene in data["motion_plan"]["scenes"]:
        photo = next(e for e in scene["elements"] if e["role"] == "image")
        scene["photo_layout"] = {"mode": "cover", "primary_element_id": photo["id"], "crop_exception": None}
    final = data["motion_plan"]["scenes"][-1]
    final["photo_closing"] = {
        "brand_element_id": None,
        "surface": "transparent_overlay",
        "cta_element_id": next(e["id"] for e in final["elements"] if e["role"] == "text"),
    }
    plan = MotionConstructionPlan.model_validate(data)
    png = frame()
    asset = RenderAsset(ASSET_ID, "image/png", png.png, png.sha256)
    prepared = PreparedMotionInput(
        context,
        (asset, *load_sound_library(context)),
        (),
        15000,
        context["authorized_audio"],
        asset_previews=((ASSET_ID, png),),
        reference_images=load_repertoire_images(context),
    )
    return body, prepared, plan


@pytest.mark.parametrize("human_review", [False, True])
def test_shared_photo_contract_has_real_photo_evidence_and_no_new_audio_selection(human_review):
    body, prepared, plan = photo_case(human_review=human_review)
    assert body.review_checkpoints == human_review
    assert body.automatic_plan != human_review
    assert body.storyboard == human_review
    assert body.sound_library_id == "public-cc0-v1"
    assert prepared.context["photo_motion"]["music_policy"] == "elevenlabs-music-v1"
    assert body.preparation.evidence[0].kind == "material"
    assert prepared.source_frames == ()
    assert staged_generation_enabled(prepared.context)
    validate_declarations(plan, prepared)
    assert planning_input(prepared.context, [])["sound"]["source"] == {
        "kind": "photos",
        "has_recorded_audio": False,
    }
    recaptured = capture_motion_guidance(body, previous=prepared.context)
    assert recaptured["generation_contract"] == PHOTO_GENERATION_CONTRACT
    assert recaptured["photo_motion"] == prepared.context["photo_motion"]


@pytest.mark.parametrize("change", ["video", "missing_photo", "protagonist", "old_version"])
def test_photo_relations_are_not_a_video_or_graphic_workaround(change):
    _, prepared, plan = photo_case()
    data = plan.model_dump(mode="json")
    ctx = deepcopy(prepared.context)
    if change == "video":
        data["staging"]["moments"][0]["media_relation"] = "recording_dominant"
    elif change == "missing_photo":
        ctx["available_materials"] = []
    elif change == "protagonist":
        data["staging"]["moments"][0]["protagonist_id"] = "answer"
    else:
        data["staging"]["version"] = "motion-staging-v1"
    with pytest.raises(AuthError, match="MOTION_STAGING"):
        validate_staging(MotionConstructionPlan.model_validate(data), ctx)
    data = plan.model_dump(mode="json")
    data["staging"]["moments"][0]["media_relation"] = "integrated"
    validate_staging(MotionConstructionPlan.model_validate(data), prepared.context)


def test_automatic_plan_does_not_disable_video_checkpoints_or_accept_missing_evidence():
    body, _, _ = photo_case()
    for update in [
        dict(review_checkpoints=True),
        dict(storyboard=True),
        dict(source_asset_id=uuid4(), photo_duration_ms=None),
        dict(preparation=None),
    ]:
        with pytest.raises(ValidationError):
            MotionRequest.model_validate({**body.model_dump(mode="json"), **update})
    with pytest.raises(AuthError, match="MOTION_PHOTOS_REQUIRED"):
        planned_photo_request(body, [], human_review=False)


@pytest.mark.parametrize(
    "version,relation",
    [
        ("motion-staging-photo-v2", "photo_dominant"),
        ("motion-staging-photo-v1", "photo_dominant"),
        ("motion-staging-v1", "recording_dominant"),
    ],
)
def test_wire_schema_is_pinned_without_mutating_shared_models(version, relation):
    schema = _format(MotionStagedPlanningOutput, allow_staging=True, staging_version=version)["schema"]
    assert schema["$defs"]["MotionStaging"]["properties"]["version"]["enum"] == [version]
    values = schema["$defs"]["StagedMoment"]["properties"]["media_relation"]["enum"]
    assert relation in values
    assert ("photo_dominant" in values) == (version in ("motion-staging-photo-v1", "motion-staging-photo-v2"))
    assert (
        len(MotionStagedPlanningOutput.model_json_schema()["$defs"]["MotionStaging"]["properties"]["version"]["enum"])
        == 3
    )


@pytest.mark.parametrize("human_review", [False, True])
async def test_orchestrator_pauses_only_lab_and_automatically_implements_whatsapp(unit_case, human_review):  # noqa: F811
    c = unit_case
    _, prepared, plan = photo_case(human_review=human_review)
    composition = HTMLMotionComposition.model_validate(
        {**plan.model_dump(mode="json"), "html": "<main></main>", "scene_init": "window.seek=()=>{}"}
    )
    c.runner.inputs.prepare.return_value = prepared
    c.runner.effects.requests = c.runner.requests
    c.runner.effects.capacity = AsyncMock(return_value=True)
    c.runner.effects.model.side_effect = [
        MotionModelResult(construction_plan=plan),
        MotionModelResult(composition=composition),
    ]
    checkpoints = SimpleNamespace(capture=AsyncMock())
    c.runner.checkpoints = lambda: checkpoints
    c.runner.produce = AsyncMock(return_value="completed")
    assert await c.runner.run(c.event) == ("awaiting_plan" if human_review else "completed")
    assert c.runner.effects.model.await_count == (1 if human_review else 2)
    if human_review:
        assert checkpoints.capture.call_args.args[2] == "plan"
        c.runner.produce.assert_not_awaited()
    else:
        checkpoints.capture.assert_not_awaited()
        assert c.runner.produce.call_args.args[-1] == composition


@pytest.mark.parametrize("stage", ["plan", "implementation"])
async def test_full_path_budget_is_checked_before_paid_steps(settings, stage):
    _, prepared, plan = photo_case(human_review=True)
    settings.motion_ai_reservation_usd_micros = 100
    effects = SimpleNamespace(
        requests=SimpleNamespace(settings=settings), capacity=AsyncMock(return_value=False), model=AsyncMock()
    )
    row, token = {"operation_id": uuid4(), "max_corrections": 2}, uuid4()
    with pytest.raises(AuthError, match="MOTION_CONSTRUCTION_BUDGET_REQUIRED"):
        if stage == "plan":
            await plan_motion(effects, object(), row, token, prepared)
        else:
            await implement_motion(effects, object(), row, token, prepared, plan, None)
    assert effects.capacity.call_args.args[-1] == (700 if stage == "plan" else 600)
    effects.model.assert_not_awaited()


@pytest.mark.parametrize("number", [0, 1])
async def test_photo_dom_guard_binds_render_effect_and_blocks_upload_on_failure(unit_case, number):  # noqa: F811
    from app.adapters.motion_html_renderer import MotionRenderError
    from app.services.motion_context import digest
    from app.services.motion_photo_hard import guarded_photo_scene_init

    c = unit_case
    _, prepared, plan = photo_case()
    composition = HTMLMotionComposition.model_validate(
        {**plan.model_dump(mode="json"), "html": "<main></main>", "scene_init": "window.seek=()=>{}"}
    )
    c.runner.renderer.render.side_effect = MotionRenderError("MOTION_RENDER_EXECUTION_FAILED")
    with pytest.raises(MotionRenderError):
        await c.runner.render(c.row, c.token, prepared, number, composition)
    bundle = c.runner.renderer.render.call_args.args[0]
    assert bundle.scene_init == guarded_photo_scene_init(composition, prepared.context)
    assert bundle.audio == prepared.audio
    assert c.runner.effects.claim.call_args.args[-1]["executed_scene_init_sha256"] == digest(bundle.scene_init)
    c.runner.store.put.assert_not_awaited()
    c.runner.effects.received.assert_not_awaited()
