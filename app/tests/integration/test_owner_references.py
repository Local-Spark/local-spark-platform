import asyncio
import json
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.schemas.owner_references import ReferenceCreate
from app.services.outbox import claim_events
from app.services.owner_references import OwnerReferencesService
from app.tests.unit.test_core import access_token

pytestmark = pytest.mark.integration


async def test_indications_replay_remove_and_tenant_isolation(admin, api, seeded, settings, database, relay_database):
    tenant, actor, business = seeded["t1"], seeded["a1"], uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Test','UTC')"),
            {"id": business, "tenant": tenant},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles
          (tenant_id,business_id,category,city,description,phone,brand_color)
          VALUES(:tenant,:business,'Food','Rio','Test','+5511999999999','#6557ed')"""),
            {"tenant": tenant, "business": business},
        )
    base = f"/api/v1/organizations/{tenant}/businesses/{business}/references"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    viewer = {"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"}
    other = {"Authorization": f"Bearer {access_token(settings, seeded['a2'])}"}
    payload = {"operation_id": str(uuid4()), "instagram": "@Cafe.Exemplo", "note": "gosto das fotos"}
    assert (await api.post(base, headers=viewer, json=payload)).status_code == 403
    assert (await api.get(base, headers=other)).status_code == 403
    assert (await api.get(base, headers=owner)).json() == []
    first = await api.post(base, headers=owner, json=payload)
    assert first.status_code == 200, first.text
    item = first.json()
    assert item["instagram_handle"] == "cafe.exemplo"
    assert item["instagram_url"] == "https://www.instagram.com/cafe.exemplo/"
    assert item["access_status"] == "not_checked" and item["selected"] is True
    assert (await api.post(base, headers=owner, json=payload)).json() == item
    changed = {**payload, "note": "outra"}
    assert (await api.post(base, headers=owner, json=changed)).json()["error_code"] == "REFERENCE_OPERATION_CONFLICT"
    duplicate = {**payload, "operation_id": str(uuid4())}
    assert (await api.post(base, headers=owner, json=duplicate)).json()["error_code"] == "REFERENCE_ALREADY_EXISTS"
    assert (await api.get(base, headers=owner)).json() == [item]
    op = str(uuid4())
    remove = {"operation_id": op}
    url = f"{base}/{item['id']}"
    assert (await api.request("DELETE", url, headers=other, json=remove)).status_code == 403
    assert (await api.request("DELETE", url, headers=owner, json=remove)).status_code == 204
    assert (await api.request("DELETE", url, headers=owner, json=remove)).status_code == 204
    assert (await api.get(base, headers=owner)).json() == []
    assert (await api.post(base, headers=owner, json=payload)).json() == item
    assert (await api.request("DELETE", url, headers=owner, json={"operation_id": str(uuid4())})).status_code == 404
    assert (await api.post(base, headers=owner, json=duplicate)).status_code == 200
    assert (await api.request("DELETE", f"{base}/{uuid4()}", headers=owner, json=remove)).json()[
        "error_code"
    ] == "REFERENCE_OPERATION_CONFLICT"
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM owner_references")) == 2
        assert await connection.scalar(text("SELECT count(*) FROM owner_references WHERE removed_at IS NOT NULL")) == 1
        assert (
            await connection.scalar(
                text("SELECT count(*) FROM audit_events WHERE action IN ('reference.created','reference.removed')")
            )
            == 3
        )
        events = (
            (
                await connection.execute(
                    text(
                        "SELECT event_type,payload,state,attempts FROM outbox_events WHERE event_type IN ('ref\
erence.created','reference.removed')"
                    )
                )
            )
            .mappings()
            .all()
        )
        assert sorted(event["event_type"] for event in events) == [
            "reference.created",
            "reference.created",
            "reference.removed",
        ]
        assert (
            await connection.scalar(
                text("SELECT count(*) FROM outbox_events WHERE event_type='reference.learning_requested'")
            )
            == 2
        )
        assert all(event["state"] == "pending" and event["attempts"] == 0 for event in events)
        assert all(
            set(event["payload"]) == {"business_id", "actor_id", "operation_id", "reference_id"} for event in events
        )
    assert await claim_events(relay_database, uuid4()) == []
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
              VALUES(:id,:tenant,'business.created',CAST(:payload AS jsonb))"""),
            {
                "id": uuid4(),
                "tenant": tenant,
                "payload": json.dumps(
                    {"business_id": str(business), "actor_id": str(actor), "operation_id": str(uuid4())}
                ),
            },
        )
    assert len(await claim_events(relay_database, uuid4(), limit=1)) == 1
    async with admin.connect() as connection:
        assert (
            await connection.scalar(
                text(
                    "SELECT count(*) FROM outbox_events WHERE state='pending' AND attempts=0 AND event_type IN\
 ('reference.created','reference.removed')"
                )
            )
            == 3
        )
    async with database.transaction(seeded["t2"], seeded["a2"]) as session:
        assert await session.scalar(text("SELECT count(*) FROM owner_references")) == 0
        assert await session.scalar(text("SELECT count(*) FROM owner_reference_operations")) == 0


async def test_concurrent_requests_are_idempotent(admin, api, seeded, settings):
    tenant, actor, business = seeded["t1"], seeded["a1"], uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Test','UTC')"),
            {"id": business, "tenant": tenant},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles
          (tenant_id,business_id,category,city,description,phone,brand_color)
          VALUES(:tenant,:business,'Food','Rio','Test','+5511999999999','#6557ed')"""),
            {"tenant": tenant, "business": business},
        )
    base = f"/api/v1/organizations/{tenant}/businesses/{business}/references"
    headers = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    payload = {"operation_id": str(uuid4()), "instagram": "@cafe"}
    responses = await asyncio.gather(*(api.post(base, headers=headers, json=payload) for _ in range(2)))
    assert [response.status_code for response in responses] == [200, 200]
    assert responses[0].json() == responses[1].json()
    new = [{"operation_id": str(uuid4()), "instagram": "@outro"} for _ in range(2)]
    responses = await asyncio.gather(*(api.post(base, headers=headers, json=body) for body in new))
    assert sorted(response.status_code for response in responses) == [200, 409]


async def test_reference_audit_and_outbox_roll_back_together(admin, database, seeded, monkeypatch):
    tenant, actor, business = seeded["t1"], seeded["a1"], uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Test','UTC')"),
            {"id": business, "tenant": tenant},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles
          (tenant_id,business_id,category,city,description,phone,brand_color)
          VALUES(:tenant,:business,'Food','Rio','Test','+5511999999999','#6557ed')"""),
            {"tenant": tenant, "business": business},
        )
    original = OwnerReferencesService._audit

    async def fail_after_audit(*args):
        await original(*args)
        raise RuntimeError("test rollback")

    monkeypatch.setattr(OwnerReferencesService, "_audit", staticmethod(fail_after_audit))
    with pytest.raises(RuntimeError, match="test rollback"):
        await OwnerReferencesService(database).create(
            tenant, business, actor, ReferenceCreate(operation_id=uuid4(), instagram="@cafe")
        )
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM owner_references")) == 0
        assert await connection.scalar(text("SELECT count(*) FROM owner_reference_operations")) == 0
        assert await connection.scalar(text("SELECT count(*) FROM audit_events WHERE action='reference.created'")) == 0
        assert (
            await connection.scalar(text("SELECT count(*) FROM outbox_events WHERE event_type='reference.created'"))
            == 0
        )
