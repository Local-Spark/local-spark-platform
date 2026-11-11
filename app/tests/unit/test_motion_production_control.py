"""Selection, privacy and Temporal behavior without a paid transport."""

from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from temporalio.exceptions import ApplicationError

from app.adapters.motion_html_renderer import RenderedMotion
from app.schemas.motion_production import MotionReview
from app.services.auth import AuthError
from app.services.content_pieces import PieceArtifact
from app.services.motion_context import MotionContext, canonical, digest
from app.services.motion_orchestrator import Candidate, choose_candidate, needs_correction
from app.tests.unit.test_motion_ai import composition, frame, review_data
from app.workflows.contracts import BusinessEvent
from app.workflows.motion_activities import MotionActivities
from app.workflows.motion_production import MotionProductionWorkflow


def candidate(number=0, **updates):
    video = RenderedMotion(b"synthetic", "a" * 64, (frame(),), {})
    data = review_data()
    data.update(updates)
    return Candidate(
        number,
        composition(),
        video,
        PieceArtifact(uuid4(), "private/key", "a" * 64, "video/mp4", 9),
        MotionReview.model_validate(data),
    )


def test_selection_requires_adequacy_and_comparative_gain():
    first = candidate()
    assert choose_candidate(None, first) is first
    assert choose_candidate(first, replace(first, review=None)) is first
    rejected = candidate(verdict="reject")
    assert choose_candidate(None, rejected) is None
    assert choose_candidate(first, rejected) is first
    assert choose_candidate(None, candidate(1, preferred="undetermined")) is None
    assert choose_candidate(first, candidate(1, preferred="previous")) is first
    improved = candidate(1)
    assert choose_candidate(first, improved) is improved
    assert not needs_correction(first.review)
    data = review_data(revise=True)
    assert needs_correction(MotionReview.model_validate(data))
    # Defense in depth against a caller bypassing Pydantic validation.
    data["issues"] = []
    invalid = first.review.model_copy(update={"verdict": "needs_revision", "issues": ()})
    assert not needs_correction(invalid)


def test_context_cipher_and_fingerprint_are_stable_and_private(settings):
    context = MotionContext(settings)
    with pytest.raises(AuthError, match="MOTION_ENCRYPTION_REQUIRED"):
        context.cipher()
    context = MotionContext(
        settings.model_copy(update={"meta_encryption_key": SecretStr(Fernet.generate_key().decode())})
    )
    private = {"customer": "segredo", "id": uuid4()}
    sealed = context.seal(private)
    assert "segredo" not in sealed and context.open(sealed)["customer"] == "segredo"
    assert context.fingerprint(private) == context.fingerprint(dict(reversed(list(private.items()))))
    assert len(context.fingerprint(private)) == 64
    assert digest(private) == digest(private) and "id" in canonical(private)


def test_snapshot_with_wrong_key_fails_closed_without_revealing_content(settings):
    first = MotionContext(
        settings.model_copy(update={"meta_encryption_key": SecretStr(Fernet.generate_key().decode())})
    )
    second = MotionContext(
        settings.model_copy(update={"meta_encryption_key": SecretStr(Fernet.generate_key().decode())})
    )
    with pytest.raises(AuthError, match="MOTION_SNAPSHOT_INVALID") as exc:
        second.open(first.seal({"private": "material"}))
    assert "material" not in str(exc.value)


def test_snapshot_must_decode_to_a_json_object(settings):
    context = MotionContext(
        settings.model_copy(update={"meta_encryption_key": SecretStr(Fernet.generate_key().decode())})
    )
    for plaintext in (b"not json", b"[]", b"\xff"):
        with pytest.raises(AuthError, match="MOTION_SNAPSHOT_INVALID"):
            context.open(context.cipher().encrypt(plaintext).decode())


@pytest.mark.parametrize(
    "updates,error",
    [
        ({}, "MOTION_LOCAL_QUALIFICATION_REQUIRED"),
        ({"motion_ai_reservation_usd_micros": 0}, "MOTION_BUDGET_REQUIRED"),
        ({"motion_request_budget_usd_micros": 1}, "MOTION_BUDGET_REQUIRED"),
    ],
)
def test_local_qualification_is_explicit_and_budgeted(settings, updates, error):
    business, source = uuid4(), uuid4()
    base = {
        "motion_execution_enabled": True,
        "motion_ai_mode": "fake",
        "motion_local_qualification_business_id": business,
        "motion_local_qualification_asset_ids": (source,),
        "motion_ai_reservation_usd_micros": 10,
        "motion_request_budget_usd_micros": 20,
        "meta_encryption_key": SecretStr(Fernet.generate_key().decode()),
    }
    cfg = settings.model_copy(update={**base, **updates}) if updates else settings
    with pytest.raises(AuthError, match=error):
        MotionContext(cfg).require_qualification(business, source)
    MotionContext(settings.model_copy(update=base)).require_qualification(business, source)


