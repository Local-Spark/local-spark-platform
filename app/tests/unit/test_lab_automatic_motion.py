"""New lab snapshots build automatically, including legacy video drafts."""

from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr

from app.schemas.creation_lab import LabStart
from app.services.creation_lab_motion_requests import LabMotionRequests


@pytest.mark.parametrize("flow_version", [1, 2])
async def test_video_draft_has_no_construction_approval(settings, fake_database, monkeypatch, flow_version):
    settings.meta_encryption_key = SecretStr(Fernet.generate_key().decode())
    run, source = uuid4(), uuid4()
    requests = LabMotionRequests(settings, fake_database, run)
    monkeypatch.setattr("app.services.message_creation.message_text", lambda *args: "Reel automático")
    requests.context.capture = AsyncMock(return_value={"snapshot": True})
    assert await requests.build_snapshot(
        Mock(),
        {"tenant_id": uuid4(), "business_id": uuid4(), "flow_version": flow_version},
        LabStart(operation_id=uuid4(), source_attachment_id=source),
    ) == {"snapshot": True}
    request = requests.context.capture.await_args.args[3]
    assert request.source_asset_id == source
    assert not request.review_checkpoints
    assert not request.storyboard
    assert request.propose_direction and request.automatic_plan


async def test_video_lab_capture_pins_contracts_and_preserves_previous(settings, fake_database, monkeypatch):
    from app.schemas.motion_production import MotionRequest
    from app.services.motion_context import capture_motion_guidance
    from app.services.motion_generation import VIDEO_GENERATION_CONTRACT, staged_generation_enabled
    from app.services.motion_quality import QUALITY_CONTRACT
    from app.services.motion_repertoire import capture_repertoire
    from app.services.motion_skills import _SKILLS, load_motion_skill
    from app.services.motion_staging import STAGING_CONTRACT

    settings.meta_encryption_key = SecretStr(Fernet.generate_key().decode())
    requests = LabMotionRequests(settings, fake_database, uuid4())
    message = "Pausa suave. " * 100
    monkeypatch.setattr("app.services.message_creation.message_text", lambda *args: message)

    async def capture(session, tenant, business, request):
        return {**capture_motion_guidance(request), "request": request.model_dump(mode="json")}

    requests.context.capture = AsyncMock(side_effect=capture)
    snapshot = await requests.build_snapshot(
        Mock(),
        {"tenant_id": uuid4(), "business_id": uuid4()},
        LabStart(operation_id=uuid4(), source_attachment_id=uuid4()),
    )
    assert snapshot["generation_contract"] == VIDEO_GENERATION_CONTRACT
    assert snapshot["quality_contract"] == QUALITY_CONTRACT
    assert snapshot["staging_contract"] == STAGING_CONTRACT
    assert snapshot["repertoire"] == capture_repertoire("business-video-reel-v2")
    assert snapshot["skill"]["id"] == "instagram-reel-video-v19"
    assert staged_generation_enabled(snapshot)
    import json
    from dataclasses import replace

    from app.tests.unit.test_motion_ai import frame, provider
    from app.tests.unit.test_motion_staging import staged_job

    job = staged_job()
    context = {**job.context, **snapshot}
    context.pop("sound_library", None)
    payload = provider().build_request(replace(job, context=context, reference_images=(), source_frames=(frame(0),)))
    assert payload["text"]["format"]["name"] == "MotionStagedPlanningOutput"
    transmitted = json.loads(payload["input"][0]["content"][0]["text"])["authorized_context"]
    assert transmitted["repertoire"] == snapshot["repertoire"]
    assert transmitted["video_scene_visibility_contract"] == snapshot["video_scene_visibility_contract"]
    assert "antes e depois de cada seek" in transmitted["video_scene_visibility_contract"]["rules"]
    assert "proibir IDs de outra cena" in transmitted["skill"]["instructions"]
    body = MotionRequest.model_validate(snapshot["request"])
    assert body.preparation.client_message == message
    assert "".join(d.source_excerpt for d in body.preparation.decisions) == message
    assert capture_motion_guidance(body, previous=snapshot) == snapshot
    # Historical lab requests retain the absence of staging and repertoire.
    old_body = MotionRequest(operation_id=uuid4(), source_asset_id=uuid4(), instruction="Soft")
    old = capture_motion_guidance(old_body)
    for skill, repertoire in [
        ("instagram-reel-video-v15", None),
        ("instagram-reel-video-v15", "business-video-reel-v2"),
        ("instagram-reel-video-v14", "business-video-reel-v1"),
    ]:
        digest = _SKILLS[skill][1]
        old["skill"] = {"id": skill, "sha256": digest, "instructions": load_motion_skill(skill, digest, "reel")}
        if repertoire:
            old["repertoire"] = capture_repertoire(repertoire)
        assert capture_motion_guidance(old_body, previous=old) == old
        assert "staging_contract" not in old


@pytest.mark.parametrize("mutation", ["source", "automatic", "quality", "legacy_contract"])
def test_automatic_video_contract_rejects_incoherent_context(mutation):
    from app.schemas.motion_production import MotionRequest
    from app.services.auth import AuthError
    from app.services.motion_context import capture_motion_guidance
    from app.services.motion_generation import PRODUCTION_GENERATION_CONTRACT, staged_generation_enabled
    from app.services.motion_video_requests import planned_video_request

    body = planned_video_request(MotionRequest(operation_id=uuid4(), source_asset_id=uuid4(), instruction="Soft"))
    context = {**capture_motion_guidance(body), "request": body.model_dump(mode="json")}
    if mutation == "source":
        context["request"]["source_asset_id"] = None
    elif mutation == "automatic":
        context["request"].pop("automatic_plan")
    elif mutation == "quality":
        context.pop("quality_contract")
    else:
        context["generation_contract"] = PRODUCTION_GENERATION_CONTRACT
    with pytest.raises(AuthError, match="MOTION_(PROPOSED_DIRECTION_CONTEXT|QUALITY_CONTRACT)_REQUIRED"):
        staged_generation_enabled(context)
