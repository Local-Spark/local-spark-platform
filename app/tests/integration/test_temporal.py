import json
import os
from uuid import uuid4

import pytest
from sqlalchemy import text
from temporalio import activity
from temporalio.client import Client
from temporalio.worker import Worker

from app.schemas.business import BusinessCreate
from app.services.business import create_business
from app.services.outbox import dispatch_once
from app.workflows.activities import FoundationActivities
from app.workflows.contracts import BusinessEvent
from app.workflows.foundation import BusinessCreatedWorkflow

pytestmark = [pytest.mark.integration, pytest.mark.temporal]


@pytest.mark.parametrize("transient_failure", [False, True])
async def test_real_workflow_retries_and_duplicate_delivery(
    database,
    relay_database,
    seeded,
    admin,
    settings,
    transient_failure,
):
    address = os.environ["TEST_TEMPORAL_ADDRESS"]
    client = await Client.connect(address)
    queue = f"test-foundation-{uuid4()}"
    settings = settings.model_copy(update={"temporal_task_queue": queue})
    attempts = 0
    implementation = FoundationActivities(database)

    @activity.defn(name="record_business_created")
    async def record(event: BusinessEvent) -> str:
        nonlocal attempts
        attempts += 1
        if transient_failure and attempts == 1:
            raise ConnectionError("simulated transient connection failure")
        return await implementation.record_business_created(event)

    async with database.transaction(seeded["t1"], seeded["a1"]) as session:
        created = await create_business(
            session, seeded["t1"], seeded["a1"], "temporal-request", BusinessCreate(name="Store")
        )
        # Persist an old receipt explicitly; current CRUD no longer emits it.
        await session.execute(
            text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
              VALUES(:id,:tenant,'business.created',CAST(:payload AS jsonb))"""),
            {
                "id": uuid4(),
                "tenant": seeded["t1"],
                "payload": json.dumps(
                    {
                        "business_id": str(created.business.id),
                        "actor_id": str(seeded["a1"]),
                        "operation_id": str(created.operation_id),
                    }
                ),
            },
        )
    async with admin.connect() as connection:
        event_id = await connection.scalar(text("SELECT id FROM outbox_events"))
    async with Worker(client, task_queue=queue, workflows=[BusinessCreatedWorkflow], activities=[record]):
        assert await dispatch_once(relay_database, client, settings, uuid4()) == 1
        handle = client.get_workflow_handle(f"business-created/{seeded['t1']}/{event_id}")
        assert await handle.result() == "recorded"
        async with admin.begin() as connection:
            await connection.execute(text("UPDATE outbox_events SET state='pending',available_at=clock_timestamp()"))
        assert await dispatch_once(relay_database, client, settings, uuid4()) == 1
        assert attempts == (2 if transient_failure else 1)
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM processed_events")) == 1
        assert await connection.scalar(text("SELECT count(*) FROM audit_events")) == 2
