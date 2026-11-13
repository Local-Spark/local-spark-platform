"""The v3 floor rejects caption-on-photo plans and stays off unless selected."""

from app.services.motion_structural_floor import (
    ENABLED_BY_DEFAULT,
    FLOOR_VERSION,
    evaluate_structural_floor,
    structural_floor_enabled,
)


def _beat(**overrides):
    base = {
        "t_in_ms": 0,
        "t_out_ms": 1500,
        "role": "establish",
        "scale": "medium",
        "protagonist": "gesture",
        "copy": "",
        "anchor": {"kind": "none"},
        "mechanism": [],
        "hold_ms": 0,
        "crop_changes_inside": False,
        "text_outside_media": False,
    }
    base.update(overrides)
    return base


def _passing_service_piece():
    """A non-cafe business: a workshop tool, not a cup. Same gates."""
    return {
        "duration_ms": 10000,
        "letterbox": "kit_color",
        "third_party_mark_legible": False,
        "audio_trimmed": False,
        "spoken_phrases": ["Olha o corte", "Aqui perto"],
        "beats": [
            _beat(
                t_in_ms=0,
                t_out_ms=2000,
                role="establish",
                scale="macro",
                protagonist="product",
                crop_changes_inside=True,
            ),
            _beat(
                t_in_ms=2000,
                t_out_ms=4500,
                role="extract",
                scale="medium",
                protagonist="type",
                copy="Olha o corte",
                anchor={"kind": "object_edge", "object": "serra"},
                mechanism=["axis_type_in"],
                hold_ms=800,
                hero_height_ratio=0.22,
                contrast_ratio=5.1,
                moves_during_hold=False,
            ),
            _beat(
                t_in_ms=4500,
                t_out_ms=7000,
                role="extract",
                scale="medium",
                protagonist="gesture",
                crop_changes_inside=True,
            ),
            _beat(
                t_in_ms=7000,
                t_out_ms=10000,
                role="invite",
                scale="card",
                protagonist="cta",
                copy="Aqui perto",
                anchor={"kind": "object_edge"},
                mechanism=["plate_cta"],
                hold_ms=1200,
                cta_plate=True,
                cta_outside_media=False,
                crop_changes_inside=True,
            ),
        ],
    }


def _rejected_cafe_piece():
    """Shape of the 13/11 reel: one scale, type in the margin, underlined CTA."""
    return {
        "duration_ms": 11200,
        "letterbox": "document_margin",
        "third_party_mark_legible": True,
        "audio_trimmed": False,
        "spoken_phrases": ["Feche os olhos", "Sinta o cheiro", "Pausa"],
        "beats": [
            _beat(
                t_in_ms=0,
                t_out_ms=11200,
                role="establish",
                scale="medium",
                protagonist="type",
                copy="Pausa",
                support_copy="Um momento seu.",
                anchor={"kind": "none"},
                mechanism=[],
                hold_ms=0,
                hero_height_ratio=0.08,
                contrast_ratio=2.0,
                text_outside_media=True,
                cta_plate=False,
            )
        ],
    }


def test_floor_is_opt_in():
    assert ENABLED_BY_DEFAULT is False
    assert structural_floor_enabled(None) is False
    assert structural_floor_enabled("motion-production-quality-v2") is False
    assert structural_floor_enabled(FLOOR_VERSION) is True


def test_service_piece_passes_without_cafe_specific_rules():
    assert evaluate_structural_floor(_passing_service_piece()) == ()


def test_rejected_cafe_shape_fails_the_product_gates():
    failed = set(evaluate_structural_floor(_rejected_cafe_piece()))
    assert {"scale_count", "margin_ban", "third_party_mark", "copy_coverage", "anchor_required"} <= failed


def test_short_piece_needs_two_scales_and_skips_role_sequence():
    piece = {
        "duration_ms": 4000,
        "letterbox": "kit_color",
        "beats": [
            _beat(t_in_ms=0, t_out_ms=2000, scale="macro", protagonist="product"),
            _beat(t_in_ms=2000, t_out_ms=4000, scale="medium", protagonist="gesture"),
        ],
    }
    assert evaluate_structural_floor(piece) == ()


