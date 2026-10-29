"""Changes wait for an admitted simulated visual preview to finish."""

import asyncio
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text

from app.db.session import Database
from app.schemas.brand_kits import BrandKitConfirmRequest, BrandKitDraftRequest, BrandKitLogoUpload
from app.schemas.business_catalog import CatalogUpdate
from app.schemas.business_collection import CollectionPhotoUpdate
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
from app.tests.integration.test_brand_kits import _draft, _logo, _overrides
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


@pytest.mark.parametrize("change", ["kit", "logo", "photo", "photo_update", "catalog"])
async def test_kit_or_photo_change_waits_and_preview_remains_reviewable(change, admin, database, seeded, settings):
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
    overrides = _overrides()
    if change == "logo":
        original_logo = await kits.upload_logo(
            tenant,
            business,
            actor,
            BrandKitLogoUpload(
                operation_id=uuid4(), mime_type="image/png", content_base64=_logo(), rights_confirmed=True
            ),
        )
        overrides["logo_asset_id"] = str(original_logo.id)
    draft = await kits.draft(tenant, business, actor, BrandKitDraftRequest.model_validate(_draft(0, overrides)))
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
            if change in {"kit", "logo"}:
                current = await kits.read(tenant, business, actor)
                changed_overrides = _overrides("Novo nome")
                if change == "logo":
                    new_logo = await asyncio.wait_for(
                        kits.upload_logo(
                            tenant,
                            business,
                            actor,
                            BrandKitLogoUpload(
                                operation_id=uuid4(),
                                mime_type="image/png",
                                content_base64=_logo((200, 30, 40, 220)),
                                rights_confirmed=True,
                            ),
                        ),
                        5,
                    )
                    changed_overrides["logo_asset_id"] = str(new_logo.id)
                    assert current.confirmed.overrides.logo_asset_id == original_logo.id
                    assert await kits.reconcile_pending_logos(tenant, business, actor) == 0
                changed = await asyncio.wait_for(
                    kits.draft(
                        tenant,
                        business,
                        actor,
                        BrandKitDraftRequest.model_validate(_draft(current.head_version, changed_overrides)),
                    ),
                    5,
                )
                assert changed.draft is not None
                confirmation = await asyncio.wait_for(
                    kits.confirm(
                        tenant,
                        business,
                        actor,
                        BrandKitConfirmRequest(operation_id=uuid4(), expected_version=changed.draft.version),
                    ),
                    5,
                )
                assert confirmation.pending_change is True
                waiting = await kits.read(tenant, business, actor)
                assert waiting.pending_change is True
                if change == "logo":
                    assert waiting.confirmed.overrides.logo_asset_id == original_logo.id
            elif change == "photo":
                deleted = await asyncio.wait_for(
                    collection.delete(tenant, business, actor, photo.id, uuid4(), photo.version), 5
                )
                assert deleted.status == "waiting_for_generation"
                assert (await collection.list_photos(tenant, business, actor))[0].pending_change is True
            elif change == "photo_update":
                updated = await collection.update(
                    tenant,
                    business,
                    actor,
                    photo.id,
                    CollectionPhotoUpdate(
                        operation_id=uuid4(),
                        expected_version=photo.version,
                        title="Foto atualizada",
                        item_id=photo.item_id,
                        space_kind=photo.space_kind,
                        sort_order=photo.sort_order,
                        status="active",
                    ),
                )
                assert updated.pending_change is True and updated.title == photo.title
            elif change == "catalog":
                update = deepcopy(catalog)
                update["operation_id"] = str(uuid4())
                update["expected_version"] = 1
                update["offerings"][0]["price_minor"] = 2200
                update["promotions"][0]["price_minor"] = 1900
                pending = await BusinessCatalogService(database).update(
                    tenant, business, actor, CatalogUpdate.model_validate(update)
                )
                assert pending.version == 1 and pending.pending_change is not None
            assert not task.done(), "The change must remain pending while rendering is active"
        finally:
            store.release.set()
        assert await task == "completed"
        assert store.preview_key is not None and store.preview_key in store.objects
        visible = await owner.list(tenant, business, actor)
        assert len(visible) == 1 and visible[0].created_before_change is True
        assert await owner.file_key(tenant, business, actor, preview.id, review=True) == store.preview_key
        async with admin.connect() as conn:
            state = await conn.scalar(text("SELECT state FROM media_previews WHERE id=:id"), {"id": preview.id})
            assert state == "completed"
        if change in {"kit", "logo"}:
            updated = await kits.read(tenant, business, actor)
            assert not updated.pending_change
            assert updated.confirmed is not None and updated.confirmed.overrides.brand_name == "Novo nome"
            if change == "logo":
                assert updated.confirmed.overrides.logo_asset_id == new_logo.id
                assert await kits.logo_url(tenant, business, actor, original_logo.id)
                async with admin.connect() as conn:
                    frozen = await conn.scalar(
                        text("SELECT brand_kit_document FROM editorial_proposals WHERE id=:id"), {"id": proposal}
                    )
                    assert frozen["overrides"]["logo_asset_id"] == str(original_logo.id)
            # The preserved-preview proof must match the actual image and must
            # not bypass a later withdrawal of editorial permission.
            async with admin.begin() as conn:
                await conn.execute(
                    text("UPDATE visual_change_completed_previews SET sha256=:sha WHERE preview_id=:id"),
                    {"id": preview.id, "sha": "0" * 64},
                )
            with pytest.raises(AuthError, match="PREVIEW_NOT_READY"):
                await owner.file_key(tenant, business, actor, preview.id, review=True)
            async with admin.begin() as conn:
                await conn.execute(
                    text("""UPDATE visual_change_completed_previews v SET sha256=p.sha256
                      FROM media_previews p WHERE p.id=v.preview_id AND v.preview_id=:id"""),
                    {"id": preview.id},
                )
                await conn.execute(
                    text(
                        "UPDATE editorial_ai_consents SET revoked_at=now() "
                        "WHERE tenant_id=:tenant AND business_id=:business"
                    ),
                    {"tenant": tenant, "business": business},
                )
            with pytest.raises(AuthError, match="PREVIEW_NOT_READY"):
                await owner.file_key(tenant, business, actor, preview.id, review=True)
        elif change == "photo":
            assert await collection.list_photos(tenant, business, actor) == []
        elif change == "photo_update":
            updated = await collection.list_photos(tenant, business, actor)
            assert len(updated) == 1 and updated[0].title == "Foto atualizada" and not updated[0].pending_change
        elif change == "catalog":
            updated_catalog = await BusinessCatalogService(database).read(tenant, business, actor)
            assert updated_catalog.version == 2 and updated_catalog.offerings[0].price_minor == 2200
    finally:
        await worker.close()
