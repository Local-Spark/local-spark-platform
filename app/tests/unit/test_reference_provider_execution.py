from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.services import reference_provider_execution as module
from app.services.reference_context_loader import LoadedSearchContext
from app.tests.unit.test_reference_execution_store import candidate, state
from app.workflows.contracts import BusinessEvent


def event():
    return BusinessEvent(*[str(uuid4()) for _ in range(5)])


def runner(settings, monkeypatch):
    monkeypatch.setattr(type(settings), "reference_discovery_ready", lambda _: True)
    settings.reference_provider_hmac_key = SecretStr("synthetic-key-012345678901234567890")
    settings.reference_provider_key_version = "test-v1"
    settings.reference_provider_pilot_id = uuid4()
    session = SimpleNamespace(scalar=AsyncMock())

    @asynccontextmanager
    async def transaction(*_):
        yield session

    value = module.ReferenceProviderExecution(SimpleNamespace(transaction=transaction), settings)
    value._progress = AsyncMock()
    monkeypatch.setattr(
        module, "load_search_context", AsyncMock(return_value=LoadedSearchContext(1, 5, 1, 1, ("cafe",), None))
    )
    return value, session


async def test_disabled_and_unexpected_failure_never_disclose_activity_inputs(settings, monkeypatch):
    r, _ = runner(settings, monkeypatch)
    monkeypatch.setattr(type(settings), "reference_discovery_ready", lambda _: False)
    assert await r.run(event()) == "disabled"
    monkeypatch.setattr(type(settings), "reference_discovery_ready", lambda _: True)
    r._run = AsyncMock(side_effect=RuntimeError("private source data"))
    with pytest.raises(module.ReferenceExecutionError, match="^REFERENCE_EXECUTION_INCOMPLETE$"):
        await r.run(event())
    r._progress = AsyncMock(side_effect=RuntimeError("private DB diagnostic"))
    with pytest.raises(module.ReferenceExecutionError, match="^REFERENCE_EXECUTION_INCOMPLETE$"):
        await r.run(event())


@pytest.mark.parametrize(
    "status,execution,expected",
    [
        ("completed", "completed", "completed"),
        ("cancelled", "type_mapping_unavailable", "type_mapping_unavailable"),
        ("failed", "provider_uncertain", "unavailable"),
    ],
)
async def test_terminal_search_is_reused_without_provider_work(settings, monkeypatch, status, execution, expected):
    r, _ = runner(settings, monkeypatch)
    r._state = AsyncMock(return_value=state(state=status, execution_status=execution))
    assert await r.run(event()) == expected
    module.load_search_context.assert_not_awaited()


@pytest.mark.parametrize(
    "google_state,expected", [("uncertain", "provider_uncertain"), ("completed_empty", "radius_successor")]
)
async def test_sent_google_without_response_is_never_dispatched_again(settings, monkeypatch, google_state, expected):
    r, _ = runner(settings, monkeypatch)
    old = state(batch_id=None, source_batch_mac=None)
    google = old.effects[0].model_copy(update={"state": google_state})
    r._state = AsyncMock(return_value=old.model_copy(update={"effects": (google,)}))
    r._map = AsyncMock(return_value=("coffee_shop",))
    r._discover = AsyncMock()
    r._empty = AsyncMock(return_value="radius_successor")
    assert await r.run(event()) == expected
    r._discover.assert_not_awaited()


async def test_own_review_pauses_without_preparing_shortlist_or_buying_contacts(settings, monkeypatch):
    from app.services.reference_own_review import ReferenceOwnReviewService

    r, session = runner(settings, monkeypatch)
    r._state = AsyncMock(return_value=state(execution_status="running"))
    monkeypatch.setattr(
        ReferenceOwnReviewService,
        "read",
        AsyncMock(return_value=SimpleNamespace(status="awaiting_confirmation", excluded_place_id=None)),
    )
    assert await r.run(event()) == "awaiting_own_review"
    session.scalar.assert_not_awaited()


@pytest.mark.parametrize(
    "outcome,expected",
    [
        ("pending", "contacts_pending"),
        ("failed", "contacts_failed"),
        ("uncertain", "provider_uncertain"),
        (None, "completed"),
    ],
)
async def test_incomplete_contacts_dont_publish_partial_selection(settings, monkeypatch, outcome, expected):
    from app.services.reference_own_review import ReferenceOwnReviewService

    r, _ = runner(settings, monkeypatch)
    r._state = AsyncMock(return_value=state(candidates=(candidate("8", "high", 1),)))
    monkeypatch.setattr(
        ReferenceOwnReviewService,
        "read",
        AsyncMock(return_value=SimpleNamespace(status="resolved", excluded_place_id=None)),
    )
    r._recommend = AsyncMock(return_value=None)
    r._contacts = AsyncMock(return_value=outcome)
    publish = AsyncMock(return_value=uuid4())
    monkeypatch.setattr(module, "publish_reference_shortlist", publish)
    assert await r.run(event()) == expected
    assert publish.await_count == (1 if outcome is None else 0)


