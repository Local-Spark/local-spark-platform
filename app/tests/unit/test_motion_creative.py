"""Creative adequacy requires observed development, without forcing an intense style."""

import json
from copy import deepcopy
from dataclasses import replace

import httpx
import pytest
from pydantic import ValidationError

from app.adapters.motion_ai import MotionAIError
from app.adapters.motion_fixture import FixtureMotionProvider
from app.schemas.motion_production import MotionReview
from app.services.motion_creative import CREATIVE_CRITERIA, motion_creative_contract
from app.services.motion_orchestrator import needs_correction
from app.services.motion_review import MotionReviewError, validate_review
from app.tests.unit.test_motion_ai import composition, frame, provider, request, response_data, review_data


def creative_case():
    frames = (frame(0), frame(600, "blue"))
    context = {"creative_contract": motion_creative_contract(), "request": {"instruction": "Motion editorial discreto"}}
    # Historical creative checks without the later temporal capability.
    context["creative_contract"].pop("temporal_review")
    job = replace(request("review", composition=composition(), frames=frames), context=context)
    data = review_data(current=frames[0])
    data["creative_checks"] = [
        {
            "name": name,
            "status": "met",
            "brief_basis": "Motion editorial discreto adequado ao pedido",
            "observation": "Mudança da hierarquia revela o convite e direciona a atenção, preservando sobriedade.",
            "evidence": [{"version": "current", "at_ms": f.ms, "sha256": f.sha256} for f in frames],
        }
        for name in CREATIVE_CRITERIA
    ]
    return job, data


def test_restrained_functional_motion_can_pass_without_an_effect_count():
    job, data = creative_case()
    review = MotionReview.model_validate(data)
    validate_review(job, review)
    assert not needs_correction(review)


@pytest.mark.parametrize("status", ["not_met", "uncertain"])
def test_readable_technically_correct_piece_is_not_adequate_with_unmet_creative_requirement(status):
    _, data = creative_case()
    data["creative_checks"][2]["status"] = status
    with pytest.raises(ValidationError, match="creative"):
        MotionReview.model_validate(data)


def test_motion_failure_cannot_be_hidden_by_omitting_an_actionable_issue():
    _, data = creative_case()
    next(c for c in data["criteria"] if c["name"] == "motion")["status"] = "fail"
    with pytest.raises(ValidationError, match="creative"):
        MotionReview.model_validate(data)


@pytest.mark.parametrize("change", ["missing", "duplicate", "single_moment", "unsent", "source_only", "unknown"])
def test_live_critique_requires_complete_grounded_creative_checks(change):
    job, data = creative_case()
    if change == "missing":
        data.pop("creative_checks")
    elif change == "duplicate":
        data["creative_checks"][1] = deepcopy(data["creative_checks"][0])
    elif change == "single_moment":
        data["creative_checks"][2]["evidence"] = data["creative_checks"][2]["evidence"][:1]
    elif change == "unsent":
        data["creative_checks"][2]["evidence"][1]["at_ms"] = 500
    elif change == "source_only":
        job = replace(job, source_frames=job.frames)
        for ref in data["creative_checks"][2]["evidence"]:
            ref["version"] = "source"
    else:
        job = replace(job, context={"creative_contract": {"version": "unknown"}})
    with pytest.raises(MotionReviewError):
        validate_review(job, MotionReview.model_validate(data))


def test_demonstrated_creative_gap_triggers_existing_conditional_correction_only():
    job, data = creative_case()
    data["verdict"] = "needs_revision"
    data["creative_checks"][2]["status"] = "not_met"
    next(c for c in data["criteria"] if c["name"] == "motion")["status"] = "fail"
    data["issues"] = [
        {
            "criterion": "motion",
            "severity": "major",
            "actionable": True,
            "at_ms": job.frames[1].ms,
            "evidence_sha256": job.frames[1].sha256,
            "problem": "Nos dois momentos a janela só muda de escala, sem desenvolver o convite elaborado solicitado.",
            "correction": "Conectar o detalhe do preparo ao convite com revelação tipográfica, preservando a gravação.",
        }
    ]
    review = MotionReview.model_validate(data)
    validate_review(job, review)
    assert needs_correction(review)
    data["issues"][0]["criterion"] = "legibility"
    next(c for c in data["criteria"] if c["name"] == "legibility")["status"] = "fail"
    with pytest.raises(MotionReviewError, match="CORRECTION_UNGROUNDED"):
        validate_review(job, MotionReview.model_validate(data))


def test_uncertainty_never_invents_a_paid_correction_and_history_still_parses():
    job, data = creative_case()
    data["verdict"] = "insufficient_evidence"
    for check in data["creative_checks"]:
        check.update(status="uncertain", evidence=[])
    review = MotionReview.model_validate(data)
    validate_review(job, review)
    assert not needs_correction(review)
    historical = MotionReview.model_validate(review_data())
    validate_review(replace(job, context={}), historical)
    assert historical.creative_checks == ()


async def test_provider_cannot_accept_an_old_technical_only_review_for_a_new_contract():
    job, _ = creative_case()
    calls = []

    def handler(sent):
        calls.append(sent)
        return httpx.Response(200, json=response_data(review_data()))

    client = provider(handler)
    with pytest.raises(MotionAIError, match="RESPONSE_INVALID"):
        await client.submit(job, client.build_request(job))
    assert len(calls) == 1


async def test_same_contract_reaches_generation_review_and_correction_without_extra_requests():
    review_job, data = creative_case()
    client = provider()
    before = deepcopy(review_job.context)
    for kind in ("generate", "review", "correct"):
        if kind == "correct":
            correction = MotionReview.model_validate(review_data(revise=True))
            job = replace(review_job, kind=kind, review=correction)
        else:
            job = replace(review_job, kind=kind)
        payload = client.build_request(job)
        context = json.loads(payload["input"][0]["content"][0]["text"])
        assert context["authorized_context"]["creative_contract"] == before["creative_contract"]
        assert payload["text"]["format"]["strict"] is True
    assert review_job.context == before
    # A caller cannot mutate the next request's policy through a returned dictionary.
    before["creative_contract"]["requirements"].clear()
    assert len(motion_creative_contract()["requirements"]) == 4


async def test_synthetic_fixture_remains_explicit_and_obeys_contract_shape():
    job, _ = creative_case()
    fake = FixtureMotionProvider()
    result = await fake.submit(job, fake.build_request(job))
    validate_review(job, result.review)
    assert len(result.review.creative_checks) == 4
    assert "Synthetic" in result.review.creative_checks[0].observation
