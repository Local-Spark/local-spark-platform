"""Direction failures cannot spend on local code repair or silently change approved plans."""

from dataclasses import replace

import pytest

from app.schemas.motion_production import MotionReview
from app.services.auth import AuthError
from app.services.motion_plan_revision import requires_replanning, revision_request
from app.services.motion_protocols import MotionModelResult
from app.services.motion_review import MotionReviewError, validate_review
from app.tests.unit.test_motion_ai import frame, review_data
from app.tests.unit.test_motion_audiovisual import natural_body
from app.tests.unit.test_motion_orchestrator import stub_render, unit_case  # noqa: F401
from app.tests.unit.test_motion_staging import staged_composition, staged_context, staged_job


def rejected_review():
    data = review_data(current=frame(), revise=True)
    data.update(verdict="reject", preferred="undetermined", preference_evidence=[])
    data["issues"][0].update(actionable=False, repair_kind="direction")
    return MotionReview.model_validate(data)


def test_revision_preserves_simple_message_and_has_stable_operation_without_reusing_a_baseline():
    original, review = natural_body(repertoire_id="business-reel-v5"), rejected_review()
    revised = revision_request(original, review, "a" * 64)
    assert revised == revision_request(original, review, "a" * 64)
    assert revised.operation_id != original.operation_id and revised.source_asset_id == original.source_asset_id
    assert revised.instruction == original.instruction and revised.evolution is None
    assert revised.preparation.decisions[-1].origin == "operator"
    assert revised.preparation.decisions[-1].kind == "observation"
    assert len(original.preparation.decisions) == 1
    with pytest.raises(AuthError, match="REVISION_LIMIT"):
        revision_request(revised, review, "b" * 64)


@pytest.mark.parametrize("change", ["preparation", "mode", "review"])
def test_ineligible_replanning_is_rejected(change):
    body, review = natural_body(), rejected_review()
    if change == "preparation":
        body = body.model_copy(update={"preparation": None})
    elif change == "mode":
        body = body.model_copy(update={"propose_direction": False})
    else:
        review = review.model_copy(update={"issues": ()})
    with pytest.raises(AuthError, match="INELIGIBLE"):
        revision_request(body, review, "a" * 64)


@pytest.mark.parametrize("kind", [None, "direction", "material", "uncertain"])
def test_new_review_cannot_label_direction_or_uncertainty_as_paid_code_correction(kind):
    data = review_data(current=frame(), revise=True)
    data["issues"][0]["repair_kind"] = kind
    review = MotionReview.model_validate(data)
    with pytest.raises(MotionReviewError, match="REPAIR_KIND_INVALID"):
        validate_review(
            replace(staged_job(), kind="review", composition=staged_composition(), frames=(frame(),)), review
        )


def test_replanning_issue_cannot_hide_behind_an_adequate_verdict():
    review = rejected_review().model_copy(update={"verdict": "adequate"})
    with pytest.raises(MotionReviewError, match="PLAN_REVISION_REQUIRED"):
        validate_review(staged_job(), review)


async def test_render_and_critique_are_saved_before_replanning_without_a_paid_code_repair(unit_case):  # noqa: F811
    c = unit_case
    stub_render(c)
    # Legacy context omits creative checks; the issue is already grounded in the current render.
    c.runner.effects.model.return_value = MotionModelResult(review=rejected_review())
    with pytest.raises(AuthError, match="PLAN_REVISION_REQUIRED"):
        await c.runner.produce(c.row, c.token, c.prepared, staged_composition())
    c.runner.record_review.assert_awaited_once()
    assert c.runner.effects.model.await_count == 1
    c.runner.effects.capacity_for_correction.assert_not_awaited()
    c.runner.complete.assert_not_awaited()
    assert requires_replanning(rejected_review())


def test_replanning_is_not_inferred_from_a_generic_legacy_issue():
    review = rejected_review()
    issue = review.issues[0].model_copy(update={"repair_kind": None})
    assert not requires_replanning(review.model_copy(update={"issues": (issue,)}))
    assert staged_context()["staging_contract"]["version"] == "motion-staging-v1"


