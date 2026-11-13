"""Natural intake, functional freedom and real offline sounds; no paid calls or render."""

import json
import shutil
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from pydantic import ValidationError

from app.adapters import motion_inputs
from app.adapters.motion_inputs import PreparedMotionInput
from app.schemas.motion_audiovisual import MotionPlannedSound
from app.schemas.motion_evolution import MotionEvolutionRequest
from app.schemas.motion_production import DirectedHTMLMotionComposition, MotionConstructionPlan, MotionRequest
from app.services import motion_sound_library as library
from app.services.auth import AuthError
from app.services.motion_checkpoint_execution import restore_input
from app.services.motion_checkpoints import input_manifest
from app.services.motion_construction import implement_motion, plan_motion
from app.services.motion_context import capture_motion_guidance
from app.services.motion_evolution import sha, validate_evolution_plan
from app.services.motion_generation import (
    PROPOSED_GENERATION_CONTRACT,
    construction_plan_hash,
    decode_construction_plan,
    provided_output_enabled,
)
from app.services.motion_materials import prepare_implementation_materials
from app.services.motion_preparation import PROPOSED_PREPARATION_RULES
from app.services.motion_protocols import MotionModelResult
from app.services.motion_quality import QUALITY_CONTRACT
from app.services.motion_repertoire import capture_repertoire, load_repertoire_images
from app.tests.unit.test_motion_ai import frame, provider, request, response_data
from app.tests.unit.test_motion_construction import plan_wire
from app.tests.unit.test_motion_inputs import source_snapshot, video_info
from app.tests.unit.test_motion_plan import direction_data, planned


def natural_body(**updates):
    message = "Faça um Reel com esse vídeo para divulgar minha cafeteria."
    data = dict(
        operation_id=uuid4(),
        source_asset_id=uuid4(),
        instruction=message,
        storyboard=True,
        propose_direction=True,
        review_checkpoints=True,
        sound_library_id="public-cc0-v1",
        repertoire_id="business-reel-v4",
        preparation={
            "client_message": message,
            "decisions": [
                {
                    "id": "intent",
                    "kind": "requirement",
                    "origin": "client",
                    "source_excerpt": message,
                    "interpretation": "Divulgar o negócio com a gravação selecionada.",
                    "scope": "request",
                }
            ],
            "evidence": [
                {
                    "id": "source",
                    "kind": "source",
                    "at_ms": [100, 300],
                    "observation": "Dois estados amostrados",
                    "intended_use": "Planejar a partir do material",
                    "limitations": "Sem escuta ou movimento contínuo",
                }
            ],
        },
    )
    return MotionRequest.model_validate({**data, **updates})


def natural_context():
    return {
        **capture_motion_guidance(natural_body()),
        "output": {"width": 720, "height": 1280, "fps": 30, "duration_ms": 1000},
        "authorized_audio": {"mode": "silent", "tracks": []},
        "source": {"asset_id": "assets/source.mp4", "sha256": "a" * 64, "duration_ms": 1000},
        "styles": [{"id": "editorial"}],
    }


def sound_data():
    item = library.capture_sound_library("public-cc0-v1")["items"][1]
    return dict(
        candidate_id=item["id"],
        candidate_sha256=item["sha256"],
        scene_id="hook",
        element_id="title",
        action_start_ms=0,
        action_end_ms=300,
        purpose="Acentuar contato justificado pela ação sintética",
        listening_checks=["suitability", "source_duplication", "voice_intelligibility"],
        trim_start_ms=0,
        trim_end_ms=200,
        offset_ms=50,
        volume=0.1,
        fade_in_ms=10,
        fade_out_ms=30,
    )


def audiovisual_wire():
    data = {
        **plan_wire(),
        "scene_direction": direction_data(),
        "audiovisual": {
            "interpretation": "Convite fundamentado na mensagem simples e no contexto do negócio",
            "functions": [
                {
                    "function_id": item["id"],
                    "target_element_ids": ["title", "answer"],
                    "disposition": "satisfy_requirement",
                    "justification": item["expectation"],
                    "verification": "Conferir a função na candidata e nos trechos pertinentes.",
                    "limitations": "Intenção sintética; não comprova qualidade visual ou sonora.",
                }
                for item in QUALITY_CONTRACT["requirements"]
            ],
            "sounds": [sound_data()],
            "omitted_sounds": [{"candidate_id": "coffee-pour", "reason": "Não há ação de servir neste plano"}],
            "limitations": ["Sem escuta, vídeo ou qualidade artística validada"],
        },
    }
    data["motion_plan"]["scenes"][0]["keyframe_ms"] = 300
    data["motion_plan"]["scenes"][1]["keyframe_ms"] = 800
    return data


