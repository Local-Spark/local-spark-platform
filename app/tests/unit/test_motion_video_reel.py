"""VR1–VR3 contract, admission and replay isolation; synthetic material only."""

import hashlib
import json
from copy import deepcopy

import pytest

from app.adapters.motion_ai import _format
from app.schemas.motion_production import HTMLMotionComposition
from app.services.auth import AuthError
from app.services.motion_context import capture_motion_guidance
from app.services.motion_repertoire import capture_repertoire, validate_repertoire_images
from app.services.motion_video_reel import (
    GUARD_PATH,
    VIDEO_REEL_CONTRACT,
    _state,
    guarded_video_scene_init,
    validate_video_reel,
    video_reel_rules,
)
from app.tests.unit.test_motion_audiovisual import natural_body

CTX = {"video_reel_contract": VIDEO_REEL_CONTRACT}
ASSETS = {"assets/source.mp4", "assets/logo.png"}


def video_case():
    def state(x, opacity):
        return json.dumps(dict(x=x, y=0, opacity=opacity))

    def beat(phase, start, end, a, z):
        return dict(
            phase=phase,
            start_ms=start,
            end_ms=end,
            start_state=a,
            end_state=z,
            trajectory="gentle",
            curve=dict(kind="linear", parameters=[]),
        )

    still = [beat("hold", 0, 3000, "visible", "visible")]
    text = [
        beat("enter", 0, 300, state(0, 0), state(0, 1)),
        beat("transform", 300, 700, state(0, 1), state(4, 1)),
        beat("hold", 700, 2700, state(4, 1), state(4, 1)),
        beat("exit", 2700, 3000, state(4, 1), state(4, 0)),
    ]
    elements = [
        dict(
            id=id,
            role=role,
            asset_id=asset,
            purpose="pause",
            coordination="action first",
            related_element_ids=["recording"] if role == "text" else [],
            beats=beats,
        )
        for id, role, asset, beats in [
            ("recording", "video", "assets/source.mp4", still),
            ("logo", "image", "assets/logo.png", still),
            ("cta", "text", None, text),
        ]
    ]
    return dict(
        html="<div></div>",
        scene_init="window.seek=()=>{}",
        concept="Pause",
        source_usage="whole recording",
        audio=dict(mode="silent", tracks=[]),
        motion_plan=dict(
            version="motion-plan-v1",
            identity_source="business_kit",
            duration_ms=3000,
            scenes=[
                dict(
                    id="scene",
                    start_ms=0,
                    end_ms=3000,
                    message="pause",
                    transition_to_next="end",
                    elements=elements,
                    video_layout=dict(
                        mode="cover",
                        video_element_id="recording",
                        brand_element_id="logo",
                        text_element_ids=["cta"],
                        cta_element_id="cta",
                    ),
                )
            ],
        ),
    )


def artifact(data=None):
    return HTMLMotionComposition.model_validate(data or video_case())


def test_capture_pin_replay_and_legacy_schema():
    body = natural_body(repertoire_id=None)
    new = capture_motion_guidance(body)
    assert new["video_reel_contract"] == VIDEO_REEL_CONTRACT
    assert new["executor_contract"]["integration_policy"] == video_reel_rules(new).strip()
    assert "proporção/contain" not in new["creative_contract"]["direction"]
    assert "não exige vídeo sempre visível" not in new["creative_contract"]["direction"]
    assert new["skill"]["id"] == "instagram-reel-video-v21"
    assert new["repertoire"]["id"] == "business-video-reel-v4"
    assert capture_motion_guidance(body, previous=new) == new
    old = deepcopy(new)
    old.pop("video_reel_contract")
    assert "video_reel_contract" not in capture_motion_guidance(body, previous=old)
    pack = capture_repertoire("business-video-reel-v1")
    validate_repertoire_images({"repertoire": pack}, ())
    assert video_reel_rules({}) == ""
    assert guarded_video_scene_init(artifact(), {}, "historic bytes") == "historic bytes"
    validate_video_reel(artifact(), {}, asset_ids=set())
    old_schema = _format(HTMLMotionComposition, allow_staging=False)["schema"]["$defs"]
    assert "VideoLayout" not in old_schema
    assert "video_layout" not in old_schema["MotionScenePlan"]["properties"]
    new_schema = _format(HTMLMotionComposition, allow_staging=False, allow_video_layout=True)["schema"]["$defs"]
    assert "VideoLayout" in new_schema


