"""Read-only evidence for reviewing a future unified-agreement transition.

This test does not activate capabilities, expose an endpoint or call providers.
"""

from uuid import uuid4

import pytest
from sqlalchemy import text

from app.tests.integration.test_editorial_proposals import _business

pytestmark = pytest.mark.integration


PROOF_QUERY = text("""SELECT
  EXISTS(SELECT 1 FROM visual_consent_runs r WHERE r.tenant_id=:tenant AND r.business_id=:business
    AND r.state='in_flight') AS visual,
  EXISTS(SELECT 1 FROM audit_events s WHERE s.tenant_id=:tenant AND s.resource_id=:business
    AND s.action='editorial.proposal_submitted' AND NOT EXISTS(
      SELECT 1 FROM audit_events done WHERE done.tenant_id=s.tenant_id AND done.operation_id=s.operation_id
        AND done.resource_id=s.resource_id AND done.action='editorial.proposal_completed')) AS editorial,
  EXISTS(SELECT 1 FROM audit_events s LEFT JOIN whatsapp_material_events e
      ON e.id=s.resource_id AND e.tenant_id=s.tenant_id
    WHERE s.tenant_id=:tenant AND s.action='whatsapp.audio_submitted'
      AND (e.business_id=:business OR e.id IS NULL)
      AND NOT EXISTS(SELECT 1 FROM audit_events done WHERE done.tenant_id=s.tenant_id
        AND done.resource_id=s.resource_id AND done.action='whatsapp.audio_completed')) AS audio,
  EXISTS(SELECT 1 FROM editorial_intent_usage u WHERE u.tenant_id=:tenant
    AND u.business_id=:business AND u.state IN ('submitted','uncertain')) AS intent""")


async def test_owner_can_read_isolated_durable_submission_evidence(admin, database, seeded):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    visual, editorial, audio, intent = (uuid4() for _ in range(4))
    params = {"tenant": tenant, "business": business, "actor": actor}

    async def evidence(scope_tenant, scope_actor):
        async with database.transaction(scope_tenant, scope_actor) as session:
            return (await session.execute(PROOF_QUERY, params)).one()

    assert tuple(await evidence(tenant, actor)) == (False, False, False, False)
    async with admin.begin() as session:
        await session.execute(
            text("""INSERT INTO visual_consent_runs
              (tenant_id,business_id,preview_id,operation_id,actor_id,fence,state,consent_accepted_at)
              VALUES(:tenant,:business,:preview,:operation,:actor,1,'in_flight',now())"""),
            {**params, "preview": uuid4(), "operation": visual},
        )
        await session.execute(
            text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
              VALUES(:tenant,:actor,:operation,'editorial.proposal_submitted',:business)"""),
            {**params, "operation": editorial},
        )
        # No source event is inserted: the audit must remain visible after source deletion.
        await session.execute(
            text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
              VALUES(:tenant,:actor,:operation,'whatsapp.audio_submitted',:event)"""),
            {**params, "operation": uuid4(), "event": audio},
        )
        await session.execute(
            text("""INSERT INTO editorial_intent_usage
              (tenant_id,business_id,actor_id,operation_id,request_hash,provider,model,
               rate_input_micros,rate_output_micros,reserved_micros,state)
              VALUES(:tenant,:business,:actor,:operation,:hash,'test','test',1,0,1,'uncertain')"""),
            {**params, "operation": intent, "hash": "a" * 64},
        )

    assert tuple(await evidence(tenant, actor)) == (True, True, True, True)
    assert tuple(await evidence(seeded["t2"], seeded["a2"])) == (False, False, False, False)

    async with admin.begin() as session:
        await session.execute(
            text("UPDATE visual_consent_runs SET state='finished' WHERE tenant_id=:tenant AND operation_id=:operation"),
            {**params, "operation": visual},
        )
        await session.execute(
            text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
              VALUES(:tenant,:actor,:operation,'editorial.proposal_completed',:business)"""),
            {**params, "operation": editorial},
        )
        await session.execute(
            text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
              VALUES(:tenant,:actor,:operation,'whatsapp.audio_completed',:event)"""),
            {**params, "operation": uuid4(), "event": audio},
        )
        await session.execute(
            text(
                "UPDATE editorial_intent_usage SET state='completed' "
                "WHERE tenant_id=:tenant AND operation_id=:operation"
            ),
            {**params, "operation": intent},
        )
    assert tuple(await evidence(tenant, actor)) == (False, False, False, False)
