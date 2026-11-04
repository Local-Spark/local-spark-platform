"""Equal event contents cannot replace the event bound to a durable intent."""

from dataclasses import replace
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.adapters.jev_reference_similarity import SimilarityCandidate, SimilarityInput
from app.db.session import Database
from app.services.reference_google_intent import create_google_intent
from app.services.reference_jev_budget_guard import DatabaseJevBudgetGuard
from app.services.reference_places_budget_guard import DatabasePlacesBudgetGuard
from app.tests.integration.test_reference_google_intent import _parent
from app.tests.integration.test_reference_jev_budget_guard import _google_started, _jev_intent
from app.tests.integration.test_reference_places_budget_guard import _request

pytestmark = pytest.mark.integration


async def _duplicate_event(admin, context):
    event = uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
          SELECT :new,tenant_id,event_type,payload FROM outbox_events WHERE id=:original"""),
            {"new": event, "original": context.event},
        )
    return event


async def test_google_claim_requires_original_event(admin, api, seeded, settings):
    context = await _parent(admin, api, seeded, settings)
    worker = Database(settings, correlator=True)
    try:
        context = await create_google_intent(worker, context, _request())
        duplicate = await _duplicate_event(admin, context)
        with pytest.raises(DBAPIError, match="REFERENCE_PROVIDER_EVENT_INVALID"):
            await DatabasePlacesBudgetGuard(worker, replace(context, event=duplicate)).claim(context.effect, _request())
        assert await DatabasePlacesBudgetGuard(worker, context).claim(context.effect, _request()) is True
        with pytest.raises(DBAPIError, match="REFERENCE_PROVIDER_EVENT_INVALID"):
            await DatabasePlacesBudgetGuard(worker, replace(context, event=duplicate)).claim(context.effect, _request())
    finally:
        await worker.close()


async def test_jev_claim_requires_original_event(admin, api, seeded, settings):
    parent, google, worker = await _google_started(admin, api, seeded, settings)
    data = SimilarityInput(("cafe",), None, (SimilarityCandidate(uuid4(), "fixture", ("cafe",)),))
    context, request = await _jev_intent(admin, worker, parent, google.execution_token(), data)
    try:
        duplicate = await _duplicate_event(admin, context)
        with pytest.raises(DBAPIError, match="REFERENCE_PROVIDER_EVENT_INVALID"):
            await DatabaseJevBudgetGuard(worker, replace(context, event=duplicate)).claim(context.effect, request)
        assert await DatabaseJevBudgetGuard(worker, context).claim(context.effect, request) is True
        with pytest.raises(DBAPIError, match="REFERENCE_PROVIDER_EVENT_INVALID"):
            await DatabaseJevBudgetGuard(worker, replace(context, event=duplicate)).claim(context.effect, request)
    finally:
        await worker.close()
