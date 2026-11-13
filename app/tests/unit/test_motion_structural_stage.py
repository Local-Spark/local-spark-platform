"""The v3 stage is code. These tests do not render or spend."""

import struct
import zlib
from types import SimpleNamespace

import pytest

from app.services.motion_structural_floor import FLOOR_VERSION, evaluate_structural_floor
from app.services.motion_structural_stage import (
    _paeth,
    assign_structure,
    assignment_context,
    compose_structural_stage,
    decode_png_rgb,
    duck_for_speech,
    measure_subject_rect,
    prove_beat_pixels,
    prove_storyboard_frames,
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


def chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def encode_png(width: int, height: int, pixels: bytes, png_filter: int = 0, channels: int = 3) -> bytes:
    raw = b""
    previous = bytearray(width * channels)
    for y in range(height):
        row = bytearray(pixels[y * width * channels : (y + 1) * width * channels])
        stored = bytearray(row)
        if png_filter == 1:
            for index in range(width * channels):
                left = row[index - channels] if index >= channels else 0
                stored[index] = (row[index] - left) & 255
        elif png_filter == 2:
            for index in range(width * channels):
                stored[index] = (row[index] - previous[index]) & 255
        elif png_filter == 3:
            for index in range(width * channels):
                left = row[index - channels] if index >= channels else 0
                stored[index] = (row[index] - ((left + previous[index]) // 2)) & 255
        elif png_filter == 4:
            for index in range(width * channels):
                left = row[index - channels] if index >= channels else 0
                up_left = previous[index - channels] if index >= channels else 0
                estimate = left + previous[index] - up_left
                predictor = left
                if abs(estimate - previous[index]) < abs(estimate - left):
                    predictor = previous[index]
                if abs(estimate - up_left) < abs(estimate - predictor):
                    predictor = up_left
                stored[index] = (row[index] - predictor) & 255
        raw += bytes([png_filter]) + bytes(stored)
        previous = row
    color = 2 if channels == 3 else 6
    header = struct.pack(">IIBBBBB", width, height, 8, color, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def test_stage_replaces_model_html_only_when_v3_is_selected():
    plan = SimpleNamespace(scenes=(scene(("ellipse_to_glyph",)), scene((), "", "shape")))
    page, code = compose_structural_stage(plan, "assets/source.mp4")
    assert 'data-stage="media"' in page
    assert 'data-mechanism="ellipse_to_glyph"' in page
    assert "MechanismsV1.seek" in code
    assert "Café" in page
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
    spoken = {
        "speech_result": {
            "cues": [
                {"text": "pausa", "start_ms": 100, "end_ms": 400},
                {"text": " ", "start_ms": 1500, "end_ms": 1800},
            ]
        }
    }
    later = scene((), "fora", "text")
    later.start_ms, later.end_ms = 1400, 2000
    composition.motion_plan = SimpleNamespace(scenes=(scene(("ellipse_to_glyph",)), later))
    staged = stage_if_structural(composition, {"structural_floor": FLOOR_VERSION, **spoken}, (video,))
    assert staged.update["html"].count("assets/clip.mp4") == 2
    assert "pausa" in staged.update["html"]
    assert "fora" in staged.update["html"]


def test_structure_is_chosen_from_speech_without_the_model():
    assigned = assign_structure(2, [{"text": "pausa"}])
    assert evaluate_structural_floor(assigned) == ()
    assert [beat["scale"] for beat in assigned["beats"]] == ["macro", "medium", "card"]
    assert assigned["stage_beats"][0]["text"] == "pausa"
    plan = SimpleNamespace(duration_ms=9000, scenes=())
    assert assignment_context({}, plan) is not None and "structural_assignment" not in assignment_context({}, plan)
    context = {
        "structural_floor": FLOOR_VERSION,
        "speech_result": {"cues": [{"text": "pausa", "start_ms": 0, "end_ms": 10}]},
    }
    owned = assignment_context(context, plan)
    assert owned["structural_assignment"]["beats"][0]["role"] == "establish"
    assert assignment_context(context, None) is context
    assert assignment_context(context, SimpleNamespace(duration_ms="9000")) is context
    page, _code = compose_structural_stage(plan, "assets/source.mp4", context["speech_result"]["cues"])
    assert page.count("data-mechanism=") == 3
    width = height = 20
    pixels = bytearray(width * height * 3)
    for y in range(8, 14):
        for x in range(8, 14):
            pixels[(y * width + x) * 3] = 255
    png = encode_png(width, height, bytes(pixels))
    rect = measure_subject_rect((SimpleNamespace(png=png),))
    assert rect is not None and rect[2] < 0.8
    assert measure_subject_rect(()) is None
    assert measure_subject_rect((SimpleNamespace(png=b"\x89PNG\r\n\x1a\nnot"),)) is None
    flat = encode_png(width, height, bytes(width * height * 3))
    assert measure_subject_rect((SimpleNamespace(png=flat),)) is None
    rgb, decoded_width, decoded_height = decode_png_rgb(png)
    assert (decoded_width, decoded_height, len(rgb)) == (width, height, width * height * 3)
    decode_png_rgb(encode_png(4, 2, bytes([index % 256 for index in range(4 * 2 * 3)]), 1))
    decode_png_rgb(encode_png(4, 2, bytes([index % 256 for index in range(4 * 2 * 3)]), 2))
    decode_png_rgb(encode_png(4, 2, bytes([index % 256 for index in range(4 * 2 * 3)]), 3))
    decode_png_rgb(encode_png(4, 2, bytes([80, 10, 10] * 8), 4))
    rgba = bytes([255, 0, 0, 128] * 4)
    decode_png_rgb(encode_png(2, 2, rgba, channels=4))
    assert _paeth(5, 0, 0) == 5 and _paeth(0, 5, 0) == 5 and _paeth(0, 10, 5) == 5
    with pytest.raises(ValueError, match="STRUCTURAL_FRAME_INVALID"):
        decode_png_rgb(b"nope")
    bad = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 0, 0, 0, 0))
    with pytest.raises(ValueError, match="STRUCTURAL_FRAME_INVALID"):
        decode_png_rgb(bad)
    broken = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 40) + b"IHDR"
    with pytest.raises(ValueError, match="STRUCTURAL_FRAME_INVALID"):
        decode_png_rgb(broken)
    header = struct.pack(">IIBBBBB", 2, 1, 8, 2, 0, 0, 0)
    text_chunk = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"tEXt", b"a\x00b")
        + chunk(b"IDAT", zlib.compress(bytes([0, 1, 2, 3, 4, 5, 6])))
        + chunk(b"IEND", b"")
    )
    decode_png_rgb(text_chunk)
    corrupt = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", b"not-zlib") + chunk(b"IEND", b"")
    with pytest.raises(zlib.error):
        decode_png_rgb(corrupt)
    assert measure_subject_rect((SimpleNamespace(png=corrupt),)) is None
    unknown = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(bytes([5, 1, 2, 3, 4, 5, 6])))
        + chunk(b"IEND", b"")
    )
    with pytest.raises(ValueError, match="STRUCTURAL_FRAME_INVALID"):
        decode_png_rgb(unknown)
    audio = {"tracks": [{"role": "music"}, {"role": "original"}], "ducking": None}
    context = {"structural_floor": FLOOR_VERSION, "speech_result": {"cues": [{"start_ms": 0, "end_ms": 10}]}}
    assert duck_for_speech(audio, context)["ducking"]["ratio"] == 8
    assert duck_for_speech(audio, {}) is audio
    assert duck_for_speech(audio, {"structural_floor": FLOOR_VERSION}) is audio
    assert duck_for_speech(None, context) is None
    assert duck_for_speech({"tracks": [{"role": "original"}]}, context)["tracks"][0]["role"] == "original"
    assert duck_for_speech({**audio, "ducking": {"ratio": 2}}, context)["ducking"]["ratio"] == 2
    start = {"scene_id": "abertura", "kind": "structural_start"}
    end = {"scene_id": "abertura", "kind": "structural_end"}
    frames = (SimpleNamespace(png=flat), SimpleNamespace(png=flat))
    with pytest.raises(ValueError, match="STRUCTURAL_MEDIA_UNCHANGED"):
        prove_storyboard_frames((start, end), frames)
    with pytest.raises(ValueError, match="STRUCTURAL_FRAME_INVALID"):
        prove_beat_pixels(b"123", b"123", 4, 1)
    bright = bytearray(pixels)
    for index in range(width * 3, width * height * 3):
        bright[index] = 200
    prove_storyboard_frames(
        (start, end),
        (SimpleNamespace(png=flat), SimpleNamespace(png=encode_png(width, height, bytes(bright)))),
    )
    with pytest.raises(ValueError, match="STRUCTURAL_BEAT_UNPROVEN"):
        prove_storyboard_frames((start,), (SimpleNamespace(png=flat),))
    with pytest.raises(ValueError, match="STRUCTURAL_FRAME_INVALID"):
        prove_storyboard_frames((start, end), (SimpleNamespace(png=b"nope"), SimpleNamespace(png=flat)))
    prove_storyboard_frames(({"scene_id": "abertura", "kind": "card"},), (SimpleNamespace(png=flat),))
    with pytest.raises(ValueError, match="STRUCTURAL_BEAT_UNPROVEN"):
        prove_storyboard_frames(({"scene_id": "abertura", "kind": "structural_end"},), (SimpleNamespace(png=flat),))
    mid = {"scene_id": "abertura", "kind": "structural_mid"}
    prove_storyboard_frames(
        (mid, end),
        (SimpleNamespace(png=flat), SimpleNamespace(png=encode_png(width, height, bytes(bright)))),
    )
