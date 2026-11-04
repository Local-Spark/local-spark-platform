"""Real owner scope, immutable proposal snapshots and no paid use after removal."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db.session import Database
from app.schemas.editorial_proposals import ProposalDraft, ProposalRequest
from app.schemas.owner_references import ReferenceCreate
from app.services.auth import AuthError
from app.services.editorial_dispatch import claim_proposals, finish_proposal_dispatch
from app.services.editorial_proposals import EditorialProposalService
from app.services.owner_references import OwnerReferencesService
from app.services.reference_generation_context import capture_generation_context, generation_context_is_current
from app.services.visual_context import VisualContextService
from app.tests.integration.test_visual_admission import _ready

pytestmark = pytest.mark.integration


async def _proposal_row(admin, proposal):
    async with admin.connect() as connection:
        return (
            (await connection.execute(text("SELECT * FROM editorial_proposals WHERE id=:id"), {"id": proposal}))
            .mappings()
            .one()
        )


async def persist_synthetic_learning(admin, database, tenant, business, actor):
    """A stored producer result fixture; no feed collection or paid effect is asserted."""
    async with database.transaction(tenant, actor) as session:
        captured = await capture_generation_context(session, business)
    assert len(captured.selected) == 1
    selected = captured.selected[0]
    event = uuid4()
    async with admin.begin() as connection:
        window = await connection.scalar(
            text("""SELECT id FROM reference_feed_windows WHERE tenant_id=:tenant AND business_id=:business
              AND reference_id=:reference AND association_version=:version ORDER BY scheduled_at DESC LIMIT 1"""),
            {
                "tenant": tenant,
                "business": business,
                "reference": selected.reference_id,
                "version": selected.association_version,
            },
        )
        assert window is not None
        await connection.execute(
            text("""INSERT INTO outbox_events(id,tenant_id,event_type,payload)
              VALUES(:event,:tenant,'reference.learning_completed',jsonb_build_object(
                'business_id',CAST(:business AS text),'actor_id',CAST(:actor AS text),
                'operation_id',CAST(:window AS text)))"""),
            {"event": event, "tenant": tenant, "business": str(business), "actor": str(actor), "window": str(window)},
        )
        await connection.execute(
            text("""INSERT INTO reference_learning_results
              (tenant_id,business_id,window_id,reference_id,association_version,status,patterns,posts,images,
               coverage,event_id) VALUES(:tenant,:business,:window,:reference,:version,'partial',
                 CAST(:patterns AS jsonb),2,3,'partial',:event)"""),
            {
                "tenant": tenant,
                "business": business,
                "window": window,
                "reference": selected.reference_id,
                "version": selected.association_version,
                "event": event,
                "patterns": json.dumps(
                    [
                        {"dimension": "visual", "observation": "Composição com espaço vazio"},
                        {"dimension": "editorial", "observation": "Tom acolhedor"},
                    ]
                ),
            },
        )
        await connection.execute(
            text("UPDATE reference_feed_windows SET status='partial' WHERE id=:id"), {"id": window}
        )


async def test_snapshot_is_immutable_scoped_and_replay_does_not_recapture(admin, database, seeded, settings):
    tenant, business, actor, _, admission = await _ready(
        admin,
        database,
        seeded,
        settings,
        owner_reference={"instagram": "@indicado", "note": "Gosto da apresentação"},
    )
    row = await _proposal_row(admin, admission.proposal)
    pinned = row["reference_generation_snapshot"]
    assert len(pinned["selected"]) == 1 and pinned["learnings"] == []
    assert pinned["selected"][0]["instagram_handle"] == "indicado"
    assert pinned["selected"][0]["analysis_status"] == "not_requested"
    assert row["owner_reference_snapshot"][0]["access_status"] == "not_checked"
    references = OwnerReferencesService(database)
    await references.create(tenant, business, actor, ReferenceCreate(operation_id=uuid4(), instagram="@nova"))
    replay = await EditorialProposalService(admission.settings, database).request(
        tenant,
        business,
        actor,
        ProposalRequest(operation_id=row["operation_id"], source_asset_id=row["source_asset_id"]),
        briefing_id=row["briefing_id"],
    )
    assert replay.id == row["id"]
    assert (await _proposal_row(admin, row["id"]))["reference_generation_snapshot"] == pinned
    async with database.transaction(tenant, actor) as session:
        current = await capture_generation_context(session, business)
        assert len(current.selected) == 2
        assert await generation_context_is_current(session, business, current)
    async with database.transaction(seeded["t2"], seeded["a2"]) as session:
        assert (
            await session.scalar(text("SELECT count(*) FROM editorial_proposals WHERE id=:id"), {"id": row["id"]}) == 0
        )
    with pytest.raises(DBAPIError, match="REFERENCE_GENERATION_SNAPSHOT_IMMUTABLE"):
        async with admin.begin() as connection:
            await connection.execute(
                text(
                    "UPDATE editorial_proposals SET reference_generation_snapshot=CAST(:snapshot AS jsonb) WHERE id=:id"
                ),
                {"id": row["id"], "snapshot": json.dumps(current.model_dump(mode="json"))},
            )
    async with admin.begin() as connection:
        await connection.execute(
            text(
                "UPDATE editorial_proposals SET reference_generation_snapshot=reference_generation_snapshot "
                "WHERE id=:id"
            ),
            {"id": row["id"]},
        )


@pytest.mark.parametrize("remove_during_effect", [False, True])
async def test_removed_reference_prevents_submission_or_discards_inflight_result(
    admin, database, seeded, settings, remove_during_effect
):
    tenant, business, actor, _, admission = await _ready(
        admin,
        database,
        seeded,
        settings,
        owner_reference={"instagram": "@indicado"},
    )
    cfg = admission.settings
    first = await _proposal_row(admin, admission.proposal)
    requested = await EditorialProposalService(cfg, database).request(
        tenant,
        business,
        actor,
        ProposalRequest(operation_id=uuid4(), source_asset_id=first["source_asset_id"]),
        briefing_id=first["briefing_id"],
    )
    references = OwnerReferencesService(database)
    reference = (await references.list(tenant, business, actor))[0]

    async def complete(data, operation, *, prepared_request):
        assert data["reference_context"][0]["perfil_instagram"] == "indicado"
        assert prepared_request["input"] and operation == requested.id
        await references.remove(tenant, business, actor, reference.id, uuid4())
        return ProposalDraft.model_validate(first["document"]), 10, 10

    provider = SimpleNamespace(propose=AsyncMock(side_effect=complete))
    if not remove_during_effect:
        await references.remove(tenant, business, actor, reference.id, uuid4())
    worker = Database(cfg, correlator=True)
    try:
        claim = (await claim_proposals(worker, uuid4()))[0]
        await finish_proposal_dispatch(worker, claim, True)
        state = await EditorialProposalService(cfg, worker, provider, owner_database=database).run(requested.id)
        assert state == ("uncertain" if remove_during_effect else "rejected")
        assert provider.propose.await_count == int(remove_during_effect)
        row = await _proposal_row(admin, requested.id)
        assert row["document"] is None
        assert row["error_code"] == (
            "EDITORIAL_RESULT_UNCERTAIN" if remove_during_effect else "REFERENCE_GENERATION_CONTEXT_CHANGED"
        )
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM editorial_ai_usage")) == 1 + int(
                remove_during_effect
            )
            assert await connection.scalar(text("SELECT count(*) FROM editorial_request_traces")) == 1 + int(
                remove_during_effect
            )
        with pytest.raises(AuthError, match="REFERENCE_GENERATION_CONTEXT_CHANGED"):
            await VisualContextService(cfg, database).capture(tenant, business, actor, first["id"], candidate=True)
        # A historic request trace remains an honest record of what was used.
        trace = await EditorialProposalService(cfg, database).get_request_trace(tenant, business, actor, first["id"])
        assert trace["proposal_state"] == "completed"
        assert "indicado" in trace["request"]["body"]["input"][1]["content"]
    finally:
        await worker.close()
