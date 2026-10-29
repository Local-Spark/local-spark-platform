"""Immutable logo uploads enter visual sources through a serialized kit change."""

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.schemas.brand_kits import BrandKitConfirmRequest, BrandKitDraftRequest, BrandKitLogoUpload
from app.services.auth import AuthError
from app.services.brand_kits import BrandKitService
from app.services.visual_admission import VisualAdmissionChecks
from app.services.visual_consent_gate import VisualConsentGate
from app.tests.integration.test_brand_kits import _draft, _logo, _overrides
from app.tests.integration.test_business_collection import Store
from app.tests.integration.test_visual_admission import _ready
from app.tests.integration.test_visual_attempts import preview as create_preview

pytestmark = pytest.mark.integration


async def test_logo_selection_waits_for_concurrent_admission_and_retains_previous_sources(
    admin, database, seeded, settings, monkeypatch
):
    tenant, business, actor, _, admission = await _ready(admin, database, seeded, settings)
    gate = VisualConsentGate(database)
    store = Store()
    kits = BrandKitService(admission.settings, database, store)
    active_preview, queued_preview = (
        await create_preview(admin, tenant, business, actor),
        await create_preview(admin, tenant, business, actor),
    )
    entered, release = asyncio.Event(), asyncio.Event()
    original = VisualAdmissionChecks.validate

    async def pause(self, *args):
        await original(self, *args)
        entered.set()
        await release.wait()

    monkeypatch.setattr(VisualAdmissionChecks, "validate", pause)
    operation = uuid4()
    admitted = asyncio.create_task(
        gate.admit(tenant, business, actor, active_preview, operation, 1, admission=admission)
    )
    drafting = None
    try:
        await asyncio.wait_for(entered.wait(), 5)
        # An immutable new object can upload while admission holds the source
        # gate. Merely uploading it must not replace the confirmed source.
        logo = await asyncio.wait_for(
            kits.upload_logo(
                tenant,
                business,
                actor,
                BrandKitLogoUpload(
                    operation_id=uuid4(), mime_type="image/png", content_base64=_logo(), rights_confirmed=True
                ),
            ),
            5,
        )
        overrides = _overrides()
        overrides["logo_asset_id"] = str(logo.id)
        drafting = asyncio.create_task(
            kits.draft(tenant, business, actor, BrandKitDraftRequest.model_validate(_draft(1, overrides)))
        )
        before = await kits.read(tenant, business, actor)
        assert before.head_version == 1 and before.confirmed.overrides.logo_asset_id is None
        assert not drafting.done()
    finally:
        release.set()
    assert await asyncio.wait_for(admitted, 5)
    assert drafting is not None
    draft = await asyncio.wait_for(drafting, 5)
    assert draft.head_version == 2 and draft.confirmed.version == 1
    command = BrandKitConfirmRequest(operation_id=uuid4(), expected_version=2)
    requested = await kits.confirm(tenant, business, actor, command)
    assert requested.pending_change and requested.confirmed.overrides.logo_asset_id is None
    assert (await kits.confirm(tenant, business, actor, command)).pending_change
    with pytest.raises(AuthError, match="VISUAL_CHANGE_PENDING"):
        await gate.admit(tenant, business, actor, uuid4(), uuid4(), 1)
    with pytest.raises(AuthError, match="VISUAL_CHANGE_ALREADY_PENDING"):
        await kits.draft(tenant, business, actor, BrandKitDraftRequest.model_validate(_draft(2)))

    # A ready logo is private durable source data, never an orphan candidate,
    # even when its upload lease and original upload date are old.
    async with admin.begin() as connection:
        await connection.execute(
            text("""UPDATE business_brand_kit_logos SET created_at=now()-interval '2 days',
              upload_lease_until=now()-interval '1 day' WHERE id=:id"""),
            {"id": logo.id},
        )
    assert await kits.reconcile_pending_logos(tenant, business, actor) == 0
    assert await kits.logo_url(tenant, business, actor, logo.id)
    await gate.finish(tenant, business, actor, operation, 1)
    applied = await kits.read(tenant, business, actor)
    assert applied.head_version == 3 and not applied.pending_change
    assert applied.confirmed.overrides.logo_asset_id == logo.id
    assert len(store.objects) == 1
    with pytest.raises(AuthError, match="VISUAL_CHANGE_QUEUE_CANCELLED"):
        await gate.admit(tenant, business, actor, queued_preview, uuid4(), 1)
    async with database.transaction(tenant, actor) as session:
        assert await session.scalar(text("SELECT count(*) FROM audit_events WHERE action='visual.change_applied'")) == 1
    async with database.transaction(seeded["t2"], seeded["a2"]) as session:
        assert await session.scalar(text("SELECT count(*) FROM business_visual_pending_changes")) == 0
        assert await session.scalar(text("SELECT count(*) FROM business_brand_kit_logos")) == 0
