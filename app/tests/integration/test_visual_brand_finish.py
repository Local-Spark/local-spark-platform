"""Brand finishing verifies the owner snapshot and logo on the real DB roles."""

import base64
import hashlib
import io
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import httpx
import pytest
from cryptography.fernet import Fernet
from PIL import Image
from pydantic import SecretStr
from sqlalchemy import text

from app.adapters.material_media import FetchedMedia
from app.adapters.visual_ai import OpenAIVisualProvider
from app.db.session import Database
from app.schemas.business_catalog import CatalogUpdate
from app.services.auth import AuthError
from app.services.business_catalog import BusinessCatalogService
from app.services.creative_catalog_resolution import CatalogIntent
from app.services.editorial_dispatch import claim_proposals, finish_proposal_dispatch
from app.services.editorial_proposals import EditorialProposalService
from app.services.visual_attempts import VisualAttemptService
from app.services.visual_brand_finish import VisualBrandFinishService
from app.services.visual_consent import VisualConsentService
from app.services.visual_context import VisualContextService
from app.services.visual_cost_ledger import VisualCostLedger
from app.services.visual_provider_execution import VisualSubmissionClaims
from app.services.visual_real_orchestrator import VisualRealOrchestrator, VisualRunScope
from app.tests.integration.test_brand_kits import _overrides
from app.tests.integration.test_business_catalog import _payload
from app.tests.integration.test_editorial_briefings import _enable
from app.tests.integration.test_editorial_proposals import _asset, _business
from app.tests.integration.test_visual_attempts import preview
from app.workflows.content_activities import ContentCandidateActivities

pytestmark = pytest.mark.integration


def _png(size, color):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return buf.getvalue()


async def test_finishing_requires_valid_logo_and_discards_after_kit_change(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr(key), "visual_ai_mode": "openai"})
    source = await _asset(admin, tenant, business, key, kind="image", body="Crie uma imagem do croissant")
    raw, logo = _png((80, 80), "red"), _png((60, 60), "green")
    catalog = _payload()
    await BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
    logo_id = uuid4()
    overrides = _overrides()
    overrides["logo_asset_id"] = str(logo_id)
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
                "doc": json.dumps({"kit_id": "cafe-pausas", "kit_version": 1, "overrides": overrides}),
            },
        )
        await conn.execute(
            text("""INSERT INTO business_brand_kit_logos
              (id,tenant_id,business_id,operation_id,actor_id,request_hash,object_key,sha256,mime_type,
               size_bytes,state,rights_scope) VALUES (:logo,:tenant,:business,:operation,:actor,:hash,
                 'private/logo',:sha,'image/png',:size,'ready','business_brand_confirmed')"""),
            {
                **params,
                "logo": logo_id,
                "operation": uuid4(),
                "hash": "b" * 64,
                "sha": hashlib.sha256(logo).hexdigest(),
                "size": len(logo),
            },
        )
    interpreter = SimpleNamespace(
        interpret=AsyncMock(
            return_value=CatalogIntent("selected", UUID(catalog["offerings"][0]["id"]), "content_request", "photo")
        )
    )
    worker = Database(cfg, correlator=True)
    store = SimpleNamespace(
        get_image=AsyncMock(side_effect=lambda key: {"private/test": raw, "private/logo": logo}[key])
    )
    try:
        activity = ContentCandidateActivities(cfg, database, worker, interpreter=interpreter)
        proposal = UUID(await activity.request_candidate_proposal(str(source)))
        claims = await claim_proposals(worker, uuid4())
        await finish_proposal_dispatch(worker, claims[0], True)
        assert await EditorialProposalService(cfg, worker, owner_database=database).run(proposal) == "completed"
        await VisualConsentService(cfg, database).set(tenant, business, actor, True)
        service = VisualBrandFinishService(cfg, database, store)
        prepared = await service.prepare(tenant, business, actor, proposal, uuid4(), candidate=True)
        assert prepared.logo is not None and prepared.logo.data == logo
        assert "Não acrescente palavras" in prepared.request.request.prompt
        generated = _png((1024, 1280), "blue")
        scene = FetchedMedia(generated, "image/png", hashlib.sha256(generated).hexdigest())
        output = await service.finish(actor, prepared, scene, candidate=True)
        assert output.sha256 == hashlib.sha256(output.data).hexdigest()
        async with admin.begin() as conn:
            await conn.execute(
                text("""UPDATE business_brand_kit_heads SET confirmed_version=NULL
              WHERE tenant_id=:tenant AND business_id=:business"""),
                {"tenant": tenant, "business": business},
            )
        with pytest.raises(AuthError, match="VISUAL_KIT_CHANGED"):
            await service.finish(actor, prepared, scene, candidate=True)
    finally:
        await worker.close()


