"""A confirmed change invalidates an in-flight simulated visual preview."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text

from app.db.session import Database
from app.schemas.brand_kits import BrandKitConfirmRequest, BrandKitDraftRequest
from app.schemas.business_catalog import CatalogUpdate
from app.schemas.media_previews import PreviewRequest
from app.services.auth import AuthError
from app.services.brand_kits import BrandKitService
from app.services.business_catalog import BusinessCatalogService
from app.services.business_collection import BusinessCollectionService
from app.services.creative_catalog_resolution import CatalogIntent
from app.services.editorial_dispatch import claim_proposals, finish_proposal_dispatch
from app.services.editorial_proposals import EditorialProposalService
from app.services.media_dispatch import claim_previews
from app.services.media_previews import MediaPreviewService
from app.services.visual_consent import VisualConsentService
from app.tests.integration.test_brand_kits import _draft, _overrides
from app.tests.integration.test_business_catalog import _payload
from app.tests.integration.test_business_collection import Store
from app.tests.integration.test_editorial_briefings import _enable
from app.tests.integration.test_editorial_proposals import _asset, _business
from app.tests.unit.test_business_collection_contract import upload
from app.workflows.content_activities import ContentCandidateActivities

pytestmark = pytest.mark.integration


class PausingStore(Store):
    def __init__(self):
        super().__init__()
        self.entered = asyncio.Event()
        self.release = asyncio.Event()
        self.preview_key = None

    async def put(self, key, media):
        await super().put(key, media)
        if key.startswith("previews/"):
            self.preview_key = key
            self.entered.set()
            await self.release.wait()


@pytest.mark.parametrize("change", ["kit", "photo"])
async def test_kit_or_photo_change_during_processing_discards_preview(change, admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(
        update={
            "meta_encryption_key": SecretStr(key),
            "visual_ai_mode": "fake",
            "visual_ai_monthly_budget_usd_micros": 100,
        }
    )
    source = await _asset(admin, tenant, business, key, body="Crie uma imagem do croissant")
    catalog = _payload()
    await BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
    store = PausingStore()
    collection = BusinessCollectionService(cfg, database, store)
    photo = await collection.upload(
        tenant,
        business,
        actor,
        upload(item_id=catalog["offerings"][0]["id"], space_kind=None),
    )
    kits = BrandKitService(cfg, database, store)
    draft = await kits.draft(tenant, business, actor, BrandKitDraftRequest.model_validate(_draft(0)))
    assert draft.draft is not None
    await kits.confirm(
        tenant,
        business,
        actor,
        BrandKitConfirmRequest(operation_id=uuid4(), expected_version=draft.draft.version),
    )
    interpreter = SimpleNamespace(
        interpret=AsyncMock(
            return_value=CatalogIntent("selected", UUID(catalog["offerings"][0]["id"]), "content_request", "photo")
        )
    )
    worker = Database(cfg, correlator=True)
    try:
        activity = ContentCandidateActivities(cfg, database, worker, interpreter=interpreter)
        proposal = UUID(await activity.request_candidate_proposal(str(source)))
        claim = (await claim_proposals(worker, uuid4()))[0]
        await finish_proposal_dispatch(worker, claim, True)
        assert await EditorialProposalService(cfg, worker, owner_database=database).run(proposal) == "completed"
        await VisualConsentService(cfg, database).set(tenant, business, actor, True)
        owner = MediaPreviewService(cfg, database, store)
        preview = await owner.request_candidate(
            tenant,
            business,
            actor,
            PreviewRequest(operation_id=uuid4(), proposal_id=proposal, generation_mode="visual_fake"),
        )
        claim = (await claim_previews(worker, uuid4()))[0]
        renderer = MediaPreviewService(cfg, worker, store, database)
        task = asyncio.create_task(renderer.render(preview.id, claim.fence))
        try:
            await asyncio.wait_for(store.entered.wait(), 20)
            if change == "kit":
                current = await kits.read(tenant, business, actor)
                changed = await asyncio.wait_for(
                    kits.draft(
                        tenant,
                        business,
                        actor,
                        BrandKitDraftRequest.model_validate(_draft(current.head_version, _overrides("Novo nome"))),
                    ),
                    5,
                )
                assert changed.draft is not None
                await asyncio.wait_for(
                    kits.confirm(
                        tenant,
                        business,
                        actor,
                        BrandKitConfirmRequest(operation_id=uuid4(), expected_version=changed.draft.version),
                    ),
                    5,
                )
            else:
                deleted = await asyncio.wait_for(
                    collection.delete(tenant, business, actor, photo.id, uuid4(), photo.version), 5
                )
                assert deleted.status == "deleted"
            assert not task.done(), "The edit must not wait for rendering to finish"
        finally:
            store.release.set()
        assert await task == "failed"
        assert store.preview_key is not None and store.preview_key not in store.objects
        assert await owner.list(tenant, business, actor) == []
        with pytest.raises(AuthError, match="PREVIEW_NOT_READY"):
            await owner.file_key(tenant, business, actor, preview.id)
        async with admin.connect() as conn:
            state = await conn.scalar(text("SELECT state FROM media_previews WHERE id=:id"), {"id": preview.id})
            assert state == "failed"
    finally:
        await worker.close()
