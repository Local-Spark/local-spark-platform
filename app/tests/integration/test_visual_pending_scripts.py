"""Script edits and review wait for admitted visual work without changing its inputs."""

import asyncio
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.db.session import Database
from app.schemas.editorial_context import ContextUpdate
from app.schemas.editorial_proposals import ScriptEdit, ScriptReview
from app.schemas.media_previews import PreviewRequest
from app.services.auth import AuthError
from app.services.editorial_context import EditorialContextService
from app.services.editorial_proposals import EditorialProposalService
from app.services.media_dispatch import claim_previews
from app.services.media_previews import MediaPreviewService
from app.services.visual_consent_gate import VisualConsentGate
from app.tests.integration.test_visual_admission import _ready

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("change", ["edit", "review"])
async def test_script_change_waits_for_visual_run_and_preserves_previous_preview(
    admin, database, seeded, settings, change
):
    tenant, business, actor, _, admission = await _ready(admin, database, seeded, settings)
    cfg = admission.settings.model_copy(update={"visual_ai_monthly_budget_usd_micros": 100})
    worker = Database(cfg, correlator=True)
    entered, release = asyncio.Event(), asyncio.Event()

    async def put(*_):
        entered.set()
        await release.wait()

    store = SimpleNamespace(put=AsyncMock(side_effect=put), delete=AsyncMock())
    owner = MediaPreviewService(cfg, database, store)
    scripts = EditorialProposalService(cfg, database)
    original = (await scripts.list(tenant, business, actor))[0]
    preview = await owner.request_candidate(
        tenant,
        business,
        actor,
        PreviewRequest(operation_id=uuid4(), proposal_id=admission.proposal, generation_mode="visual_fake"),
    )
    queued = await owner.request_candidate(
        tenant,
        business,
        actor,
        PreviewRequest(operation_id=uuid4(), proposal_id=admission.proposal, generation_mode="visual_fake"),
    )
    claims = {claim.id: claim for claim in await claim_previews(worker, uuid4())}
    renderer = MediaPreviewService(cfg, worker, store, database)
    task = asyncio.create_task(renderer.render(preview.id, claims[preview.id].fence))
    try:
        await asyncio.wait_for(entered.wait(), 20)
        if change == "edit":
            scenes = [scene.model_dump(mode="json") for scene in original.document.script]
            cta = next(scene for scene in scenes if scene["role"] == "cta")
            cta["on_screen_text"] = cta["voiceover"] = "Converse com nossa equipe"
            body = ScriptEdit(
                operation_id=uuid4(),
                expected_version=1,
                title="Conheça nosso croissant",
                angle="Uma pausa para conhecer o croissant",
                script=scenes,
            )
            with pytest.raises(AuthError, match="SCRIPT_GENERATED_COPY_EDIT_UNSUPPORTED"):
                await scripts.edit_script(tenant, business, actor, admission.proposal, body)
            unchanged = (await scripts.list(tenant, business, actor))[0]
            assert unchanged.pending_change is None and unchanged.document == original.document
        else:
            body = ScriptReview(operation_id=uuid4(), decision="changes_requested", note="Ajustar o roteiro")
            pending = await scripts.review_script(tenant, business, actor, admission.proposal, body)
            replay = await scripts.review_script(tenant, business, actor, admission.proposal, body)
            assert pending.review_state is None
        if change == "review":
            assert pending == replay and pending.pending_change.operation_id == body.operation_id
            waiting = (await scripts.list(tenant, business, actor))[0]
            assert waiting.pending_change.status == "pending"
            assert (
                waiting.document == original.document and waiting.script_version == 1 and waiting.review_state is None
            )
            with pytest.raises(AuthError, match="VISUAL_CHANGE_PENDING"):
                await owner.request_candidate(
                    tenant,
                    business,
                    actor,
                    PreviewRequest(operation_id=uuid4(), proposal_id=admission.proposal, generation_mode="visual_fake"),
                )
    finally:
        release.set()
    try:
        assert await asyncio.wait_for(task, 20) == "completed"
        applied = (await scripts.list(tenant, business, actor))[0]
        assert applied.pending_change is None
        assert applied.script_version == 1
        assert applied.review_state == (None if change == "edit" else "changes_requested")
        assert (await owner.file_key(tenant, business, actor, preview.id, review=True)).endswith(".jpg")
        if change == "edit":
            assert not next(
                item for item in await owner.list(tenant, business, actor) if item.id == preview.id
            ).created_before_change
            assert await renderer.render(queued.id, claims[queued.id].fence) == "completed"
            assert store.put.await_count == 2
            return
        assert next(
            item for item in await owner.list(tenant, business, actor) if item.id == preview.id
        ).created_before_change
        assert await renderer.render(queued.id, claims[queued.id].fence) == "failed"
        store.put.assert_awaited_once()
        async with admin.connect() as connection:
            command = (
                (
                    await connection.execute(
                        text("SELECT state,payload FROM business_visual_pending_changes WHERE operation_id=:operation"),
                        {"operation": body.operation_id},
                    )
                )
                .mappings()
                .one()
            )
            assert command["state"] == "completed"
            assert command["payload"]["proposal_id"] == str(admission.proposal)
    finally:
        await worker.close()


