"""Skill snapshot is carried through the real database guard with fake HTTP."""

import base64
import io
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import NAMESPACE_URL, uuid4, uuid5

import httpx
import pytest
from PIL import Image
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.db.session import Database
from app.schemas.media_previews import PreviewRequest
from app.services.auth import AuthError
from app.services.editorial_consent_scope import VisualRunScope as AdmittedVisualRunScope
from app.services.editorial_consent_scope import admitted_visual_run
from app.services.media_dispatch import claim_previews
from app.services.media_previews import MediaPreviewService
from app.services.service_agreement import SERVICE_AGREEMENT_HASH, SERVICE_AGREEMENT_VERSION, ServiceAgreementService
from app.services.visual_brand_finish import VisualBrandFinishService
from app.services.visual_generation_runner import DatabaseVisualGenerationRunner
from app.services.visual_skills import select_visual_skill
from app.tests.integration.test_business_collection import Store
from app.tests.integration.test_visual_admission import _ready

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "format,skill,other_skill,dimensions",
    [
        ("photo", "instagram-feed-v1", "instagram-story-v1", (1024, 1280)),
        ("story", "instagram-story-v1", "instagram-feed-v1", (1152, 2048)),
    ],
)
async def test_visual_skill_is_persisted_idempotent_and_used_in_real_guarded_worker(
    admin, database, seeded, settings, format, skill, other_skill, dimensions
):
    tenant, business, actor, _, admission = await _ready(admin, database, seeded, settings, format)
    # Supply a validated model-shaped proposal to the image-only integration;
    # the separate product-path test exercises the editorial provider itself.
    async with admin.begin() as connection:
        await connection.execute(
            text("""UPDATE editorial_proposals SET document=document || CAST(:copy AS jsonb)
              WHERE id=:proposal"""),
            {
                "proposal": admission.proposal,
                "copy": json.dumps(
                    {
                        "title": "Conheça Croissant",
                        "angle": "Conheça o Croissant",
                        "art_text": "Conheça Croissant",
                        "caption": "Conheça nosso Croissant",
                        "cta": "Fale com a gente",
                    }
                ),
            },
        )
    cfg = admission.settings.model_copy(
        update={
            "visual_ai_mode": "openai",
            "visual_ai_execution_enabled": True,
            "visual_skill_experiment_enabled": True,
            "visual_ai_reservation_usd_micros": 70,
            "visual_ai_monthly_budget_usd_micros": 300,
            "visual_ai_global_monthly_budget_usd_micros": 300,
            "openai_api_key": SecretStr("synthetic-unused-key"),
            "service_agreement_required": True,
        }
    )
    await ServiceAgreementService(cfg, database).accept(
        tenant, business, actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH
    )
    store = Store()
    service = MediaPreviewService(cfg, database, store)
    operation = uuid4()
    body = PreviewRequest(
        operation_id=operation,
        proposal_id=admission.proposal,
        generation_mode="visual_ai",
        visual_skill_id=skill,
    )
    cfg.visual_skill_experiment_enabled = False
    with pytest.raises(AuthError, match="VISUAL_SKILL_DISABLED"):
        await service.request_candidate(tenant, business, actor, body)
    cfg.visual_skill_experiment_enabled = True
    preview = await service.request_candidate(tenant, business, actor, body)
    assert preview.visual_skill_id == skill
    assert (await service.request_candidate(tenant, business, actor, body)).id == preview.id
    async with admin.connect() as connection:
        for invalid_skill, invalid_sha in ((None, "a" * 64), (skill, None)):
            with pytest.raises(IntegrityError):
                async with connection.begin_nested():
                    await connection.execute(
                        text("UPDATE media_previews SET visual_skill_id=:skill,visual_skill_sha256=:sha WHERE id=:id"),
                        {"id": preview.id, "skill": invalid_skill, "sha": invalid_sha},
                    )
    with pytest.raises(AuthError, match="VISUAL_SKILL_FORMAT_INVALID"):
        await service.request_candidate(
            tenant,
            business,
            actor,
            body.model_copy(update={"operation_id": uuid4(), "visual_skill_id": other_skill}),
        )
    with pytest.raises(AuthError, match="PREVIEW_OPERATION_CONFLICT"):
        await service.request_candidate(tenant, business, actor, body.model_copy(update={"visual_skill_id": None}))
    control = await service.request_candidate(
        tenant, business, actor, body.model_copy(update={"operation_id": uuid4(), "visual_skill_id": None})
    )
    sha = select_visual_skill(cfg, skill, format)
    visual_operation = uuid5(NAMESPACE_URL, f"visual-preview:{preview.id}")
    brand = VisualBrandFinishService(cfg, database, store)
    for admitted, expected in (
        (
            AdmittedVisualRunScope(
                tenant, business, actor, visual_operation, 1, preview.id, skill, None, "full_piece_v1"
            ),
            "VISUAL_SKILL_CHANGED",
        ),
        (
            AdmittedVisualRunScope(tenant, business, actor, visual_operation, 1, None, skill, sha, "full_piece_v1"),
            "VISUAL_RECIPE_CHANGED",
        ),
        (
            AdmittedVisualRunScope(tenant, business, actor, visual_operation, 1, uuid4(), skill, sha, "full_piece_v1"),
            "VISUAL_SKILL_CHANGED",
        ),
        (
            AdmittedVisualRunScope(
                tenant, business, actor, visual_operation, 1, preview.id, skill, "0" * 64, "full_piece_v1"
            ),
            "VISUAL_SKILL_CHANGED",
        ),
    ):
        with admitted_visual_run(admitted), pytest.raises(AuthError, match=expected):
            await brand.prepare(tenant, business, actor, admission.proposal, operation, candidate=True)
    async with database.transaction(seeded["t2"], seeded["a2"]) as other:
        assert await other.scalar(text("SELECT count(*) FROM media_previews WHERE id=:id"), {"id": preview.id}) == 0
    sent = []
    image = io.BytesIO()
    Image.new("RGB", dimensions, "#847766").save(image, format="PNG")

    def response(request):
        sent.append(json.loads(request.content))
        # Disabling new skill requests must not strand an already admitted run.
        cfg.visual_skill_experiment_enabled = False
        return httpx.Response(200, json={"data": [{"b64_json": base64.b64encode(image.getvalue()).decode()}]})

    worker = Database(cfg, correlator=True)
    try:
        claims = {claim.id: claim for claim in await claim_previews(worker, uuid4(), visual_enabled=True)}
        runner = DatabaseVisualGenerationRunner(
            cfg, database, worker, transport=httpx.MockTransport(response), store=store
        )
        assert await runner.run_preview(preview.id, claims[preview.id].fence) == "completed"
        assert await runner.run_preview(control.id, claims[control.id].fence) == "completed"
        assert len(sent) == 2
        assert all("Orientação criativa de referência versionada" in item["prompt"] for item in sent)
        assert all(skill in item["prompt"] and sha in item["prompt"] for item in sent)
        assert all("Não acrescente palavras" not in item["prompt"] for item in sent)
        assert sent[0]["model"] == sent[1]["model"] and sent[0]["size"] == sent[1]["size"]
        async with admin.connect() as connection:
            row = (
                (
                    await connection.execute(
                        text("SELECT visual_skill_id,visual_skill_sha256,state FROM media_previews WHERE id=:id"),
                        {"id": preview.id},
                    )
                )
                .mappings()
                .one()
            )
            assert row["visual_skill_id"] == skill and len(row["visual_skill_sha256"]) == 64
            assert row["state"] == "completed"
        cfg.visual_skill_experiment_enabled = False
        assert (await service.file_key(tenant, business, actor, preview.id, review=True)).endswith(".jpg")
        assert (await service.file_key(tenant, business, actor, control.id, review=True)).endswith(".jpg")
    finally:
        await worker.close()