def test_dead_hold_copy_hold_contrast_mechanism_and_cta():
    piece = _passing_service_piece()
    piece["beats"][0]["crop_changes_inside"] = False
    piece["beats"][0]["t_out_ms"] = 3000
    piece["spoken_phrases"] = ["frase sem beat"]
    piece["beats"][1]["hold_ms"] = 100
    assert "no_dead_hold" in evaluate_structural_floor(piece)
    assert "copy_coverage" in evaluate_structural_floor(piece)
    assert "hold_legibility" in evaluate_structural_floor(piece)

    piece["beats"][0]["crop_changes_inside"] = True
    piece["beats"][0]["t_out_ms"] = 2000
    piece["spoken_phrases"] = ["Olha o corte", "Aqui perto"]
    piece["beats"][1]["hold_ms"] = 800
    piece["beats"][1]["moves_during_hold"] = True
    assert "hold_legibility" in evaluate_structural_floor(piece)

    piece["beats"][1]["moves_during_hold"] = False
    piece["beats"][1]["hero_height_ratio"] = 0.1
    assert "hold_legibility" in evaluate_structural_floor(piece)

    piece["beats"][1]["hero_height_ratio"] = 0.22
    piece["beats"][1]["contrast_ratio"] = 2
    assert "contrast" in evaluate_structural_floor(piece)

    piece["beats"][1]["contrast_ratio"] = 5
    piece["beats"][1]["mechanism"] = []
    assert "mechanism_known" in evaluate_structural_floor(piece)
    piece["beats"][1]["mechanism"] = ["not-a-card"]
    assert "mechanism_known" in evaluate_structural_floor(piece)

    piece["beats"][1]["mechanism"] = ["axis_type_in"]
    piece["beats"][3]["cta_plate"] = False
    assert "cta_block" in evaluate_structural_floor(piece)

    piece["beats"][3]["cta_plate"] = True
    piece["beats"][3]["cta_outside_media"] = True
    assert "cta_block" in evaluate_structural_floor(piece)

    piece["beats"][3]["cta_outside_media"] = False
    piece["beats"][3]["hold_ms"] = 100
    assert "cta_block" in evaluate_structural_floor(piece)


def test_role_sequence_and_text_in_the_margin():
    piece = _passing_service_piece()
    for beat in piece["beats"]:
        beat["role"] = "establish"
    assert "role_sequence" in evaluate_structural_floor(piece)

    piece = _passing_service_piece()
    piece["letterbox"] = "document_margin"
    piece["beats"][2]["text_outside_media"] = True
    failed = evaluate_structural_floor(piece)
    assert failed.count("margin_ban") == 1
    assert "margin_ban" in failed


def test_audio_trim_covers_missing_phrases_and_empty_plan_fails_closed():
    piece = _passing_service_piece()
    piece["spoken_phrases"] = ["nao esta na tela"]
    piece["audio_trimmed"] = True
    assert evaluate_structural_floor(piece) == ()
    assert "scale_count" in evaluate_structural_floor({})


def test_real_plan_is_rejected_or_admitted_before_render():
    from types import SimpleNamespace

    from app.services.motion_structural_floor import StructuralFloorRejected, enforce_structural_floor, view_from_plan

    def beat(phase: str, start: int, end: int):
        return SimpleNamespace(phase=phase, start_ms=start, end_ms=end)

    def text(purpose: str, mechanisms: tuple[str, ...]):
        return SimpleNamespace(
            role="text",
            purpose=purpose,
            related_element_ids=("clip",),
            mechanism_ids=mechanisms,
            hero_height_ratio=0.22,
            contrast_ratio=5.0,
            text_outside_media=False,
            beats=(beat("enter", 0, 400), beat("hold", 400, 1600)),
        )

    def scene(start, end, scale, role, elements):
        return SimpleNamespace(
            start_ms=start,
            end_ms=end,
            structural_scale=scale,
            structural_role=role,
            elements=elements,
        )

    video = SimpleNamespace(role="video", beats=(beat("hold", 0, 1500),))
    admitted = SimpleNamespace(
        duration_ms=8000,
        scenes=(
            scene(0, 2000, "macro", None, (SimpleNamespace(role="graphic", beats=()),)),
            scene(2000, 4000, "medium", None, (video,)),
            scene(4000, 6000, "medium", "extract", (text("Corte limpo", ("axis_type_in",)),)),
            scene(6000, 8000, "card", "invite", (text("Saiba mais", ("plate_cta",)),)),
        ),
    )
    assert evaluate_structural_floor(view_from_plan(admitted)) == ()
    enforce_structural_floor(admitted, {"structural_floor": FLOOR_VERSION})
    enforce_structural_floor(admitted, {})

    rejected = SimpleNamespace(
        duration_ms=11200,
        scenes=(
            scene(
                0,
                11200,
                None,
                None,
                (
                    SimpleNamespace(
                        role="text",
                        purpose="Pausa",
                        related_element_ids=(),
                        mechanism_ids=(),
                        hero_height_ratio=None,
                        contrast_ratio=None,
                        text_outside_media=True,
                        beats=(beat("enter", 0, 11200),),
                    ),
                ),
            ),
        ),
    )
    assert "scale_count" in evaluate_structural_floor(view_from_plan(rejected))
    try:
        enforce_structural_floor(rejected, {"structural_floor": FLOOR_VERSION})
    except StructuralFloorRejected:
        assert True
    else:
        raise AssertionError("expected rejection")
    try:
        enforce_structural_floor(None, {"structural_floor": FLOOR_VERSION})
    except StructuralFloorRejected:
        assert True
    else:
        raise AssertionError("expected rejection")