def natural_plan():
    return decode_construction_plan(json.dumps(audiovisual_wire()), natural_context())


@pytest.mark.parametrize("change", [None, "graphic", "different_video", "past_source", "legacy"])
def test_recorded_action_can_receive_sound_while_its_video_window_is_stationary(change):
    from app.services.motion_quality import LEGACY_QUALITY_CONTRACT

    ctx = natural_context()
    data = natural_plan().model_dump(mode="json")
    element = data["motion_plan"]["scenes"][0]["elements"][0]
    element.update(role="video", asset_id="assets/source.mp4")
    element["beats"][0]["phase"] = "hold"
    if change == "graphic":
        element.update(role="graphic", asset_id=None)
    elif change == "different_video":
        element["asset_id"] = "assets/other.mp4"
    elif change == "past_source":
        ctx["source"]["duration_ms"] = 100
    elif change == "legacy":
        ctx["quality_contract"] = LEGACY_QUALITY_CONTRACT
    plan = MotionConstructionPlan.model_validate(data)
    if change is None:
        library.validate_sound_design(plan, ctx)
    else:
        with pytest.raises(AuthError, match="MOTION_SOUND_ACTION_INVALID"):
            library.validate_sound_design(plan, ctx)


def natural_prepared():
    ctx = natural_context()
    return PreparedMotionInput(
        ctx, library.load_sound_library(ctx), (frame(100), frame(300)), 1000, ctx["authorized_audio"]
    )


async def test_simple_message_reaches_real_planner_then_frozen_implementation_with_all_sound_metadata():
    p = natural_prepared()
    job = replace(request(), context=p.context, assets=p.assets, source_frames=p.source_frames)
    model = provider(lambda _: httpx.Response(200, json=response_data(audiovisual_wire())))
    payload = model.build_request(job)
    assert payload["text"]["format"]["name"] == "MotionAudiovisualPlanningOutput"
    assert not {"html", "scene_init"} & payload["text"]["format"]["schema"]["properties"].keys()
    sent = json.loads(payload["input"][0]["content"][0]["text"])
    assert sent["authorized_context"]["request"]["instruction"] == natural_body().instruction
    assert "scene_direction" not in sent["authorized_context"]["request"]
    assert sent["visual_direction_input"]["mode"] == "model_proposed"
    assert sent["authorized_context"]["sound_library"]["items"][0]["license"] == "CC0-1.0"
    assert "reference_images" in sent["authorized_context"]["repertoire"]
    assert load_repertoire_images(p.context) == ()
    assert len(sent["authorized_context"]["repertoire"]["examples"]) == 3
    assert all('"finish_reference":' not in block.get("text", "") for block in payload["input"][0]["content"])
    result = await model.submit(job, payload)
    plan = result.construction_plan
    assert plan == natural_plan()
    p = prepare_implementation_materials(plan, library.apply_planned_sound(p, plan))
    job = replace(job, context=p.context, construction_plan=plan)
    output = dict(
        plan_sha256=construction_plan_hash(plan),
        status="implemented",
        html=planned().html,
        scene_init=planned().scene_init,
        revision_reason=None,
    )
    model = provider(lambda _: httpx.Response(200, json=response_data(output)))
    built = await model.submit(job, model.build_request(job))
    assert built.composition.audiovisual == plan.audiovisual
    assert built.composition.scene_direction == plan.scene_direction
    assert built.composition.audio == plan.audio


