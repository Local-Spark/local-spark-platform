"""Restricted PostgreSQL proof of Reel orchestration with synthetic IO boundaries."""

import asyncio
import hashlib
import json
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4, uuid5

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.adapters.material_media import MaterialError
from app.adapters.motion_ai import MotionAIError
from app.adapters.motion_html_renderer import RenderAsset, RenderedMotion
from app.adapters.motion_inputs import PreparedMotionInput
from app.db.session import Database
from app.schemas.motion_production import MotionRequest, MotionReview
from app.services.auth import AuthError
from app.services.content_pieces import ContentPieceService
from app.services.motion_orchestrator import MotionOrchestrator
from app.services.motion_protocols import MotionModelResult
from app.services.motion_requests import MotionRequestService
from app.services.visual_consent_gate import VisualConsentGate
from app.services.whatsapp_retention import claim_expired_assets
from app.tests.integration.test_brand_kits import _overrides
from app.tests.integration.test_editorial_proposals import _asset, _business
from app.tests.unit.test_motion_ai import composition, frame, review_data
from app.workflows.contracts import BusinessEvent

pytestmark = pytest.mark.integration


class Store:
    single_attempt_put = True

    def __init__(self):
        self.objects = {}
        self.puts = 0
        self.fail = False

    async def put(self, key, media):
        self.puts += 1
        self.objects[key] = media.data
        if self.fail:
            raise MaterialError("MATERIAL_STORAGE_UNAVAILABLE", retryable=True)

    async def get_video(self, key):
        return self.objects[key]

    async def get_motion_payload(self, key):
        return self.objects[key]


class Provider:
    provider = "fake"
    model = "synthetic-model"

    def __init__(self):
        self.calls = []
        self.reviews = []
        self.effect = None
        self.estimate = 0

    def build_request(self, request):
        return {"kind": request.kind, "context": request.context, "max_output_tokens": 5}

    async def count_input_tokens(self, request, payload):
        return 10

    async def submit(self, request, payload):
        self.calls.append(request.kind)
        if self.effect:
            await self.effect(request)
        if request.kind != "review":
            return MotionModelResult(
                composition=composition(), estimated_usd_micros=self.estimate, raw_response=b"private-response"
            )
        review = (
            self.reviews.pop(0)
            if self.reviews
            else review_data(
                current=request.frames[0], previous=request.incumbent_frames[0] if request.incumbent_frames else None
            )
        )
        return MotionModelResult(review=MotionReview.model_validate(review), estimated_usd_micros=self.estimate)


@pytest.fixture
async def motion_case(admin, settings, database, seeded):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    key = Fernet.generate_key().decode()
    source = await _asset(admin, tenant, business, key, kind="video", body="synthetic recording")
    video = b"synthetic source"
    async with admin.begin() as conn:
        await conn.execute(
            text("""UPDATE whatsapp_material_assets SET object_key='synthetic/source.mp4',
          mime_type='video/mp4',size_bytes=:size,sha256=:hash WHERE id=:source"""),
            {"source": source, "size": len(video), "hash": hashlib.sha256(video).hexdigest()},
        )
        params = {"tenant": tenant, "business": business, "actor": actor, "operation": uuid4()}
        await conn.execute(
            text("""INSERT INTO business_brand_kit_heads(tenant_id,business_id,version,confirmed_version)
          VALUES(:tenant,:business,1,1)"""),
            params,
        )
        await conn.execute(
            text("""INSERT INTO business_brand_kit_versions
          (tenant_id,business_id,version,operation_id,actor_id,request_hash,state,document)
          VALUES(:tenant,:business,1,:operation,:actor,:hash,'confirmed',CAST(:document AS jsonb))"""),
            {
                **params,
                "hash": "a" * 64,
                "document": json.dumps(
                    {"kit_id": "cafe-pausas", "kit_version": 1, "overrides": _overrides("Synthetic brand")}
                ),
            },
        )
    cfg = settings.model_copy(
        update={
            "meta_encryption_key": SecretStr(key),
            "motion_execution_enabled": True,
            "motion_ai_mode": "fake",
            "motion_renderer_image": "sha256:" + "a" * 64,
            "motion_renderer_docker_executable": "/synthetic/docker",
            "motion_renderer_docker_socket": "/synthetic/docker.sock",
            "material_storage_bucket": "synthetic-private",
            "motion_local_qualification_business_id": business,
            "motion_local_qualification_asset_ids": (source,),
            "motion_ai_reservation_usd_micros": 1000,
            "motion_request_budget_usd_micros": 6000,
            "visual_ai_monthly_budget_usd_micros": 100000,
            "motion_max_corrections": 2,
        }
    )
    requests = MotionRequestService(cfg, database)
    await VisualConsentGate(database).enable(tenant, business, actor)
    body = MotionRequest(operation_id=uuid4(), source_asset_id=source, instruction="Mostre a gravação fictícia.")
    provider, store = Provider(), Store()
    pixels = frame()
    rendered_video = b"\x00\x00\x00\x20ftyp" + b"synthetic-render"
    rendered = RenderedMotion(
        rendered_video, hashlib.sha256(rendered_video).hexdigest(), (pixels,), {"synthetic": True}
    )
    renderer = SimpleNamespace(render=AsyncMock(return_value=rendered))
    prepared = PreparedMotionInput(
        {"authorized_audio": {"mode": "silent", "tracks": []}},
        (RenderAsset("assets/source.mp4", "video/mp4", video, hashlib.sha256(video).hexdigest()),),
        (pixels,),
        1000,
        {"mode": "silent", "tracks": []},
    )
    inputs = SimpleNamespace(prepare=AsyncMock(return_value=prepared))
    worker = Database(cfg, correlator=True)
    runner = MotionOrchestrator(requests, worker, provider, renderer, inputs, store)
    event = BusinessEvent(
        str(uuid5(body.operation_id, "motion.requested")),
        str(tenant),
        str(business),
        str(actor),
        str(body.operation_id),
    )
    try:
        yield SimpleNamespace(
            tenant=tenant,
            actor=actor,
            business=business,
            source=source,
            body=body,
            requests=requests,
            cfg=cfg,
            provider=provider,
            store=store,
            renderer=renderer,
            inputs=inputs,
            worker=worker,
            runner=runner,
            event=event,
            database=database,
            rendered=rendered,
            frame=pixels,
        )
    finally:
        await worker.close()


