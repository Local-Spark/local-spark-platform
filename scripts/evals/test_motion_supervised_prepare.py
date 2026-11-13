"""Offline evidence propagation and mismatch rejection, without reading customer services."""

from dataclasses import replace

import pytest

from app.tests.unit.test_motion_audiovisual import natural_prepared
from app.tests.unit.test_motion_speech import timing_data
from scripts.evals.motion_supervised_prepare import reuse_speech


def test_archived_speech_preserves_provenance_and_rejects_a_different_recording():
    prepared = natural_prepared()
    prepared = replace(
        prepared, context={**prepared.context, "source": {**prepared.context["source"], "has_audio": True}}
    )
    with pytest.raises(ValueError, match="ARCHIVED_SPEECH_FORBIDDEN"):
        reuse_speech(prepared, timing_data())
    prepared.context.pop("quality_contract")
    timing = timing_data()
    result = reuse_speech(prepared, timing)
    assert result.context["transcript"]["provenance"] == "owner_reviewed"
    assert result.context["speech_result"] == timing
    assert result.assets == prepared.assets and result.source_frames == prepared.source_frames
    timing["source_sha256"] = "b" * 64
    with pytest.raises(ValueError, match="SPEECH_SOURCE_CHANGED"):
        reuse_speech(prepared, timing)