async def test_generated_script_edit_is_blocked_but_review_replays(admin, database, seeded, settings):
    tenant, business, actor, _, admission = await _ready(admin, database, seeded, settings)
    service = EditorialProposalService(admission.settings, database)
    original = (await service.list(tenant, business, actor))[0]
    scenes = deepcopy(original.document.script)
    cta = next(scene for scene in scenes if scene.role == "cta")
    cta.on_screen_text = cta.voiceover = "Converse com nossa equipe"
    body = ScriptEdit(
        operation_id=uuid4(),
        expected_version=1,
        title="Conheça nosso croissant",
        angle="Uma pausa para conhecer o croissant",
        script=scenes,
    )
    with pytest.raises(AuthError, match="SCRIPT_GENERATED_COPY_EDIT_UNSUPPORTED"):
        await service.edit_script(tenant, business, actor, admission.proposal, body)
    review = ScriptReview(operation_id=uuid4(), decision="accepted")
    reviewed = await service.review_script(tenant, business, actor, admission.proposal, review)
    assert reviewed.review_state == "accepted" and reviewed.pending_change is None
    assert await service.review_script(tenant, business, actor, admission.proposal, review) == reviewed
    async with admin.connect() as connection:
        assert (
            await connection.scalar(
                text(
                    "SELECT count(*) FROM business_visual_pending_changes WHERE kind IN ('script_edit','script_review')"
                )
            )
            == 1
        )


async def test_legacy_script_edit_waits_for_gate_and_replays(admin, database, seeded, settings):
    from app.tests.integration.test_media_previews import _accepted_case

    tenant, business, actor, _, proposal, _ = await _accepted_case(admin, seeded)
    service = EditorialProposalService(settings, database)
    original = (await service.list(tenant, business, actor))[0]
    gate = VisualConsentGate(database)
    await gate.enable(tenant, business, actor)
    run = uuid4()
    assert await gate.admit(tenant, business, actor, uuid4(), run, 1)
    scenes = deepcopy(original.document.script)
    cta = next(scene for scene in scenes if scene.role == "cta")
    cta.on_screen_text = cta.voiceover = "Converse com nossa equipe"
    body = ScriptEdit(
        operation_id=uuid4(),
        expected_version=1,
        title="Conheça o lanche",
        angle="Mostre o lanche artesanal",
        script=scenes,
    )
    pending = await service.edit_script(tenant, business, actor, proposal, body)
    assert pending.pending_change is not None and pending.pending_change.status == "pending"
    assert await service.edit_script(tenant, business, actor, proposal, body) == pending
    with pytest.raises(AuthError, match="VISUAL_CHANGE_OPERATION_CONFLICT"):
        await service.edit_script(tenant, business, actor, proposal, body.model_copy(update={"title": "Outro título"}))
    await gate.finish(tenant, business, actor, run, 1)
    changed = (await service.list(tenant, business, actor))[0]
    assert changed.pending_change is None and changed.script_version == 2
    replay = await service.edit_script(tenant, business, actor, proposal, body)
    assert replay.version == 2 and replay.document == changed.document


async def test_internal_script_tools_wait_for_another_pending_source_change(admin, database, seeded, settings):
    tenant, business, actor, _, admission = await _ready(admin, database, seeded, settings)
    service = EditorialProposalService(admission.settings, database)
    original = (await service.list(tenant, business, actor))[0]
    gate = VisualConsentGate(database, admission.settings)
    run = uuid4()
    await gate.admit(tenant, business, actor, uuid4(), run, 1, admission=admission)
    pending = await EditorialContextService(database).update(
        tenant,
        business,
        actor,
        ContextUpdate(operation_id=uuid4(), expected_version=0, preferences={"tone": "friendly"}),
    )
    assert pending.pending_change is not None
    edit = ScriptEdit(
        operation_id=uuid4(),
        expected_version=1,
        title="Conheça nosso croissant",
        angle="Uma pausa para conhecer o croissant",
        script=original.document.script,
    )
    with pytest.raises(AuthError, match="SCRIPT_GENERATED_COPY_EDIT_UNSUPPORTED"):
        await service.edit_script(tenant, business, actor, admission.proposal, edit)
    with pytest.raises(AuthError, match="VISUAL_CHANGE_PENDING"):
        await service.review_script(
            tenant, business, actor, admission.proposal, ScriptReview(operation_id=uuid4(), decision="accepted")
        )
    async with admin.connect() as connection:
        assert (
            await connection.scalar(
                text(
                    "SELECT count(*) FROM business_visual_pending_changes WHERE kind IN ('script_edit','script_review')"
                )
            )
            == 0
        )
    current = (await service.list(tenant, business, actor))[0]
    assert current.document == original.document and current.script_version == 1 and current.review_state is None
    await gate.finish(tenant, business, actor, run, 1)
    assert (await EditorialContextService(database).read(tenant, business, actor)).version == 1