def test_valid_plan_and_guard_pin(monkeypatch, tmp_path):
    comp = artifact()
    validate_video_reel(comp, CTX, asset_ids=ASSETS)
    assert hashlib.sha256(GUARD_PATH.read_bytes()).hexdigest() == VIDEO_REEL_CONTRACT["dom_guard_sha256"]
    assert "installVideoReelV1" in guarded_video_scene_init(comp, CTX, comp.scene_init)
    changed = tmp_path / "guard.js"
    changed.write_text("changed")
    monkeypatch.setattr("app.services.motion_video_reel.GUARD_PATH", changed)
    with pytest.raises(AuthError, match="GUARD_CHANGED"):
        guarded_video_scene_init(comp, CTX, comp.scene_init)
    with pytest.raises(AuthError, match="CONTRACT_CHANGED"):
        video_reel_rules({"video_reel_contract": {}})
    with pytest.raises(AuthError, match="KIT_SOURCE_REQUIRED"):
        validate_video_reel(comp, CTX, asset_ids=set())
    with pytest.raises(AuthError, match="PLAN_REQUIRED"):
        validate_video_reel(comp.model_copy(update={"motion_plan": None}), CTX, asset_ids=ASSETS)


@pytest.mark.parametrize(
    "value",
    [
        "bad",
        "[]",
        "null",
        '{"x":0}',
        '{"x":true,"y":0,"opacity":1}',
        '{"x":NaN,"y":0,"opacity":1}',
        '{"x":0,"y":0,"opacity":2}',
    ],
)
def test_bad_states(value):
    with pytest.raises(AuthError, match="TEXT_STATE_INVALID"):
        _state(value)


@pytest.mark.parametrize(
    "change",
    [
        "layout",
        "video_id",
        "video_asset",
        "video_role",
        "brand_id",
        "brand_asset",
        "brand_role",
        "duplicate_text",
        "missing_text",
        "second_video",
        "relation",
        "phase",
        "start",
        "end",
        "curve",
        "gap",
        "continuity",
        "enter",
        "exit",
        "hold",
        "transform",
        "cta",
        "short_cta",
    ],
)
def test_rejects_poster_or_weak_text(change):
    data = video_case()
    scene = data["motion_plan"]["scenes"][0]
    layout, elements = scene["video_layout"], scene["elements"]
    beats = elements[-1]["beats"]
    if change == "layout":
        scene.pop("video_layout")
    elif change == "video_id":
        layout["video_element_id"] = "missing"
    elif change == "video_asset":
        elements[0]["asset_id"] = "assets/other.mp4"
    elif change == "video_role":
        elements[0]["role"] = "image"
    elif change == "brand_id":
        layout["brand_element_id"] = "missing"
    elif change == "brand_asset":
        elements[1]["asset_id"] = "assets/other.png"
    elif change == "brand_role":
        elements[1]["role"] = "video"
    elif change == "duplicate_text":
        layout["text_element_ids"] *= 2
    elif change == "missing_text":
        layout["text_element_ids"] = ["missing"]
    elif change == "second_video":
        elements.append({**elements[0], "id": "second"})
    elif change == "relation":
        elements[-1]["related_element_ids"] = []
    elif change == "phase":
        beats[1]["phase"] = "hold"
    elif change == "start":
        beats[0]["start_ms"] = 1
    elif change == "end":
        beats[-1]["end_ms"] -= 1
    elif change == "curve":
        beats[1]["curve"]["kind"] = "ease_in"
    elif change == "gap":
        beats[1]["start_ms"] += 1
    elif change == "continuity":
        beats[1]["start_state"] = '{"x":3,"y":0,"opacity":1}'
    elif change == "enter":
        beats[0]["start_state"] = '{"x":0,"y":0,"opacity":1}'
    elif change == "exit":
        beats[-1]["end_state"] = beats[-1]["start_state"]
    elif change == "hold":
        beats[2]["end_state"] = '{"x":5,"y":0,"opacity":1}'
    elif change == "transform":
        beats[1]["end_state"] = beats[1]["start_state"]
    elif change == "cta":
        layout["cta_element_id"] = None
    elif change == "short_cta":
        beats[1]["end_ms"] = 1300
        beats[2]["start_ms"] = 1300
    with pytest.raises(AuthError, match="MOTION_VIDEO_"):
        validate_video_reel(artifact(data), CTX, asset_ids=ASSETS)