async def create(case):
    return await case.requests.create(case.tenant, case.business, case.actor, case.body)


@pytest.mark.parametrize("implementation_fails", [False, True])
async def test_staged_generation_keeps_plan_receipt_and_never_retries(motion_case, admin, implementation_fails):
    from app.services.motion_construction import construct_motion
    from app.tests.unit.test_motion_construction import plan, staged_context
    from app.tests.unit.test_motion_plan import planned

    c = motion_case
    requested = await create(c)
    row, token = await c.requests.begin(c.tenant, c.business, c.actor, c.body.operation_id, UUID(c.event.event_id))
    prepared = replace(c.inputs.prepare.return_value, context=staged_context())
    calls = []

    async def submit(job, _payload):
        calls.append(job.operation_id)
        if job.construction_plan is None:
            return MotionModelResult(construction_plan=plan(), estimated_usd_micros=0)
        # The preceding result must already be committed and visible outside its transaction.
        async with c.database.transaction(c.tenant, c.actor) as session:
            receipt = await session.scalar(
                text("SELECT response_ciphertext FROM motion_effects WHERE operation_id=:id AND state='received'"),
                {"id": uuid5(c.body.operation_id, "generate:plan:0")},
            )
        assert c.requests.context.open(receipt)["construction_plan"] == plan().model_dump(mode="json")
        if implementation_fails:
            raise MotionAIError("MOTION_AI_OUTPUT_LIMIT", raw_response=b"synthetic-incomplete", estimated_usd_micros=0)
        return MotionModelResult(composition=planned(), estimated_usd_micros=0)

    c.provider.submit = submit
    if implementation_fails:
        with pytest.raises(MotionAIError, match="OUTPUT_LIMIT"):
            await construct_motion(c.runner.effects, c.provider, row, token, prepared)
    else:
        assert await construct_motion(c.runner.effects, c.provider, row, token, prepared) == planned()
    assert len(calls) == 2 and len(set(calls)) == 2
    async with admin.connect() as conn:
        effects = (
            (
                await conn.execute(
                    text(
                        "SELECT state,response_ciphertext FROM motion_effects WHERE request_id=:id AND kind='generate'"
                    ),
                    {"id": requested.id},
                )
            )
            .mappings()
            .all()
        )
        assert len(effects) == 2 and all(e["state"] == "received" for e in effects)
        assert all("construction_plan" not in e["response_ciphertext"] for e in effects)
    c.renderer.render.assert_not_awaited()
    assert c.store.puts == 0


