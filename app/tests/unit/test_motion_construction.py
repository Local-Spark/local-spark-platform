"""No paid IO: split output, immutable joins, durable boundaries and bounded failures."""

import base64
import hashlib
import json
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid5

import httpx
import pytest

from app.adapters.motion_ai import MotionAIError, request_bytes
from app.schemas.motion_production import MotionConstructionPlan, MotionReview
from app.services.auth import AuthError
from app.services.motion_construction import construct_motion, construct_motion_with_assets
from app.services.motion_context import digest
from app.services.motion_generation import (
    ASSET_INFORMED_GENERATION_CONTRACT,
    STAGED_GENERATION_CONTRACT,
    construction_plan_hash,
    decode_construction_plan,
)
from app.services.motion_protocols import MotionModelResult
from app.tests.unit.test_motion_ai import frame, provider, request, response_data, review_data
from app.tests.unit.test_motion_effects import setup
from app.tests.unit.test_motion_generation import compact_wire, wire_data
from app.tests.unit.test_motion_illustrations import art_case  # noqa: F401
from app.tests.unit.test_motion_orchestrator import unit_case  # noqa: F401
from app.tests.unit.test_motion_plan import planned
from app.tests.unit.test_motion_visual_direction import provided_context


def staged_context():
    return {**provided_context(), "generation_contract": deepcopy(STAGED_GENERATION_CONTRACT)}


def plan_wire():
    return {key: value for key, value in compact_wire(wire_data()).items() if key not in {"html", "scene_init"}}


def plan():
    return decode_construction_plan(json.dumps(plan_wire()), staged_context())


def implementation():
    return {"plan_sha256": construction_plan_hash(plan()), "html": planned().html, "scene_init": planned().scene_init}


async def test_two_completions_keep_all_images_and_join_only_server_owned_plan():
    seen = []

    def handler(sent):
        seen.append(json.loads(sent.content))
        return httpx.Response(200, json=response_data(plan_wire() if len(seen) == 1 else implementation()))

    client = provider(handler)
    job = replace(request(source_frames=(frame(),)), context=staged_context())
    payload = client.build_request(job)
    assert payload["text"]["format"]["name"] == "MotionPlanningOutput"
    assert not {"html", "scene_init", "scene_direction"} & payload["text"]["format"]["schema"]["properties"].keys()
    assert "somente o plano estruturado, sem código" in payload["instructions"]
    result = await client.submit(job, payload)
    assert result.composition is None and result.construction_plan == plan()
    build = replace(
        job, operation_id=uuid5(job.operation_id, "implementation"), construction_plan=result.construction_plan
    )
    built_payload = client.build_request(build)
    assert list(built_payload["text"]["format"]["schema"]["properties"]) == ["plan_sha256", "html", "scene_init"]
    context = json.loads(built_payload["input"][0]["content"][0]["text"])
    assert context["validated_plan"] == plan().model_dump(mode="json")
    assert context["plan_sha256"] == construction_plan_hash(plan())
    assert built_payload["input"][0]["content"][1:] == payload["input"][0]["content"][1:]
    built = await client.submit(build, built_payload)
    assert built.composition.model_dump() == planned().model_dump() and built.construction_plan is None
    assert len(seen) == 2
    assert list(seen[0]["text"]["format"]["schema"]["properties"]) == [
        "concept",
        "source_usage",
        "audio",
        "illustrations",
        "motion_plan",
    ]


@pytest.mark.parametrize("change", ["hash", "audio", "truncated", "invalid_plan", "code_in_plan"])
async def test_bad_or_cross_stage_output_is_not_accepted(change):
    data = implementation()
    is_plan = change in {"invalid_plan", "code_in_plan"}
    if is_plan:
        data = plan_wire()
    if change == "hash":
        data["plan_sha256"] = "0" * 64
    elif change == "audio":
        data["audio"] = {"mode": "silent", "tracks": []}
    elif change == "invalid_plan":
        data["motion_plan"]["scenes"][0]["elements"][0]["beats"] *= 2
    elif change == "code_in_plan":
        data["scene_init"] = "window.seek=()=>{}"
    response = response_data(data)
    if change == "truncated":
        response["status"] = "incomplete"
        response["incomplete_details"] = {"reason": "max_output_tokens"}
    client = provider(lambda _: httpx.Response(200, json=response, headers={"x-request-id": "stage-error"}))
    job = replace(request(), context=staged_context(), construction_plan=None if is_plan else plan())
    with pytest.raises(MotionAIError) as caught:
        await client.submit(job, client.build_request(job))
    assert caught.value.raw_response and caught.value.estimated_usd_micros is not None
    assert caught.value.provider_request_id == "stage-error"