def test_cta_only_final_scene_and_minimum_boundary():
    data = video_case()
    beats = data["motion_plan"]["scenes"][0]["elements"][-1]["beats"]
    beats[1]["end_ms"] = beats[2]["start_ms"] = 1200
    validate_video_reel(artifact(data), CTX, asset_ids=ASSETS)
    scene = data["motion_plan"]["scenes"][0]
    next_scene = deepcopy(scene)
    next_scene["id"] = "next"
    for e in next_scene["elements"]:
        e["id"] += "2"
        e["related_element_ids"] = [id + "2" for id in e["related_element_ids"]]
    layout = next_scene["video_layout"]
    for key in ["video_element_id", "brand_element_id", "cta_element_id"]:
        layout[key] += "2"
    layout["text_element_ids"] = ["cta2"]
    data["motion_plan"]["scenes"].append(next_scene)
    with pytest.raises(AuthError, match="CTA_WINDOW"):
        validate_video_reel(artifact(data), CTX, asset_ids=ASSETS)
    scene["video_layout"]["cta_element_id"] = None
    validate_video_reel(artifact(data), CTX, asset_ids=ASSETS)


def test_compact_wire_and_shared_validator_keep_video_layout():
    from app.schemas.motion_generation import MotionStagedPlanningOutput
    from app.services.motion_generation import expand_compact_output
    from app.services.motion_plan import validate_motion_plan

    for enabled in (False, True):
        defs = _format(MotionStagedPlanningOutput, allow_staging=True, allow_video_layout=enabled)["schema"]["$defs"]
        assert ("video_layout" in defs["CompactMotionScene"]["properties"]) == enabled
    layout = video_case()["motion_plan"]["scenes"][0]["video_layout"]
    data = {"motion_plan": {"scenes": [{"video_layout": layout, "elements": []}]}}
    assert expand_compact_output(deepcopy(data)) == data
    validate_motion_plan(artifact(), CTX, duration_ms=3000, asset_ids=ASSETS)
    bad = video_case()
    bad["motion_plan"]["scenes"][0].pop("video_layout")
    with pytest.raises(AuthError, match="VIDEO_LAYOUT_REQUIRED"):
        validate_motion_plan(artifact(bad), CTX, duration_ms=3000, asset_ids=ASSETS)


def canonical_vr3_case():
    """Execute the example actually transmitted to the model, not a parallel fixture."""
    pack = capture_repertoire("business-video-reel-v2")
    example = json.loads(next(e["content"] for e in pack["examples"] if e["id"] == "cta-plan"))
    data = video_case()
    scene = data["motion_plan"]["scenes"][0]
    data["motion_plan"]["duration_ms"] = scene["end_ms"] = example["scene_end_ms"]
    for element in scene["elements"][:2]:
        element["beats"][0]["end_ms"] = scene["end_ms"]
    scene["elements"][-1]["beats"] = example["beats"]
    return data


@pytest.mark.parametrize("missing_media", [(), (1,), (2,), (1, 2)])
def test_run_da6dd899_requires_local_media_in_every_scene(missing_media):
    """Same three-scene topology and boundaries, with synthetic text and beats."""
    from app.services.motion_plan import validate_motion_plan

    data = video_case()
    template = data["motion_plan"]["scenes"].pop()
    boundaries = [0, 4320, 8440, 11200]
    data["motion_plan"]["duration_ms"] = boundaries[-1]
    for index, (start, end) in enumerate(zip(boundaries[:-1], boundaries[1:], strict=True)):
        scene = deepcopy(template)
        scene.update(id=f"scene{index}", start_ms=start, end_ms=end)
        scene["transition_to_next"] = "continuous" if index < 2 else "end"
        for element in scene["elements"]:
            element["beats"] = deepcopy(template["elements"][0 if element["role"] != "text" else 2]["beats"])
            element["id"] += str(index)
            element["related_element_ids"] = ["recording" + str(index)] if element["role"] == "text" else []
            for beat in element["beats"]:
                beat["start_ms"] += start
                beat["end_ms"] += start
            element["beats"][-1]["end_ms"] = end
            if element["role"] == "text":
                element["beats"][-2]["end_ms"] = end - 200
                element["beats"][-1]["start_ms"] = end - 200
        scene["video_layout"].update(
            video_element_id="recording" + str(index),
            brand_element_id="logo" + str(index),
            text_element_ids=["cta" + str(index)],
            cta_element_id="cta2" if index == 2 else None,
        )
        if index in missing_media:
            scene["elements"] = scene["elements"][2:]
            scene["video_layout"].update(video_element_id="recording0", brand_element_id="logo0")
            scene["elements"][0]["related_element_ids"] = ["recording0"]
        data["motion_plan"]["scenes"].append(scene)
    if missing_media:
        with pytest.raises(AuthError, match="^MOTION_VIDEO_LAYOUT_REQUIRED$"):
            validate_video_reel(artifact(data), CTX, asset_ids=ASSETS)
    else:
        validate_motion_plan(artifact(data), CTX, duration_ms=11200, asset_ids=ASSETS)