async def test_recording_to_private_piece_is_idempotent_encrypted_and_never_publishes(motion_case, admin):
    c = motion_case
    requested = await create(c)
    assert requested.state == "queued"
    assert (await create(c)).id == requested.id
    assert await c.runner.run(c.event) == "completed"
    assert await c.runner.run(c.event) == "already_claimed"
    result = await c.requests.get(c.tenant, c.business, c.actor, requested.id)
    assert result.state == "completed" and result.piece_id is not None
    piece = await ContentPieceService(c.cfg, c.database).get(c.tenant, c.business, c.actor, result.piece_id)
    assert piece.state == "ready_for_review" and len(piece.versions) == 1
    assert c.provider.calls == ["generate", "review"] and c.store.puts == 1
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM content_deliveries")) == 0
        assert await conn.scalar(text("SELECT count(*) FROM visual_cost_reservations")) == 2
        assert await conn.scalar(text("SELECT count(*) FROM creative_active_runs")) == 0
        snapshot = await conn.scalar(text("SELECT snapshot_ciphertext FROM motion_requests"))
        assert (
            "Mostre" not in snapshot
            and c.requests.context.open(snapshot)["request"]["instruction"] == c.body.instruction
        )
        effect = await conn.scalar(text("SELECT response_ciphertext FROM motion_effects WHERE kind='generate'"))
        assert c.requests.context.open(effect)["raw_response"] == "cHJpdmF0ZS1yZXNwb25zZQ=="
        events = (await conn.execute(text("SELECT payload FROM outbox_events"))).scalars().all()
        assert all(set(item) == {"business_id", "actor_id", "operation_id"} for item in events)


async def test_correction_preserves_both_versions_and_selects_comparative_winner(motion_case, admin):
    c = motion_case
    c.provider.reviews = [review_data(current=c.frame, revise=True), review_data(current=c.frame, previous=c.frame)]
    await create(c)
    assert await c.runner.run(c.event) == "completed"
    assert c.provider.calls == ["generate", "review", "correct", "review"]
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM motion_render_versions")) == 2
        assert await conn.scalar(text("SELECT count(*) FROM content_piece_versions")) == 2
        number = await conn.scalar(
            text("""SELECT v.number FROM content_pieces p JOIN content_piece_versions v
          ON p.current_version_id=v.id""")
        )
        assert number == 2


@pytest.mark.parametrize("preferred", ["previous", "undetermined"])
async def test_no_second_correction_without_observed_gain(motion_case, preferred):
    c = motion_case
    second = review_data(current=c.frame, previous=c.frame, revise=True)
    second["preferred"] = preferred
    c.provider.reviews = [review_data(current=c.frame, revise=True), second]
    requested = await create(c)
    with pytest.raises(AuthError, match="MOTION_MANDATORY_REVIEW_FAILED"):
        await c.runner.run(c.event)
    assert c.provider.calls == ["generate", "review", "correct", "review"]
    assert (await c.requests.get(c.tenant, c.business, c.actor, requested.id)).state == "failed"


async def test_budget_requires_correction_and_its_review_together(motion_case):
    c = motion_case
    c.cfg.motion_request_budget_usd_micros = 3000
    c.provider.reviews = [review_data(current=c.frame, revise=True)]
    await create(c)
    with pytest.raises(AuthError, match="MOTION_MANDATORY_REVIEW_FAILED"):
        await c.runner.run(c.event)
    assert c.provider.calls == ["generate", "review"]


@pytest.mark.parametrize("failure", ["timeout", "cancelled", "upload"])
async def test_unknown_external_effect_is_quarantined_without_retry(motion_case, admin, failure):
    c = motion_case
    if failure in {"timeout", "cancelled"}:

        async def timeout(_request):
            if failure == "cancelled":
                raise asyncio.CancelledError
            raise TimeoutError

        c.provider.effect = timeout
    else:
        c.store.fail = True
    requested = await create(c)
    with pytest.raises((TimeoutError, asyncio.CancelledError, MaterialError)):
        await c.runner.run(c.event)
    assert (await c.requests.get(c.tenant, c.business, c.actor, requested.id)).state == "uncertain"
    before = (len(c.provider.calls), c.store.puts)
    assert await c.runner.run(c.event) == "already_claimed"
    assert (len(c.provider.calls), c.store.puts) == before
    assert await VisualConsentGate(c.database).request_withdrawal(c.tenant, c.business, c.actor) == "revocation_pending"
    async with admin.begin() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM creative_active_runs")) == 1
        await conn.execute(text("UPDATE whatsapp_material_assets SET delete_requested_at=now()"))
    assert await claim_expired_assets(c.worker, uuid4()) == []


async def test_response_survives_owner_revocation_during_provider_call(motion_case, admin):
    c = motion_case

    async def revoke(_request):
        async with admin.begin() as conn:
            await conn.execute(text("UPDATE memberships SET active=false WHERE actor_id=:actor"), {"actor": c.actor})

    c.provider.effect = revoke
    await create(c)
    with pytest.raises(AuthError):
        await c.runner.run(c.event)
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT state FROM motion_requests")) == "uncertain"
        row = (await conn.execute(text("SELECT state,response_ciphertext FROM motion_effects"))).one()
        assert row.state == "received" and c.requests.context.open(row.response_ciphertext)["raw_response"]
    assert c.provider.calls == ["generate"]