async def test_real_request_and_brand_finish_fit_orchestrator_without_external_calls(
    admin, database, seeded, settings, monkeypatch
):
    """Integration evidence only: the admission/commit guard and provider are mocks."""
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(
        update={
            "meta_encryption_key": SecretStr(key),
            "visual_ai_mode": "openai",
            "visual_ai_monthly_budget_usd_micros": 100,
            "visual_ai_global_monthly_budget_usd_micros": 100,
        }
    )
    source = await _asset(admin, tenant, business, key, kind="image", body="Crie uma imagem do croissant")
    raw = _png((80, 80), "red")
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
    store = SimpleNamespace(get_image=AsyncMock(return_value=raw), put=AsyncMock(), delete=AsyncMock())
    try:
        activity = ContentCandidateActivities(cfg, database, worker, interpreter=interpreter)
        proposal = UUID(await activity.request_candidate_proposal(str(source)))
        claims = await claim_proposals(worker, uuid4())
        await finish_proposal_dispatch(worker, claims[0], True)
        assert await EditorialProposalService(cfg, worker, owner_database=database).run(proposal) == "completed"
        await VisualConsentService(cfg, database).set(tenant, business, actor, True)
        item = await preview(admin, tenant, business, actor)
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE media_previews SET proposal_id=:proposal WHERE id=:id"), {"proposal": proposal, "id": item}
            )
        snapshot = await VisualContextService(cfg, database).capture(tenant, business, actor, proposal, candidate=True)
        scope = VisualRunScope(tenant, business, actor, item, proposal, uuid4(), 1, True, snapshot.fingerprint)
        generated = _png((1024, 1280), "blue")
        sent = []

        async def fake_openai(request):
            sent.append(request)
            return httpx.Response(
                200,
                json={"data": [{"b64_json": base64.b64encode(generated).decode("ascii")}]},
                headers={"x-request-id": "synthetic-test"},
            )

        transport = httpx.MockTransport(fake_openai)
        client_type = httpx.AsyncClient

        def mock_transport_only(*args, **kwargs):
            assert kwargs.get("transport") is transport, "network access is forbidden in this test"
            return client_type(*args, **kwargs)

        monkeypatch.setattr("app.adapters.visual_ai.httpx.AsyncClient", mock_transport_only)
        provider = OpenAIVisualProvider("synthetic-test-key", transport=transport)

        async def authorize(_scope, prepared, identity):
            return await VisualAttemptService(cfg, worker).reserve(
                tenant,
                business,
                actor,
                item,
                1,
                identity.operation,
                "openai",
                prepared.request.model,
                identity.request_hash,
                70,
            )

        guard = SimpleNamespace(
            admit=AsyncMock(side_effect=[True, False]),
            authorize=AsyncMock(side_effect=authorize),
            current=AsyncMock(return_value=True),
            commit=AsyncMock(return_value=True),
            finish=AsyncMock(),
        )
        service = VisualRealOrchestrator(
            guard=guard,
            brand=VisualBrandFinishService(cfg, database, store),
            provider=provider,
            ledger=VisualCostLedger(cfg, worker),
            claims=VisualSubmissionClaims(worker),
            store=store,
            signing_key=key,
        )
        assert await service.run(scope) == "completed"
        assert await service.run(scope) == "not_started"
        assert len(sent) == 1 and str(sent[0].url) == "https://api.openai.com/v1/images/edits"
        submitted = json.loads(sent[0].content)
        assert "Croissant" in submitted["prompt"] and "Não acrescente palavras" in submitted["prompt"]
        assert len(submitted["images"]) == 1
        encoded_reference = submitted["images"][0]["image_url"].split(",", 1)[1]
        with Image.open(io.BytesIO(base64.b64decode(encoded_reference))) as normalized:
            assert not normalized.getexif()
        stored_key, stored = store.put.await_args.args
        assert stored_key.startswith(f"previews/{tenant}/{business}/{item}/attempt-1/")
        with Image.open(io.BytesIO(stored.data)) as output:
            assert output.format == "JPEG" and output.size == (1024, 1280)
        guard.commit.assert_awaited_once()
        guard.finish.assert_awaited_once_with(scope, completed=True)
        async with admin.connect() as conn:
            assert (
                await conn.scalar(text("SELECT count(*) FROM visual_ai_attempts WHERE tenant_id=:t"), {"t": tenant})
                == 1
            )
            assert (
                await conn.scalar(text("SELECT state FROM visual_cost_reservations WHERE tenant_id=:t"), {"t": tenant})
                == "uncertain"
            )
    finally:
        await worker.close()
