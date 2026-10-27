from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.auth import AuthError
from app.services.creative_catalog_resolution import (
    CatalogIntent,
    CatalogInterpreterUnavailable,
    resolve_catalog_context,
)


class FakeDatabase:
    def __init__(self):
        self.active = False
        self.calls = []

    @asynccontextmanager
    async def transaction(self, tenant, actor):
        assert not self.active
        self.active = True
        self.calls.append((tenant, actor))
        try:
            yield object()
        finally:
            self.active = False


@pytest.fixture
def setup(monkeypatch):
    database = FakeDatabase()
    tenant, business, actor, item = (uuid4() for _ in range(4))
    choices = [{"id": str(item), "kind": "product", "name": "Croissant"}]
    candidates = AsyncMock(return_value={"status": "needs_selection", "catalog_version": 4, "candidates": choices})
    snapshot = AsyncMock(return_value={"catalog_version": 4})
    monkeypatch.setattr("app.services.creative_catalog_resolution.catalog_candidates", candidates)
    monkeypatch.setattr("app.services.creative_catalog_resolution.selected_catalog_snapshot", snapshot)
    return SimpleNamespace(
        database=database,
        tenant=tenant,
        business=business,
        actor=actor,
        item=item,
        choices=choices,
        candidates=candidates,
        snapshot=snapshot,
    )


async def _resolve(s, interpreter, message="crie imagem do croissant"):
    return await resolve_catalog_context(s.database, s.tenant, s.business, s.actor, message, interpreter)


async def test_resolves_only_after_explicit_decision_and_without_a_lock(setup):
    s = setup

    async def interpret(message, candidates):
        assert not s.database.active
        assert message == "crie imagem do croissant"
        assert candidates == s.choices
        candidates[0]["name"] = "mutated by provider"
        return CatalogIntent("selected", s.item)

    result = await _resolve(s, SimpleNamespace(interpret=interpret))
    assert result.status == "resolved" and result.snapshot == {"catalog_version": 4}
    assert len(s.database.calls) == 2
    assert s.snapshot.await_args.args[5:7] == (s.item, 4)
    assert s.choices[0]["name"] == "Croissant"


@pytest.mark.parametrize("status", ["no_text", "not_found", "catalog_too_large", "too_many_matches", "unexpected"])
async def test_no_interpretation_for_no_bounded_candidates(setup, status):
    setup.candidates.return_value = {"status": status, "catalog_version": 0, "candidates": []}
    interpreter = SimpleNamespace(interpret=AsyncMock())
    result = await _resolve(setup, interpreter)
    assert result.status == (status if status != "unexpected" else "invalid_decision")
    interpreter.interpret.assert_not_awaited()
    setup.snapshot.assert_not_awaited()


@pytest.mark.parametrize(
    "intent,expected",
    [
        (CatalogIntent("none"), "none"),
        (CatalogIntent("clarify"), "clarify"),
        (CatalogIntent("selected"), "invalid_decision"),
        (CatalogIntent("selected", uuid4()), "invalid_decision"),
        (CatalogIntent("none", uuid4()), "invalid_decision"),
        ({"decision": "selected"}, "invalid_decision"),
    ],
)
async def test_abstentions_and_invalid_selections_do_not_produce_snapshots(setup, intent, expected):
    result = await _resolve(setup, SimpleNamespace(interpret=AsyncMock(return_value=intent)))
    assert result.status == expected and result.snapshot is None
    setup.snapshot.assert_not_awaited()


async def test_unavailable_and_catalog_changed_are_not_resolved(setup):
    unavailable = SimpleNamespace(interpret=AsyncMock(side_effect=CatalogInterpreterUnavailable()))
    assert (await _resolve(setup, unavailable)).status == "interpreter_unavailable"
    setup.snapshot.side_effect = AuthError("COLLECTION_CONTEXT_CHANGED", 409)
    selected = SimpleNamespace(interpret=AsyncMock(return_value=CatalogIntent("selected", setup.item)))
    assert (await _resolve(setup, selected)).status == "context_changed"


async def test_permission_error_is_not_silently_ignored(setup):
    setup.snapshot.side_effect = AuthError("BUSINESS_OWNER_REQUIRED", 403)
    selected = SimpleNamespace(interpret=AsyncMock(return_value=CatalogIntent("selected", setup.item)))
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await _resolve(setup, selected)


async def test_message_is_bounded_for_both_lookup_and_interpreter(setup):
    selected = SimpleNamespace(interpret=AsyncMock(return_value=CatalogIntent("none")))
    await _resolve(setup, selected, "x" * 5000)
    assert len(setup.candidates.await_args.args[-1]) == 4000
    assert len(selected.interpret.await_args.args[0]) == 4000