async def test_invalid_response_is_preserved_before_invoice_finalization(motion_case, admin):
    c = motion_case

    async def reject(_request):
        raise MotionAIError("MOTION_AI_INVALID_RESPONSE", raw_response=b"private-invalid-json")

    c.provider.effect = reject
    await create(c)
    with pytest.raises(MotionAIError):
        await c.runner.run(c.event)
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT state FROM motion_requests")) == "failed"
        result = await conn.scalar(text("SELECT response_ciphertext FROM motion_effects"))
        assert c.requests.context.open(result)["raw_response_base64"] == "cHJpdmF0ZS1pbnZhbGlkLWpzb24="


async def test_request_event_and_owner_scope_cannot_be_replaced(motion_case, seeded):
    c = motion_case
    requested = await create(c)
    with pytest.raises(AuthError, match="MOTION_OPERATION_CONFLICT"):
        await c.requests.create(c.tenant, c.business, c.actor, c.body.model_copy(update={"instruction": "different"}))
    with pytest.raises(AuthError, match="MOTION_EVENT_MISMATCH"):
        await c.runner.run(replace(c.event, event_id=str(uuid4())))
    with pytest.raises(AuthError):
        await c.requests.get(c.tenant, c.business, seeded["viewer"], requested.id)
    async with c.database.transaction(seeded["t2"], seeded["a2"]) as session:
        assert await session.scalar(text("SELECT count(*) FROM motion_requests")) == 0
        with pytest.raises(DBAPIError):
            await session.scalar(text("SELECT motion_asset_in_use(:source)"), {"source": c.source})
    assert not c.provider.calls


async def test_context_change_before_worker_prevents_any_effect(motion_case, admin):
    c = motion_case
    await create(c)
    async with admin.begin() as conn:
        await conn.execute(text("UPDATE whatsapp_material_assets SET sha256=:sha"), {"sha": "f" * 64})
    with pytest.raises(AuthError, match="MOTION_CONTEXT_CHANGED"):
        await c.runner.run(c.event)
    assert not c.provider.calls


@pytest.mark.parametrize("environment", ["staging", "production"])
async def test_old_agreement_never_enables_real_video(motion_case, environment):
    c = motion_case
    c.cfg.environment = environment
    with pytest.raises(AuthError, match="MOTION_LOCAL_QUALIFICATION_REQUIRED"):
        await create(c)


async def test_real_provider_estimate_keeps_reservation_without_fabricated_invoice(motion_case, admin):
    c = motion_case
    c.provider.provider = "openai"  # Transport still synthetic; test shared ledger semantics only.
    c.provider.model = "gpt-6.1-sol"
    c.cfg.visual_ai_global_monthly_budget_usd_micros = 100000
    c.cfg.motion_ai_input_usd_micros_per_million_tokens = 2_500_000
    c.cfg.motion_ai_output_usd_micros_per_million_tokens = 10_000_000
    c.provider.estimate = 50
    await create(c)
    assert await c.runner.run(c.event) == "completed"
    async with admin.connect() as conn:
        rows = (
            await conn.execute(text("SELECT state,actual_usd_micros,reserved_usd_micros FROM visual_cost_reservations"))
        ).all()
        assert len(rows) == 2 and all(row.state == "uncertain" and row.actual_usd_micros is None for row in rows)
        assert sum(row.reserved_usd_micros for row in rows) == 2000
        assert await conn.scalar(text("SELECT simulated FROM content_pieces")) is False


@pytest.mark.parametrize(
    "estimate,code", [(None, "MOTION_COST_ESTIMATE_UNKNOWN"), (1001, "MOTION_COST_ESTIMATE_EXCEEDED")]
)
async def test_unknown_or_excessive_cost_prevents_subsequent_calls(motion_case, estimate, code):
    c = motion_case
    c.provider.estimate = estimate
    await create(c)
    with pytest.raises(AuthError, match=code):
        await c.runner.run(c.event)
    assert c.provider.calls == ["generate"] and c.store.puts == 0


async def test_result_is_durable_even_if_ledger_finalization_fails(motion_case, admin):
    c = motion_case
    c.runner.effects.ledger.finish = AsyncMock(side_effect=RuntimeError("simulated DB interruption"))
    await create(c)
    with pytest.raises(RuntimeError, match="simulated DB interruption"):
        await c.runner.run(c.event)
    async with admin.connect() as conn:
        row = (await conn.execute(text("SELECT state,response_ciphertext FROM motion_effects"))).one()
        assert row.state == "received" and c.requests.context.open(row.response_ciphertext)["raw_response"]
    assert c.provider.calls == ["generate"]


