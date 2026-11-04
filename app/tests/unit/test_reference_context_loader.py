from contextlib import asynccontextmanager
from unittest.mock import AsyncMock
from uuid import uuid4, uuid5

import pytest
from pydantic import SecretStr

from app.services.reference_context_loader import ReferenceContextLoadError, load_search_context
from app.services.reference_search_admission import search_identity_mac


async def test_context_loader_binds_the_search_and_key_before_exposing_context():
    tenant, business, actor, operation, event = (uuid4() for _ in range(5))
    search = uuid5(operation, f"reference-provider-search-v1:{tenant}:{business}")
    key = SecretStr("synthetic-reference-search-key-0123456789")
    payload = {
        "operation_id": str(operation),
        "context_version": 1,
        "radius_km": 5,
        "identity_key_version": "test-v1",
        "request_mac": search_identity_mac(key, "test-v1", tenant, business, actor, operation, 1, 5),
        "latitude": 1.0,
        "longitude": 2.0,
        "business_terms": ["Café"],
        "business_description": "Bairro",
    }
    session = AsyncMock()
    session.scalar.return_value = payload

    class _Database:
        @asynccontextmanager
        async def transaction(self, tenant_id, actor_id):
            assert tenant_id == tenant and actor_id == actor
            yield session

    database = _Database()
    context = await load_search_context(database, {"test-v1": key}, tenant, business, actor, search, event)
    assert context.business_terms == ("Café",) and context.latitude == 1.0 and context.radius_km == 5
    assert "Café" not in repr(context)
    for changed, keys, search_id in (
        ({**payload, "request_mac": "a" * 64}, {"test-v1": key}, search),
        (payload, {}, search),
        (payload, {"test-v1": key}, uuid4()),
        ({**payload, "business_terms": []}, {"test-v1": key}, search),
        ({**payload, "latitude": 300.0}, {"test-v1": key}, search),
        ({**payload, "extra": "private"}, {"test-v1": key}, search),
        (payload, {"test-v1": SecretStr("short")}, search),
    ):
        session.scalar.return_value = changed
        with pytest.raises(ReferenceContextLoadError, match="REFERENCE_CONTEXT_INTEGRITY_INVALID") as error:
            await load_search_context(database, keys, tenant, business, actor, search_id, event)
        assert "private" not in str(error.value)
