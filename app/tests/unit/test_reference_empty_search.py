from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.schemas.business_address import ShopAddress
from app.services.reference_business_identity_mac import BusinessIdentityBindingError, business_identity_mac
from app.services.reference_empty_search import advance_empty_search


class Database:
    def __init__(self, values):
        self.values = iter(values)
        self.calls = []

    @asynccontextmanager
    async def transaction(self, tenant, actor):
        yield self

    async def scalar(self, sql, params):
        self.calls.append((str(sql), params))
        return next(self.values)


def context():
    tenant, business, actor, root, operation = [uuid4() for _ in range(5)]
    key = SecretStr("synthetic-empty-family-key-0123456789")
    address = ShopAddress(street="Rua Ficticia", number="10", city="São Paulo", state_code="SP")
    value = {
        "root_id": str(root),
        "root_operation": str(operation),
        "context_version": 1,
        "key_version": "v1",
        "row_version": 1,
        "address_version": 1,
        "location_version": None,
        "name": "Loja Teste",
        "address": address.model_dump(mode="json"),
        "next_radius": 20,
    }
    value["identity_mac"] = business_identity_mac(
        key,
        key_version="v1",
        tenant=tenant,
        business=business,
        search=root,
        search_actor=actor,
        context_version=1,
        business_row_version=1,
        address_version=1,
        location_version=None,
        name=value["name"],
        address=address,
    )
    return tenant, business, actor, root, key, value


@pytest.mark.parametrize("field,value", [("key_version", "v2"), ("identity_mac", "f" * 64)])
async def test_untrusted_identity_never_schedules_an_effect(field, value):
    tenant, business, actor, root, key, stored = context()
    db = Database([None, stored | {field: value}])
    with pytest.raises(BusinessIdentityBindingError):
        await advance_empty_search(db, key, "v1", tenant, business, actor, root)
    assert len(db.calls) == 2


async def test_cached_empty_chain_continues_without_repeating_a_source_effect():
    tenant, business, actor, root, key, stored = context()
    next_search, result = uuid4(), uuid4()
    db = Database(
        [
            None,
            stored,
            {"state": "cached", "next_search_id": str(next_search), "result_id": None, "next_empty": True},
            None,
            stored | {"next_radius": None},
            result,
        ]
    )
    value = await advance_empty_search(db, key, "v1", tenant, business, actor, root)
    assert value.state == "exhausted" and value.result_id == result
    assert db.calls[-1][1]["parent"] == next_search


async def test_replayed_cached_empty_link_can_reach_a_published_cached_result():
    tenant, business, actor, root, key, stored = context()
    next_search, final, result = uuid4(), uuid4(), uuid4()
    db = Database(
        [
            {
                "state": "cached",
                "root_id": str(root),
                "next_search_id": str(next_search),
                "result_id": None,
                "next_empty": True,
            },
            None,
            stored,
            {"state": "cached", "next_search_id": str(final), "result_id": str(result), "next_empty": False},
        ]
    )
    value = await advance_empty_search(db, key, "v1", tenant, business, actor, root)
    assert value.state == "cached" and value.result_id == result and value.next_search_id == final


@pytest.mark.parametrize("state,has_next,has_result", [("scheduled", True, False), ("exhausted", False, True)])
async def test_committed_replay_needs_neither_current_head_nor_identity_recomputation(state, has_next, has_result):
    tenant, business, actor, root, key, _ = context()
    next_search = uuid4() if has_next else None
    result = uuid4() if has_result else None
    db = Database(
        [
            {
                "state": state,
                "root_id": str(root),
                "next_search_id": str(next_search) if next_search else None,
                "result_id": str(result) if result else None,
                "next_empty": False,
            }
        ]
    )
    outcome = await advance_empty_search(db, key, "rotated-key-version", tenant, business, actor, root)
    assert outcome.state == state and outcome.next_search_id == next_search and outcome.result_id == result
    assert len(db.calls) == 1