@pytest.mark.parametrize("kind", ["review", "correct", "generate"])
def test_plan_cannot_be_smuggled_into_another_contract_or_operation(kind):
    job = replace(request(kind), construction_plan=plan())
    with pytest.raises(MotionAIError, match="PLAN_UNEXPECTED"):
        provider().build_request(job)


def test_implementation_rejects_changed_supplied_direction():
    ctx = staged_context()
    ctx["request"]["scene_direction"]["scenes"][0]["narrative_action"] = "changed direction"
    with pytest.raises(AuthError):
        provider().build_request(replace(request(), context=ctx, construction_plan=plan()))


async def test_reordering_output_schema_is_an_actual_wire_change():
    client = provider()
    job = replace(request(), context=staged_context(), construction_plan=plan())
    payload = client.build_request(job)
    changed = deepcopy(payload)
    props = changed["text"]["format"]["schema"]["properties"]
    changed["text"]["format"]["schema"]["properties"] = dict(reversed(list(props.items())))
    assert digest(payload) == digest(changed)
    assert request_bytes(payload) != request_bytes(changed)
    for method in (client.count_input_tokens, client.submit):
        with pytest.raises(MotionAIError, match="REQUEST_CHANGED"):
            await method(job, changed)


async def test_planning_receipt_is_sealed_before_cost_finish_and_has_wire_hash():
    case = setup()
    case.provider.submit.side_effect = None
    case.provider.submit.return_value = MotionModelResult(construction_plan=plan(), estimated_usd_micros=50)
    result = await case.effects.model(case.row, case.token, case.provider, case.request)
    assert result.construction_plan == plan()
    assert case.sealed[-1]["construction_plan"] == plan().model_dump(mode="json")
    assert case.sealed[-1]["composition"] is None
    payload = case.provider.build_request.return_value
    assert case.sealed[0]["wire_sha256"] == hashlib.sha256(request_bytes(payload)).hexdigest()
    assert case.order.index("worker_commit") < case.order.index("finish")


@pytest.fixture
def construction_case(unit_case):  # noqa: F811
    c = unit_case
    c.prepared = replace(c.prepared, context=staged_context())
    c.runner.effects.requests = SimpleNamespace(settings=SimpleNamespace(motion_ai_reservation_usd_micros=100))
    c.runner.effects.capacity = AsyncMock(return_value=True)
    c.runner.effects.model.side_effect = [
        MotionModelResult(construction_plan=plan()),
        MotionModelResult(composition=planned()),
    ]
    return c


async def construct(c):
    return await construct_motion(c.runner.effects, c.runner.provider, c.row, c.token, c.prepared)


async def test_orchestration_uses_separate_effect_ids_and_validates_before_second_call(construction_case):
    c = construction_case
    assert await construct(c) == planned()
    jobs = [call.args[-1] for call in c.runner.effects.model.await_args_list]
    assert [job.operation_id for job in jobs] == [
        uuid5(c.row["operation_id"], "generate:plan:0"),
        uuid5(c.row["operation_id"], "generate:0"),
    ]
    assert jobs[0].construction_plan is None and jobs[1].construction_plan == plan()
    assert [call.args[-1] for call in c.runner.effects.capacity.await_args_list] == [300, 200]


