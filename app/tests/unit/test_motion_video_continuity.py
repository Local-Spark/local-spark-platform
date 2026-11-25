"""Structural continuity fills beat holes without inventing creative layers."""

from copy import deepcopy

import pytest

from app.schemas.motion_plan import MotionPlan
from app.services.motion_video_capabilities import validate_development
from app.services.motion_video_continuity import (
    maybe_normalize_video_html,
    maybe_normalize_video_plan,
    normalize_video_html,
    normalize_video_motion_plan,
    normalize_video_scene_init,
)


def _beat(phase: str, start: int, end: int, a: str, z: str) -> dict:
    return {
        "phase": phase,
        "start_ms": start,
        "end_ms": end,
        "start_state": a,
        "end_state": z,
        "trajectory": phase,
        "curve": {"kind": "linear", "parameters": []},
    }


def gapped_plan() -> dict:
    bar = {
        "id": "s0-bar",
        "role": "graphic",
        "asset_id": None,
        "purpose": "accent",
        "related_element_ids": ["s0-rec"],
        "coordination": "pulse",
        "beats": [
            _beat("enter", 0, 400, '{"x":0,"y":0,"opacity":0}', '{"x":0,"y":0,"opacity":1}'),
            _beat("transform", 2000, 3000, '{"x":0,"y":0,"opacity":1}', '{"x":60,"y":0,"opacity":1}'),
        ],
    }
    photo = {
        "id": "s1-photo",
        "role": "image",
        "asset_id": "assets/photo-demo.png",
        "purpose": "pause",
        "related_element_ids": ["s1-rec"],
        "coordination": "show",
        "beats": [_beat("enter", 3000, 3800, '{"x":0,"y":24,"opacity":0}', '{"x":0,"y":0,"opacity":1}')],
    }
    bar2 = {
        "id": "s1-bar",
        "role": "graphic",
        "asset_id": None,
        "purpose": "accent",
        "related_element_ids": ["s1-rec"],
        "coordination": "hold",
        "beats": [_beat("hold", 3000, 6000, '{"x":60,"y":0,"opacity":1}', '{"x":60,"y":0,"opacity":1}')],
    }
    line = {
        "id": "s0-line",
        "role": "text",
        "asset_id": None,
        "purpose": "line",
        "related_element_ids": ["s0-bar"],
        "coordination": "read",
        "beats": [
            _beat("enter", 0, 400, '{"x":0,"y":12,"opacity":0}', '{"x":0,"y":0,"opacity":1}'),
            _beat("transform", 400, 800, '{"x":0,"y":0,"opacity":1}', '{"x":4,"y":0,"opacity":1}'),
            _beat("exit", 2600, 3000, '{"x":4,"y":0,"opacity":1}', '{"x":4,"y":0,"opacity":0}'),
        ],
    }
    cta = {
        "id": "s1-cta",
        "role": "text",
        "asset_id": None,
        "purpose": "cta",
        "related_element_ids": ["s1-photo"],
        "coordination": "invite",
        "beats": [
            _beat("enter", 3000, 3400, '{"x":0,"y":12,"opacity":0}', '{"x":0,"y":0,"opacity":1}'),
            _beat("transform", 3400, 3800, '{"x":0,"y":0,"opacity":1}', '{"x":4,"y":0,"opacity":1}'),
            _beat("exit", 5600, 6000, '{"x":4,"y":0,"opacity":1}', '{"x":4,"y":0,"opacity":0}'),
        ],
    }

    def shell(
        prefix: str,
        start: int,
        end: int,
        texts: list,
        layers: list,
        extras: list,
        purpose: str,
        cta_id: str | None,
    ):
        rec = f"{prefix}-rec"
        logo = f"{prefix}-logo"
        return {
            "id": prefix,
            "start_ms": start,
            "end_ms": end,
            "message": "pause",
            "transition_to_next": "end",
            "elements": [
                {
                    "id": rec,
                    "role": "video",
                    "asset_id": "assets/source.mp4",
                    "purpose": "source",
                    "related_element_ids": [],
                    "coordination": "hold",
                    "beats": [_beat("hold", start, end, "visible", "visible")],
                },
                {
                    "id": logo,
                    "role": "image",
                    "asset_id": "assets/logo.png",
                    "purpose": "brand",
                    "related_element_ids": [],
                    "coordination": "hold",
                    "beats": [
                        _beat("hold", start, end, '{"x":0,"y":0,"opacity":1}', '{"x":0,"y":0,"opacity":1}')
                    ],
                },
                *texts,
                *extras,
            ],
            "video_layout": {
                "mode": "cover",
                "video_element_id": rec,
                "brand_element_id": logo,
                "text_element_ids": [t["id"] for t in texts],
                "cta_element_id": cta_id,
                "edit": {
                    "source_in_ms": start,
                    "source_out_ms": end,
                    "purpose": purpose,
                    "transition": "cut",
                    "intent": "passagem",
                    "crop_from": {"scale": 1.0, "x": 0.0, "y": 0.0},
                    "crop_to": {"scale": 1.06, "x": 0.0, "y": 0.0},
                },
                "design": {
                    "version": "video-design-v2",
                    "viewport": {"x": 0, "y": 0, "width": 1, "height": 1},
                    "layers": layers,
                    "transition_reason": "passagem",
                },
            },
        }

    return {
        "version": "motion-plan-v1",
        "identity_source": "business_kit",
        "duration_ms": 6000,
        "scenes": [
            shell(
                "s0",
                0,
                3000,
                [line],
                [
                    {
                        "element_id": "s0-bar",
                        "box": {"x": 0.1, "y": 0.8, "width": 0.03, "height": 0.03},
                        "z_index": 14,
                        "shape": "bar",
                        "color": "#c8a070",
                    }
                ],
                [bar],
                "hook",
                None,
            ),
            shell(
                "s1",
                3000,
                6000,
                [cta],
                [
                    {
                        "element_id": "s1-photo",
                        "box": {"x": 0.2, "y": 0.25, "width": 0.6, "height": 0.4},
                        "z_index": 12,
                        "shape": "rounded",
                        "color": "#00000000",
                    },
                    {
                        "element_id": "s1-bar",
                        "box": {"x": 0.1, "y": 0.8, "width": 0.03, "height": 0.03},
                        "z_index": 14,
                        "shape": "bar",
                        "color": "#c8a070",
                    },
                ],
                [photo, bar2],
                "invitation",
                "s1-cta",
            ),
        ],
    }