async def test_real_visual_worker_rejects_baseline_without_calling_image_provider(admin, database, seeded, settings):
    tenant, business, actor, _, admission = await _ready(admin, database, seeded, settings)
    async with admin.begin() as connection:
        await connection.execute(
            text("""UPDATE editorial_proposals SET model='baseline-v1',
              document=document - 'art_text' - 'caption' - 'cta' - 'creative_brief'
                - 'editorial_skill_id' - 'editorial_skill_sha256' WHERE id=:id"""),
            {"id": admission.proposal},
        )
    cfg = admission.settings.model_copy(
        update={
            "visual_ai_mode": "openai",
            "visual_ai_execution_enabled": True,
            "visual_ai_reservation_usd_micros": 70,
            "visual_ai_monthly_budget_usd_micros": 100,
            "visual_ai_global_monthly_budget_usd_micros": 100,
            "openai_api_key": SecretStr("synthetic-unused-key"),
            "service_agreement_required": True,
        }
    )
    await ServiceAgreementService(cfg, database).accept(
        tenant, business, actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH
    )
    preview = await MediaPreviewService(cfg, database, Store()).request_candidate(
        tenant,
        business,
        actor,
        PreviewRequest(operation_id=uuid4(), proposal_id=admission.proposal, generation_mode="visual_ai"),
    )
    worker = Database(cfg, correlator=True)
    provider = SimpleNamespace(generate=AsyncMock())
    try:
        claim = (await claim_previews(worker, uuid4(), visual_enabled=True))[0]
        runner = DatabaseVisualGenerationRunner(cfg, database, worker, provider=provider, store=Store())
        assert await runner.run_preview(preview.id, claim.fence) == "stale"
        provider.generate.assert_not_awaited()
        async with admin.connect() as connection:
            row = (
                (
                    await connection.execute(
                        text("SELECT state,error_code FROM media_previews WHERE id=:id"), {"id": preview.id}
                    )
                )
                .mappings()
                .one()
            )
            assert row["state"] == "failed" and row["error_code"] == "VISUAL_ADMISSION_ABORTED"
            assert await connection.scalar(text("SELECT count(*) FROM visual_ai_attempts")) == 0
    finally:
        await worker.close()
