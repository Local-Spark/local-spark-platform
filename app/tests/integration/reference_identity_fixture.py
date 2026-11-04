"""Explicit synthetic identity/review for historical private-batch tests."""

from uuid import uuid4

from sqlalchemy import text

from app.tests.unit.test_core import access_token


async def prepare_review_fixture(admin, api, settings, google, batch):
    base = f"/api/v1/organizations/{google.tenant}/businesses/{google.business}"
    response = await api.put(
        base + "/address",
        headers={"Authorization": f"Bearer {access_token(settings, google.actor)}"},
        json={
            "operation_id": str(uuid4()),
            "expected_version": 0,
            "address": {"street": "Rua Ficticia", "number": "10", "city": "São Paulo", "state_code": "SP"},
        },
    )
    assert response.status_code == 200
    async with admin.begin() as conn:
        await conn.execute(
            text("SELECT set_config('app.tenant_id',:t,true),set_config('app.actor_id',:a,true)"),
            {"t": str(google.tenant), "a": str(google.actor)},
        )
        own = await conn.scalar(text("SELECT reference_prepare_business_identity(:b)"), {"b": google.business})
        await conn.execute(
            text("""UPDATE reference_provider_searches SET business_name=:name,
          business_row_version=:row,
          business_address_version=:address,business_location_version=:location,
              business_identity_mac=:mac WHERE id=:s"""),
            {
                "name": own["name"],
                "row": own["row_version"],
                "address": own["address_version"],
                "location": own["location_version"],
                "mac": "d" * 64,
                "s": google.search,
            },
        )
        event = uuid4()
        await conn.execute(
            text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
          SELECT :event,tenant_id,'reference.own_business_match_recorded',jsonb_build_object(
            'business_id',business_id::text,'actor_id',actor_id::text,'operation_id',operation_id::text)
          FROM reference_provider_searches WHERE id=:s"""),
            {"event": event, "s": google.search},
        )
        await conn.execute(
            text("""INSERT INTO reference_own_business_reviews
          (tenant_id,business_id,search_id,batch_id,original_actor,request_hash,status,possible_place_ids,event_id)
          VALUES(:t,:b,:s,:batch,:a,:hash,'resolved','{}',:event)"""),
            {
                "t": google.tenant,
                "b": google.business,
                "s": google.search,
                "batch": batch,
                "a": google.actor,
                "hash": "d" * 64,
                "event": event,
            },
        )
