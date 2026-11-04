"""Guard and activity boundaries expose no claim token or private exception data."""

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from temporalio.exceptions import ApplicationError

from app.services.reference_geocoding_budget_guard import DatabaseGeocodingBudgetGuard, GeocodingGuardError
from app.workflows.business_geocoding_activities import BusinessGeocodingActivities
from app.workflows.contracts import BusinessEvent


def test_unclaimed_geocode_cannot_expose_executor_token():
    guard = DatabaseGeocodingBudgetGuard(None, None, shop_address=True)
    with pytest.raises(GeocodingGuardError, match="GEOCODING_EXECUTOR_NOT_CLAIMED"):
        _ = guard.executor_token


async def test_geocoding_activity_sanitizes_private_failure():
    event = BusinessEvent(*(str(uuid4()) for _ in range(5)))
    activities = BusinessGeocodingActivities(SimpleNamespace(run=AsyncMock(side_effect=ValueError("private address"))))
    with pytest.raises(ApplicationError) as error:
        await activities.resolve(event)
    assert "private address" not in str(error.value)
    assert error.value.type == "BusinessGeocodingUnavailable"


async def test_explicit_geocode_settings_register_the_real_runner(settings, monkeypatch):
    from unittest.mock import MagicMock

    from pydantic import SecretStr

    from app.entrypoints import worker

    configured = settings.model_copy(
        update={
            "reference_geocoding_enabled": True,
            "reference_google_api_key": SecretStr("synthetic-key"),
            "reference_provider_hmac_key": SecretStr("synthetic-reference-key-0123456789abcdef"),
            "reference_provider_key_version": "test-v1",
            "reference_google_credential_version": "test-v1",
            "reference_provider_pilot_id": uuid4(),
            "reference_geocoding_tariff_version": "test-v1",
            "reference_geocoding_reserved_usd_micros": 10,
            "correlator_database_url": settings.database_url,
        }
    )
    database = AsyncMock()
    constructor = MagicMock(return_value=MagicMock(run=AsyncMock()))
    monkeypatch.setattr(worker, "get_settings", lambda: configured)
    monkeypatch.setattr(worker, "Database", lambda *args, **kwargs: database)
    monkeypatch.setattr(worker, "connect_temporal", AsyncMock())
    monkeypatch.setattr(worker, "Worker", constructor)
    await worker.run_worker()
    assert worker.BusinessGeocodingWorkflow in constructor.call_args.kwargs["workflows"]
    assert any(activity.__name__ == "resolve" for activity in constructor.call_args.kwargs["activities"])
    assert database.close.await_count == 2
