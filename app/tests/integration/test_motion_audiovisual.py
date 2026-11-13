"""Restricted existing _test: persist natural preparation, review exact plan, stop before render."""

from dataclasses import replace
from uuid import UUID, uuid4, uuid5

import pytest
from sqlalchemy import text

from app.schemas.motion_production import DirectedHTMLMotionComposition, MotionAudio
from app.services.auth import AuthError
from app.services.motion_checkpoints import MotionCheckpoints
from app.services.motion_protocols import MotionModelResult
from app.services.motion_sound_library import load_sound_library
from app.tests.integration.test_motion_checkpoints import decide, decision, event, inspect
from app.tests.integration.test_motion_production import motion_case  # noqa: F401
from app.tests.unit.test_motion_ai import frame
from app.tests.unit.test_motion_audiovisual import natural_body, natural_plan
from app.tests.unit.test_motion_plan import planned

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("failure", [None, "changed_plan", "changed_sound", "stationary_recording"])
async def test_natural_preparation_reuses_real_checkpoints_and_never_calls_renderer(motion_case, failure):  # noqa: F811
    c = motion_case
    c.cfg = c.cfg.model_copy(update={"motion_storyboard_enabled": True})
    c.requests.settings = c.requests.context.settings = c.cfg
    c.body = natural_body(operation_id=c.body.operation_id, source_asset_id=c.source)
    prior = c.inputs.prepare.return_value
    audio = {
        "mode": "mix",
        "tracks": [
            {"asset_id": "assets/source.mp4", "offset_ms": 0, "trim_start_ms": 0, "trim_end_ms": 1000, "volume": 1.0}
        ],
    }
    prior = replace(prior, audio=audio)
    plan = natural_plan()
    if failure == "stationary_recording":
        data = plan.model_dump(mode="json")
        element = data["motion_plan"]["scenes"][0]["elements"][0]
        element.update(role="video", asset_id="assets/source.mp4")
        element["beats"][0]["phase"] = "hold"
        data["scene_direction"]["scenes"][0]["elements"][0]["construction"] = "authorized_asset"
        plan = plan.model_validate(data)
    plan = plan.model_copy(
        update={
            "motion_plan": plan.motion_plan.model_copy(update={"style_id": None}),
            "audio": MotionAudio.model_validate(audio),
        }
    )
    composition = DirectedHTMLMotionComposition(
        **plan.model_dump(), html=planned().html, scene_init=planned().scene_init
    )
    if failure == "changed_plan":
        composition = composition.model_copy(update={"concept": "Unauthorized replacement"})

    async def prepare(snapshot):
        context = {
            k: v
            for k, v in snapshot.items()
            if k
            not in {
                "tenant_id",
                "business_id",
                "source",
                "logo",
                "execution",
                "references",
            }
        }
        context.update(
            source={"asset_id": "assets/source.mp4", "sha256": prior.assets[0].sha256, "duration_ms": 1000},
            output={"width": 720, "height": 1280, "fps": 30, "duration_ms": 1000},
            authorized_audio=prior.audio,
        )
        sounds = load_sound_library(context)
        if failure == "changed_sound" and c.provider.calls:
            sounds = (replace(sounds[0], data=b"changed"), sounds[1])
        return replace(prior, context=context, assets=(*prior.assets, *sounds), source_frames=(frame(100), frame(300)))

    async def submit(job, _payload):
        c.provider.calls.append("plan" if job.construction_plan is None else "implementation")
        if job.construction_plan is None:
            assert "scene_direction" not in job.context["request"]
            assert job.context["request"]["instruction"] == c.body.preparation.client_message
            return MotionModelResult(construction_plan=plan, estimated_usd_micros=0)
        assert job.construction_plan == plan
        assert job.context["authorized_soundtrack"]["tracks"][0] == {
            **audio["tracks"][0],
            "role": "original",
            "fade_in_ms": 0,
            "fade_out_ms": 0,
        }
        assert job.context["authorized_soundtrack"]["tracks"][1]["asset_id"] == "assets/sfx-cup-contact.mp3"
        return MotionModelResult(composition=composition, estimated_usd_micros=0)

    c.inputs.prepare.side_effect, c.provider.submit = prepare, submit
    c.checkpoints = MotionCheckpoints(c.requests, c.store)
    c.requested = await c.requests.create(c.tenant, c.business, c.actor, c.body)
    assert await c.runner.run(c.event) == "awaiting_plan"
    view = await inspect(c, "plan")
    assert view["packet"]["artifact"]["audiovisual"] == plan.audiovisual.model_dump(mode="json")
    assert view["packet"]["context"]["repertoire"]["reference_images"] == []
    assert view["packet"]["context"]["sound_library"]["items"][0]["license"] == "CC0-1.0"
    c.renderer.render.assert_not_awaited()
    await decide(c, "plan", await decision(c, "plan"))
    if failure in {"changed_plan", "changed_sound"}:
        with pytest.raises(AuthError, match="(PLAN_CHANGED|SOUND_FILE_CHANGED)"):
            await c.runner.run(event(c, "plan"))
    else:
        assert await c.runner.run(event(c, "plan")) == "awaiting_render"
        view = await inspect(c, "render")
        assert view["decision"] is None and not view["rendered"]
        assert view["packet"]["artifact"] == composition.model_dump(mode="json")
        assert view["packet"]["model_operation_id"] == str(uuid5(c.body.operation_id, "generate:0"))
    assert c.provider.calls == (["plan"] if failure == "changed_sound" else ["plan", "implementation"])
    c.renderer.render.assert_not_awaited()
    assert await c.runner.run(event(c, "plan")) == "already_claimed"


async def test_product_discovers_bounded_scoped_materials_without_client_technical_selection(
    motion_case,  # noqa: F811
    admin,
    seeded,
):
    from app.tests.integration.test_business_collection import _business

    c = motion_case
    foreign = await _business(admin, {**seeded, "t1": seeded["t2"]})
    c.requests.context.settings = c.cfg.model_copy(update={"motion_storyboard_enabled": True})
    ids = [UUID(int=i) for i in range(1, 8)]
    async with admin.begin() as conn:
        for index, identifier in enumerate(ids):
            other = index == 6
            await conn.execute(
                text("""INSERT INTO business_collection_photos
                (id,tenant_id,business_id,operation_id,actor_id,request_hash,object_key,sha256,mime_type,size_bytes,
                 title,space_kind,sort_order,version,state,source,rights_scope,status)
                VALUES(:id,:tenant,:business,:operation,:actor,:hash,:key,:hash,'image/png',10,
                       'Synthetic interior','room',0,1,'ready','upload','business_collection_confirmed',:status)"""),
                dict(
                    id=identifier,
                    tenant=seeded["t2"] if other else c.tenant,
                    business=foreign if other else c.business,
                    operation=uuid4(),
                    actor=seeded["a2"] if other else c.actor,
                    hash="a" * 64,
                    key=f"synthetic/{identifier}",
                    status="archived" if index == 5 else "active",
                ),
            )
    body = natural_body(source_asset_id=c.source)
    async with c.database.transaction(c.tenant, c.actor) as session:
        captured = await c.requests.context.capture(session, c.tenant, c.business, body)
    assert [UUID(p["id"]) for p in captured["collection_photos"]] == ids[:4]
    assert body.collection_photo_ids == ()
    assert captured["kit"]["overrides"]["brand_name"] == "Synthetic brand"
