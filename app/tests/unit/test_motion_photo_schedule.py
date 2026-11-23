"""Energy scheduling guidance does not lower gates or silently rewrite old requests."""

from copy import deepcopy
from dataclasses import replace
from uuid import uuid4

import pytest

from app.services.auth import AuthError
from app.services.motion_construction import construction_job
from app.services.motion_context import capture_motion_guidance
from app.services.motion_photo_energy import energetic, validate_photo_energy
from app.services.motion_photo_intent import photo_intent_rules
from app.services.motion_photo_polish import PHOTO_POLISH_CONTRACT, PHOTO_POLISH_CONTRACT_V1, polish_enabled
from app.tests.unit.test_motion_ai import provider
from app.tests.unit.test_motion_photo_dense import dense_plan
from app.tests.unit.test_motion_photo_planning import photo_case


def test_v1_replay_keeps_exact_rules_while_new_capture_sends_latest_to_planner():
    body, prepared, _ = photo_case()
    old = {**prepared.context, "photo_polish_contract": deepcopy(PHOTO_POLISH_CONTRACT_V1)}
    replay = capture_motion_guidance(body, previous=old)
    assert replay["photo_polish_contract"] == PHOTO_POLISH_CONTRACT_V1
    assert polish_enabled(old)
    assert photo_intent_rules(old).endswith(PHOTO_POLISH_CONTRACT_V1["rules"])
    new = capture_motion_guidance(body)
    assert new["photo_polish_contract"] == PHOTO_POLISH_CONTRACT
    assert PHOTO_POLISH_CONTRACT["version"] == "motion-photo-polish-v3"
    for key in ("photo_motion", "photo_intent_contract", "photo_finish_contract", "photo_readability_contract"):
        assert replay[key] == new[key]
    job = construction_job({"operation_id": uuid4()}, prepared)
    payload = provider().build_request(job)
    old_payload = provider().build_request(replace(job, context=old))
    assert PHOTO_POLISH_CONTRACT["rules"] in payload["instructions"]
    assert "Enter/exit NÃO contam" not in old_payload["instructions"]
    assert PHOTO_POLISH_CONTRACT_V1["rules"] in old_payload["instructions"]
    assert PHOTO_POLISH_CONTRACT["dom_guard_sha256"] != PHOTO_POLISH_CONTRACT_V1["dom_guard_sha256"]


def text_driven_plan(duration, intervals):
    plan = dense_plan([(0, 5000)])
    scene = plan.scenes[0]
    photo = scene.elements[0]
    base = photo.beats[0]
    slow = base.model_copy(update={"end_ms": duration, "end_state": "scale=1.04 x_pct=0 y_pct=0"})
    texts = []
    for index, (start, end) in enumerate(intervals):
        beats = (
            base.model_copy(update={"phase": "enter", "start_ms": max(0, start - 250), "end_ms": start}),
            base.model_copy(update={"start_ms": start, "end_ms": end}),
            base.model_copy(update={"phase": "exit", "start_ms": end, "end_ms": min(duration, end + 250)}),
        )
        texts.append(
            photo.model_copy(
                update={
                    "id": f"text{index}",
                    "role": "text",
                    "asset_id": None,
                    "beats": tuple(b for b in beats if b.end_ms > b.start_ms),
                }
            )
        )
    photo = photo.model_copy(update={"beats": (slow,), "related_element_ids": tuple(t.id for t in texts)})
    scene = scene.model_copy(update={"end_ms": duration, "elements": (photo, *texts)})
    return plan.model_copy(update={"duration_ms": duration, "scenes": (scene,)})


@pytest.mark.parametrize(
    "duration,intervals",
    [
        (5000, [(350, 2100), (2750, 4550)]),
        (5500, [(550, 2600), (3250, 5050)]),
        (4900, [(550, 2200), (2750, 4900)]),
    ],
)
def test_failed_run_schedules_remain_rejected_even_with_energetic_enters_and_exits(duration, intervals):
    plan = text_driven_plan(duration, intervals)
    before = plan.model_dump()
    assert not energetic(plan.scenes[0].elements[0].beats[0], stronger=True)
    with pytest.raises(AuthError, match="MOTION_PHOTO_ENERGY_REQUIRED"):
        validate_photo_energy(plan, stronger=True, dense=True)
    assert plan.model_dump() == before


def test_guidance_example_meets_density_without_speeding_up_photo():
    plan = text_driven_plan(5000, [(250, 4750)])
    scene = plan.scenes[0]
    photo, text = scene.elements
    move = text.beats[1].model_copy(update={"end_state": "scale=1 x_pct=0 y_pct=-4.5"})
    text = text.model_copy(update={"beats": (text.beats[0], move, text.beats[2])})
    plan = plan.model_copy(update={"scenes": (scene.model_copy(update={"elements": (photo, text)}),)})
    assert not energetic(photo.beats[0], stronger=True)
    assert energetic(move, stronger=True)
    validate_photo_energy(plan, stronger=True, dense=True)