@pytest.mark.parametrize(
    "change", ["no_checkpoint", "different_message", "fixed_direction", "fixed_sound", "library_only"]
)
def test_natural_path_rejects_inconsistent_input(change):
    data = natural_body().model_dump(mode="json")
    if change == "no_checkpoint":
        data["review_checkpoints"] = False
    elif change == "different_message":
        data["instruction"] = "Falsa instrução técnica do cliente"
    elif change == "fixed_direction":
        data["scene_direction"] = direction_data()
    elif change == "fixed_sound":
        data["music_ducking"] = {"threshold": 0.1, "ratio": 2.0, "attack_ms": 20, "release_ms": 100}
    else:
        data["propose_direction"] = False
    with pytest.raises(ValidationError):
        MotionRequest.model_validate(data)


def test_v4_removes_only_selected_prints_and_preserves_old_versions_and_examples():
    new = capture_repertoire("business-reel-v4")
    old = capture_repertoire("business-reel-v3")
    assert len(old["reference_images"]) == 8 and new["reference_images"] == []
    assert new["examples"] == old["examples"] and new["licenses"] == old["licenses"]
    assert load_repertoire_images(natural_context()) == ()


@pytest.mark.parametrize("change", ["library", "file", "missing", "duplicate", "unknown", "io"])
def test_library_rejects_unregistered_or_changed_bytes_before_provider(tmp_path, monkeypatch, change):
    ctx = natural_context()
    if change == "unknown":
        with pytest.raises(AuthError, match="LIBRARY_UNAVAILABLE"):
            library.capture_sound_library("unknown")
        return
    if change in {"library", "file", "io"}:
        shutil.copytree(library.ROOT, tmp_path / "sounds")
        monkeypatch.setattr(library, "ROOT", tmp_path / "sounds")
        path = library.ROOT / "public-cc0-v1" / ("manifest.json" if change in {"library", "io"} else "coffee-pour.mp3")
        if change == "io":
            path.unlink()
        else:
            path.write_bytes(b"changed")
        with pytest.raises(AuthError, match="MOTION_SOUND_"):
            library.load_sound_library(ctx)
    else:
        assets = library.load_sound_library(ctx)
        assets = assets[:-1] if change == "missing" else (*assets, assets[0])
        with pytest.raises(AuthError, match="FILE_CHANGED"):
            provider().build_request(
                replace(request(), context=ctx, assets=assets, source_frames=(frame(100), frame(300)))
            )


@pytest.mark.parametrize(
    "change",
    [
        "hash",
        "duration",
        "scene",
        "element",
        "action",
        "offset",
        "static",
        "duplicate",
        "unaccounted",
        "omitted_twice",
        "both",
        "no_design",
    ],
)
def test_sound_selection_requires_integrity_action_and_explicit_accounting(change):
    plan = natural_plan().model_dump(mode="json")
    sound = plan["audiovisual"]["sounds"][0]
    if change == "hash":
        sound["candidate_sha256"] = "0" * 64
    elif change == "duration":
        sound["trim_end_ms"] = 6000
    elif change in {"scene", "element"}:
        sound[f"{change}_id"] = "absent"
    elif change == "action":
        sound["action_end_ms"] = 500
    elif change == "offset":
        sound["offset_ms"] = 500
    elif change == "static":
        plan["motion_plan"]["scenes"][0]["elements"][0]["beats"][0]["phase"] = "hold"
    elif change == "duplicate":
        plan["audiovisual"]["sounds"].append(deepcopy(sound))
    elif change == "unaccounted":
        plan["audiovisual"]["omitted_sounds"] = []
    elif change == "omitted_twice":
        plan["audiovisual"]["omitted_sounds"] *= 2
    elif change == "both":
        plan["audiovisual"]["omitted_sounds"].append({"candidate_id": "cup-contact", "reason": "contradiction"})
    else:
        plan.pop("audiovisual")
    with pytest.raises(AuthError, match="MOTION_(SOUND|AUDIOVISUAL)_"):
        library.apply_planned_sound(natural_prepared(), MotionConstructionPlan.model_validate(plan))


@pytest.mark.parametrize("change", ["trim", "action", "output", "fades", "checks", "precision"])
def test_sound_schema_rejects_invalid_intervals_and_unverified_listening_claims(change):
    sound = sound_data()
    if change == "trim":
        sound["trim_end_ms"] = 0
    elif change == "action":
        sound["action_end_ms"] = 0
    elif change == "output":
        sound["offset_ms"] = 59999
    elif change == "fades":
        sound["fade_in_ms"] = 500
    elif change == "checks":
        sound["listening_checks"] = ["suitability"] * 3
    else:
        sound["volume"] = 0.1234567
    with pytest.raises(ValidationError):
        MotionPlannedSound.model_validate(sound)


