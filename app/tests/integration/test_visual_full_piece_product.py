"""The guarded worker receives a complete brief and preserves provider pixels."""

import base64
import hashlib
import io
import json
from uuid import UUID, uuid4

import httpx
import pytest
from PIL import Image
from pydantic import SecretStr
from sqlalchemy import text

from app.db.session import Database
from app.schemas.media_previews import PreviewRequest
from app.services.editorial_briefings import EditorialBriefingService
from app.services.editorial_proposals import EditorialProposalService, _catalog_price_fact
from app.services.media_dispatch import claim_previews
from app.services.media_previews import MediaPreviewService
from app.services.service_agreement import SERVICE_AGREEMENT_HASH, SERVICE_AGREEMENT_VERSION, ServiceAgreementService
from app.services.visual_generation_runner import DatabaseVisualGenerationRunner
from app.services.visual_request_trace import VisualRequestTraceService
from app.services.visual_skills import select_visual_skill
from app.tests.integration.test_business_collection import Store
from app.tests.integration.test_reference_generation_pipeline import persist_synthetic_learning
from app.tests.integration.test_visual_admission import _ready

pytestmark = pytest.mark.integration


def _png(color, size=(64, 64)):
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    return buffer.getvalue()


async def test_integral_piece_uses_snapshot_full_context_and_no_overlay(admin, database, seeded, settings):
    async def analysis_fixture(tenant, business, actor):
        await persist_synthetic_learning(admin, database, tenant, business, actor)

    tenant, business, actor, _, admission = await _ready(
        admin,
        database,
        seeded,
        settings,
        owner_reference={"instagram": "@cafe.referencia", "note": "Gosto das fotos"},
        before_proposal=analysis_fixture,
    )
    editorial_trace = await EditorialProposalService(admission.settings, database).get_request_trace(
        tenant, business, actor, admission.proposal
    )
    editorial_references = json.loads(editorial_trace["request"]["body"]["input"][1]["content"])["reference_context"]
    assert editorial_references[0]["estado_analise"] == "partial"
    cfg = admission.settings.model_copy(
        update={
            "visual_ai_mode": "openai",
            "visual_ai_execution_enabled": True,
            "visual_skill_experiment_enabled": True,
            "visual_ai_reservation_usd_micros": 70,
            "visual_ai_monthly_budget_usd_micros": 100,
            "visual_ai_global_monthly_budget_usd_micros": 100,
            "openai_api_key": SecretStr("synthetic-unused-key"),
            "service_agreement_required": True,
        }
    )
    skill_hash = select_visual_skill(cfg, "instagram-feed-v1", "photo")
    photo, logo = _png("orange"), _png("purple")
    photo_hash, logo_hash = hashlib.sha256(photo).hexdigest(), hashlib.sha256(logo).hexdigest()
    photo_key, logo_key, logo_id = "private/source.png", "private/logo.png", uuid4()
    async with admin.connect() as connection:
        briefing_id = await connection.scalar(
            text("SELECT briefing_id FROM editorial_proposals WHERE id=:id"), {"id": admission.proposal}
        )
    async with database.transaction(tenant, actor) as session:
        status, catalog = await EditorialBriefingService(cfg, database).read_valid(
            session, tenant, business, actor, briefing_id
        )
    assert status == "prepared" and catalog is not None
    price_fact = _catalog_price_fact(catalog)
    assert price_fact is not None
    fact_id = UUID(str(price_fact["id"]))
    store = Store()
    store.objects.update({photo_key: photo, logo_key: logo})

    async with admin.begin() as connection:
        params = {"tenant": tenant, "business": business, "actor": actor, "id": admission.proposal}
        proposal = (
            (await connection.execute(text("SELECT * FROM editorial_proposals WHERE id=:id"), params)).mappings().one()
        )
        document = proposal["document"]
        fact_statement = "Croissant por R$ 18,00"
        document.update(
            title="Uma pausa gostosa",
            angle="Descubra o croissant nesta pausa",
            fact_ids=[str(fact_id)],
            art_text="Croissant por R$ 18,00",
            caption="Uma pausa gostosa com croissant por R$ 18,00",
            cta="Faça seu pedido",
            creative_brief={
                "objective": "Divulgar o croissant",
                "concept": "Uma pausa gostosa",
                "visual_direction": "Valorizar a fotografia",
                "hierarchy": "Produto, preço e chamada",
                "photo_use": "Usar a foto original como foco",
            },
            editorial_skill_id="instagram-feed-v1",
            editorial_skill_sha256=skill_hash,
        )
        for scene in document["script"]:
            if scene["role"] == "fact":
                scene.update(
                    fact_ids=[str(fact_id)], on_screen_text=fact_statement + ".", voiceover=fact_statement + "."
                )
            if scene["role"] == "cta":
                scene.update(on_screen_text="Faça seu pedido", voiceover="Faça seu pedido")
        context = {
            "facts": [
                {
                    "id": str(fact_id),
                    "kind": "price",
                    "statement": fact_statement,
                    "source_detail": "Titular",
                    "valid_until": "2026-12-31",
                }
            ]
        }
        await connection.execute(
            text("INSERT INTO business_context_heads(tenant_id,business_id,version) VALUES(:tenant,:business,1)"),
            params,
        )
        await connection.execute(
            text("""INSERT INTO business_context_versions
              (tenant_id,business_id,version,operation_id,actor_id,request_hash,document)
              VALUES(:tenant,:business,1,:operation,:actor,:hash,CAST(:document AS jsonb))"""),
            {**params, "operation": uuid4(), "hash": "a" * 64, "document": json.dumps(context)},
        )
        await connection.execute(
            text("""INSERT INTO business_brand_kit_logos
              (id,tenant_id,business_id,operation_id,actor_id,request_hash,object_key,sha256,mime_type,
               size_bytes,state,rights_scope)
              VALUES(:logo,:tenant,:business,:operation,:actor,:hash,:key,:sha,'image/png',:size,'ready',
                'business_brand_confirmed')"""),
            {
                **params,
                "logo": logo_id,
                "operation": uuid4(),
                "hash": "b" * 64,
                "key": logo_key,
                "sha": logo_hash,
                "size": len(logo),
            },
        )
        kit = proposal["brand_kit_document"]
        kit["overrides"]["logo_asset_id"] = str(logo_id)
        await connection.execute(
            text("""UPDATE business_brand_kit_versions SET document=CAST(:document AS jsonb)
              WHERE tenant_id=:tenant AND business_id=:business AND version=1"""),
            {**params, "document": json.dumps(kit)},
        )
        await connection.execute(
            text("""UPDATE editorial_proposals SET document=CAST(:document AS jsonb),
              context_version=1,brand_kit_document=CAST(:kit AS jsonb) WHERE id=:id"""),
            {
                **params,
                "document": json.dumps(document),
                "kit": json.dumps(kit),
            },
        )
        await connection.execute(
            text("""UPDATE whatsapp_material_assets SET kind='image',object_key=:key,
              mime_type='image/png',sha256=:sha WHERE id=:source"""),
            {"source": proposal["source_asset_id"], "key": photo_key, "sha": photo_hash},
        )
    await ServiceAgreementService(cfg, database).accept(
        tenant, business, actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH
    )
    service = MediaPreviewService(cfg, database, store)
    preview = await service.request_candidate(
        tenant,
        business,
        actor,
        PreviewRequest(operation_id=uuid4(), proposal_id=admission.proposal, generation_mode="visual_ai"),
    )
    assert preview.visual_recipe == "full_piece_v1"
    sent = []
    provider_image = _png("#847766", (1024, 1280))

    def response(request):
        sent.append(json.loads(request.content))
        return httpx.Response(200, json={"data": [{"b64_json": base64.b64encode(provider_image).decode()}]})

    worker = Database(cfg, correlator=True)
    try:
        claim = (await claim_previews(worker, uuid4(), visual_enabled=True))[0]
        runner = DatabaseVisualGenerationRunner(
            cfg, database, worker, transport=httpx.MockTransport(response), store=store
        )
        assert await runner.run_preview(preview.id, claim.fence) == "completed"
        assert len(sent) == 1
        prompt = sent[0]["prompt"]
        assert "Crie uma imagem do croissant" in prompt
        assert "Croissant por R$ 18,00" in prompt and "Uma pausa gostosa" in prompt
        assert "Faça seu pedido" in prompt and "Orientação criativa de referência versionada" in prompt
        assert "logomarca original autorizada" in prompt
        assert len(sent[0]["images"]) == 3
        assert "imagem de exemplo do kit é fictícia" in prompt
        assert "cafe.referencia" in prompt and "Gosto das fotos" in prompt
        assert "Composição com espaço vazio" in prompt and "Tom acolhedor" in prompt
        assert '"estado_analise": "partial"' in prompt
        assert json.dumps(editorial_references, sort_keys=True, ensure_ascii=False) in prompt
        assert "não presuma acesso a perfis sem análise" in prompt
        trace = await VisualRequestTraceService(cfg, database).read(tenant, business, actor, preview.id)
        assert trace["request"]["prompt"] == prompt
        assert "Não acrescente palavras" not in prompt
        async with admin.connect() as connection:
            row = (
                (await connection.execute(text("SELECT * FROM media_previews WHERE id=:id"), {"id": preview.id}))
                .mappings()
                .one()
            )
            assert row["visual_recipe"] == "full_piece_v1" and row["state"] == "completed"
            output = store.objects[row["object_key"]]
        with Image.open(io.BytesIO(output)) as image:
            assert image.convert("RGB").getpixel((25, 25)) == image.convert("RGB").getpixel((25, 1200))
    finally:
        await worker.close()
