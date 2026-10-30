"""Configured WhatsApp-to-review path with production worker and fake HTTP IO."""

import asyncio
import base64
import hashlib
import io
import json
import os
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import httpx
import pytest
from cryptography.fernet import Fernet
from PIL import Image
from pydantic import SecretStr
from sqlalchemy import text
from temporalio.client import Client
from temporalio.worker import Worker

from app.adapters.editorial_ai import OpenAIEditorialProvider
from app.adapters.jev_intent_ai import JevIntentProvider
from app.adapters.visual_ai import OpenAIVisualProvider
from app.api.v1 import media_previews as preview_routes
from app.db.session import Database
from app.entrypoints import worker as worker_entrypoint
from app.main import create_app
from app.schemas.brand_kits import BrandKitConfirmRequest, BrandKitDraftRequest
from app.schemas.business_catalog import CatalogUpdate
from app.schemas.editorial_proposals import ProposalDraft
from app.services.brand_kits import BrandKitService
from app.services.business_catalog import BusinessCatalogService
from app.services.business_collection import BusinessCollectionService
from app.services.editorial_dispatch import dispatch_proposals
from app.services.media_dispatch import dispatch_previews
from app.services.service_agreement import SERVICE_AGREEMENT_HASH, SERVICE_AGREEMENT_VERSION, ServiceAgreementService
from app.services.whatsapp_ingest import sender_hash
from app.tests.integration.test_brand_kits import _draft, _overrides
from app.tests.integration.test_business_catalog import _payload
from app.tests.integration.test_business_collection import Store
from app.tests.integration.test_editorial_proposals import _asset, _business
from app.tests.unit.test_business_collection_contract import upload
from app.tests.unit.test_core import access_token
from app.tests.unit.test_jev_intent_provider import answer
from app.workflows.content_candidate import ContentCandidateWorkflow
from app.workflows.media_preview import StaticPreviewWorkflow
from app.workflows.visual_generation import VisualGenerationWorkflow

pytestmark = [pytest.mark.integration, pytest.mark.temporal]


class PrivateStore(Store):
    async def signed_url(self, key, mime):
        assert key in self.objects and mime == "image/jpeg"
        return f"https://private.test/{key}?expires=120"


async def _assert_uncertain_path(admin, client, dispatcher, cfg, queue, source):
    async with admin.connect() as connection:
        row = (await connection.execute(text("SELECT * FROM media_previews"))).mappings().one()
        assert row["generation_mode"] == "visual_ai" and row["state"] == "failed"
        assert row["error_code"] == "VISUAL_OUTCOME_UNCERTAIN"
        assert row["attempts"] == row["dispatch_fence"] == 1
        assert row["object_key"] is None and row["sha256"] is None
        assert await connection.scalar(text("SELECT count(*) FROM visual_ai_attempts")) == 1
        assert await connection.scalar(text("SELECT state FROM visual_consent_runs")) == "in_flight"
        assert await connection.scalar(text("SELECT state FROM visual_cost_reservations")) == "uncertain"
        assert await connection.scalar(text("SELECT committed_usd_micros FROM visual_global_monthly_budget")) == 70
        assert await connection.scalar(text("SELECT count(*) FROM content_deliveries")) == 0
    handle = client.get_workflow_handle(f"visual-preview/{row['id']}")
    assert await handle.result() == "uncertain"
    history = await handle.fetch_history()
    assert sum(event.HasField("activity_task_scheduled_event_attributes") for event in history.events) == 1
    assert await dispatch_previews(dispatcher, client, cfg, uuid4()) == 0
    async with asyncio.timeout(15):
        replay = await client.execute_workflow(
            ContentCandidateWorkflow.run,
            str(source),
            id=f"test-visual-product-replay/{source}",
            task_queue=queue,
        )
    assert replay == "preview_failed"
    assert await dispatch_previews(dispatcher, client, cfg, uuid4()) == 0
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM visual_ai_attempts")) == 1
        assert await connection.scalar(text("SELECT state FROM visual_consent_runs")) == "in_flight"
        assert await connection.scalar(text("SELECT state FROM visual_cost_reservations")) == "uncertain"