def test_normalize_fills_gaps_wires_video_and_floors_bar_width():
    plan = normalize_video_motion_plan(gapped_plan())
    scene0, scene1 = plan["scenes"]
    assert "s0-rec" in next(e for e in scene0["elements"] if e["id"] == "s0-line")["related_element_ids"]
    assert "s1-rec" in next(e for e in scene1["elements"] if e["id"] == "s1-cta")["related_element_ids"]
    bar_beats = next(e for e in scene0["elements"] if e["id"] == "s0-bar")["beats"]
    assert bar_beats[0]["start_ms"] == 0 and bar_beats[-1]["end_ms"] == 3000
    assert any(b["phase"] == "hold" and b["start_ms"] == 400 for b in bar_beats)
    cta_beats = next(e for e in scene1["elements"] if e["id"] == "s1-cta")["beats"]
    assert any(b["phase"] == "hold" and b["end_ms"] - b["start_ms"] >= 1500 for b in cta_beats)
    photo_beats = next(e for e in scene1["elements"] if e["id"] == "s1-photo")["beats"]
    assert photo_beats[-1]["end_ms"] == 6000
    assert scene0["video_layout"]["design"]["layers"][0]["box"]["width"] == pytest.approx(0.04)
    photo_box = scene1["video_layout"]["design"]["layers"][0]["box"]
    assert photo_box["width"] >= 0.5 and photo_box["height"] >= 0.5
    validate_development(MotionPlan.model_validate(plan), unlocked=True)


def test_normalize_skipped_without_design_schema():
    original = gapped_plan()
    assert maybe_normalize_video_plan(deepcopy(original), {}) == original


def test_normalize_video_html_clears_cream_document_chrome():
    html = (
        '<!doctype html><html style="background:#FFF8EC"><body style="margin:0;background:#FFF8EC">'
        '<main style="background:#FFF8EC;overflow:hidden">'
        '<div style="background:rgba(0,0,0,0.78)"><div id="t">Oi</div></div>'
        "</main></body></html>"
    )
    out = normalize_video_html(html)
    assert "background:#FFF8EC" not in out
    assert out.count("background:transparent") >= 3
    assert "overflow:hidden" not in out
    assert out.count("overflow:visible") >= 3
    assert "background:rgba(0,0,0,0.78)" in out


def test_maybe_normalize_video_html_requires_video_plan():
    cream = '<body style="background:#FFF8EC"></body>'
    assert maybe_normalize_video_html(cream, {"scenes": []}) == cream
    cleared = maybe_normalize_video_html(cream, gapped_plan())
    assert "background:transparent" in cleared and "#FFF8EC" not in cleared


def test_normalize_video_scene_init_drops_runtime_owned_layer_control():
    plan = gapped_plan()
    init = (
        "const tracks=[{id:'s0-line'},{id:'s0-bar'}];"
        "[['s0-bar',1]].forEach(([id,i])=>{const node=document.getElementById(id);"
        "if(node)node.style.display=i===index?'block':'none';});"
        "timeline=MotionV1.timeline(tracks);"
    )
    out = normalize_video_scene_init(init, plan)
    assert "[['s0-bar',1]].forEach" not in out
    assert "MotionV1.timeline(tracks.filter" in out
    assert '"s0-bar"' in out