async def test_worker_recorder_is_narrow_fenced_and_not_a_login(motion_case, admin, seeded):
    c = motion_case
    requested = await create(c)
    row, token = await c.requests.begin(c.tenant, c.business, c.actor, c.body.operation_id, UUID(c.event.event_id))
    operation = uuid4()
    await c.runner.effects.claim(row, token, operation, "generate", {"synthetic": True}, 1000)
    with pytest.raises(AuthError, match="MOTION_EFFECT_ALREADY_CLAIMED"):
        await c.runner.effects.claim(row, token, operation, "generate", {"synthetic": True}, 1000)
    with pytest.raises(AuthError, match="MOTION_EFFECT_FENCED"):
        await c.runner.effects.received(row, uuid4(), operation, {"private": True})
    async with c.worker.transaction(seeded["t2"], seeded["a2"]) as session:
        assert (
            await session.scalar(
                text("""SELECT motion_record_result(
          :tenant,:business,:id,:actor,:token,:operation,'ciphertext',0)"""),
                {
                    "tenant": c.tenant,
                    "business": c.business,
                    "id": requested.id,
                    "actor": c.actor,
                    "token": token,
                    "operation": operation,
                },
            )
            is False
        )
    await c.runner.effects.received(row, token, operation, {"private": True})
    with pytest.raises(AuthError, match="MOTION_EFFECT_FENCED"):
        await c.runner.effects.received(row, token, operation, {"private": False})
    async with admin.connect() as conn:
        role = (
            await conn.execute(
                text("""SELECT rolcanlogin,rolsuper,rolbypassrls FROM pg_roles
          WHERE rolname='meu_braco_direito_motion_recorder'""")
            )
        ).one()
        assert not any(role)
        assert (
            await conn.scalar(
                text("""SELECT has_column_privilege('meu_braco_direito_motion_recorder',
          'motion_requests','snapshot_ciphertext','SELECT')""")
            )
            is False
        )


async def test_running_reel_blocks_new_agreement_until_its_effects_finish(motion_case, admin):
    from app.services.service_agreement import (
        SERVICE_AGREEMENT_HASH,
        SERVICE_AGREEMENT_VERSION,
        ServiceAgreementService,
    )

    c = motion_case
    agreement = ServiceAgreementService(c.cfg, c.database)
    checked = []

    async def attempt_during_generation(request):
        if request.kind != "generate":
            return
        with pytest.raises(AuthError, match="SERVICE_AGREEMENT_CHANGE_PENDING"):
            await agreement.accept(c.tenant, c.business, c.actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM service_agreement_acceptances")) == 0
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM audit_events WHERE action LIKE 'service.agreement.%'")
                )
                == 0
            )
        checked.append(request.kind)

    c.provider.effect = attempt_during_generation
    await create(c)
    assert await c.runner.run(c.event) == "completed"
    assert checked == ["generate"]
    accepted = await agreement.accept(c.tenant, c.business, c.actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH)
    assert accepted["accepted"] is True


async def test_active_reel_defers_context_change_and_drains_withdrawal_after_completion(motion_case, admin):
    from app.schemas.editorial_context import ContextUpdate, EditorialPreferences
    from app.services.editorial_context import EditorialContextService

    c = motion_case
    context = EditorialContextService(c.database)

    async def change_during_call(request):
        if request.kind != "generate":
            return
        changed = await context.update(
            c.tenant,
            c.business,
            c.actor,
            ContextUpdate(operation_id=uuid4(), expected_version=0, preferences=EditorialPreferences(goal="awareness")),
        )
        assert changed.pending_change is not None and changed.version == 0
        assert (
            await VisualConsentGate(c.database).request_withdrawal(c.tenant, c.business, c.actor)
            == "revocation_pending"
        )

    c.provider.effect = change_during_call
    await create(c)
    assert await c.runner.run(c.event) == "completed"
    assert await VisualConsentGate(c.database).status(c.tenant, c.business, c.actor) == "revoked"
    assert (await context.read(c.tenant, c.business, c.actor)).version == 1
    async with admin.connect() as conn:
        original = c.requests.context.open(await conn.scalar(text("SELECT snapshot_ciphertext FROM motion_requests")))
        assert original["context_version"] == 0
        assert await conn.scalar(text("SELECT count(*) FROM creative_active_runs")) == 0


@pytest.mark.temporal
async def test_temporal_outbox_executes_private_reel_once(motion_case, relay_database, admin):
    import os

    from temporalio.client import Client
    from temporalio.worker import Worker

    from app.services.outbox import dispatch_once
    from app.workflows.motion_activities import MotionActivities
    from app.workflows.motion_production import MotionProductionWorkflow

    c = motion_case
    client = await Client.connect(os.environ["TEST_TEMPORAL_ADDRESS"])
    c.cfg.temporal_task_queue = f"test-motion-{uuid4()}"
    await create(c)
    async with Worker(
        client,
        task_queue=c.cfg.temporal_task_queue,
        workflows=[MotionProductionWorkflow],
        activities=[MotionActivities(c.runner).run],
    ):
        assert await dispatch_once(relay_database, client, c.cfg, uuid4()) == 1
        handle = client.get_workflow_handle(f"motion-production/{c.tenant}/{c.event.event_id}")
        assert await asyncio.wait_for(handle.result(), timeout=90) == "completed"
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE outbox_events SET state='pending',available_at=clock_timestamp() WHERE id=:event"),
                {"event": UUID(c.event.event_id)},
            )
        assert await dispatch_once(relay_database, client, c.cfg, uuid4()) == 1
        assert c.provider.calls == ["generate", "review"] and c.store.puts == 1
        assert c.body.instruction not in str(await handle.fetch_history())