def test_soundtrack_keeps_original_branch_and_restores_same_reviewed_mix_without_render():
    p = natural_prepared()
    original = {
        "mode": "mix",
        "tracks": [
            {"asset_id": "assets/source.mp4", "offset_ms": 0, "trim_start_ms": 0, "trim_end_ms": 1000, "volume": 1.0}
        ],
    }
    p = replace(p, audio=original, context={**p.context, "authorized_audio": original})
    plan = natural_plan().model_copy(update={"audio": planned().audio.model_validate(original)})
    mixed = library.apply_planned_sound(p, plan)
    assert mixed.soundtrack["tracks"][0] == {
        **original["tracks"][0],
        "role": "original",
        "fade_in_ms": 0,
        "fade_out_ms": 0,
    }
    assert mixed.context["sound_listening_status"].startswith("unreviewed")
    composition = DirectedHTMLMotionComposition(
        **plan.model_dump(), html=planned().html, scene_init=planned().scene_init
    )
    resolved = prepare_implementation_materials(plan, mixed)
    packet = dict(
        stage="render",
        artifact=composition.model_dump(mode="json"),
        context=resolved.context,
        inputs=input_manifest(resolved),
        resolved_images=[],
    )
    assert restore_input(p, packet) == resolved
    packet["context"] = {**resolved.context, "authorized_soundtrack": {"changed": True}}
    with pytest.raises(AuthError, match="INPUT_CHANGED"):
        restore_input(p, packet)


def functional_selection():
    return MotionEvolutionRequest(
        version="motion-evolution-v2",
        baseline_request_id=uuid4(),
        baseline_number=0,
        baseline_video_sha256="a" * 64,
        owner_reference_confirmed=True,
        hypothesis="Piso funcional sem molde",
        functions=[
            dict(
                id="reveal",
                function="Revelar assunto e transferir atenção",
                baseline_element_ids=["title"],
                evidence_at_ms=[100],
                observation="Hierarquia na base",
                verification="Comparar revelação e leitura",
            )
        ],
    )


def functional_case():
    selection = functional_selection()
    plan = natural_plan()
    function = dict(
        function_id="reveal",
        target_element_ids=["answer"],
        disposition="replace_representation",
        justification="Outra hierarquia atende à mesma função",
        verification="Conferir passagem no vídeo",
        limitations="Intenção; sem prova visual",
    )
    data = plan.model_dump(mode="json")
    data["audiovisual"]["functions"] = [function]
    plan = MotionConstructionPlan.model_validate(data)
    base = planned()
    ctx = {
        **natural_context(),
        "evolution": {
            "selection": selection.model_dump(mode="json"),
            "composition": base.model_dump(mode="json"),
            "composition_sha256": sha(base.model_dump(mode="json")),
            "rules": "Synthetic functional floor; not a fixed composition.",
        },
    }
    ctx["request"]["evolution"] = selection.model_dump(mode="json")
    ctx.pop("quality_contract")
    ctx["generation_contract"] = PROPOSED_GENERATION_CONTRACT
    ctx["preparation_contract"] = PROPOSED_PREPARATION_RULES
    return plan, ctx


def test_functional_floor_allows_different_representations_but_never_silent_function_loss():
    plan, ctx = functional_case()
    validate_evolution_plan(plan, ctx)
    # No fixed target exists in the request; the model chose the replacement.
    assert not ctx["request"]["evolution"]["elements"]
    assert "target_element_ids" not in ctx["request"]["evolution"]["functions"][0]
    missing = plan.audiovisual.model_copy(update={"functions": ()})
    with pytest.raises(AuthError, match="FUNCTION_TARGET_MISSING"):
        validate_evolution_plan(plan.model_copy(update={"audiovisual": missing}), ctx)
    with pytest.raises(AuthError, match="COVERAGE_REQUIRED"):
        validate_evolution_plan(plan.model_copy(update={"audiovisual": None}), ctx)
    invalid = plan.audiovisual.functions[0].model_copy(update={"target_element_ids": ("absent",)})
    with pytest.raises(AuthError, match="TARGET_MISSING"):
        validate_evolution_plan(
            plan.model_copy(update={"audiovisual": plan.audiovisual.model_copy(update={"functions": (invalid,)})}), ctx
        )