@pytest.mark.parametrize(
    "format,dimensions,outcome",
    [("photo", (1024, 1280), "completed"), ("story", (1152, 2048), "completed"), ("photo", (1024, 1280), "timeout")],
)
async def test_configured_worker_creates_real_mode_private_candidate_with_simulated_providers(
    admin, database, seeded, settings, monkeypatch, format, dimensions, outcome
):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    key = Fernet.generate_key().decode()
    queue = f"test-visual-product-{uuid4()}"
    cfg = settings.model_copy(
        update={
            "meta_encryption_key": SecretStr(key),
            "service_agreement_required": True,
            "visual_ai_mode": "openai",
            "visual_ai_execution_enabled": True,
            "visual_ai_reservation_usd_micros": 70,
            "visual_ai_monthly_budget_usd_micros": 100,
            "visual_ai_global_monthly_budget_usd_micros": 100,
            "openai_api_key": SecretStr("synthetic-unused-openai-key"),
            "editorial_ai_mode": "openai",
            "editorial_daily_token_limit": 30000,
            "intent_ai_mode": "jev",
            "typesafe_api_key": SecretStr("synthetic-unused-jev-key"),
            "intent_ai_daily_budget_usd_micros": 3000,
            "temporal_address": os.environ["TEST_TEMPORAL_ADDRESS"],
            "temporal_task_queue": queue,
        }
    )
    async with admin.begin() as connection:
        params = {"tenant": tenant, "business": business, "actor": actor}
        await connection.execute(
            text("UPDATE business_profiles SET phone_verified=true WHERE tenant_id=:tenant AND business_id=:business"),
            params,
        )
        await connection.execute(
            text("""INSERT INTO whatsapp_channel_links
              (tenant_id,business_id,actor_id,sender_hash,proof_event_id,linked_at)
              VALUES(:tenant,:business,:actor,:sender,:proof,clock_timestamp()-interval '1 minute')"""),
            {**params, "sender": sender_hash(cfg, "+5511999999999"), "proof": uuid4()},
        )
    agreement = await ServiceAgreementService(cfg, database).accept(
        tenant, business, actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH
    )
    assert agreement["accepted"] and agreement["access_active"]
    message = "Crie uma imagem do croissant com preço" if format == "photo" else "Crie um story do croissant com preço"
    source = await _asset(admin, tenant, business, key, body=message)
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE whatsapp_material_events SET ciphertext=:cipher WHERE id=:id"),
            {
                "id": source,
                "cipher": Fernet(key.encode()).encrypt(json.dumps({"from": "5511999999999"}).encode()).decode(),
            },
        )
    catalog = _payload()
    catalog["promotions"] = []
    await BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
    offering = UUID(catalog["offerings"][0]["id"])
    store = PrivateStore()
    await BusinessCollectionService(cfg, database, store).upload(
        tenant, business, actor, upload(item_id=str(offering), space_kind=None)
    )
    kits = BrandKitService(cfg, database, store)
    draft = await kits.draft(
        tenant, business, actor, BrandKitDraftRequest.model_validate(_draft(0, _overrides("Café sintético")))
    )
    assert draft.draft is not None
    await kits.confirm(
        tenant, business, actor, BrandKitConfirmRequest(operation_id=uuid4(), expected_version=draft.draft.version)
    )

    jev_calls, image_calls = [], []

    def jev_http(request):
        assert request.url == "https://api.typesafe.ai/v1/systemone"
        body = json.loads(request.content)
        state = json.loads(body["state"])
        assert state["message"] == message
        assert state["candidates"] == [{"id": str(offering), "kind": "product", "name": "Croissant"}]
        jev_calls.append(request.headers["X-Client-Request-Id"])
        return httpx.Response(
            200,
            json={
                "model": cfg.intent_ai_model,
                "usage": {"input_tokens": 720, "output_tokens": 15},
                "answers": {
                    "intent": answer("content_request", set(body["questions"]["intent"]["criteria"])),
                    "offering": answer("item_0", set(body["questions"]["offering"]["criteria"])),
                    "format": answer(format, set(body["questions"]["format"]["criteria"])),
                },
            },
        )

    def images_http(request):
        assert request.url == "https://api.openai.com/v1/images/edits"
        body = json.loads(request.content)
        assert body["size"] == f"{dimensions[0]}x{dimensions[1]}"
        assert body["n"] == 1 and body["output_format"] == "png"
        assert len(body["images"]) == 2
        assert body["images"][0]["image_url"].startswith("data:image/png;base64,")
        assert "Croissant" in body["prompt"] and "R$ 18,00" in body["prompt"]
        assert "Orientação criativa de referência versionada" in body["prompt"]
        assert "Não acrescente palavras" not in body["prompt"]
        image_calls.append(request.headers["X-Client-Request-Id"])
        if outcome == "timeout":
            raise httpx.ReadTimeout("synthetic lost response", request=request)
        output = io.BytesIO()
        Image.new("RGB", dimensions, "#96826e").save(output, format="PNG")
        return httpx.Response(
            200,
            headers={"x-request-id": "synthetic-image-response"},
            json={"data": [{"b64_json": base64.b64encode(output.getvalue()).decode()}]},
        )

    monkeypatch.setattr(
        "app.services.jev_interpreter.JevIntentProvider",
        lambda secret, model: JevIntentProvider(secret, model, transport=httpx.MockTransport(jev_http)),
    )
    monkeypatch.setattr(
        "app.services.visual_generation_runner.OpenAIVisualProvider",
        lambda secret, **_: OpenAIVisualProvider(secret, transport=httpx.MockTransport(images_http)),
    )

    async def editorial_result(payload, proposal_id, *, prepared_request):
        assert prepared_request["input"][1]["content"]
        fact = next(item for item in payload["confirmed_facts"] if item["kind"] == "price")
        assert fact["statement"] == "Croissant por R$ 18,00"
        assert payload["material"] == message
        assert payload["editorial_skill"]["id"] == ("instagram-feed-v1" if format == "photo" else "instagram-story-v1")
        return (
            ProposalDraft(
                title="Conheça Croissant",
                format=format,
                angle="Conheça o Croissant",
                fact_ids=[UUID(fact["id"])],
                hypotheses=[],
                questions=[],
                scene_plan=["fact", "cta"],
                art_text="Croissant por R$ 18,00",
                caption="Conheça Croissant por R$ 18,00",
                cta="Fale com a gente",
                creative_brief={
                    "objective": "Divulgar croissant",
                    "concept": "Uma pausa gostosa",
                    "visual_direction": "Valorizar foto e produto",
                    "hierarchy": "Produto, preço e chamada",
                    "photo_use": "Usar a foto como foco",
                },
            ),
            100,
            100,
        )

    editorial_call = AsyncMock(side_effect=editorial_result)
    monkeypatch.setattr(OpenAIEditorialProvider, "propose", editorial_call)
    monkeypatch.setattr(worker_entrypoint, "get_settings", lambda: cfg)
    monkeypatch.setattr(worker_entrypoint, "MaterialStore", lambda _: store)
    monkeypatch.setattr("app.services.visual_generation_runner.MaterialStore", lambda _: store)
    monkeypatch.setattr(preview_routes, "MaterialStore", lambda _: store)
    initialized = asyncio.Event()
    registered = []

    def register_worker(*args, **kwargs):
        assert VisualGenerationWorkflow in kwargs["workflows"]
        assert StaticPreviewWorkflow in kwargs["workflows"]
        assert any(callback.__name__ == "run_visual_generation" for callback in kwargs["activities"])
        execution = Worker(*args, **kwargs)
        registered.append(execution)
        initialized.set()
        return execution

    monkeypatch.setattr(worker_entrypoint, "Worker", register_worker)
    client = await Client.connect(cfg.temporal_address)
    dispatcher_database = Database(cfg, correlator=True)
    worker_task = asyncio.create_task(worker_entrypoint.run_worker())
    handle = result_task = None
    try:
        await asyncio.wait_for(initialized.wait(), timeout=10)
        handle = await client.start_workflow(
            ContentCandidateWorkflow.run, str(source), id=f"test-visual-product/{source}", task_queue=queue
        )
        result_task = asyncio.create_task(handle.result())
        async with asyncio.timeout(45):
            while not result_task.done():
                await dispatch_proposals(dispatcher_database, client, cfg, uuid4())
                await dispatch_previews(dispatcher_database, client, cfg, uuid4())
                await asyncio.sleep(0.1)
            assert await result_task == ("candidate_delivered" if outcome == "completed" else "preview_failed")
        assert len(jev_calls) == len(image_calls) == 1
        editorial_call.assert_awaited_once()
        if outcome == "timeout":
            await _assert_uncertain_path(admin, client, dispatcher_database, cfg, queue, source)
            assert len(jev_calls) == len(image_calls) == 1
            return
        app = create_app(cfg, database)
        base = f"/api/v1/organizations/{tenant}/businesses/{business}"
        owner = {"Authorization": f"Bearer {access_token(cfg, actor)}"}
        async with (
            app.router.lifespan_context(app),
            httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as api,
        ):
            response = await api.get(f"{base}/media-previews", headers=owner)
            assert response.status_code == 200, response.text
            previews = response.json()
            assert len(previews) == 1
            preview = previews[0]
            assert preview["generation_mode"] == "visual_ai" and preview["state"] == "completed"
            assert (preview["width"], preview["height"]) == dimensions
            link = await api.get(f"{base}/media-previews/{preview['id']}/download-link", headers=owner)
            assert link.status_code == 200, link.text
            object_key = link.json()["url"].removeprefix("https://private.test/").split("?")[0]
            with Image.open(io.BytesIO(store.objects[object_key])) as image:
                assert image.format == "JPEG" and image.size == dimensions
                assert image.convert("RGB").getpixel((25, 25)) == image.convert("RGB").getpixel(
                    (25, dimensions[1] - 25)
                )
            deliveries = (await api.get(f"{base}/content-deliveries", headers=owner)).json()
            assert len(deliveries) == 1 and deliveries[0]["kind"] == "candidate"
            assert deliveries[0]["caption"] == "Conheça Croissant por R$ 18,00"
            assert deliveries[0]["preview_id"] == preview["id"] and deliveries[0]["decision_state"] == "pending"
            approval = await api.post(
                f"{base}/content-deliveries/{deliveries[0]['id']}/decision",
                headers=owner,
                json={"operation_id": str(uuid4()), "decision": "approve"},
            )
            assert approval.status_code == 409
            assert approval.json()["error_code"] == "VISUAL_REVIEW_REQUIRED"
            checksum = hashlib.sha256(store.objects[object_key]).hexdigest()
            approval = await api.post(
                f"{base}/content-deliveries/{deliveries[0]['id']}/decision",
                headers=owner,
                json={
                    "operation_id": str(uuid4()),
                    "decision": "approve",
                    "visual_review": {
                        "preview_sha256": checksum,
                        "price_and_terms": True,
                        "spelling": True,
                        "identity": True,
                        "fidelity": True,
                        "legibility": True,
                    },
                },
            )
            assert approval.status_code == 200, approval.text
            assert approval.json()["decision_state"] == "approved"
            other = {"Authorization": f"Bearer {access_token(cfg, seeded['a2'])}"}
            assert (await api.get(f"{base}/media-previews", headers=other)).status_code == 403

        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM visual_ai_attempts")) == 1
            assert await connection.scalar(text("SELECT count(*) FROM content_deliveries")) == 1
            assert await connection.scalar(text("SELECT state FROM visual_consent_runs")) == "finished"
            assert await connection.scalar(text("SELECT state FROM visual_cost_reservations")) == "uncertain"
            assert await connection.scalar(text("SELECT committed_usd_micros FROM visual_global_monthly_budget")) == 70
            assert (
                await connection.scalar(text("SELECT count(*) FROM visual_cost_events WHERE action='uncertain'")) == 1
            )
            assert await connection.scalar(text("SELECT state FROM editorial_intent_usage")) == "completed"
            assert await connection.scalar(text("SELECT count(*) FROM service_agreement_acceptances")) == 1
            for table in (
                "whatsapp_processing_consents",
                "editorial_ai_consents",
                "intent_jev_consents",
                "visual_ai_consents",
            ):
                assert await connection.scalar(text(f"SELECT count(*) FROM {table}")) == 0
            row = (await connection.execute(text("SELECT sha256,object_key FROM media_previews"))).mappings().one()
            assert row["sha256"] == hashlib.sha256(store.objects[row["object_key"]]).hexdigest()
        assert store.reads > 0 and len(jev_calls) == len(image_calls) == 1
    finally:
        if result_task is not None and not result_task.done():
            result_task.cancel()
            if handle is not None:
                await handle.cancel()
            await asyncio.gather(result_task, return_exceptions=True)
        if registered:
            await asyncio.wait_for(registered[0].shutdown(), timeout=20)
        else:
            worker_task.cancel()
        await asyncio.gather(worker_task, return_exceptions=True)
        await dispatcher_database.close()
