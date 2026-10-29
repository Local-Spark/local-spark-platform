"""Admission checks fail before creating a visual run or reading image bytes."""

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.auth import AuthError
from app.services.visual_admission import VisualAdmissionChecks


async def test_proposal_lock_requires_an_owner_visible_proposal(settings):
    checks = VisualAdmissionChecks(settings, uuid4(), "a" * 64)
    session = SimpleNamespace(scalar=AsyncMock(return_value=None))
    with pytest.raises(AuthError, match="PROPOSAL_NOT_FOUND"):
        await checks.lock_proposal(session, uuid4(), uuid4())
    session.scalar.return_value = checks.proposal
    await checks.lock_proposal(session, uuid4(), uuid4())
    assert "FOR UPDATE" in str(session.scalar.await_args.args[0])


@pytest.mark.parametrize(
    ("active", "plan", "agreement_required", "agreement", "fingerprint", "error"),
    [
        (False, True, False, True, "a" * 64, "BUSINESS_OWNER_REQUIRED"),
        (True, False, False, True, "a" * 64, "PLAN_REQUIRED"),
        (True, True, True, False, "a" * 64, "SERVICE_AGREEMENT_REQUIRED"),
        (True, True, True, True, "b" * 64, "PREVIEW_INPUT_CHANGED"),
        (True, True, False, True, "a" * 64, None),
        (True, True, True, True, "a" * 64, None),
    ],
)
async def test_sources_and_current_authority_are_checked_inside_admission(
    settings, monkeypatch, active, plan, agreement_required, agreement, fingerprint, error
):
    cfg = settings.model_copy(update={"service_agreement_required": agreement_required})
    checks = VisualAdmissionChecks(cfg, uuid4(), "a" * 64, True)
    session = SimpleNamespace(execute=AsyncMock(), scalar=AsyncMock(side_effect=[active, plan]))
    consent = AsyncMock(return_value=agreement)
    monkeypatch.setattr("app.services.visual_admission.service_agreement_allowed", consent)
    context = SimpleNamespace(capture_in_transaction=AsyncMock(return_value=SimpleNamespace(fingerprint=fingerprint)))
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    if error:
        with pytest.raises(AuthError, match=error):
            await checks.validate(session, tenant, business, actor, context)
    else:
        await checks.validate(session, tenant, business, actor, context)
        context.capture_in_transaction.assert_awaited_once_with(
            session, tenant, business, actor, checks.proposal, candidate=True
        )
    assert "pg_advisory_xact_lock" in str(session.execute.await_args.args[0])
    assert consent.await_count == int(active and plan and agreement_required)


async def test_production_admission_always_checks_the_contract(settings, monkeypatch):
    cfg = settings.model_copy(update={"environment": "production", "service_agreement_required": False})
    session = SimpleNamespace(execute=AsyncMock(), scalar=AsyncMock(side_effect=[True, True]))
    consent = AsyncMock(return_value=False)
    monkeypatch.setattr("app.services.visual_admission.service_agreement_allowed", consent)
    with pytest.raises(AuthError, match="SERVICE_AGREEMENT_REQUIRED"):
        await VisualAdmissionChecks(cfg, uuid4(), "a" * 64).validate(session, uuid4(), uuid4(), uuid4(), AsyncMock())
    assert session.scalar.await_args.args[1]["live"] is True
