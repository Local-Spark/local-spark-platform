"""Speech assertions bind to source bytes and beats, without transcriber or customer media."""

import json
from copy import deepcopy
from dataclasses import replace

import pytest
from pydantic import ValidationError

from app.schemas.motion_production import MotionRequest, MotionReview
from app.schemas.motion_speech import MotionSpeechTiming
from app.services.auth import AuthError
from app.services.motion_plan import validate_motion_plan
from app.services.motion_speech import speech_context, speech_timing, validate_speech_plan, validate_speech_source
from app.tests.unit.test_motion_ai import frame, provider, request, review_data
from app.tests.unit.test_motion_plan import context, plan_data, planned


def timing_data():
    return {
        "version": "motion-speech-v1",
        "source_sha256": "a" * 64,
        "provenance": "owner_reviewed",
        "alignment": "segment",
        "cues": [
            {"id": "question", "text": "Uma pergunta", "start_ms": 0, "end_ms": 300},
            {"id": "answer", "text": "Uma resposta", "start_ms": 500, "end_ms": 900},
        ],
        "focus_cue_ids": ["question", "answer"],
    }


def speech_case():
    ctx = context()
    ctx["request"] = {"speech_timing": timing_data()}
    ctx["source"] = {"sha256": "a" * 64, "duration_ms": 1000, "has_audio": True}
    ctx["transcript"] = speech_context(ctx, ctx["source"])
    data = plan_data()
    for scene, cue in zip(data["scenes"], ("question", "answer"), strict=True):
        scene["elements"][0]["beats"][0]["speech_cue_id"] = cue
    return ctx, planned(data)


@pytest.mark.parametrize(
    "change",
    [
        {"cues": []},
        {"focus_cue_ids": []},
        {"focus_cue_ids": ["missing"]},
        {"focus_cue_ids": ["answer", "answer"]},
        {"source_sha256": "bad"},
        {"provenance": "model_inferred"},
        {"alignment": "none"},
    ],
)
def test_rejects_unreviewed_or_ambiguous_timing(change):
    with pytest.raises(ValidationError):
        MotionSpeechTiming.model_validate({**timing_data(), **change})


@pytest.mark.parametrize(
    "change",
    [
        {"id": "question"},
        {"start_ms": 200},
        {"end_ms": 500},
        {"start_ms": -1},
        {"start_ms": 0.5},
        {"end_ms": 60001},
        {"text": " "},
    ],
)
def test_cues_reject_duplicates_overlap_reversed_and_invalid_times(change):
    data = timing_data()
    data["cues"][1].update(change)
    with pytest.raises(ValidationError):
        MotionSpeechTiming.model_validate(data)


def test_source_hash_audio_and_duration_are_checked_without_inventing_silence():
    ctx, _ = speech_case()
    timing = speech_timing(ctx)
    validate_speech_source(timing, ctx["source"])
    for change, error in [
        ({"sha256": "b" * 64}, "SOURCE_CHANGED"),
        ({"has_audio": False}, "SOURCE_INVALID"),
        ({"duration_ms": 899}, "SOURCE_INVALID"),
        ({"duration_ms": None}, "SOURCE_INVALID"),
    ]:
        with pytest.raises(AuthError, match=error):
            validate_speech_source(timing, {**ctx["source"], **change})
    validate_speech_source(None, {})
    assert speech_context({}, {}) is None
    assert ctx["transcript"]["scope"] == "selected_passages"
    assert ctx["transcript"]["text"] == "Uma pergunta Uma resposta"
    with pytest.raises(AuthError, match="TIMING_INVALID"):
        speech_timing({"request": {"speech_timing": {}}})


def test_plan_requires_each_focus_and_validates_the_exact_onset_not_full_cue_duration():
    ctx, composition = speech_case()
    validate_motion_plan(composition, ctx, duration_ms=1000, asset_ids=set())
    assert composition.motion_plan.scenes[1].elements[0].beats[0].end_ms == 800  # cue ends at 900
    data = composition.model_dump(mode="json")
    for change, error in [
        ({"speech_cue_id": "missing"}, "BEAT_INVALID"),
        ({"start_ms": 35}, "BEAT_INVALID"),
        ({"phase": "hold"}, "BEAT_INVALID"),
        ({"speech_cue_id": None}, "FOCUS_MISSING"),
    ]:
        changed = deepcopy(data)
        changed["motion_plan"]["scenes"][0]["elements"][0]["beats"][0].update(change)
        with pytest.raises(AuthError, match=error):
            validate_speech_plan(type(composition).model_validate(changed), ctx)
    data["motion_plan"]["scenes"][0]["elements"][0]["beats"][0]["start_ms"] = 34
    validate_speech_plan(type(composition).model_validate(data), ctx)
    with pytest.raises(AuthError, match="FOCUS_MISSING"):
        validate_speech_plan(composition.model_copy(update={"motion_plan": None}), ctx)
    with pytest.raises(AuthError, match="BEAT_INVALID"):
        validate_speech_plan(composition, context())
    with pytest.raises(AuthError, match="CONTEXT_CHANGED"):
        validate_speech_plan(composition, {**ctx, "transcript": None})
    validate_speech_plan(planned(), context())
    validate_speech_plan(composition.model_copy(update={"motion_plan": None}), {})


@pytest.mark.parametrize("kind", ["generate", "review", "correct"])
def test_identical_timing_reaches_model_and_invalid_provenance_stops_before_submission(kind):
    ctx, composition = speech_case()
    job = replace(
        request(
            kind,
            composition=composition,
            frames=(frame(),),
            review=MotionReview.model_validate(review_data(revise=True)),
        ),
        context=ctx,
    )
    payload = provider().build_request(job)
    sent = json.loads(payload["input"][0]["content"][0]["text"])["authorized_context"]
    assert sent == ctx
    with pytest.raises(AuthError, match="CONTEXT_CHANGED"):
        provider().build_request(replace(job, context={**ctx, "transcript": {}}))


def test_old_request_and_beats_keep_their_serialized_shape():
    from uuid import uuid4

    body = MotionRequest(operation_id=uuid4(), source_asset_id=uuid4(), instruction="Editorial motion")
    assert "speech_timing" not in body.model_dump(mode="json")
    assert "speech_cue_id" not in planned().motion_plan.scenes[0].elements[0].beats[0].model_dump(mode="json")