@pytest.mark.parametrize("fail_image", [False, True])
async def test_v4_material_precedes_implementation_and_is_not_generated_twice(art_case, fail_image):  # noqa: F811
    c = art_case
    raw = c.composition.model_dump(mode="json", exclude={"html", "scene_init"})
    original_plan = MotionConstructionPlan.model_validate(raw)
    ctx = staged_context()
    ctx["generation_contract"] = deepcopy(ASSET_INFORMED_GENERATION_CONTRACT)
    ctx["illustration_generation"] = c.prepared.context["illustration_generation"]
    ctx["request"]["scene_direction"] = c.composition.scene_direction.model_dump(mode="json")
    prepared = replace(c.prepared, context=ctx)
    sequence = []
    requests = []

    async def model(*args):
        job = args[-1]
        requests.append(job)
        if job.construction_plan is None:
            sequence.append("plan")
            return MotionModelResult(construction_plan=original_plan)
        sequence.append("implementation")
        payload = provider().build_request(job)
        content = payload["input"][0]["content"]
        metadata = json.loads(content[0]["text"])
        assert metadata["plan_sha256"] == construction_plan_hash(original_plan)
        assert metadata["validated_plan"] == raw
        assert metadata["authorized_context"]["implementation_materials"][0]["width"] == 1024
        assert metadata["authorized_context"]["implementation_materials"][0]["transparency"] == "has_transparency"
        position = next(i for i, block in enumerate(content) if "material_asset_id" in block.get("text", ""))
        sent_png = base64.b64decode(content[position + 1]["image_url"].split(",", 1)[1])
        assert sent_png == job.asset_previews[0][1].png
        return MotionModelResult(composition=c.composition)

    async def generate(*_):
        sequence.append("image")
        if fail_image:
            raise RuntimeError("synthetic failure")
        from app.tests.unit.test_motion_illustrations import image_result

        return image_result()

    c.effects.model = AsyncMock(side_effect=model)
    c.provider.generate.side_effect = generate
    if fail_image:
        with pytest.raises(RuntimeError, match="synthetic failure"):
            await construct_motion_with_assets(c.effects, provider(), c.row, c.token, prepared, c.service)
        assert sequence == ["plan", "image"] and len(requests) == 1
    else:
        built, composition = await construct_motion_with_assets(
            c.effects, provider(), c.row, c.token, prepared, c.service
        )
        assert sequence == ["plan", "image", "implementation"]
        assert composition == c.composition and built.assets[0].sha256 == c.provider.generate.return_value.sha256
        assert requests[1].construction_plan == original_plan
        c.provider.generate.assert_awaited_once()


async def test_v4_export_requires_resolved_image_and_rejects_changed_preview(art_case):  # noqa: F811
    from app.adapters.motion_html_renderer import RenderAsset
    from scripts.evals.motion_external_export import assemble_files, implementation_job

    c = art_case
    ctx = staged_context()
    ctx["generation_contract"] = deepcopy(ASSET_INFORMED_GENERATION_CONTRACT)
    ctx["illustration_generation"] = c.prepared.context["illustration_generation"]
    ctx["request"]["scene_direction"] = c.composition.scene_direction.model_dump(mode="json")
    job = replace(request(), context=ctx, assets=())
    original = c.composition.model_dump(mode="json", exclude={"html", "scene_init", "scene_direction"})
    output = json.dumps(compact_wire(original))
    with pytest.raises(ValueError, match="RESOLVED_MATERIALS_REQUIRED"):
        implementation_job(job, output)
    image = c.provider.generate.return_value
    asset = RenderAsset(c.composition.illustrations[0].asset_id, "image/png", image.content, image.sha256)
    built = implementation_job(job, output, (asset,))
    payload = provider().build_request(built)
    manifest = json.loads(payload["input"][0]["content"][0]["text"])
    assert manifest["plan_sha256"] == construction_plan_hash(built.construction_plan)
    assert manifest["authorized_context"]["implementation_materials"][0]["sha256"] == image.sha256
    files = assemble_files(built, {"model": "synthetic", "max_output_tokens": 64000})
    assert any(item["role"] == "material" for item in json.loads(files["input/order.json"]))
    bad = replace(built, asset_previews=((asset.id, frame()),))
    with pytest.raises(AuthError, match="MATERIAL_CHANGED"):
        provider().build_request(bad)
    bad = replace(built, assets=(replace(asset, data=b"changed"),))
    with pytest.raises(AuthError, match="MATERIAL_INVALID"):
        provider().build_request(bad)
    with pytest.raises(AuthError, match="MATERIAL_INVALID"):
        provider().build_request(replace(built, assets=()))

    complete = {
        "plan_sha256": manifest["plan_sha256"],
        "status": "implemented",
        "html": c.composition.html,
        "scene_init": c.composition.scene_init,
        "revision_reason": None,
    }
    client = provider(lambda _: httpx.Response(200, json=response_data(complete)))
    result = await client.submit(built, client.build_request(built))
    assert result.composition.model_dump(mode="json") == c.composition.model_dump(mode="json")
    revision = {
        "plan_sha256": manifest["plan_sha256"],
        "status": "requires_plan_revision",
        "html": None,
        "scene_init": None,
        "revision_reason": "Fixture requires another angle",
    }
    client = provider(lambda _: httpx.Response(200, json=response_data(revision), headers={"x-request-id": "test"}))
    with pytest.raises(MotionAIError, match="MOTION_PLAN_REVISION_REQUIRED") as exc:
        await client.submit(built, client.build_request(built))
    assert exc.value.raw_response and exc.value.estimated_usd_micros is not None
    revision["html"] = "<div>unsafe</div>"
    client = provider(lambda _: httpx.Response(200, json=response_data(revision)))
    with pytest.raises(MotionAIError, match="MOTION_AI_RESPONSE_INVALID"):
        await client.submit(built, client.build_request(built))