async def test_temporal_activity_hides_private_errors_and_does_not_retry(monkeypatch):
    event = BusinessEvent(*(str(uuid4()) for _ in range(5)))
    runner = SimpleNamespace(run=AsyncMock(return_value="completed"))
    assert await MotionActivities(runner).run(event) == "completed"
    runner.run.side_effect = RuntimeError("private credential and request")
    with pytest.raises(ApplicationError, match="Motion production unavailable") as exc:
        await MotionActivities(runner).run(event)
    assert exc.value.non_retryable and "private" not in str(exc.value)
    execute = AsyncMock(return_value="completed")
    monkeypatch.setattr("app.workflows.motion_production.workflow.execute_activity", execute)
    assert await MotionProductionWorkflow().run(event) == "completed"
    assert execute.call_args.kwargs["retry_policy"].maximum_attempts == 1
    assert execute.call_args.args == ("run_motion_production", event)


async def test_outbox_registers_motion_only_when_explicitly_ready(settings, monkeypatch):
    from app.services import outbox

    event = BusinessEvent(*(str(uuid4()) for _ in range(5)))
    claim = outbox.ClaimedEvent(event, 1, "motion.requested")
    claims = AsyncMock(return_value=[claim])
    finish = AsyncMock(return_value=True)
    monkeypatch.setattr(outbox, "claim_events", claims)
    monkeypatch.setattr(outbox, "finish_event", finish)
    configured = SimpleNamespace(motion_execution_ready=lambda: True, temporal_task_queue="synthetic-motion")
    client = SimpleNamespace(start_workflow=AsyncMock())
    assert await outbox.dispatch_once(object(), client, configured, uuid4()) == 1
    assert claims.call_args.kwargs["include_motion"] is True
    assert client.start_workflow.call_args.args == ("MotionProductionWorkflow", event)
    assert client.start_workflow.call_args.kwargs["id"] == f"motion-production/{event.tenant_id}/{event.event_id}"


async def test_worker_wires_motion_without_changing_existing_workflows(settings, monkeypatch):
    from unittest.mock import MagicMock

    from app.entrypoints import worker

    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr(Fernet.generate_key().decode())})
    monkeypatch.setattr(type(cfg), "motion_execution_ready", lambda _settings: True)
    db = AsyncMock()
    monkeypatch.setattr(worker, "get_settings", lambda: cfg)
    monkeypatch.setattr(worker, "Database", lambda *args, **kwargs: db)
    monkeypatch.setattr(worker, "connect_temporal", AsyncMock())
    runner = SimpleNamespace(run=AsyncMock())
    build = MagicMock(return_value=runner)
    monkeypatch.setattr(worker, "build_motion_runner", build)
    constructor = MagicMock(return_value=SimpleNamespace(run=AsyncMock()))
    monkeypatch.setattr(worker, "Worker", constructor)
    await worker.run_worker()
    assert worker.MotionProductionWorkflow in constructor.call_args.kwargs["workflows"]
    assert any(
        getattr(item, "__self__", None).runner is runner
        for item in constructor.call_args.kwargs["activities"]
        if isinstance(getattr(item, "__self__", None), MotionActivities)
    )
    build.assert_called_once_with(cfg, db, db)


def test_motion_http_routes_keep_private_content_out_of_responses(client, settings, monkeypatch):
    from app.api.v1 import motion_requests as routes
    from app.schemas.motion_production import MotionRequestRead
    from app.tests.unit.test_core import access_token

    tenant, business, actor, request_id, operation = (uuid4() for _ in range(5))
    saved = MotionRequestRead(
        id=request_id, operation_id=operation, format="reel", state="queued", piece_id=None, failure_code=None
    )
    service = SimpleNamespace(
        create=AsyncMock(return_value=saved), get=AsyncMock(return_value=saved), list=AsyncMock(return_value=[saved])
    )
    monkeypatch.setattr(routes, "MotionRequestService", lambda *args: service)
    path = f"/api/v1/organizations/{tenant}/businesses/{business}/motion-requests"
    headers = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    for response in (
        client.get(path, headers=headers),
        client.get(f"{path}/{request_id}", headers=headers),
        client.post(
            path,
            headers=headers,
            json={
                "operation_id": str(operation),
                "source_asset_id": str(uuid4()),
                "instruction": "Private instruction",
            },
        ),
    ):
        assert response.status_code in {200, 202}
        assert response.headers["Cache-Control"] == "no-store" and "Private instruction" not in response.text
    assert client.get(path).status_code == 401
