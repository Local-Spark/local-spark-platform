from contextlib import asynccontextmanager
from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4, uuid5

import pytest

from app.services.reference_feed_budget_guard import FeedGuardContext
from app.services.reference_learning_projection import DerivedPattern
from app.services.reference_learning_store import (
    LearningWindow,
    ReferenceLearningStore,
    StoredFeedRun,
    StoredLearningFeed,
)
from app.tests.unit.test_reference_feed_request_mac import example
from app.workflows.contracts import BusinessEvent


class Database:
    def __init__(self, result=None):
        self.result = result
        self.calls = []

    @asynccontextmanager
    async def transaction(self, tenant, actor):
        self.calls.append((tenant, actor))
        yield self

    async def scalar(self, sql, params):
        self.calls.append((str(sql), params))
        return self.result


def window():
    return LearningWindow(
        **{name: uuid4() for name in ("tenant", "business", "actor", "window", "event", "reference")},
        association_version=1,
        profile="synthetic",
        accepted_at=datetime.now(UTC),
        scheduled_at=datetime.now(UTC),
        state="pending",
        feed=StoredLearningFeed(
            effect=uuid4(),
            event=uuid4(),
            pilot=uuid4(),
            state="running",
            executor_token=uuid4(),
            key_version="v1",
            tariff_version="v1",
            credential_version="v1",
            build="1.2.3",
            reserved_usd_micros=50_000,
            request_mac="a" * 64,
            run=StoredFeedRun(
                run_id="run",
                dataset_id="dataset",
                store_id="store",
                queue_id="queue",
                build_id="build",
                actor_build="1.2.3",
            ),
        ),
    )


async def test_load_uses_event_scope_and_run_is_reconstructed_without_provider_content():
    w = window()
    db = Database(w.model_dump(mode="json"))
    event = BusinessEvent(str(w.event), str(w.tenant), str(w.business), str(w.actor), str(w.window))
    loaded = await ReferenceLearningStore(db).load(event)
    assert loaded == w and db.calls[0] == (w.tenant, w.actor)
    assert db.calls[1][1] == {"business": w.business, "window": w.window, "event": w.event}
    run = loaded.submitted_run()
    assert run.username == "synthetic" and run.submission_id == w.feed.effect and run.results_limit == 20
    assert w.model_copy(update={"feed": None}).submitted_run() is None
    assert w.model_copy(update={"feed": w.feed.model_copy(update={"run": None})}).submitted_run() is None


async def test_claim_binds_full_scope_and_exact_request():
    values = example()
    request = values.pop("request")
    context = FeedGuardContext(**values, event=uuid4())
    db = Database({"created": True})
    assert await ReferenceLearningStore(db).claim_feed(context, request) == {"created": True}
    assert db.calls[0] == (context.tenant, context.actor)
    params = db.calls[1][1]
    assert params["reference"] == context.reference and params["version"] == 1
    assert params["profile"] == context.profile and len(params["mac"]) == 64
    assert context.key.get_secret_value() not in str(params)


@pytest.mark.parametrize("change", [{"username": "different"}, {"submission_id": uuid4()}, {"results_limit": 19}])
async def test_authorize_and_record_reject_unbound_run_without_database(change):
    w = window()
    db = Database()
    store = ReferenceLearningStore(db)
    invalid = replace(w.submitted_run(), **change)
    assert not await store.authorize(w, w.feed.effect, w.feed.executor_token, invalid)
    with pytest.raises(ValueError, match="RUN_INVALID"):
        await store.record_run(w, w.feed.effect, w.feed.executor_token, invalid)
    assert db.calls == []


@pytest.mark.parametrize("answer,allowed", [(True, True), (False, False), (None, False)])
async def test_authorize_requires_explicit_database_fence(answer, allowed):
    w = window()
    db = Database(answer)
    assert (
        await ReferenceLearningStore(db).authorize(w, w.feed.effect, w.feed.executor_token, w.submitted_run())
        is allowed
    )
    assert db.calls[1][1]["run"] == "run"


async def test_record_finish_and_block_store_only_derived_information():
    w = window()
    db = Database({"state": "completed"})
    store = ReferenceLearningStore(db)
    await store.record_run(w, w.feed.effect, w.feed.executor_token, w.submitted_run())
    assert db.calls[1][1]["operation"] == uuid5(w.feed.effect, "reference-feed-resources-v1")
    result = await store.finish(
        w,
        w.feed.effect,
        w.feed.executor_token,
        patterns=(DerivedPattern(dimension="editorial", observation="Tom acolhedor e próximo."),),
        status="completed",
        posts=1,
        images=2,
        coverage="unconfirmed",
        profile_name="Synthetic",
    )
    assert result == {"state": "completed"}
    assert db.calls[3][1]["profile_name"] == "Synthetic" and db.calls[3][1]["images"] == 2
    assert "Tom acolhedor" in db.calls[3][1]["patterns"]
    await store.block(w, "budget")
    assert db.calls[5][1] == {"business": w.business, "window": w.window, "reason": "budget"}
