"""The v3 stage is code. These tests do not render or spend."""

from types import SimpleNamespace

import pytest

from app.services.motion_structural_floor import FLOOR_VERSION
from app.services.motion_structural_stage import (
    compose_structural_stage,
    prove_beat_pixels,
    source_asset_id,
    stage_if_structural,
)


def scene(mechanism=(), text="Café", kind="text"):
    return SimpleNamespace(
        id="abertura",
        message="mensagem",
        start_ms=0,
        end_ms=1000,
        structural_scale="macro",
        elements=(SimpleNamespace(kind=kind, text=text, mechanism_ids=mechanism),),
    )


def test_stage_replaces_model_html_only_when_v3_is_selected():
    plan = SimpleNamespace(scenes=(scene(("ellipse_to_glyph",)), scene((), "", "shape")))
    page, code = compose_structural_stage(plan, "assets/source.mp4")
    assert 'data-stage="media"' in page
    assert 'data-mechanism="ellipse_to_glyph"' in page
    assert "MechanismsV1.seek" in code
    assert "<script" not in page.split("structural-beats")[0] or "Café" in page
    assert source_asset_id(()) == "assets/source.mp4"
    video = SimpleNamespace(id="assets/clip.mp4", mime_type="video/mp4")
    assert source_asset_id((SimpleNamespace(id="assets/a.png", mime_type="image/png"), video)) == "assets/clip.mp4"

    class Composition:
        def __init__(self):
            self.motion_plan = plan

        def model_copy(self, update):
            self.update = update
            return self

    composition = Composition()
    assert stage_if_structural(composition, {}, ()) is composition
    assert (
        stage_if_structural(SimpleNamespace(motion_plan=None), {"structural_floor": FLOOR_VERSION}, ()).motion_plan
        is None
    )
    staged = stage_if_structural(composition, {"structural_floor": FLOOR_VERSION}, (video,))
    assert staged.update["html"].count("assets/clip.mp4") == 2
    assert "mensagem" in staged.update["html"]


def test_pixel_proof_rejects_an_unchanged_media_rectangle():
    width, height = 4, 4
    still = bytes(width * height * 3)
    with pytest.raises(ValueError, match="STRUCTURAL_FRAME_INVALID"):
        prove_beat_pixels(still, still[:-1], width, height)
    with pytest.raises(ValueError, match="STRUCTURAL_FRAME_INVALID"):
        prove_beat_pixels(still, still, 1, 4)
    with pytest.raises(ValueError, match="STRUCTURAL_MEDIA_UNCHANGED"):
        prove_beat_pixels(still, still, width, height)
    changed = bytearray(still)
    for index in range(width * 3, width * 3 * 3):
        changed[index] = 40
    prove_beat_pixels(still, bytes(changed), width, height)
