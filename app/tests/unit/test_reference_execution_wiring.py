"""Provider admission and Temporal routing expose only durable identities."""

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4, uuid5

import pytest
from pydantic import SecretStr
from temporalio.common import WorkflowIDReusePolicy
from temporalio.exceptions import ApplicationError

from app.services import outbox
from app.workflows.contracts import BusinessEvent
from app.workflows.reference_provider_activities import ReferenceProviderActivities
from app.workflows.reference_provider_discovery import ReferenceProviderDiscoveryWorkflow


def configured(settings, **changes):
    values = {
        "reference_discovery_execution_enabled": True,
        "correlator_database_url": settings.database_url,
        "reference_google_api_key": SecretStr("synthetic-google"),
        "reference_provider_hmac_key": SecretStr("synthetic-hmac-key-longer-than-32-bytes"),
        "reference_provider_key_version": "synthetic-v1",
        "reference_google_credential_version": "synthetic-v1",
        "reference_provider_pilot_id": uuid4(),
        "reference_google_tariff_version": "synthetic-google",
        "reference_google_reserved_usd_micros": 35_000,
        "typesafe_api_key": SecretStr("synthetic-jev"),
        "reference_jev_tariff_version": "synthetic-jev",
        "reference_jev_credential_version": "synthetic-v1",
        "reference_jev_reserved_usd_micros": 3_000,
        "reference_apify_api_token": SecretStr("synthetic-apify"),
        "reference_apify_actor_id": "nwua9Gu5YrADL7ZDj",
        "reference_apify_actor_build": "1.2.3",
        "reference_apify_tariff_version": "synthetic-contacts",
        "reference_apify_credential_version": "synthetic-v1",
        "reference_apify_reserved_usd_micros": 500_000,
    }
    return settings.model_copy(update={**values, **changes})


def event():
    return BusinessEvent(**{field: str(uuid4()) for field in BusinessEvent.__dataclass_fields__})


def test_discovery_default_off_requires_explicit_complete_configuration(settings):
    assert not settings.reference_discovery_ready()
    assert configured(settings).reference_discovery_ready()


@pytest.mark.parametrize(
    "field,value",
    [
        ("reference_discovery_execution_enabled", False),
        ("environment", "production"),
        ("environment", "staging"),
        ("correlator_database_url", None),
        ("reference_google_api_key", None),
        ("reference_google_api_key", SecretStr(" ")),
        ("reference_provider_hmac_key", None),
        ("reference_provider_hmac_key", SecretStr("short")),
        ("reference_provider_key_version", ""),
        ("reference_google_credential_version", ""),
        ("reference_provider_pilot_id", None),
        ("reference_google_tariff_version", ""),
        ("reference_google_reserved_usd_micros", 0),
        ("typesafe_api_key", None),
        ("typesafe_api_key", SecretStr(" ")),
        ("reference_jev_tariff_version", ""),
        ("reference_jev_credential_version", ""),
        ("reference_jev_reserved_usd_micros", 0),
        ("reference_apify_api_token", None),
        ("reference_apify_api_token", SecretStr(" ")),
        ("reference_apify_actor_id", ""),
        ("reference_apify_actor_build", ""),
        ("reference_apify_tariff_version", ""),
        ("reference_apify_credential_version", ""),
        ("reference_apify_reserved_usd_micros", 499_999),
    ],
)
def test_each_missing_pilot_requirement_blocks_execution(settings, field, value):
    assert not configured(settings, **{field: value}).reference_discovery_ready()


async def test_workflow_waits_for_review_and_polls_only_existing_runs(monkeypatch):
    flow = ReferenceProviderDiscoveryWorkflow()
    item = event()
    execute = AsyncMock(side_effect=["awaiting_own_review", "contacts_pending", "contacts_failed", "completed"])
    sleep = AsyncMock()

    async def wait(predicate):
        assert not predicate()
        await flow.resume()
        assert predicate()

    monkeypatch.setattr("app.workflows.reference_provider_discovery.workflow.execute_activity", execute)
    monkeypatch.setattr("app.workflows.reference_provider_discovery.workflow.wait_condition", wait)
    monkeypatch.setattr("app.workflows.reference_provider_discovery.workflow.sleep", sleep)
    assert await flow.run(item) == "completed"
    assert execute.await_count == 4 and flow._resumed is False
    sleep.assert_awaited_once_with(timedelta(seconds=10))
    for call in execute.await_args_list:
        assert call.args == ("execute_reference_provider_discovery", item)
        assert call.kwargs["retry_policy"].maximum_attempts == 2
        assert call.kwargs["result_type"] is str


