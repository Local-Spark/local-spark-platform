"""Prepare a visual request from a real briefing and a private WhatsApp photo."""

import hashlib
import io
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from cryptography.fernet import Fernet
from PIL import Image
from pydantic import SecretStr
from sqlalchemy import text

from app.db.session import Database
from app.schemas.business_catalog import CatalogUpdate
from app.services.auth import AuthError
from app.services.business_catalog import BusinessCatalogService
from app.services.creative_catalog_resolution import CatalogIntent
from app.services.editorial_consent_scope import VisualRunScope, admitted_visual_run
from app.services.editorial_dispatch import claim_proposals, finish_proposal_dispatch
from app.services.editorial_proposals import EditorialProposalService
from app.services.visual_consent import VisualConsentService
from app.services.visual_context import VisualContextService
from app.services.visual_requests import VisualRequestService
from app.tests.integration.test_brand_kits import _overrides
from app.tests.integration.test_business_catalog import _payload
from app.tests.integration.test_editorial_briefings import _enable
from app.tests.integration.test_editorial_proposals import _asset, _business
from app.tests.integration.test_visual_attempts import preview
from app.tests.integration.test_visual_brand_finish import _editorial_provider
from app.workflows.content_activities import ContentCandidateActivities

pytestmark = pytest.mark.integration


async def test_request_preparation_uses_whatsapp_photo_and_rejects_revocation(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(
        update={
            "meta_encryption_key": SecretStr(key),
            "visual_ai_mode": "openai",
            "editorial_ai_mode": "openai",
            "openai_api_key": SecretStr("synthetic-key"),
            "editorial_daily_token_limit": 100000,
        }
    )
    source = await _asset(admin, tenant, business, key, kind="image", body="Crie uma imagem do croissant")
    image = io.BytesIO()
    exif = Image.Exif()
    exif[270] = "private"
    Image.new("RGB", (80, 80), "red").save(image, format="PNG", exif=exif)
    raw = image.getvalue()
    catalog = _payload()
    await BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
    async with admin.begin() as conn:
        params = {"tenant": tenant, "business": business, "actor": actor, "operation": uuid4()}
        await conn.execute(
            text("""UPDATE whatsapp_material_assets SET object_key='private/test',mime_type='image/png',sha256=:sha,
              size_bytes=:size WHERE id=:id"""),
            {"id": source, "sha": hashlib.sha256(raw).hexdigest(), "size": len(raw)},
        )
        await conn.execute(
            text("""INSERT INTO business_brand_kit_heads(tenant_id,business_id,version,confirmed_version)
              VALUES(:tenant,:business,1,1)"""),
            params,
        )
        await conn.execute(
            text("""INSERT INTO business_brand_kit_versions
              (tenant_id,business_id,version,operation_id,actor_id,request_hash,state,document)
              VALUES(:tenant,:business,1,:operation,:actor,:hash,'confirmed',CAST(:doc AS jsonb))"""),
            {
                **params,
                "hash": "a" * 64,
                "doc": json.dumps({"kit_id": "cafe-pausas", "kit_version": 1, "overrides": _overrides()}),
            },
        )
    interpreter = SimpleNamespace(
        interpret=AsyncMock(
            return_value=CatalogIntent("selected", UUID(catalog["offerings"][0]["id"]), "content_request", "photo")
        )
    )
    worker = Database(cfg, correlator=True)
    store = SimpleNamespace(get_image=AsyncMock(return_value=raw))
    try:
        activity = ContentCandidateActivities(cfg, database, worker, interpreter=interpreter)
        proposal = UUID(await activity.request_candidate_proposal(str(source)))
        claims = await claim_proposals(worker, uuid4())
        await finish_proposal_dispatch(worker, claims[0], True)
        provider = _editorial_provider()
        assert (
            await EditorialProposalService(cfg, worker, provider, owner_database=database).run(proposal) == "completed"
        )
        provider.propose.assert_awaited_once()
        consent = VisualConsentService(cfg, database)
        await consent.set(tenant, business, actor, True)
        service = VisualRequestService(cfg, database, store)
        item, operation = await preview(admin, tenant, business, actor), uuid4()
        snapshot = await VisualContextService(cfg, database).capture(tenant, business, actor, proposal, candidate=True)
        async with admin.begin() as conn:
            await conn.execute(
                text("""UPDATE media_previews SET proposal_id=:proposal,operation_id=:operation,
                  generation_mode='visual_ai',visual_recipe='full_piece_v1',visual_fingerprint=:fingerprint
                  WHERE id=:id"""),
                {"proposal": proposal, "operation": operation, "id": item, "fingerprint": snapshot.fingerprint},
            )
        scope = VisualRunScope(tenant, business, actor, operation, 1, item, visual_recipe="full_piece_v1")
        with admitted_visual_run(scope):
            result = await service.prepare(tenant, business, actor, proposal, operation, candidate=True)
        assert result.sources[0].kind == "source_photo" and result.sources[0].id == source
        assert "Croissant" in result.request.prompt and "Faça seu pedido" in result.request.prompt
        with Image.open(io.BytesIO(result.request.references[0].content)) as normalized:
            assert not normalized.getexif()
        await consent.set(tenant, business, actor, False)
        with pytest.raises(AuthError, match="VISUAL_AI_CONSENT_REQUIRED"):
            await service.prepare(tenant, business, actor, proposal, uuid4(), candidate=True)
    finally:
        await worker.close()