async def test_recommendation_failure_never_fabricates_highlights(settings, monkeypatch):
    r, _ = runner(settings, monkeypatch)
    ev = event()
    search = uuid4()
    ctx = LoadedSearchContext(1, 5, 1, 1, ("cafe",), None)
    candidates = (candidate("8", "high", 1),)
    old = state()
    prior = old.effects[1].model_copy(update={"purpose": "recommendation", "state": "uncertain", "output": None})
    value = old.model_copy(update={"effects": (*old.effects, prior)})
    assert await r._recommend(ev, search, value, ctx, candidates) is None
    assert await r._recommend(ev, search, old, ctx, ()) is None
    prior = prior.model_copy(update={"output": {"candidate_ids": [str(candidates[0].candidate_id)]}, "token": None})
    value = value.model_copy(update={"effects": (*old.effects, prior)})
    with pytest.raises(module.ReferenceExecutionError, match="REFERENCE_RECOMMENDATION_INVALID"):
        await r._recommend(ev, search, value, ctx, candidates)
    prior = prior.model_copy(update={"token": uuid4()})
    result = await r._recommend(
        ev, search, value.model_copy(update={"effects": (*old.effects, prior)}), ctx, candidates
    )
    assert result.candidate_ids == (candidates[0].candidate_id,)


async def test_mapping_reuses_stored_conclusion_and_does_not_repeat_unknown_send(settings, monkeypatch):
    r, _ = runner(settings, monkeypatch)
    ev = event()
    search = uuid4()
    ctx = LoadedSearchContext(1, 5, 1, 1, ("cafe",), None)
    old = state()
    prior = old.effects[1].model_copy(update={"purpose": "mapping", "output": {"state": "uncertain", "types": []}})
    assert await r._map(ev, search, old.model_copy(update={"effects": (prior,)}), ctx) == ()
    prior = prior.model_copy(update={"output": None, "state": "uncertain"})
    with pytest.raises(module.ReferenceExecutionError, match="REFERENCE_MAPPING_UNCERTAIN"):
        await r._map(ev, search, old.model_copy(update={"effects": (prior,)}), ctx)


@pytest.mark.parametrize("cache,expected", [("completed", None), ("pending", "pending")])
async def test_other_radius_cache_avoids_another_apify_submission(settings, monkeypatch, cache, expected):
    r, _ = runner(settings, monkeypatch)
    item = candidate("8", "high", 1).model_copy(update={"contacts_cache": cache})
    assert await r._contacts(event(), uuid4(), state(), item) == expected


async def test_pending_google_intent_can_dispatch_but_a_claimed_send_cannot(settings, monkeypatch):
    r, _ = runner(settings, monkeypatch)
    empty = state(batch_id=None, source_batch_mac=None)
    google = empty.effects[0].model_copy(update={"state": "pending", "token": None})
    first = empty.model_copy(update={"effects": (google,)})
    after = empty.model_copy(update={"effects": (google.model_copy(update={"state": "completed_empty"}),)})
    r._state = AsyncMock(side_effect=[first, after])
    r._map = AsyncMock(return_value=("coffee_shop",))
    r._discover = AsyncMock()
    r._empty = AsyncMock(return_value="completed")
    assert await r.run(event()) == "completed"
    r._discover.assert_awaited_once()


async def test_stored_contact_projection_survives_a_crash_before_publication(settings, monkeypatch):
    r, _ = runner(settings, monkeypatch)
    item = candidate("8", "high", 1)
    value = state()
    prior = value.effects[0].model_copy(
        update={
            "provider": "apify",
            "candidate_id": item.candidate_id,
            "attempt_no": 1,
            "state": "running",
            "output": {"handles": ["cafe.real"], "primary_handle": "cafe.real"},
        }
    )
    value = value.model_copy(update={"effects": (*value.effects, prior)})
    result = await r._contacts(event(), uuid4(), value, item)
    assert result.handles == ("cafe.real",) and result.effect.executor_token == prior.token


@pytest.mark.parametrize("prior_state", ["uncertain", "pending"])
async def test_missing_run_identity_never_repeats_a_sent_post_and_unknown_cost_stays_reserved(
    settings, monkeypatch, prior_state
):
    from app.adapters.apify_place_contacts import PlaceContactsResult

    r, _ = runner(settings, monkeypatch)
    item = candidate("8", "high", 1)
    value = state()
    prior = value.effects[0].model_copy(
        update={
            "provider": "apify",
            "candidate_id": item.candidate_id,
            "attempt_no": 1,
            "state": prior_state,
            "output": None,
        }
    )
    value = value.model_copy(update={"effects": (*value.effects, prior)})
    monkeypatch.setattr(module, "load_contacts_run", AsyncMock(return_value=None))
    adapter = SimpleNamespace(
        submit=AsyncMock(return_value=object()),
        inspect=AsyncMock(return_value=PlaceContactsResult("not_found_unconfirmed")),
    )
    monkeypatch.setattr(module, "ApifyPlaceContacts", lambda *_args, **_kwargs: adapter)
    monkeypatch.setattr(module, "IntentContactsGuard", lambda *_: SimpleNamespace(execution_token=lambda: prior.token))
    monkeypatch.setattr(module, "record_contacts_run", AsyncMock())
    cost = AsyncMock()
    output = AsyncMock()
    monkeypatch.setattr(module, "record_contacts_cost", cost)
    monkeypatch.setattr(module, "record_output", output)
    result = await r._contacts(event(), uuid4(), value, item)
    if prior_state == "uncertain":
        assert result == "uncertain"
        adapter.submit.assert_not_awaited()
    else:
        assert result.handles == () and result.primary_handle is None
        adapter.submit.assert_awaited_once()
        assert output.call_args.args[-1] == {"handles": [], "primary_handle": None}
    cost.assert_not_awaited()