def test_staging_reviews_accept_grounded_rejection_and_do_not_invent_replanning_for_clean_evidence():
    from app.services.motion_staging import STAGING_CONTRACT
    from app.tests.unit.test_motion_ai import request

    job = replace(request("review", frames=(frame(),)), context={"staging_contract": STAGING_CONTRACT})
    validate_review(job, rejected_review())
    validate_review(job, MotionReview.model_validate(review_data()))
    minor = rejected_review()
    issue = minor.issues[0].model_copy(update={"severity": "minor"})
    assert not requires_replanning(minor.model_copy(update={"issues": (issue,)}))


def test_review_requires_composition_for_local_repair_and_rejects_unsolicited_baseline():
    from app.services.motion_review import validate_baseline_review
    from app.tests.unit.test_motion_ai import request

    data = review_data(revise=True)
    data["issues"][0]["repair_kind"] = "implementation"
    with pytest.raises(MotionReviewError, match="CORRECTION_COMPOSITION_REQUIRED"):
        validate_review(replace(staged_job(), composition=None), MotionReview.model_validate(data))
    baseline = MotionReview.model_validate(review_data()).model_copy(update={"baseline_video_sha256": "a" * 64})
    with pytest.raises(MotionReviewError, match="EVOLUTION_REVIEW_UNEXPECTED"):
        validate_baseline_review(request(), baseline)


def observation_case():
    from app.schemas.motion_plan_revision import MotionDirectionObservation

    data = review_data()
    refs = [dict(version="current", at_ms=ms, sha256=frame(ms).sha256) for ms in (100, 300)]
    data["criteria"][0]["evidence"] = refs
    review = MotionReview.model_validate(data)
    observation = MotionDirectionObservation(
        mp4_sha256="a" * 64,
        frames=[{k: v for k, v in f.items() if k != "version"} for f in refs],
        observation="Operator observed the same flat middle state at 100 and 300 ms; revise direction.",
    )
    return review, observation


def test_operator_direction_observation_keeps_native_verdict_and_client_message():
    review, observation = observation_case()
    original = natural_body(repertoire_id="business-reel-v5")
    revised = revision_request(original, review, "a" * 64, observation)
    assert review.verdict == "adequate" and not review.issues
    assert revised.instruction == original.instruction and revised.evolution is None
    basis = revised.preparation.decisions[-1]
    assert basis.origin == "operator" and basis.kind == "observation"
    assert basis.interpretation == observation.observation
    assert "100ms/" in basis.source_excerpt and "native adequate retained" in basis.source_excerpt
    with pytest.raises(AuthError, match="REVISION_LIMIT"):
        revision_request(revised, review, "a" * 64, observation)


@pytest.mark.parametrize("change", ["verdict", "mp4", "duplicate", "frame", "previous"])
def test_operator_observation_requires_received_mp4_and_distinct_current_frames(change):
    review, observation = observation_case()
    if change == "verdict":
        review = review.model_copy(update={"verdict": "reject"})
    elif change == "mp4":
        observation = observation.model_copy(update={"mp4_sha256": "b" * 64})
    elif change == "duplicate":
        observation = observation.model_copy(update={"frames": (observation.frames[0],) * 2})
    elif change == "frame":
        observation = observation.model_copy(
            update={"frames": (observation.frames[0], observation.frames[1].model_copy(update={"at_ms": 999}))}
        )
    else:
        first = review.criteria[0]
        first = first.model_copy(
            update={"evidence": tuple(f.model_copy(update={"version": "previous"}) for f in first.evidence)}
        )
        review = review.model_copy(update={"criteria": (first, *review.criteria[1:])})
    with pytest.raises(AuthError, match="OBSERVATION_UNGROUNDED"):
        revision_request(natural_body(), review, "a" * 64, observation)
