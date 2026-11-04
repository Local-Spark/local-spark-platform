"""Authorized context stays within a worker transaction, using fixture data."""

from uuid import uuid4

import pytest
from sqlalchemy.exc import DBAPIError

from app.db.session import Database
from app.services.reference_context_loader import ReferenceContextLoadError, load_search_context
from app.services.reference_search_admission import admit_provider_search
from app.tests.integration.test_reference_discovery import local_scope, save_scope
from app.tests.integration.test_reference_search_admission import _KEY, _business

pytestmark = pytest.mark.integration


async def test_loader_requires_owner_search_event_and_current_version(admin, api, seeded, settings, database):
    tenant, actor, business, base, headers = await _business(admin, api, seeded, settings)
    search = await admit_provider_search(database, _KEY, "test-v1", tenant, business, actor, uuid4(), 1, 5)
    worker = Database(settings, correlator=True)
    try:
        result = await load_search_context(
            worker, {"test-v1": _KEY}, tenant, business, actor, search.search_id, search.event_id
        )
        assert result.radius_km == 5 and result.business_terms == ("Café",)
        assert result.latitude == -23.55 and result.longitude == -46.63
        with pytest.raises(DBAPIError, match="REFERENCE_CONTEXT_LOAD_INVALID"):
            await load_search_context(worker, {"test-v1": _KEY}, tenant, business, actor, search.search_id, uuid4())
        with pytest.raises(DBAPIError, match="REFERENCE_OWNER_INACTIVE"):
            await load_search_context(
                worker, {"test-v1": _KEY}, tenant, business, seeded["viewer"], search.search_id, search.event_id
            )
        with pytest.raises(ReferenceContextLoadError, match="REFERENCE_CONTEXT_INTEGRITY_INVALID"):
            await load_search_context(worker, {}, tenant, business, actor, search.search_id, search.event_id)
        assert (await save_scope(api, base, headers, 1, local_scope(20))).status_code == 200
        with pytest.raises(DBAPIError, match="REFERENCE_CONTEXT_LOAD_INVALID"):
            await load_search_context(
                worker, {"test-v1": _KEY}, tenant, business, actor, search.search_id, search.event_id
            )
    finally:
        await worker.close()