@pytest.mark.parametrize("upload_failure", [False, True])
async def test_large_motion_payloads_keep_sql_bounded_and_stop_before_ai_on_storage_failure(
    motion_case, upload_failure
):
    c = motion_case
    prepared = c.inputs.prepare.return_value
    c.inputs.prepare.return_value = replace(prepared, context={**prepared.context, "synthetic_note": "x" * 200_000})
    png = c.frame.png + b"synthetic evidence" * 10_000
    large_frame = replace(c.frame, png=png, sha256=hashlib.sha256(png).hexdigest())
    c.renderer.render.return_value = replace(c.rendered, evidence=(large_frame,))
    c.store.fail = upload_failure
    requested = await create(c)
    if upload_failure:
        with pytest.raises(MaterialError, match="STORAGE_UNAVAILABLE"):
            await c.runner.run(c.event)
        assert c.provider.calls == []
        assert (await c.requests.get(c.tenant, c.business, c.actor, requested.id)).state == "uncertain"
    else:
        assert await c.runner.run(c.event) == "completed"
        async with c.database.transaction(c.tenant, c.actor) as session:
            records = (
                (
                    await session.execute(
                        text(
                            "SELECT request_ciphertext FROM motion_effects WHERE request_id=:id "
                            "AND kind IN ('generate','review')"
                        ),
                        {"id": requested.id},
                    )
                )
                .scalars()
                .all()
            )
            evidence = await session.scalar(
                text("SELECT evidence_ciphertext FROM motion_render_versions WHERE request_id=:id"),
                {"id": requested.id},
            )
        assert all(len(value) <= 65536 for value in [*records, evidence])
        scope = {"tenant_id": c.tenant, "business_id": c.business, "id": requested.id}
        restored = await c.runner.effects.payloads.open(scope, records[0])
        assert restored["payload"]["context"]["synthetic_note"] == "x" * 200_000
        restored_frames = await c.runner.effects.payloads.open(scope, evidence)
        assert restored_frames["frames"][0]["sha256"] == large_frame.sha256
        assert c.provider.calls == ["generate", "review"]
    puts = c.store.puts
    assert await c.runner.run(c.event) == "already_claimed"
    assert c.store.puts == puts


async def test_new_creative_contract_cannot_release_piece_from_technical_only_review(motion_case):
    from app.services.motion_creative import motion_creative_contract
    from app.services.motion_review import MotionReviewError

    c = motion_case
    prepared = c.inputs.prepare.return_value
    c.inputs.prepare.return_value = replace(
        prepared,
        context={
            **prepared.context,
            "creative_contract": {
                **{k: v for k, v in motion_creative_contract().items() if k != "temporal_review"},
                "version": "reel-creative-v1",
            },
        },
    )
    requested = await create(c)
    # This synthetic provider still returns only the seven historical criteria.
    with pytest.raises(MotionReviewError, match="CREATIVE_CHECKS_REQUIRED"):
        await c.runner.run(c.event)
    result = await c.requests.get(c.tenant, c.business, c.actor, requested.id)
    assert result.state == "failed" and result.piece_id is None
    assert c.provider.calls == ["generate", "review"]
    assert await c.runner.run(c.event) == "already_claimed"


@pytest.mark.parametrize("missing", ["motion_plan", "scene_direction"])
async def test_new_motion_plan_required_before_render_and_duplicate_cannot_retry(motion_case, missing):
    from app.services.motion_creative import motion_creative_contract
    from app.tests.unit.test_motion_plan import planned

    c = motion_case
    prepared = c.inputs.prepare.return_value
    c.inputs.prepare.return_value = replace(
        prepared, context={**prepared.context, "creative_contract": motion_creative_contract()}
    )
    if missing == "scene_direction":
        original_submit = c.provider.submit

        async def no_direction(request, payload):
            result = await original_submit(request, payload)
            return replace(result, composition=planned().model_copy(update={"scene_direction": None}))

        c.provider.submit = no_direction
    requested = await create(c)
    code = "MOTION_PLAN_REQUIRED" if missing == "motion_plan" else "MOTION_SCENE_DIRECTION_REQUIRED"
    with pytest.raises(AuthError, match=code):
        await c.runner.run(c.event)
    result = await c.requests.get(c.tenant, c.business, c.actor, requested.id)
    assert result.state == "failed" and result.piece_id is None
    assert c.provider.calls == ["generate"]
    assert c.store.puts == 0
    assert await c.runner.run(c.event) == "already_claimed"
    assert c.provider.calls == ["generate"]


