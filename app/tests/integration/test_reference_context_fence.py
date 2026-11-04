"""A context update blocks only new effects, not recovery of admitted ones."""

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.adapters.jev_reference_similarity import SimilarityCandidate, SimilarityInput
from app.db.session import Database
from app.services.reference_google_intent import create_google_intent
from app.services.reference_jev_budget_guard import DatabaseJevBudgetGuard
from app.services.reference_jev_intent import create_jev_intent
from app.services.reference_places_budget_guard import DatabasePlacesBudgetGuard
from app.tests.integration.test_reference_geocoding_ledger import _claim as geocode_claim
from app.tests.integration.test_reference_geocoding_ledger import _effect as geocode_effect
from app.tests.integration.test_reference_geocoding_ledger import _revoke as revoke_geocode
from app.tests.integration.test_reference_geocoding_ledger import _setup as geocode_setup
from app.tests.integration.test_reference_google_intent import _parent
from app.tests.integration.test_reference_jev_budget_guard import _google_started, _jev_intent
from app.tests.integration.test_reference_places_budget_guard import _request

pytestmark = pytest.mark.integration


async def _set_context(admin, context, version):
    async with admin.begin() as connection:
        await connection.execute(
            text(
                "UPDATE business_context_heads SET version=:version WHERE tenant_id=:tenant AND business_id=:business"
            ),
            {"version": version, "tenant": context.tenant, "business": context.business},
        )


async def test_google_intent_and_claim_require_current_context_but_replay_survives(admin, api, seeded, settings):
    context = await _parent(admin, api, seeded, settings)
    worker = Database(settings, correlator=True)
    try:
        await _set_context(admin, context, 2)
        with pytest.raises(DBAPIError, match="REFERENCE_CONTEXT_STALE"):
            await create_google_intent(worker, context, _request())
        await _set_context(admin, context, 1)
        context = await create_google_intent(worker, context, _request())
        await _set_context(admin, context, 2)
        assert (await create_google_intent(worker, context, _request())).event == context.event
        with pytest.raises(DBAPIError, match="REFERENCE_CONTEXT_STALE"):
            await DatabasePlacesBudgetGuard(worker, context).claim(context.effect, _request())
        await _set_context(admin, context, 1)
        assert await DatabasePlacesBudgetGuard(worker, context).claim(context.effect, _request()) is True
        await _set_context(admin, context, 2)
        assert await DatabasePlacesBudgetGuard(worker, context).claim(context.effect, _request()) is False
    finally:
        await worker.close()


async def test_jev_intent_and_claim_require_current_context_but_replay_survives(admin, api, seeded, settings):
    parent, google, worker = await _google_started(admin, api, seeded, settings)
    data = SimilarityInput(("cafe",), None, (SimilarityCandidate(uuid4(), "fixture", ("cafe",)),))
    context, request = await _jev_intent(admin, worker, parent, google.execution_token(), data, create=False)
    try:
        await _set_context(admin, parent, 2)
        with pytest.raises(DBAPIError, match="REFERENCE_CONTEXT_STALE"):
            await create_jev_intent(worker, context, parent.event, request)
        await _set_context(admin, parent, 1)
        await create_jev_intent(worker, context, parent.event, request)
        await _set_context(admin, parent, 2)
        assert (await create_jev_intent(worker, context, parent.event, request)).event == context.event
        with pytest.raises(DBAPIError, match="REFERENCE_CONTEXT_STALE"):
            await DatabaseJevBudgetGuard(worker, context).claim(context.effect, request)
        await _set_context(admin, parent, 1)
        assert await DatabaseJevBudgetGuard(worker, context).claim(context.effect, request) is True
        await _set_context(admin, parent, 2)
        assert await DatabaseJevBudgetGuard(worker, context).claim(context.effect, request) is False
    finally:
        await worker.close()


async def test_geocode_blocks_stale_context_but_preserves_replay(admin, api, seeded, settings):
    parent, tariff = await geocode_setup(admin, api, seeded, settings)
    values = await geocode_effect(admin, parent, tariff)
    worker = Database(settings, correlator=True)
    try:
        await _set_context(admin, parent, 2)
        with pytest.raises(DBAPIError, match="REFERENCE_CONTEXT_STALE"):
            await geocode_claim(worker, parent, values)
        await _set_context(admin, parent, 1)
        assert (await geocode_claim(worker, parent, values))["created"] is True
        await _set_context(admin, parent, 2)
        assert (await geocode_claim(worker, parent, values))["created"] is False
    finally:
        await worker.close()
        await revoke_geocode(admin)


async def test_concurrent_context_update_committed_before_claim_blocks_spending(admin, api, seeded, settings):
    context = await _parent(admin, api, seeded, settings)
    worker = Database(settings, correlator=True)
    try:
        context = await create_google_intent(worker, context, _request())
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE business_context_heads SET version=2 WHERE tenant_id=:tenant AND business_id=:business"),
                {"tenant": context.tenant, "business": context.business},
            )
            claim = asyncio.create_task(DatabasePlacesBudgetGuard(worker, context).claim(context.effect, _request()))
            await asyncio.sleep(0.15)
            assert not claim.done()
        with pytest.raises(DBAPIError, match="REFERENCE_CONTEXT_STALE"):
            await asyncio.wait_for(claim, 3)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT reserved_usd_micros FROM reference_provider_pilots")) == 0
    finally:
        await worker.close()