async def test_checkpoints_budget_only_next_stage_and_do_not_render_or_generate_assets():
    p = natural_prepared()
    plan = natural_plan()
    composition = DirectedHTMLMotionComposition(
        **plan.model_dump(), html=planned().html, scene_init=planned().scene_init
    )
    effects = SimpleNamespace(
        requests=SimpleNamespace(settings=SimpleNamespace(motion_ai_reservation_usd_micros=100)),
        capacity=AsyncMock(return_value=True),
        model=AsyncMock(
            side_effect=[MotionModelResult(construction_plan=plan), MotionModelResult(composition=composition)]
        ),
    )
    row, token = {"operation_id": uuid4()}, uuid4()
    assert await plan_motion(effects, provider(), row, token, p) == plan
    images = SimpleNamespace(prepare=AsyncMock(side_effect=lambda *args: args[-2]))
    built, result = await implement_motion(effects, provider(), row, token, p, plan, images)
    assert result == composition and built.soundtrack is not None
    assert [call.args[-1] for call in effects.capacity.await_args_list] == [100, 100]
    assert effects.model.await_args.args[-1].construction_plan == plan


async def test_loader_binds_public_sound_files_and_metadata_without_storage_audio_or_network(monkeypatch):
    from app.services import motion_sound_analysis

    monkeypatch.setattr(motion_sound_analysis, "decode_analysis_pcm", AsyncMock(return_value=b"\0\0" * 160))
    snapshot = {**source_snapshot(), **capture_motion_guidance(natural_body())}
    monkeypatch.setattr(motion_inputs, "inspect_and_extract_motion_audio", AsyncMock(return_value=(video_info(), None)))
    monkeypatch.setattr(motion_inputs, "source_frames", AsyncMock(return_value=(frame(100), frame(300))))
    store = SimpleNamespace(get_video=AsyncMock(return_value=b"original recording"))
    p = await motion_inputs.MotionInputLoader(store).prepare(snapshot)
    assert len(p.assets) == 5 and p.soundtrack is None
    assert len(p.context["audio_assessment"]["measurements"]) == 3
    assert {a.id for a in p.assets if a.id.startswith("assets/sfx-")} == {
        "assets/sfx-coffee-pour.mp3",
        "assets/sfx-cup-contact.mp3",
    }


def test_omitting_both_sounds_is_explicit_and_keeps_original_mix_without_fake_attestation():
    p = natural_prepared()
    data = natural_plan().model_dump(mode="json")
    data["audiovisual"]["sounds"] = []
    data["audiovisual"]["omitted_sounds"].append({"candidate_id": "cup-contact", "reason": "Ação não pede complemento"})
    result = library.apply_planned_sound(p, MotionConstructionPlan.model_validate(data))
    assert result is p and result.soundtrack is None
    p.context["sound_library"]["items"][0]["license"] = "CC-BY-NC"
    with pytest.raises(AuthError, match="LIBRARY_CHANGED"):
        library.load_sound_library(p.context)


def test_unbound_functional_claims_and_forged_proposed_context_cannot_reach_provider():
    plan, ctx = functional_case()
    ctx.pop("evolution")
    with pytest.raises(AuthError, match="COVERAGE_UNEXPECTED"):
        library.validate_sound_design(plan, ctx)
    ctx = natural_context()
    ctx["request"]["review_checkpoints"] = False
    with pytest.raises(AuthError, match="CONTEXT_REQUIRED"):
        provided_output_enabled(ctx)