async def test_workflow_has_a_bounded_pending_poll_window(monkeypatch):
    class Continued(Exception):
        pass

    flow = ReferenceProviderDiscoveryWorkflow()
    item = event()
    execute = AsyncMock(return_value="contacts_pending")
    sleep = AsyncMock()

    def continued(received):
        assert received == item and execute.await_count == 181 and sleep.await_count == 180
        raise Continued

    monkeypatch.setattr("app.workflows.reference_provider_discovery.workflow.execute_activity", execute)
    monkeypatch.setattr("app.workflows.reference_provider_discovery.workflow.sleep", sleep)
    monkeypatch.setattr("app.workflows.reference_provider_discovery.workflow.continue_as_new", continued)
    with pytest.raises(Continued):
        await flow.run(item)


async def test_disabled_discovery_waits_until_configuration_is_restored(monkeypatch):
    execute = AsyncMock(side_effect=["disabled", "completed"])
    sleep = AsyncMock()
    monkeypatch.setattr("app.workflows.reference_provider_discovery.workflow.execute_activity", execute)
    monkeypatch.setattr("app.workflows.reference_provider_discovery.workflow.sleep", sleep)
    assert await ReferenceProviderDiscoveryWorkflow().run(event()) == "completed"
    sleep.assert_awaited_once_with(timedelta(hours=1))


async def test_activity_keeps_private_failures_out_of_temporal():
    item = event()
    executor = SimpleNamespace(run=AsyncMock(return_value="completed"))
    activities = ReferenceProviderActivities(executor)
    assert await activities.execute_reference_provider_discovery(item) == "completed"
    executor.run.assert_awaited_once_with(item)
    executor.run.side_effect = ValueError("private provider payload")
    with pytest.raises(ApplicationError) as caught:
        await activities.execute_reference_provider_discovery(item)
    assert caught.value.type == "ReferenceDiscoveryUnavailable"
    assert "private" not in str(caught.value) and caught.value.__suppress_context__


@pytest.mark.parametrize(
    "event_type",
    ["reference.provider_search_requested", "reference.search_reviewed", "reference.provider_retry_requested"],
)
async def test_relay_starts_or_resumes_the_same_search_identity(settings, monkeypatch, event_type):
    review = event_type != "reference.provider_search_requested"
    item = event()
    claim = outbox.ClaimedEvent(item, 1, event_type)
    claims, finish = AsyncMock(return_value=[claim]), AsyncMock(return_value=True)
    handle = SimpleNamespace(signal=AsyncMock())
    client = SimpleNamespace(start_workflow=AsyncMock(), get_workflow_handle=MagicMock(return_value=handle))
    monkeypatch.setattr(outbox, "claim_events", claims)
    monkeypatch.setattr(outbox, "finish_event", finish)
    ready = configured(settings)
    assert await outbox.dispatch_once(object(), client, ready, uuid4()) == 1
    assert claims.await_args.kwargs["include_provider_discovery"] is True
    identity = uuid5(UUID(item.operation_id), f"reference-provider-search-v1:{item.tenant_id}:{item.business_id}")
    expected = f"reference-provider-search/{item.tenant_id}/{identity}"
    if review:
        client.get_workflow_handle.assert_called_once_with(expected)
        handle.signal.assert_awaited_once_with("resume", rpc_timeout=timedelta(seconds=5))
        client.start_workflow.assert_not_awaited()
    else:
        assert client.start_workflow.await_args.args == ("ReferenceProviderDiscoveryWorkflow", item)
        assert client.start_workflow.await_args.kwargs["id"] == expected
        assert client.start_workflow.await_args.kwargs["id_reuse_policy"] == WorkflowIDReusePolicy.REJECT_DUPLICATE
    assert finish.await_args.kwargs["success"] is True


async def test_explicit_pilot_configuration_registers_executor_with_restricted_database(settings, monkeypatch):
    from app.entrypoints import worker

    database, runner = AsyncMock(), MagicMock(run=AsyncMock())
    factory, constructor = MagicMock(return_value=SimpleNamespace(run=AsyncMock())), MagicMock(return_value=runner)
    monkeypatch.setattr(worker, "get_settings", lambda: configured(settings))
    monkeypatch.setattr(worker, "Database", lambda *args, **kwargs: database)
    monkeypatch.setattr(worker, "connect_temporal", AsyncMock())
    monkeypatch.setattr(worker, "ReferenceProviderExecution", factory)
    monkeypatch.setattr(worker, "Worker", constructor)
    await worker.run_worker()
    assert worker.ReferenceProviderDiscoveryWorkflow in constructor.call_args.kwargs["workflows"]
    assert any(
        method.__name__ == "execute_reference_provider_discovery"
        for method in constructor.call_args.kwargs["activities"]
    )
    assert factory.call_args.args[0] is database
    assert database.close.await_count == 2
