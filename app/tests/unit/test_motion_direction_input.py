"""Motion input keeps authorizations outside the builder and never calls models."""

import json
from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.brand_kits import BrandKitOverrides
from app.schemas.editorial_context import ConfirmedFact, EditorialPreferences
from app.schemas.motion import MediaSource
from app.services.auth import AuthError
from app.services.motion_direction_input import (
    MotionDirectionInputSnapshot,
    MotionFrameEvidence,
    MotionInputMedia,
    MotionTranscriptEvidence,
    build_motion_direction_input,
)
from app.services.motion_styles import list_motion_styles
from app.services.reference_generation_context import REFERENCE_CREATIVE_RULE, read_generation_snapshot
from app.tests.unit.test_reference_generation_context import context as reference_context


def kit(logo=None):
    return BrandKitOverrides.model_validate(
        {
            "palette": {"primary": "#244739", "background": "#F5F0E7", "accent": "#BB7A48"},
            "heading_font": "DejaVu Serif",
            "body_font": "DejaVu Sans",
            "brand_name": "Cafeteria fictícia",
            "tagline": "Pausa",
            "cta": "Venha conhecer",
            "logo_asset_id": logo,
            "formats": {
                "feed": {"layout": "photo_focus", "image_position": "center"},
                "story": {"layout": "photo_focus", "image_position": "center"},
                "reel_cover": {"layout": "photo_focus", "image_position": "center"},
            },
        }
    )


def video(*, audio=True):
    return MotionInputMedia(
        media=MediaSource(id=uuid4(), kind="video", origin="customer_recording", duration_ms=11180, has_audio=audio),
        sha256="a" * 64,
        frames=(MotionFrameEvidence(id=uuid4(), at_ms=2000, sha256="b" * 64),),
    )


def snapshot(*, fmt="reel", media=None, logo=None, references=None):
    return MotionDirectionInputSnapshot(
        format=fmt,
        request="Crie uma peça da cafeteria.",
        kit_id="cafe-pausas",
        kit_version=1,
        kit_sha256="c" * 64,
        kit=kit(logo),
        preferences=EditorialPreferences.model_validate(
            {
                "tone": "friendly",
                "business_terms": ["café"],
                "cta_destination": {"type": "order_link", "value": "https://example.invalid/?signed=secret"},
            }
        ),
        confirmed_facts=(
            ConfirmedFact(
                id=uuid4(),
                kind="product",
                statement="Café",
                source_detail="detalhe privado de origem",
                valid_until=date(2027, 1, 1),
            ),
        ),
        media=tuple(media or ()),
        references=references,
    )


@pytest.mark.parametrize("fmt", ["reel", "story_video", "carousel_motion"])
def test_builder_offers_all_verified_cards_without_choosing_or_sending(fmt):
    source = video()
    request = snapshot(fmt=fmt, media=(source,))
    prepared = build_motion_direction_input(request)
    assert prepared == build_motion_direction_input(request)
    data = json.loads(prepared.data_json)
    assert data["format"] == fmt and data["recording_required"] is False
    assert data["skill"]["id"].startswith("instagram-")
    assert [(x["id"], x["version"], x["sha256"]) for x in data["style_catalog"]] == [
        (style.id, style.version, style.sha256) for style in list_motion_styles()
    ]
    assert all(
        "path" not in origin and "ref" not in origin
        for item in data["style_catalog"]
        for origin in item["card"]["sources"]
    )
    assert "selected_style" not in data
    assert data["executor_capabilities"]["audio_plan"] is True
    assert data["executor_capabilities"]["audio"] is False
    assert data["media"][0]["frames"][0]["sha256"] == "b" * 64
    assert data["media_visibility"].startswith("identifiers and hashes only")
    assert "separadas" in prepared.instructions and "sem remover fala" in prepared.instructions
    assert REFERENCE_CREATIVE_RULE in prepared.instructions
    assert "source_detail" not in data["confirmed_facts"][0]
    assert "reference_search" not in data["preferences"] and "cta_destination" not in data["preferences"]
    assert "signed=secret" not in prepared.data_json and "detalhe privado de origem" not in prepared.data_json
    assert "Cafeteria fictícia" not in repr(prepared)


@pytest.mark.parametrize("fmt,required", [("reel", True), ("story_video", True), ("carousel_motion", False)])
def test_missing_recording_is_explicit_and_does_not_invent_media(fmt, required):
    data = json.loads(build_motion_direction_input(snapshot(fmt=fmt)).data_json)
    assert data["recording_required"] is required and data["media"] == []


def test_reference_projection_preserves_partial_status_without_internal_ids():
    raw = reference_context(status="partial")
    ref = read_generation_snapshot(raw)
    data = json.loads(build_motion_direction_input(snapshot(references=ref)).data_json)
    assert data["references"][0]["estado_analise"] == "partial"
    assert data["references"][0]["padroes"][0]["observacao"] == "Composições destacam o produto"
    assert raw["selected"][0]["reference_id"] not in json.dumps(data["references"])
    assert raw["learnings"][0]["analysis_id"] not in json.dumps(data["references"])


def test_transcription_and_frame_are_included_only_when_supplied():
    source = video()
    transcript = MotionTranscriptEvidence(text="Uma pausa.", review="unreviewed", alignment="none")
    source = source.model_copy(update={"transcript": transcript})
    result = json.loads(build_motion_direction_input(snapshot(media=(source,))).data_json)
    assert result["media"][0]["transcript"] == {"text": "Uma pausa.", "review": "unreviewed", "alignment": "none"}
    assert result["media"][0]["frames"][0]["at_ms"] == 2000
    no_evidence = source.model_copy(update={"transcript": None, "frames": ()})
    result = json.loads(build_motion_direction_input(snapshot(media=(no_evidence,))).data_json)
    assert result["media"][0]["transcript"] is None and result["media"][0]["frames"] == []