@pytest.mark.parametrize(
    "change", ["missing_functions", "mixed", "duplicate", "unknown_element", "unknown_time", "no_base_plan"]
)
def test_functional_floor_must_have_distinct_grounded_obligations(change):
    from app.services.motion_evolution import validate_obligations

    data = functional_selection().model_dump(mode="json")
    if change == "missing_functions":
        data["functions"] = []
    elif change == "mixed":
        from app.tests.unit.test_motion_evolution import case

        data["elements"] = case()[1].model_dump(mode="json")["elements"]
    elif change == "duplicate":
        data["functions"] *= 2
    elif change == "unknown_element":
        data["functions"][0]["baseline_element_ids"] = ["absent"]
    elif change == "unknown_time":
        data["functions"][0]["evidence_at_ms"] = [2000]
    if change in {"missing_functions", "mixed", "duplicate"}:
        with pytest.raises(ValidationError):
            MotionEvolutionRequest.model_validate(data)
    else:
        base = planned().model_copy(update={"motion_plan": None}) if change == "no_base_plan" else planned()
        with pytest.raises(AuthError, match="(EVIDENCE_INVALID|DIRECTION_REQUIRED)"):
            validate_obligations(MotionEvolutionRequest.model_validate(data), base, None)


def test_unfixed_preparation_can_be_exported_without_inventing_a_direction():
    from scripts.evals.motion_external_export import assemble_files

    p = natural_prepared()
    files = assemble_files(
        replace(request(), context=p.context, assets=p.assets, source_frames=p.source_frames),
        {"model": "synthetic", "max_output_tokens": 54000},
    )
    assert "scene-direction.json" not in files
    assert files["execution/assets/sfx-cup-contact.mp3"] == p.assets[1].data
    assert b"scene_direction" in files["output-contract.json"]


def test_legacy_sound_paths_remain_unchanged_and_never_require_public_assets():
    from app.services.motion_sound_library import validate_sound_design

    p = natural_prepared()
    legacy = replace(p, context={})
    assert library.load_sound_library({}) == ()
    validate_sound_design(planned(), {})
    assert library.apply_planned_sound(legacy, planned()) is legacy


@pytest.mark.parametrize("change", [None, "missing", "hash", "type", "empty", "too_short"])
def test_measured_sound_duration_binds_selection_to_decoded_bytes(change):
    p = natural_prepared()
    item = {
        "asset_id": "assets/sfx-cup-contact.mp3",
        "sha256": sound_data()["candidate_sha256"],
        "decoded_duration_ms": 200,
    }
    measurements = [item]
    if change == "missing":
        measurements = []
    elif change == "hash":
        item["sha256"] = "0" * 64
    elif change == "type":
        item["decoded_duration_ms"] = True
    elif change == "empty":
        item["decoded_duration_ms"] = 0
    elif change == "too_short":
        item["decoded_duration_ms"] = 100
    p.context["audio_assessment"] = {"measurements": measurements}
    if change:
        with pytest.raises(AuthError, match="(ANALYSIS_CHANGED|ACTION_INVALID)"):
            library.apply_planned_sound(p, natural_plan())
    else:
        assert library.apply_planned_sound(p, natural_plan()).soundtrack is not None


async def test_functional_evidence_must_be_present_in_actual_baseline_attachments():
    import base64

    from app.services.motion_evolution_inputs import load_evolution

    _, ctx = functional_case()
    ctx.update(source={"sha256": "b" * 64}, kit={}, authorized_audio=planned().audio.model_dump(mode="json"))
    prepared = PreparedMotionInput(ctx, (), (), 1000, ctx["authorized_audio"])
    frames = (frame(0), frame(500))
    evidence = {"frames": [{"ms": f.ms, "sha256": f.sha256, "png": base64.b64encode(f.png).decode()} for f in frames]}
    captured = {
        **ctx["evolution"],
        "version": "motion-evolution-v2",
        "source_sha256": "b" * 64,
        "kit": {},
        "row": {},
        "evidence_ciphertext": "inline",
        "materials": [],
    }
    with pytest.raises(AuthError, match="FUNCTION_EVIDENCE_INVALID"):
        await load_evolution(prepared, captured, SimpleNamespace(open=lambda _: evidence), AsyncMock())
    captured["selection"]["functions"][0]["evidence_at_ms"] = [0]
    loaded = await load_evolution(prepared, captured, SimpleNamespace(open=lambda _: evidence), AsyncMock())
    assert loaded.baseline_frames == frames