def test_transmitted_canonical_plan_passes_vr3_at_minimum_cta_window():
    from app.services.motion_plan import validate_motion_plan

    data = canonical_vr3_case()
    validate_motion_plan(artifact(data), CTX, duration_ms=2500, asset_ids=ASSETS)
    beats = data["motion_plan"]["scenes"][0]["elements"][-1]["beats"]
    assert beats[2]["end_ms"] - beats[2]["start_ms"] == 1500


@pytest.mark.parametrize("offender", ["pausa", "tempo", "cta", "all"])
def test_run_853327f8_ghost_holds_are_rejected(offender):
    """Synthetic reproduction of documented topology; no customer content or invented run timings."""
    data = canonical_vr3_case()
    scene = data["motion_plan"]["scenes"][0]
    data["motion_plan"]["duration_ms"] = scene["end_ms"] = 11200
    for element in scene["elements"][:2]:
        element["beats"][0]["end_ms"] = 11200
    template = scene["elements"].pop()
    template["beats"][-1]["end_ms"] = 11200
    for name in ("pausa", "tempo", "cta"):
        element = deepcopy(template)
        element["id"] = "cena1-" + name
        beats = element["beats"]
        if offender in (name, "all"):
            if name == "pausa":
                beats[-1]["end_ms"] = 11000
                ghost = {**beats[-1], "phase": "hold", "start_ms": 11000, "end_ms": 11200}
                ghost["start_state"] = ghost["end_state"]
                beats.append(ghost)
            else:
                beats[0]["start_ms"] = 100
                ghost = {**beats[0], "phase": "hold", "start_ms": 0, "end_ms": 100}
                ghost["end_state"] = ghost["start_state"]
                beats.insert(0, ghost)
        scene["elements"].append(element)
    scene["video_layout"]["text_element_ids"] = ["cena1-pausa", "cena1-tempo", "cena1-cta"]
    scene["video_layout"]["cta_element_id"] = "cena1-cta"
    with pytest.raises(AuthError, match="^MOTION_VIDEO_KINETIC_TEXT_REQUIRED$"):
        validate_video_reel(artifact(data), CTX, asset_ids=ASSETS)


def test_new_guidance_reaches_provider_and_v14_v1_replay_is_unchanged():
    from dataclasses import replace

    from app.services.motion_repertoire import load_repertoire_images
    from app.services.motion_skills import load_motion_skill
    from app.tests.unit.test_motion_ai import provider
    from app.tests.unit.test_motion_staging import staged_job

    body = natural_body(repertoire_id=None)
    new = capture_motion_guidance(body)
    job = staged_job()
    context = {**job.context, **CTX, "skill": new["skill"], "repertoire": new["repertoire"]}
    payload = provider().build_request(replace(job, context=context, reference_images=()))
    transmitted = json.loads(payload["input"][0]["content"][0]["text"])["authorized_context"]
    for instructions in (transmitted["skill"]["instructions"], transmitted["repertoire"]["rules"]):
        for rule in (
            "[scene.start_ms, scene.end_ms]",
            "beats[0].phase=enter",
            "beats[-1].phase=exit",
            "Proibido hold com opacity=0",
            "Invisibilidade só via enter/exit",
            "hold estável >=1500ms entre enter e exit",
        ):
            assert rule in instructions
    for rule in (
        "Cada cena inclui em scene.elements",
        "asset_id=assets/source.mp4 (VIDEO)",
        "asset_id=assets/logo.png (IMG)",
        "proibir IDs de outra cena",
        "exatamente um VIDEO no DOM em cada seek",
        "display:none não satisfaz a guarda",
        "Transform obrigatório em CADA texto",
        "enter → hold → exit é inválido",
        "CTA com hold longo também precisa de transform",
        "não conte enter/exit como transform",
        "Nunca multiplique o alpha do scrim pela opacidade do texto",
        "mesmo que estejam declarados com role=graphic",
        "function videoTextWithScrim",
        "node.children.length === 0",
        "<br> é elemento filho",
        "Use textContent",
        "white-space:pre-line",
    ):
        assert rule in transmitted["skill"]["instructions"]
    assert load_repertoire_images(new) == ()
    old = deepcopy(new)
    digest = "adb2b90b2e60883bd7fa0e1b59ddd92c3dcee47401710aa89447de1e80c8208f"
    old["skill"] = {
        "id": "instagram-reel-video-v14",
        "sha256": digest,
        "instructions": load_motion_skill("instagram-reel-video-v14", digest, "reel"),
    }
    old["repertoire"] = capture_repertoire("business-video-reel-v1")
    assert capture_motion_guidance(body, previous=old) == old
    assert load_repertoire_images(old) == ()
    explicit = capture_motion_guidance(natural_body(repertoire_id="business-video-reel-v2"))
    assert explicit["repertoire"] == capture_repertoire("business-video-reel-v2")
    assert "staging_contract" in explicit