@pytest.mark.parametrize("when", ["before_plan", "before_implementation"])
async def test_budget_failure_cannot_start_the_unfunded_stage(construction_case, when):
    c = construction_case
    c.runner.effects.capacity.side_effect = [False] if when == "before_plan" else [True, False]
    with pytest.raises(AuthError, match="CONSTRUCTION_BUDGET_REQUIRED"):
        await construct(c)
    assert c.runner.effects.model.await_count == (0 if when == "before_plan" else 1)


@pytest.mark.parametrize("failure", ["missing_plan", "mixed_plan", "duration", "audio", "implementation", "changed"])
async def test_invalid_stage_stops_without_render_or_implicit_retry(construction_case, failure):
    c = construction_case
    first = MotionModelResult(construction_plan=plan())
    second = MotionModelResult(composition=planned())
    if failure == "missing_plan":
        first = MotionModelResult()
    elif failure == "mixed_plan":
        first = replace(first, composition=planned())
    elif failure == "duration":
        c.prepared = replace(c.prepared, duration_ms=2000)
    elif failure == "audio":
        c.prepared = replace(c.prepared, audio={"mode": "mix", "tracks": []})
    elif failure == "implementation":
        second = MotionAIError("MOTION_AI_OUTPUT_LIMIT")
    else:
        second = replace(second, composition=planned().model_copy(update={"concept": "changed"}))
    c.runner.effects.model.side_effect = [first, second]
    with pytest.raises((AuthError, MotionAIError)):
        await construct(c)
    assert c.runner.effects.model.await_count == (2 if failure in {"implementation", "changed"} else 1)
    c.runner.renderer.render.assert_not_awaited()
    c.runner.store.put.assert_not_awaited()


def test_full_plan_is_a_non_executable_artifact():
    saved = plan().model_dump_json()
    restored = MotionConstructionPlan.model_validate_json(saved)
    assert restored == plan() and not hasattr(restored, "scene_init")


async def test_v3_correction_retains_existing_complete_contract_and_audio_guard():
    client = provider(lambda _: httpx.Response(200, json=response_data(compact_wire(wire_data()))))
    job = replace(
        request("correct", composition=planned(), review=MotionReview.model_validate(review_data(revise=True))),
        context=staged_context(),
    )
    payload = client.build_request(job)
    assert payload["text"]["format"]["name"] == "CompactProvidedDirectionOutput"
    assert "construction_stage" not in json.loads(payload["input"][0]["content"][0]["text"])
    result = await client.submit(job, payload)
    assert result.composition.model_dump() == planned().model_dump()


async def test_token_preflight_and_submission_receive_same_ordered_schema():
    schemas = []

    def handler(sent):
        body = json.loads(sent.content)
        schemas.append(body["text"]["format"]["schema"])
        if sent.url.path.endswith("/input_tokens"):
            return httpx.Response(200, json={"object": "response.input_tokens", "input_tokens": 100})
        return httpx.Response(200, json=response_data(plan_wire()))

    client = provider(handler)
    job = replace(request(), context=staged_context())
    payload = client.build_request(job)
    assert await client.count_input_tokens(job, payload) == 100
    await client.submit(job, payload)
    assert list(schemas[0]["properties"]) == list(schemas[1]["properties"])


@pytest.mark.parametrize("upload_fails", [False, True])
async def test_large_effect_payload_is_claimed_before_upload_and_never_retried(upload_fails):
    c = setup()
    order = []
    prepared = SimpleNamespace(manifest={"sha256": "a" * 64}, ciphertext="encrypted-pointer")

    async def claim(*_):
        order.append("claim")

    async def upload(value):
        assert value is prepared
        order.append("upload")
        if upload_fails:
            raise RuntimeError("synthetic storage failure")

    async def received(*_):
        order.append("receipt")

    c.effects.payloads = SimpleNamespace(prepare=Mock(return_value=prepared), upload=AsyncMock(side_effect=upload))
    c.effects.claim = AsyncMock(side_effect=claim)
    c.effects.received = AsyncMock(side_effect=received)
    args = (c.row, c.token, c.request.operation_id, "request", {"payload": "large"})
    if upload_fails:
        with pytest.raises(RuntimeError):
            await c.effects.persist_payload(*args)
        assert order == ["claim", "upload"]
    else:
        assert await c.effects.persist_payload(*args) == "encrypted-pointer"
        assert order == ["claim", "upload", "receipt"]