async def test_illustration_effect_retains_private_provenance_and_blocks_duplicate_dispatch(motion_case, admin):
    from app.services.motion_illustration_policy import illustration_policy
    from app.services.motion_illustrations import MotionIllustrations
    from app.tests.unit.test_motion_illustrations import composition_with_art, image_result
    from app.tests.unit.test_motion_plan import context

    c = motion_case
    c.cfg.motion_ai_mode = "openai"
    c.cfg.motion_ai_model = "gpt-6.1-sol"
    c.cfg.motion_ai_input_usd_micros_per_million_tokens = 2500000
    c.cfg.motion_ai_output_usd_micros_per_million_tokens = 10000000
    c.cfg.openai_api_key = SecretStr("synthetic-not-a-key")
    c.cfg.motion_illustrations_enabled = True
    c.cfg.motion_illustration_reservation_usd_micros = 10000
    c.cfg.motion_illustration_budget_usd_micros = 20000
    c.cfg.motion_request_budget_usd_micros = 100000
    c.cfg.visual_ai_monthly_budget_usd_micros = 1000000
    c.cfg.visual_ai_global_monthly_budget_usd_micros = 1000000
    await create(c)
    row, token = await c.requests.begin(c.tenant, c.business, c.actor, c.body.operation_id, UUID(c.event.event_id))
    ctx = context()
    ctx["illustration_generation"] = illustration_policy(c.cfg)
    prepared = replace(c.inputs.prepare.return_value, context=ctx)
    result = image_result()
    provider = SimpleNamespace(generate=AsyncMock(return_value=result))
    c.store.get_image = AsyncMock(side_effect=lambda key: c.store.objects[key])
    service = MotionIllustrations(c.runner.effects, c.store, provider)
    ready = await service.prepare(row, token, prepared, composition_with_art())
    assert ready.assets[-1].sha256 == result.sha256
    with pytest.raises(AuthError, match="MOTION_EFFECT_ALREADY_CLAIMED"):
        await service.prepare(row, token, prepared, composition_with_art())
    provider.generate.assert_awaited_once()
    async with admin.connect() as conn:
        effect = (await conn.execute(text("SELECT * FROM motion_effects WHERE kind='generate'"))).mappings().one()
        assert effect["state"] == "received" and effect["reservation_id"] is not None
        assert effect["estimated_usd_micros"] == 6500
        assert c.requests.context.open(effect["response_ciphertext"])["sha256"] == result.sha256
        assert await conn.scalar(text("SELECT count(*) FROM visual_cost_reservations")) == 1
        assert await conn.scalar(text("SELECT state FROM visual_cost_reservations")) == "uncertain"


async def test_storyboard_waits_for_exact_owner_approval_and_resumes_once(motion_case, admin, seeded):
    from app.schemas.motion_storyboards import StoryboardDecision
    from app.services.motion_storyboards import MotionStoryboards
    from app.tests.unit.test_motion_plan import context
    from app.tests.unit.test_motion_storyboards import board_output, boarded

    c = motion_case
    c.cfg.motion_storyboard_enabled = True
    c.body = c.body.model_copy(update={"storyboard": True})
    c.inputs.prepare.return_value = replace(
        c.inputs.prepare.return_value, context={**context(), "request": {"storyboard": True}}
    )
    original = c.provider.submit

    async def submit(request, payload):
        result = await original(request, payload)
        return replace(result, composition=boarded())

    c.provider.submit = submit
    c.renderer.render.return_value = board_output(boarded())
    c.store.get_image = AsyncMock(side_effect=lambda key: c.store.objects[key])
    created = await create(c)
    assert await c.runner.run(c.event) == "awaiting_storyboard"
    assert c.provider.calls == ["generate"]
    assert c.renderer.render.await_args.args[0].frames_only
    service = MotionStoryboards(c.requests, c.store)
    _, board, payload = await service.load(c.tenant, c.business, c.actor, created.id)
    assert len(payload["frames"]) == 2 and board["state"] == "awaiting_approval"
    decision = StoryboardDecision(
        operation_id=uuid4(), version_id=board["version_id"], content_sha256=board["content_sha256"], decision="approve"
    )
    with pytest.raises(AuthError, match="VERSION_CONFLICT"):
        await service.decide(
            c.tenant, c.business, c.actor, created.id, decision.model_copy(update={"content_sha256": "f" * 64})
        )
    await service.decide(c.tenant, c.business, c.actor, created.id, decision)
    await service.decide(c.tenant, c.business, c.actor, created.id, decision)
    async with admin.connect() as conn:
        assert (
            await conn.scalar(text("SELECT count(*) FROM outbox_events WHERE event_type='motion.storyboard_approved'"))
            == 1
        )
        assert await conn.scalar(text("SELECT count(*) FROM motion_render_versions")) == 0
    async with c.database.transaction(seeded["t2"], seeded["a2"]) as session:
        assert await session.scalar(text("SELECT count(*) FROM motion_storyboards")) == 0
    event = replace(c.event, event_id=str(uuid5(c.body.operation_id, "motion.storyboard_approved")))
    assert await service.begin_resume(event) is not None
    assert await service.begin_resume(event) is None
    assert c.provider.calls == ["generate"]


