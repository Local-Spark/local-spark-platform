"""Provider coverage schema mirrors the validator without changing saved plans."""

import json
from dataclasses import replace

import pytest

from app.adapters.motion_ai import _format
from app.schemas.motion_generation import MotionStagedPlanningOutput
from app.schemas.motion_production import MotionConstructionPlan
from app.services.auth import AuthError
from app.services.motion_quality import validate_quality_plan
from app.tests.unit.test_motion_ai import provider, request
from app.tests.unit.test_motion_photo_planning import photo_case


def test_real_provider_constrains_coverage_to_photo_requirements():
    _, prepared, plan = photo_case()
    job = replace(
        request(),
        context=prepared.context,
        assets=prepared.assets,
        source_frames=(),
        asset_previews=prepared.asset_previews,
        reference_images=prepared.reference_images,
    )
    payload = provider().build_request(job)
    schema = payload["text"]["format"]["schema"]
    ids = [r["id"] for r in prepared.context["quality_contract"]["requirements"]]
    props = schema["$defs"]["MotionFunctionCoverage"]["properties"]
    assert props["function_id"]["enum"] == ids
    assert props["disposition"]["enum"] == ["satisfy_requirement"]
    functions = schema["$defs"]["MotionAudiovisualDesign"]["properties"]["functions"]
    assert functions["minItems"] == functions["maxItems"] == 8
    sent = json.loads(payload["input"][0]["content"][0]["text"])
    assert sent["planning_input"]["quality_coverage"]["required_function_ids"] == ids
    valid = plan.model_dump(mode="json")["audiovisual"]["functions"]
    assert {entry["function_id"] for entry in valid} == set(props["function_id"]["enum"])
    assert {"brief_alignment", "motion_role", "narrative_progression"}.isdisjoint(props["function_id"]["enum"])


def test_historical_schema_is_not_mutated_or_forced_without_quality():
    original = MotionStagedPlanningOutput.model_json_schema()
    _format(MotionStagedPlanningOutput, allow_staging=True, quality_function_ids=("photographs",))
    assert MotionStagedPlanningOutput.model_json_schema() == original
    unrestricted = _format(MotionStagedPlanningOutput, allow_staging=True)
    assert "enum" not in unrestricted["schema"]["$defs"]["MotionFunctionCoverage"]["properties"]["function_id"]
    from app.schemas.motion_production import MotionAudio

    assert _format(MotionAudio, allow_staging=False, quality_function_ids=("photographs",))


@pytest.mark.parametrize("invalid", ["extras", "duplicate", "foreign_target"])
def test_server_still_rejects_invalid_coverage_without_normalizing(invalid):
    _, prepared, plan = photo_case()
    data = plan.model_dump(mode="json")
    fs = data["audiovisual"]["functions"]
    if invalid == "extras":
        fs.extend(
            {**fs[0], "function_id": name} for name in ["brief_alignment", "motion_role", "narrative_progression"]
        )
    elif invalid == "duplicate":
        fs[-1] = dict(fs[0])
    else:
        fs[0]["target_element_ids"] = ["unknown"]
    artifact = MotionConstructionPlan.model_validate(data)
    with pytest.raises(AuthError, match="MOTION_QUALITY_COVERAGE_INVALID"):
        validate_quality_plan(artifact, prepared.context)
    assert artifact.model_dump(mode="json") == data