@pytest.mark.parametrize("logo_state", ["not_configured", "unavailable", "available"])
def test_logo_state_never_invents_an_unavailable_asset(logo_state):
    logo_id = None if logo_state == "not_configured" else uuid4()
    image = (
        MotionInputMedia(media=MediaSource(id=logo_id, kind="image", origin="asset"), sha256="a" * 64)
        if logo_state == "available"
        else None
    )
    data = json.loads(build_motion_direction_input(snapshot(logo=logo_id, media=(image,) if image else ())).data_json)
    assert data["kit"]["logo"]["state"] == logo_state
    assert ("source_id" in data["kit"]["logo"]) == (logo_state == "available")


@pytest.mark.parametrize(
    "kind", ["image_frames", "out_of_bounds", "duplicate_frame", "image_transcript", "silent_transcript"]
)
def test_media_evidence_must_match_source(kind):
    source = video()
    evidence = MotionFrameEvidence(id=uuid4(), at_ms=100, sha256="b" * 64)
    transcript = MotionTranscriptEvidence(text="Fala", review="unreviewed", alignment="none")
    if kind == "image_frames":
        data = {
            "media": MediaSource(id=uuid4(), kind="image", origin="asset"),
            "sha256": "a" * 64,
            "frames": (evidence,),
        }
    elif kind == "out_of_bounds":
        data = {
            "media": source.media,
            "sha256": source.sha256,
            "frames": (evidence.model_copy(update={"at_ms": 11180}),),
        }
    elif kind == "duplicate_frame":
        data = {"media": source.media, "sha256": source.sha256, "frames": (evidence, evidence)}
    elif kind == "image_transcript":
        data = {
            "media": MediaSource(id=uuid4(), kind="image", origin="asset"),
            "sha256": "a" * 64,
            "transcript": transcript,
        }
    else:
        data = {
            "media": source.media.model_copy(update={"has_audio": False}),
            "sha256": source.sha256,
            "transcript": transcript,
        }
    with pytest.raises(ValidationError):
        MotionInputMedia.model_validate(data)


@pytest.mark.parametrize(
    "case", ["duplicate_source", "two_recordings", "shared_frame", "missing_parent", "wrong_parent"]
)
def test_snapshot_source_and_derivative_identities_are_checked(case):
    first = video()
    second = video()
    if case == "duplicate_source":
        media = (first, first)
    elif case == "two_recordings":
        media = (first, second)
    elif case == "shared_frame":
        second = second.model_copy(
            update={"media": second.media.model_copy(update={"origin": "asset"}), "frames": first.frames}
        )
        media = (first, second)
    else:
        parent_id = uuid4()
        audio = MotionInputMedia(
            media=MediaSource(
                id=uuid4(), kind="audio", origin="asset", duration_ms=1000, derived_from_source_id=parent_id
            ),
            sha256="a" * 64,
        )
        if case == "missing_parent":
            media = (audio,)
        else:
            image = MotionInputMedia(media=MediaSource(id=parent_id, kind="image", origin="asset"), sha256="b" * 64)
            media = (audio, image)
    with pytest.raises(ValidationError):
        snapshot(media=media)


def test_audio_derivative_keeps_its_recording_identity():
    recording = video()
    audio = MotionInputMedia(
        media=MediaSource(
            id=uuid4(),
            kind="audio",
            origin="asset",
            duration_ms=1000,
            derived_from_source_id=recording.media.id,
        ),
        sha256="d" * 64,
    )
    data = json.loads(build_motion_direction_input(snapshot(media=(recording, audio))).data_json)
    assert data["media"][1]["media"]["derived_from_source_id"] == str(recording.media.id)


def test_mutated_invalid_snapshot_fails_without_leaking_private_data():
    source = video()
    bad = snapshot(media=(source,)).model_copy(update={"request": "\ud800"})
    with pytest.raises(AuthError, match="MOTION_DIRECTION_INPUT_INVALID") as exc:
        build_motion_direction_input(bad)
    assert "Cafeteria" not in str(exc.value)


def test_direction_schema_exposes_model_facing_units_and_cross_field_constraints():
    """The exported contract must convey rules JSON Schema cannot enforce itself."""
    prepared = build_motion_direction_input(snapshot())
    schema = json.loads(prepared.data_json)["proposed_response"]["direction_schema"]
    definitions = schema["$defs"]
    font = definitions["Typography"]["properties"]
    assert "pontos-base" in font["font_size"]["description"]
    assert "1280" in font["font_size"]["description"] and "250" in font["font_size"]["description"]
    assert all("pontos-base" in font[name]["description"] for name in ("line_height", "letter_spacing"))
    for layer in ("VisualSegment", "Caption"):
        description = definitions[layer]["properties"]["keyframes"]["description"]
        assert all(term in description for term in ("timeline.end_ms", "timeline.start_ms", "null"))
    easing = definitions["VisualKeyframe"]["properties"]["easing_to_next"]["description"]
    assert "penúltimo" in easing and "null" in easing
    omission = definitions["AudioPlan"]["properties"]["omission_reason"]["description"]
    assert all(term in omission for term in ("omit", "preserve", "not_present", "null"))
