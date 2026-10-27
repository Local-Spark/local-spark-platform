"""A paid interpreter cannot submit without credentials or replay a previous operation."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.services.auth import AuthError
from app.services.creative_catalog_resolution import CatalogInterpreterBudgetBlocked, CatalogInterpreterUnavailable
from app.services.editorial_briefings import EditorialBriefingService
from app.services.jev_interpreter import BudgetedJevInterpreter


class Database:
    @asynccontextmanager
    async def transaction(self, *_):
        yield object()


@pytest.mark.parametrize("missing", ["typesafe_api_key", "meta_encryption_key"])
def test_provider_cannot_be_constructed_without_credentials(settings, missing):
    cfg = settings.model_copy(
        update={"typesafe_api_key": SecretStr("fake"), "meta_encryption_key": SecretStr("fake"), missing: None}
    )
    with pytest.raises(ValueError, match="configured credentials"):
        BudgetedJevInterpreter(cfg, Database(), *(uuid4() for _ in range(5)))


@pytest.mark.parametrize("source_changed", [True, False])
async def test_changed_source_or_existing_reservation_never_calls_provider(settings, monkeypatch, source_changed):
    cfg = settings.model_copy(update={"typesafe_api_key": SecretStr("fake"), "meta_encryption_key": SecretStr("fake")})
    provider = SimpleNamespace(interpret=AsyncMock())
    monkeypatch.setattr(
        EditorialBriefingService, "_source", AsyncMock(return_value="changed" if source_changed else "message")
    )
    reserve = AsyncMock(return_value=False)
    monkeypatch.setattr("app.services.jev_interpreter.reserve_intent", reserve)
    interpreter = BudgetedJevInterpreter(cfg, Database(), *(uuid4() for _ in range(5)), provider=provider)
    with pytest.raises(CatalogInterpreterUnavailable):
        await interpreter.interpret("message", [])
    provider.interpret.assert_not_awaited()
    assert reserve.await_count == (0 if source_changed else 1)


@pytest.mark.parametrize("error", ["INTENT_BUDGET_DISABLED", "INTENT_BUDGET_EXCEEDED"])
async def test_budget_rejection_is_distinguished_before_any_provider_call(settings, monkeypatch, error):
    cfg = settings.model_copy(update={"typesafe_api_key": SecretStr("fake"), "meta_encryption_key": SecretStr("fake")})
    provider = SimpleNamespace(interpret=AsyncMock())
    monkeypatch.setattr(EditorialBriefingService, "_source", AsyncMock(return_value="message"))
    monkeypatch.setattr("app.services.jev_interpreter.reserve_intent", AsyncMock(side_effect=AuthError(error, 409)))
    interpreter = BudgetedJevInterpreter(cfg, Database(), *(uuid4() for _ in range(5)), provider=provider)
    with pytest.raises(CatalogInterpreterBudgetBlocked):
        await interpreter.interpret("message", [])
    provider.interpret.assert_not_awaited()
