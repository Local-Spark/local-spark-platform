import asyncio
from dataclasses import replace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from temporalio.client import Client
from temporalio.exceptions import ApplicationError, WorkflowAlreadyStartedError

from app.schemas.business import BusinessCreate
from app.services.business import create_business
from app.services.outbox import claim_events, dispatch_once, finish_event
from app.workflows.activities import FoundationActivities

pytestmark = pytest.mark.integration


@pytest.fixture
async def event(database, relay_database, seeded):
    async with database.transaction(seeded["t1"], seeded["a1"]) as session:
        await create_business(session, seeded["t1"], seeded["a1"], "workflow-create", BusinessCreate(name="Store"))


async def test_concurrent_relays_have_disjoint_claims(event, relay_database):
    batches = await asyncio.gather(claim_events(relay_database, uuid4()), claim_events(relay_database, uuid4()))
    assert sum(len(batch) for batch in batches) == 1


async def test_lease_expiry_reclaims_and_fences_stale_owner(event, relay_database, admin):
    first_owner, next_owner = uuid4(), uuid4()
    first = (await claim_events(relay_database, first_owner))[0]
    async with admin.begin() as connection:
        await connection.execute(text("UPDATE outbox_events SET lease_until=clock_timestamp()-interval '1 second'"))
    next_item = (await claim_events(relay_database, next_owner))[0]
    assert next_item.fencing_token > first.fencing_token
    assert not await finish_event(relay_database, first, first_owner, success=True)
    assert await finish_event(relay_database, next_item, next_owner, success=True)
    assert not await claim_events(relay_database, uuid4())


@pytest.mark.parametrize("failure", [None, "already_started", "unavailable"])
async def test_relay_delivery_and_recovery(event, relay_database, settings, admin, failure):
    client = AsyncMock(spec=Client)
    if failure == "already_started":
        client.start_workflow.side_effect = WorkflowAlreadyStartedError("existing", "BusinessCreatedWorkflow")
    elif failure == "unavailable":
        client.start_workflow.side_effect = ConnectionError("unavailable")
    assert await dispatch_once(relay_database, client, settings, uuid4()) == 1
    async with admin.connect() as connection:
        state = await connection.scalar(text("SELECT state FROM outbox_events"))
    assert state == ("pending" if failure == "unavailable" else "delivered")
    assert await dispatch_once(relay_database, client, settings, uuid4()) == 0


async def test_delivery_failure_parks_after_limit(event, relay_database, admin):
    async with admin.begin() as connection:
        await connection.execute(text("UPDATE outbox_events SET attempts=4"))
    owner = uuid4()
    item = (await claim_events(relay_database, owner))[0]
    assert await finish_event(relay_database, item, owner, success=False)
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT state FROM outbox_events")) == "failed"


async def test_activity_is_idempotent_and_checks_durable_intent(event, database, relay_database, admin):
    item = (await claim_events(relay_database, uuid4()))[0]
    activities = FoundationActivities(database)
    assert await activities.record_business_created(item.event) == "recorded"
    assert await activities.record_business_created(item.event) == "duplicate"
    with pytest.raises(ApplicationError, match="durable intent"):
        await activities.record_business_created(replace(item.event, business_id=str(uuid4())))
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM processed_events")) == 1
        assert await connection.scalar(text("SELECT count(*) FROM audit_events")) == 2


async def test_relay_cannot_read_private_businesses(event, relay_database):
    async with relay_database.sessions() as session:
        with pytest.raises(DBAPIError):
            await session.execute(text("SELECT * FROM businesses"))


async def test_cross_tenant_event_foreign_key(event, database, relay_database, seeded):
    item = (await claim_events(relay_database, uuid4()))[0]
    with pytest.raises(DBAPIError):
        async with database.transaction(seeded["t2"], seeded["a2"]) as session:
            await session.execute(
                text("INSERT INTO processed_events(tenant_id,event_id) VALUES (:tenant,:event)"),
                {"tenant": seeded["t2"], "event": item.event.event_id},
            )


async def test_dispatch_cannot_confirm_lease_expired_during_rpc(event, relay_database, settings, admin, monkeypatch):
    from unittest.mock import Mock

    warning = Mock()
    monkeypatch.setattr("app.services.outbox.logger.warning", warning)

    async def accepted_after_lease_expiry(*args, **kwargs):
        async with admin.begin() as connection:
            await connection.execute(text("UPDATE outbox_events SET lease_until=clock_timestamp()-interval '1 second'"))

    client = AsyncMock(spec=Client)
    client.start_workflow.side_effect = accepted_after_lease_expiry
    assert await dispatch_once(relay_database, client, settings, uuid4()) == 1
    warning.assert_called_once()
    assert warning.call_args.args == ("outbox.lease_lost",)
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT state FROM outbox_events")) == "leased"
    reclaimed = await claim_events(relay_database, uuid4())
    assert len(reclaimed) == 1 and reclaimed[0].fencing_token == 2
