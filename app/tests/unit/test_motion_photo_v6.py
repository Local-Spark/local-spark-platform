"""Last Café slice: full cover, continuous primary and exact historical executors."""

import hashlib
from copy import deepcopy

import pytest

from app.services import motion_photo_polish as polish
from app.services.auth import AuthError
from app.services.motion_context import capture_motion_guidance
from app.tests.unit.test_motion_photo_hard import artifact, exception
from app.tests.unit.test_motion_photo_planning import photo_case
from app.tests.unit.test_motion_photo_polish import CONTEXT, case, check, handoff_case

# v6/v7 cover+continuous gates; CONTEXT may pin a newer polish for new captures.
V6_CONTEXT = {**CONTEXT, "photo_polish_contract": polish.PHOTO_POLISH_CONTRACT_V6}
V7_CONTEXT = {**CONTEXT, "photo_polish_contract": polish.PHOTO_POLISH_CONTRACT_V7}


@pytest.mark.parametrize(
    "version,digest",
    [
        (1, "d99346b38029e87049ef036d64ebf805a9f99405a828173ceeee4c69da7da88a"),
        (2, "d99346b38029e87049ef036d64ebf805a9f99405a828173ceeee4c69da7da88a"),
        (3, "39d040fa11c254ae1fda319a2c7e20c6fff368a10ed3b3edb2ac6f5c55072780"),
        (4, "e2149d42035bdaa77ee9f16d24de2ef3c54fb2ccbf0900d184997f8807d854f2"),
        (5, "227c47cd6b19eb87446705f1c8f35bb4c8bce0133ad527e6c62f4a7340f18fbe"),
    ],
)
def test_historical_executor_bytes_and_snapshot_replay(version, digest):
    from app.tests.unit.test_motion_photo_finish import finish_case

    body, prepared, _ = photo_case()
    contract = getattr(polish, f"PHOTO_POLISH_CONTRACT_V{version}")
    context = {**prepared.context, "photo_polish_contract": contract}
    assert capture_motion_guidance(body, previous=context)["photo_polish_contract"] == contract
    comp = artifact(finish_case())
    executor = polish.polish_scene_init(comp, context, comp.scene_init)
    assert hashlib.sha256(executor.encode()).hexdigest() == digest


@pytest.mark.parametrize("index", [0, 1, 2])
def test_no_stories_exception_even_when_old_contract_accepts(index):
    data, ids = case()
    exception(data["motion_plan"]["scenes"][index])
    old = {**CONTEXT, "photo_polish_contract": polish.PHOTO_POLISH_CONTRACT_V5}
    polish.validate_photo_polish(artifact(data), old, asset_ids=ids)
    with pytest.raises(AuthError, match="FULL_BLEED_REQUIRED"):
        polish.validate_photo_polish(artifact(data), V6_CONTEXT, asset_ids=ids)


@pytest.mark.parametrize("change", ["start", "end", "middle", "reset"])
def test_v6_closes_u2_gap_allowance_without_upgrading_v5(change):
    data, ids = case()
    beats = data["motion_plan"]["scenes"][1]["elements"][0]["beats"]
    beat = beats[0]
    if change == "start":
        beat["start_ms"] += 1
    elif change == "end":
        beat["end_ms"] -= 1
    else:
        second = dict(beat, start_ms=7500 if change == "reset" else 7501)
        beat["end_ms"] = 7500
        beats.append(second)
    before = deepcopy(data)
    polish.validate_photo_polish(
        artifact(data), {**CONTEXT, "photo_polish_contract": polish.PHOTO_POLISH_CONTRACT_V5}, asset_ids=ids
    )
    with pytest.raises(AuthError, match="CONTINUOUS_TRANSFORM_REQUIRED"):
        polish.validate_photo_polish(artifact(data), V6_CONTEXT, asset_ids=ids)
    assert before == data


def test_contiguous_beats_and_outgoing_handoff_are_allowed():
    data, ids = handoff_case()
    beats = data["motion_plan"]["scenes"][1]["elements"][0]["beats"]
    beat = beats[0]
    second = dict(beat, start_ms=7500, start_state="scale=1.16 x_pct=0 y_pct=0")
    beat.update(end_ms=7500, end_state=second["start_state"])
    beats.append(second)
    polish.validate_photo_polish(artifact(data), V6_CONTEXT, asset_ids=ids)
    # Layout absence on a scene must fail even if other scenes supply variety.
    data, ids = case(1)
    data["motion_plan"]["scenes"][1]["photo_layout"] = None
    with pytest.raises(AuthError, match="CONTINUITY_REQUIRED"):
        polish.validate_photo_polish(artifact(data), V6_CONTEXT, asset_ids=ids)


def test_new_guard_payload_is_bound_to_primary_and_timing():
    data, _ = case()
    comp = artifact(data)
    executor = polish.polish_scene_init(comp, CONTEXT, comp.scene_init)
    assert '"cover": [{"id": "photo0", "start": 0, "end": 5000}' in executor
    assert executor.index("PhotoTimingV1") < executor.index(comp.scene_init)
    assert "MOTION_PHOTO_FULL_BLEED_REQUIRED" in executor


def test_handoff_does_not_license_a_hold_after_dissolve():
    data, ids = handoff_case()
    data["motion_plan"]["scenes"][0]["elements"][0]["beats"][-1]["end_ms"] = 5100
    data["staging"]["moments"][0]["transition"]["end_ms"] = 5100
    with pytest.raises(AuthError, match="CONTINUOUS_TRANSFORM_REQUIRED"):
        polish.validate_photo_polish(artifact(data), V6_CONTEXT, asset_ids=ids)
