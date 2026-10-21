from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.main import create_app
from app.schemas.business import BusinessCreated, BusinessRead
from app.services.business import AccessDenied, IdempotencyConflict
from app.tests.unit.test_core import access_token


def test_live_and_openapi(client):
    assert client.get("/health/live").json()["status"] == "ok"
    assert client.get("/api/v1/openapi.json").status_code == 200
    assert client.get("/", follow_redirects=False).headers["location"] == "/docs"


def test_ready_failure_and_recovery(client, fake_database):
    assert client.get("/health/ready").status_code == 200
    fake_database.ready.return_value = False
    assert client.get("/health/ready").status_code == 503
    fake_database.ready.side_effect = RuntimeError("database password must not leak")
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert "password" not in response.text


def test_correlation(client):
    valid = str(uuid4())
    assert client.get("/health/live", headers={"X-Request-ID": valid}).headers["X-Request-ID"] == valid
    assert client.get("/health/live", headers={"X-Request-ID": "untrusted"}).headers["X-Request-ID"] != "untrusted"


def test_missing_or_invalid_auth(client):
    assert client.get("/api/v1/businesses", headers={"X-Tenant-ID": str(uuid4())}).status_code == 401
    assert client.get("/api/v1/businesses", headers={"Authorization": "Bearer invalid"}).status_code == 401


@pytest.mark.parametrize(
    "exception,code", [(AccessDenied(), 403), (IdempotencyConflict(), 409), (RuntimeError("secret"), 500)]
)
def test_sanitized_service_errors(client, settings, monkeypatch, exception, code):
    monkeypatch.setattr("app.api.v1.api.list_businesses", AsyncMock(side_effect=exception))
    response = client.get(
        "/api/v1/businesses",
        headers={
            "Authorization": f"Bearer {access_token(settings)}",
            "X-Tenant-ID": str(uuid4()),
        },
    )
    assert response.status_code == code
    assert "secret" not in response.text
    if code == 500:
        assert response.json()["request_id"] == response.headers["X-Request-ID"]


def test_production_docs_disabled(settings, fake_database):
    from fastapi.testclient import TestClient

    production = settings.model_copy(update={"environment": "production", "temporal_tls": True})
    with TestClient(create_app(production, fake_database)) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/", follow_redirects=False).headers["location"] == "/health/live"


def test_owned_database_lifecycle(settings, fake_database, monkeypatch):
    from fastapi.testclient import TestClient

    monkeypatch.setattr("app.main.Database", lambda *args, **kwargs: fake_database)
    with TestClient(create_app(settings)) as client:
        assert client.get("/health/ready").status_code == 200
    assert fake_database.close.await_count == 2


@pytest.mark.parametrize("replayed,status", [(False, 201), (True, 200)])
def test_business_creation_response_contract(client, settings, monkeypatch, replayed, status):
    from datetime import UTC, datetime

    tenant, actor = uuid4(), uuid4()
    result = BusinessCreated(
        business=BusinessRead(id=uuid4(), tenant_id=tenant, name="Dog", timezone="UTC", created_at=datetime.now(UTC)),
        operation_id=uuid4(),
        replayed=replayed,
    )
    service = AsyncMock(return_value=result)
    monkeypatch.setattr("app.api.v1.api.create_business", service)
    response = client.post(
        "/api/v1/businesses",
        headers={
            "Authorization": f"Bearer {access_token(settings, actor)}",
            "X-Tenant-ID": str(tenant),
            "Idempotency-Key": "business-response-001",
        },
        json={"name": "Dog", "timezone": "UTC"},
    )
    assert response.status_code == status
    assert response.json() == result.model_dump(mode="json")
    service.assert_awaited_once()
    args = service.call_args.args
    assert args[1:4] == (tenant, actor, "business-response-001")
    assert args[4].name == "Dog"


@pytest.mark.parametrize("replayed,status", [(False, 201), (True, 200)])
def test_onboarding_response_contract(client, settings, monkeypatch, replayed, status):
    from app.schemas.onboarding import OnboardingResult

    result = OnboardingResult(tenant_id=uuid4(), business_id=uuid4(), replayed=replayed)
    provision = AsyncMock(return_value=result)
    monkeypatch.setattr("app.api.v1.onboarding.provision_initial_business", provision)
    response = client.post(
        "/api/v1/onboarding",
        headers={"Authorization": f"Bearer {access_token(settings)}"},
        json={
            "name": "Ana",
            "category": "Beleza",
            "city": "São Paulo",
            "description": "Unhas",
            "phone": "11999999999",
            "accept_terms": True,
            "accept_privacy": True,
        },
    )
    assert response.status_code == status
    assert response.json() == result.model_dump(mode="json")
    provision.assert_awaited_once()


def test_readiness_checks_the_authentication_database(settings, fake_database):
    from unittest.mock import AsyncMock

    from fastapi.testclient import TestClient

    auth_database = AsyncMock()
    auth_database.ready.return_value = False
    with TestClient(create_app(settings, fake_database, auth_database)) as client:
        assert client.get("/health/ready").status_code == 503
    auth_database.ready.assert_awaited_once()