@pytest.mark.parametrize("failure_path", ["normal", "quarantine"])
async def test_reconcile_received_storyboard_after_registration_failure(
    motion_case, admin, seeded, monkeypatch, failure_path
):
    from app.services import motion_payloads, motion_storyboards
    from app.services.motion_context import digest
    from app.services.motion_storyboard_recovery import MotionStoryboardRecovery
    from app.tests.unit.test_motion_plan import context
    from app.tests.unit.test_motion_storyboards import board_output, boarded

    c = motion_case
    c.cfg.motion_storyboard_enabled = True
    c.body = c.body.model_copy(update={"storyboard": True})
    c.inputs.prepare.return_value = replace(
        c.inputs.prepare.return_value, context={**context(), "request": {"storyboard": True}}
    )
    original = c.provider.submit

    async def submit(request, payload):
        return replace(await original(request, payload), composition=boarded())

    c.provider.submit = submit
    c.renderer.render.return_value = board_output(boarded())
    c.store.get_image = AsyncMock(side_effect=lambda key: c.store.objects[key])
    monkeypatch.setattr(motion_payloads, "INLINE_BYTES", 5000)
    event = motion_storyboards._event

    async def fail_registration(*args):
        if args[-1] == "motion.storyboard_ready":
            raise RuntimeError("synthetic registration outage")
        await event(*args)

    monkeypatch.setattr(motion_storyboards, "_event", fail_registration)
    created = await create(c)
    with pytest.raises(RuntimeError, match="registration outage"):
        await c.runner.run(c.event)
    version = uuid5(c.body.operation_id, "storyboard:0")
    async with c.database.transaction(c.tenant, c.actor) as session:
        row = dict(await c.requests.row(session, c.tenant, c.business, created.id))
        encrypted = await session.scalar(
            text("SELECT response_ciphertext FROM motion_effects WHERE operation_id=:id"),
            {"id": uuid5(version, "payload:board")},
        )
    assert row["state"] == "failed" and row["failure_code"] == "MOTION_EXECUTION_FAILED"
    payload = await c.runner.effects.payloads.open(row, encrypted)
    service = MotionStoryboardRecovery(motion_storyboards.MotionStoryboards(c.requests, c.store))
    sha = digest(payload)
    with pytest.raises(AuthError):
        await service.reconcile(seeded["t2"], c.business, seeded["a2"], created.id, sha)
    assert await service.reconcile(c.tenant, c.business, c.actor, created.id, sha) == {
        "state": "awaiting_approval",
        "reconciled": True,
    }
    assert await service.reconcile(c.tenant, c.business, c.actor, created.id, sha) == {
        "state": "awaiting_approval",
        "reconciled": False,
    }
    assert c.provider.calls == ["generate"] and c.renderer.render.await_count == 1
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM motion_storyboards")) == 1
        assert await conn.scalar(text("SELECT count(*) FROM motion_render_versions")) == 0
        for action in ("motion.storyboard_ready", "motion.storyboard_reconciled"):
            assert (
                await conn.scalar(
                    text("SELECT count(*) FROM outbox_events WHERE event_type=:action"), {"action": action}
                )
                == 1
            )
        assert (
            await conn.scalar(text("SELECT count(*) FROM outbox_events WHERE event_type='motion.storyboard_approved'"))
            == 0
        )
    # A later failure must not collide with the pre-reconciliation motion.failed event.
    failed_event = uuid5(uuid5(c.body.operation_id, "motion.storyboard_approved"), "motion.failed")
    if failure_path == "normal":
        await c.runner.fail(row, row["execution_token"], "MOTION_AI_OUTPUT_LIMIT", failure_event_id=failed_event)
        await c.runner.fail(row, row["execution_token"], "MOTION_AI_OUTPUT_LIMIT", failure_event_id=failed_event)
    else:
        await c.runner.effects.quarantine(row, row["execution_token"], failure_event_id=failed_event)
        await c.runner.effects.quarantine(row, row["execution_token"], failure_event_id=failed_event)
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM outbox_events WHERE event_type='motion.failed'")) == 2
        expected_code = "MOTION_AI_OUTPUT_LIMIT" if failure_path == "normal" else "MOTION_OUTCOME_UNCERTAIN"
        assert await conn.scalar(text("SELECT failure_code FROM motion_requests")) == expected_code
        assert await conn.scalar(text("SELECT state FROM motion_requests")) == (
            "failed" if failure_path == "normal" else "uncertain"
        )
