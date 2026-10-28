from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import Response

from app.api.v1.billing import grant_sponsorship
from app.core.identity import Identity
from app.schemas.billing import SponsorshipCreate
from app.services import billing


async def test_untrusted_checkout_origin_is_rejected_before_lock_or_durable_intent(settings):
    db = AsyncMock()
    db.scalar.side_effect = ["owner", "owner"]
    actor = uuid4()
    owner = Identity(actor, "test", str(actor), "Ana", "ana@example.com", True)
    config = settings.model_copy(update={"billing_mode": "test"})
    with pytest.raises(billing.BillingError, match="ORIGIN_REJECTED") as error:
        await billing.request_checkout(db, config, uuid4(), owner, "unsafe-return", "https://untrusted.example")
    assert error.value.status == 403
    statements = [str(call.args[0]) for call in db.execute.call_args_list]
    assert not any("pg_advisory_xact_lock" in sql or "INSERT INTO billing_jobs" in sql for sql in statements)


async def test_checkout_requires_service_acceptance_before_reserving_a_payment(settings):
    db = AsyncMock()
    db.scalar.side_effect = ["owner", "owner", False]
    actor = uuid4()
    owner = Identity(actor, "test", str(actor), "Ana", "ana@example.com", True)
    config = settings.model_copy(update={"billing_mode": "test"})
    with pytest.raises(billing.BillingError, match="SERVICE_AGREEMENT_REQUIRED"):
        await billing.request_checkout(db, config, uuid4(), owner, "missing-agreement")
    assert not any("pg_advisory_xact_lock" in str(call.args[0]) for call in db.execute.call_args_list)


async def test_replays_return_durable_result_without_new_checkout_or_grant(settings):
    tenant, actor, operation = uuid4(), uuid4(), uuid4()
    db = AsyncMock()
    result = MagicMock()
    db.execute.return_value = result
    previous_job = {"id": operation, "state": "completed", "result": {"status": "open"}}
    result.mappings.return_value.one_or_none.return_value = previous_job
    db.scalar.side_effect = ["owner", "owner", True]
    owner = Identity(actor, "test", str(actor), "Ana", "ana@example.com", True)
    config = settings.model_copy(update={"billing_mode": "test"})
    assert await billing.request_checkout(db, config, tenant, owner, "existing-checkout") == previous_job
    assert not any("INSERT INTO billing_jobs" in str(call.args[0]) for call in db.execute.call_args_list)
    db.reset_mock()
    db.scalar.side_effect = [True, tenant]
    previous_grant = {"id": operation, "idempotency_key": "existing-grant", "reason": "Vídeo no canal"}
    result.mappings.return_value.one_or_none.return_value = previous_grant
    assert await billing.sponsor(db, tenant, actor, "existing-grant", "Vídeo no canal") == {
        **previous_grant,
        "replayed": True,
    }
    assert not any("INSERT INTO billing_sponsorships" in str(call.args[0]) for call in db.execute.call_args_list)


async def test_administrative_status_is_audited_even_without_customer_membership(settings):
    db = AsyncMock()
    db.scalar.side_effect = [True, None]
    result = MagicMock()
    result.mappings.return_value.one_or_none.return_value = None
    db.execute.return_value = result
    view = await billing.status(db, settings, uuid4(), uuid4(), administrative=True)
    assert not view["can_manage"] and not view["access_active"]
    assert any("INSERT INTO platform_audit" in str(call.args[0]) for call in db.execute.call_args_list)


@pytest.mark.parametrize("replayed", [False, True])
async def test_sponsorship_http_status_distinguishes_creation_and_replay(monkeypatch, replayed):
    grant = {"id": uuid4(), "replayed": replayed}
    monkeypatch.setattr(billing, "sponsor", AsyncMock(return_value=grant))
    response = Response(status_code=201)
    assert (
        await grant_sponsorship(
            uuid4(), SponsorshipCreate(reason="Vídeo no canal"), response, uuid4(), AsyncMock(), "existing-grant"
        )
        == grant
    )
    assert response.status_code == (200 if replayed else 201)
