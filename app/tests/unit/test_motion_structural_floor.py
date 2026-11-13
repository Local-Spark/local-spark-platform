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
