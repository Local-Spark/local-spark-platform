import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
import stripe
from fastapi.testclient import TestClient
from pydantic import SecretStr
from temporalio.exceptions import ActivityError, ApplicationError

from app.entrypoints import billing as entrypoint
from app.main import create_app
from app.services.billing import BillingError
from app.workflows import billing as workflow_module
from app.workflows.billing import BillingWorkflow
from app.workflows.billing_activities import BillingActivities


@pytest.mark.parametrize("open_checkout", [False, True])
async def test_workflow_schedules_checkout_expiry_without_holding_activity_slot(monkeypatch, open_checkout):
    now = datetime.now(UTC)
    result = {
        "status": "open" if open_checkout else "reconciled",
        "expires_at": (now + timedelta(seconds=30)).isoformat(),
    }
    execute = AsyncMock(return_value=result)
    sleep = AsyncMock()
    monkeypatch.setattr(workflow_module.workflow, "execute_activity", execute)
    monkeypatch.setattr(workflow_module.workflow, "now", lambda: now)
    monkeypatch.setattr(workflow_module.workflow, "sleep", sleep)
    assert await BillingWorkflow().run(str(uuid4())) == "completed"
    assert execute.await_count == (2 if open_checkout else 1)
    if open_checkout:
        sleep.assert_awaited_once_with(timedelta(seconds=30))


async def test_workflow_records_terminal_failure(monkeypatch):
    failure = ActivityError(
        "private error",
        scheduled_event_id=1,
        started_event_id=2,
        identity="test",
        activity_type="billing",
        activity_id="test",
        retry_state=None,
    )
    execute = AsyncMock(side_effect=[failure, None])
    monkeypatch.setattr(workflow_module.workflow, "execute_activity", execute)
    assert await BillingWorkflow().run("test-job") == "failed"
    assert execute.call_args.args == ("fail_billing_job", "test-job")


async def test_activity_adapters_and_fail_marker():
    processor = AsyncMock()
    processor.run.return_value = {"status": "expired"}
    activities = BillingActivities(processor)
    job_id = uuid4()
    assert (await activities.process_billing_job(str(job_id)))["status"] == "expired"
    await activities.expire_billing_checkout(str(job_id))
    processor.run.assert_awaited_with(job_id, expire=True)
    await activities.fail_billing_job(str(job_id))
    processor.fail.assert_awaited_once_with(job_id, "PROVIDER_RECONCILIATION_REQUIRED")


async def test_activity_history_does_not_retain_payment_links():
    processor = AsyncMock()
    processor.run.return_value = {
        "status": "open",
        "expires_at": "2026-10-20T20:00:00+00:00",
        "checkout_url": "private-hosted-link",
    }
    result = await BillingActivities(processor).process_billing_job(str(uuid4()))
    assert result == {"status": "open", "expires_at": "2026-10-20T20:00:00+00:00"}


@pytest.mark.parametrize(
    "error,retryable",
    [
        (BillingError("BILLING_BUSY"), True),
        (BillingError("PRICE_MISMATCH"), False),
        (stripe.AuthenticationError("private provider detail"), False),
        (stripe.APIConnectionError("private provider detail"), True),
        (ValueError("private provider detail"), False),
    ],
)
async def test_activity_errors_are_classified_and_sanitized(error, retryable):
    processor = AsyncMock()
    processor.run.side_effect = error
    with pytest.raises(ApplicationError) as raised:
        await BillingActivities(processor).process_billing_job(str(uuid4()))
    assert raised.value.non_retryable != retryable
    assert "private provider detail" not in str(raised.value)


@pytest.mark.parametrize("connection_failure", [False, True])
async def test_billing_runtime_closes_resources_on_shutdown(settings, fake_database, monkeypatch, connection_failure):
    monkeypatch.setattr(entrypoint, "get_settings", lambda: settings.model_copy(update={"billing_mode": "test"}))
    monkeypatch.setattr(entrypoint, "Database", lambda *args, **kwargs: fake_database)
    provider = MagicMock()
    provider.close = AsyncMock()
    monkeypatch.setattr(entrypoint, "StripeBilling", lambda _: provider)
    monkeypatch.setattr(
        entrypoint,
        "connect_temporal",
        AsyncMock(side_effect=RuntimeError("test failure") if connection_failure else None),
    )
    runtime = MagicMock()
    monkeypatch.setattr(entrypoint, "Worker", lambda *args, **kwargs: runtime)
    dispatch = AsyncMock()
    monkeypatch.setattr(entrypoint, "dispatch_billing", dispatch)
    monkeypatch.setattr(entrypoint.asyncio, "sleep", AsyncMock(side_effect=asyncio.CancelledError()))
    with pytest.raises(RuntimeError if connection_failure else asyncio.CancelledError):
        await entrypoint.main()
    provider.close.assert_awaited_once()
    fake_database.close.assert_awaited_once()


def test_api_owns_and_closes_optional_billing_pool(settings, fake_database, monkeypatch):
    monkeypatch.setattr("app.main.Database", lambda *args, **kwargs: fake_database)
    config = settings.model_copy(
        update={"billing_database_url": SecretStr("postgresql+asyncpg://unused@localhost/unused")}
    )
    with TestClient(create_app(config, fake_database, fake_database)) as api:
        assert api.get("/health/live").status_code == 200
    fake_database.close.assert_awaited_once()


async def test_disabled_runtime_does_not_consume_pending_provider_work(settings, fake_database, monkeypatch):
    monkeypatch.setattr(entrypoint, "get_settings", lambda: settings)
    monkeypatch.setattr(entrypoint, "Database", lambda *args, **kwargs: fake_database)
    provider = MagicMock(close=AsyncMock())
    monkeypatch.setattr(entrypoint, "StripeBilling", lambda _: provider)
    connect = AsyncMock()
    monkeypatch.setattr(entrypoint, "connect_temporal", connect)
    monkeypatch.setattr(entrypoint.asyncio, "sleep", AsyncMock(side_effect=asyncio.CancelledError()))
    with pytest.raises(asyncio.CancelledError):
        await entrypoint.main()
    connect.assert_not_awaited()
    provider.close.assert_awaited_once()
    fake_database.close.assert_awaited_once()
