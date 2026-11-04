from dataclasses import replace
from unittest.mock import AsyncMock
from uuid import uuid4, uuid5

import pytest
from pydantic import SecretStr

from app.adapters.apify_instagram_feed import FeedChargeableRequest, FeedInspectionIntent
from app.adapters.reference_feed_image import FeedImageIntent
from app.services.reference_learning_guards import LearningFeedGuard, LearningImageGuard
from app.tests.unit.test_reference_learning_execution import setup


def request(url, method="GET"):
    return FeedChargeableRequest(method, url, b"", SecretStr("synthetic"), ())


async def test_claim_is_one_shot_and_recovers_executor(settings, monkeypatch):
    r, w, _ = setup(settings, monkeypatch)
    context = r._context(w)
    token = uuid4()
    r.store.claim_feed = AsyncMock(return_value={"created": True, "executor_token": str(token)})
    g = LearningFeedGuard(r.database, context, r.store, w)
    monkeypatch.setattr(g, "_request_mac", lambda _: "a" * 64)
    with pytest.raises(ValueError, match="EXECUTOR_REQUIRED"):
        g.execution_token()
    assert not await g.claim_submission(uuid4(), request(""))
    assert await g.claim_submission(context.effect, request(""))
    assert g.execution_token() == token
    assert not await g.claim_submission(context.effect, request(""))
    r.store.claim_feed.assert_awaited_once()
    g = LearningFeedGuard(r.database, context, r.store, w)
    r.store.claim_feed.return_value = {"created": False}
    assert not await g.claim_submission(context.effect, request(""))


def inspection(run):
    return FeedInspectionIntent(
        run,
        request(f"https://api.apify.com/v2/actor-runs/{run.run_id}"),
        request(f"https://api.apify.com/v2/datasets/{run.dataset_id}/items?clean=true&limit=21"),
    )


@pytest.mark.parametrize(
    "change",
    ["none", "run", "operation", "run_method", "dataset_method", "run_url", "dataset_url", "allowed", "denied"],
)
async def test_inspection_binds_saved_run_and_both_gets(settings, monkeypatch, change):
    r, w, _ = setup(settings, monkeypatch)
    context = r._context(w)
    run = w.submitted_run()
    g = LearningFeedGuard(r.database, context, r.store, w, run=run, token=w.feed.executor_token)
    intent = inspection(run)
    operation = uuid5(context.effect, "reference-feed-inspection-v1")
    if change == "none":
        g.run = None
    if change == "run":
        intent = replace(intent, submission=replace(run, run_id="other"))
    if change == "operation":
        operation = uuid4()
    if change == "run_method":
        intent = replace(intent, run_request=replace(intent.run_request, method="POST"))
    if change == "dataset_method":
        intent = replace(intent, dataset_request=replace(intent.dataset_request, method="POST"))
    if change == "run_url":
        intent = replace(intent, run_request=replace(intent.run_request, url="https://example.com"))
    if change == "dataset_url":
        intent = replace(intent, dataset_request=replace(intent.dataset_request, url="https://example.com"))
    if change == "denied":
        r.store.authorize.return_value = False
    assert await g.claim_inspection(operation, intent) == (change == "allowed")
    if change == "allowed":
        await g.inspection_uncertain(operation, intent)
    else:
        with pytest.raises(ValueError, match="INSPECTION_INVALID"):
            await g.inspection_uncertain(operation, intent)


@pytest.mark.parametrize("change", ["operation", "method", "run", "post", "url", "allowed", "denied"])
async def test_image_read_is_bound_to_transient_post_and_current_selection(settings, monkeypatch, change):
    r, w, _ = setup(settings, monkeypatch)
    run = w.submitted_run()
    operation = uuid4()
    g = LearningImageGuard(r.store, w, run, w.feed.executor_token, operation, "post", "https://cdninstagram.com/a.jpg")
    intent = FeedImageIntent(run, "post", "https://cdninstagram.com/a.jpg")
    if change == "operation":
        operation = uuid4()
    if change == "method":
        intent = replace(intent, method="POST")
    if change == "run":
        intent = replace(intent, run=replace(run, run_id="other"))
    if change == "post":
        intent = replace(intent, post_id="other")
    if change == "url":
        intent = replace(intent, url="https://cdninstagram.com/other.jpg")
    if change == "denied":
        r.store.authorize.return_value = False
    assert await g.authorize(operation, intent) == (change == "allowed")