def test_execution_requires_stage_and_declared_mechanism():
    from types import SimpleNamespace

    from app.services.motion_structural_floor import (
        StructuralFloorRejected,
        structural_sample_points,
        structural_storyboard,
        uses_structural_runtime,
        validate_structural_execution,
    )

    assert uses_structural_runtime("window.seek=async(ms)=>{}") is False
    assert uses_structural_runtime("window.seek=async(ms)=>{StructuralFloorV1.apply(ms)}") is True
    assert structural_sample_points(SimpleNamespace(start_ms=0, end_ms=0)) == (("start", 0), ("mid", 0), ("end", 0))
    scene = SimpleNamespace(id="s", message="m", start_ms=0, end_ms=1000)
    moments = ({"frame_index": 0, "scene_id": "s"},)
    assert structural_storyboard(moments, SimpleNamespace(scenes=(scene,)), {}) == moments
    sampled = structural_storyboard(moments, SimpleNamespace(scenes=(scene,)), {"structural_floor": FLOOR_VERSION})
    assert any(item.get("kind") == "structural_mid" for item in sampled)
    assert structural_storyboard(moments, None, {"structural_floor": FLOOR_VERSION}) == moments

    element = SimpleNamespace(mechanism_ids=("ellipse_to_glyph",), text_outside_media=False)
    plan = SimpleNamespace(scenes=(SimpleNamespace(elements=(element,)),))
    html = '<div data-stage="media"><p data-mechanism="ellipse_to_glyph"></p></div>'
    code = "window.seek=async(ms)=>{StructuralFloorV1.apply(ms)}"
    composition = SimpleNamespace(html=html, scene_init=code, motion_plan=plan)
    validate_structural_execution(composition, {})
    validate_structural_execution(composition, {"structural_floor": FLOOR_VERSION})
    validate_structural_execution(
        SimpleNamespace(html=None, scene_init=None, motion_plan=None), {"structural_floor": FLOOR_VERSION}
    )

    def fails(**kwargs):
        try:
            validate_structural_execution(SimpleNamespace(**kwargs), {"structural_floor": FLOOR_VERSION})
        except StructuralFloorRejected:
            return
        raise AssertionError("execution should fail")

    fails(html="<div></div>", scene_init=code, motion_plan=plan)
    fails(html=html, scene_init="window.seek=async(ms)=>{}", motion_plan=plan)
    outside = SimpleNamespace(mechanism_ids=("ellipse_to_glyph",), text_outside_media=True)
    fails(html=html, scene_init=code, motion_plan=SimpleNamespace(scenes=(SimpleNamespace(elements=(outside,)),)))
    empty = SimpleNamespace(mechanism_ids=(), text_outside_media=False)
    fails(html=html, scene_init=code, motion_plan=SimpleNamespace(scenes=(SimpleNamespace(elements=(empty,)),)))
    unknown = SimpleNamespace(mechanism_ids=("not-real",), text_outside_media=False)
    fails(html=html, scene_init=code, motion_plan=SimpleNamespace(scenes=(SimpleNamespace(elements=(unknown,)),)))
    missing = SimpleNamespace(mechanism_ids=("plate_cta",), text_outside_media=False)
    fails(html=html, scene_init=code, motion_plan=SimpleNamespace(scenes=(SimpleNamespace(elements=(missing,)),)))