@pytest.mark.parametrize("offender", [None, "momento", "cta", "both"])
def test_run_028a10c5_each_final_text_needs_its_own_transform(offender):
    """Recorded boundaries and missing-phase topology; synthetic states/content only."""
    from app.services.motion_plan import validate_motion_plan
    from app.services.motion_skills import resolve_html_motion_skill

    instructions = resolve_html_motion_skill("reel")[2]
    canonical = json.loads(instructions.split("```json\n", 1)[1].split("```", 1)[0])
    data = video_case()
    first = data["motion_plan"]["scenes"][0]
    first["id"] = "cena1"
    first["end_ms"] = 6780
    first["transition_to_next"] = "continuous"
    first["video_layout"]["cta_element_id"] = None
    for element in first["elements"]:
        element["beats"][-1]["end_ms"] = 6780
    first["elements"][-1]["beats"][-2]["end_ms"] = 6280
    first["elements"][-1]["beats"][-1]["start_ms"] = 6280
    second = deepcopy(video_case()["motion_plan"]["scenes"][0])
    second.update(id="cena2", start_ms=6780, end_ms=11200)
    template = second["elements"].pop()
    for element in second["elements"]:
        element["id"] = "cena2-" + element["id"]
        element["beats"] = deepcopy(element["beats"])
        element["beats"][0].update(start_ms=6780, end_ms=11200)
    for name in ("momento", "cta"):
        element = deepcopy(template)
        element.update(id="cena2-" + name, related_element_ids=["cena2-recording", "cena2-haste"])
        element["beats"] = deepcopy(canonical)
        if offender in (name, "both"):
            # Enter/exit move, and the graphic transforms; neither satisfies the text phase.
            element["beats"].pop(1)
            element["beats"][1]["start_ms"] = 7380
            for beat in element["beats"]:
                beat["start_state"] = beat["end_state"] = '{"x":0,"y":0,"opacity":1}'
            element["beats"][0]["start_state"] = '{"x":0,"y":12,"opacity":0}'
            element["beats"][-1]["end_state"] = '{"x":0,"y":-8,"opacity":0}'
        second["elements"].append(element)
    graphic = deepcopy(template)
    graphic.update(id="cena2-haste", role="graphic", related_element_ids=["cena2-recording"], beats=canonical)
    second["elements"].append(graphic)
    second["video_layout"].update(
        video_element_id="cena2-recording",
        brand_element_id="cena2-logo",
        text_element_ids=["cena2-momento", "cena2-cta"],
        cta_element_id="cena2-cta",
    )
    data["motion_plan"].update(duration_ms=11200, scenes=[first, second])
    if offender:
        with pytest.raises(AuthError, match="^MOTION_VIDEO_KINETIC_TEXT_REQUIRED$"):
            validate_video_reel(artifact(data), CTX, asset_ids=ASSETS)
    else:
        validate_motion_plan(artifact(data), CTX, duration_ms=11200, asset_ids=ASSETS)


@pytest.mark.parametrize("version", [16, 17, 18])
def test_previous_replay_keeps_the_captured_guidance_and_repertoire(version):
    from app.services.motion_skills import _SKILLS, load_motion_skill

    body = natural_body(repertoire_id=None)
    previous = capture_motion_guidance(body)
    previous.pop("video_edit_contract")
    previous["repertoire"] = capture_repertoire("business-video-reel-v2")
    identifier = f"instagram-reel-video-v{version}"
    digest = _SKILLS[identifier][1]
    previous["skill"] = {
        "id": identifier,
        "sha256": digest,
        "instructions": load_motion_skill(identifier, digest, "reel"),
    }
    assert capture_motion_guidance(body, previous=previous) == previous
    assert previous["repertoire"] == capture_repertoire("business-video-reel-v2")
