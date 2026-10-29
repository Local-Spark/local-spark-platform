"""Retain completed preview artifacts and their source document after deadlines."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.db.session import Database
from app.schemas.content_deliveries import ContentDecision
from app.schemas.media_previews import PreviewRequest
from app.services.auth import AuthError
from app.services.content_deliveries import ContentDeliveryService, claim_publications
from app.services.editorial_proposals import EditorialProposalService, reconcile_stale_proposals
from app.services.media_previews import MediaPreviewService
from app.services.media_retention import claim_expired_previews, purge_expired_previews
from app.tests.integration.test_content_delivery import _candidate_case
from app.tests.integration.test_media_previews import _accepted_case, _attach_source

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("mode", ["local", "visual_fake"])
@pytest.mark.parametrize("source_revoked", [False, True])
async def test_completed_preview_preserves_artifact_and_provenance(admin, seeded, settings, mode, source_revoked):
    tenant, business, actor, _, proposal, document = await _accepted_case(admin, seeded)
    asset = await _attach_source(admin, tenant, business, proposal, document, b"source")
    owner, worker = Database(settings), Database(settings, correlator=True)
    store = AsyncMock()
    try:
        preview = await MediaPreviewService(settings, owner).request(
            tenant, business, actor, PreviewRequest(operation_id=uuid4(), proposal_id=proposal)
        )
        key = f"previews/{tenant}/{business}/{preview.id}/attempt-1/artifact.jpg"
        async with admin.begin() as connection:
            await connection.execute(
                text("""UPDATE media_previews SET state='completed',object_key=:key,sha256=:sha,
                  generation_mode=:mode,
                  visual_fingerprint=CASE WHEN :mode='visual_fake' THEN CAST(:sha AS char(64)) ELSE NULL END,
                  expires_at=now()-interval '2 days' WHERE id=:id"""),
                {"key": key, "sha": "b" * 64, "mode": mode, "id": preview.id},
            )
            await connection.execute(
                text("UPDATE editorial_proposals SET expires_at=now()-interval '1 day' WHERE id=:id"),
                {"id": proposal},
            )
            if source_revoked:
                await connection.execute(
                    text("UPDATE whatsapp_material_assets SET delete_requested_at=now() WHERE id=:id"),
                    {"id": asset},
                )
        assert await reconcile_stale_proposals(worker) == 0
        assert await purge_expired_previews(worker, store, uuid4()) == 0
        store.delete.assert_not_awaited()
        proposals = await EditorialProposalService(settings, owner).list(tenant, business, actor)
        assert [item.id for item in proposals] == [proposal]
        assert proposals[0].document is not None
        assert proposals[0].document.model_dump(mode="json") == document
        assert proposals[0].source_asset_id == asset
        versions = await EditorialProposalService(settings, owner).script_versions(tenant, business, actor, proposal)
        assert len(versions) == 1 and versions[0].source_asset_id == asset
        async with owner.transaction(tenant, actor) as session:
            retained = (
                (
                    await session.execute(
                        text("SELECT object_key,sha256,expires_at<now() AS expired FROM media_previews WHERE id=:id"),
                        {"id": preview.id},
                    )
                )
                .mappings()
                .one()
            )
            assert retained["object_key"] == key and retained["sha256"] == "b" * 64 and retained["expired"]
        async with owner.transaction(seeded["t2"], seeded["a2"]) as session:
            assert await session.scalar(text("SELECT count(*) FROM media_previews")) == 0
    finally:
        await worker.close()
        await owner.close()


async def test_unresolved_visual_admission_is_not_purged_when_lease_expires(admin, seeded, settings):
    tenant, business, actor, _, proposal, _ = await _accepted_case(admin, seeded)
    owner, worker = Database(settings), Database(settings, correlator=True)
    try:
        preview = await MediaPreviewService(settings, owner).request(
            tenant, business, actor, PreviewRequest(operation_id=uuid4(), proposal_id=proposal)
        )
        async with admin.begin() as connection:
            await connection.execute(
                text("""UPDATE media_previews SET state='rendering',expires_at=now()-interval '2 days',
                  generation_mode='visual_fake',visual_fingerprint=:sha,attempts=1,
                  dispatch_lease_until=now()-interval '1 second' WHERE id=:id"""),
                {"id": preview.id, "sha": "d" * 64},
            )
        assert await claim_expired_previews(worker, uuid4()) == []
    finally:
        await worker.close()
        await owner.close()


@pytest.mark.parametrize("mode", ["local", "visual_fake"])
async def test_legacy_purge_claim_with_known_artifact_requires_reconciliation(admin, seeded, settings, mode):
    tenant, business, actor, _, proposal, _ = await _accepted_case(admin, seeded)
    owner, worker = Database(settings), Database(settings, correlator=True)
    store = AsyncMock()
    try:
        preview = await MediaPreviewService(settings, owner).request(
            tenant, business, actor, PreviewRequest(operation_id=uuid4(), proposal_id=proposal)
        )
        key = f"previews/{tenant}/{business}/{preview.id}/attempt-1/artifact.jpg"
        async with admin.begin() as connection:
            await connection.execute(
                text("""UPDATE media_previews SET state='purging',object_key=:key,sha256=:sha,
                  generation_mode=:mode,
                  visual_fingerprint=CASE WHEN :mode='visual_fake' THEN CAST(:sha AS char(64)) ELSE NULL END,
                  dispatch_owner=:owner,dispatch_lease_until=now()-interval '1 minute',
                  expires_at=now()-interval '2 days' WHERE id=:id"""),
                {"key": key, "sha": "e" * 64, "mode": mode, "owner": uuid4(), "id": preview.id},
            )
        assert await claim_expired_previews(worker, uuid4()) == []
        assert await purge_expired_previews(worker, store, uuid4()) == 0
        store.delete.assert_not_awaited()
        async with owner.transaction(tenant, actor) as session:
            retained = (
                (await session.execute(text("SELECT * FROM media_previews WHERE id=:id"), {"id": preview.id}))
                .mappings()
                .one()
            )
            assert retained["state"] == "purging"
            assert retained["object_key"] == key and retained["sha256"] == "e" * 64
    finally:
        await worker.close()
        await owner.close()


@pytest.mark.parametrize("deadline_elapsed", [False, True])
async def test_retained_candidate_review_does_not_extend_creation_or_publication_access(
    admin, seeded, settings, deadline_elapsed
):
    cfg, owner, worker, tenant, business, actor, proposal, event, preview = await _candidate_case(
        admin, seeded, settings
    )
    try:
        deliveries = ContentDeliveryService(cfg, owner, worker)
        delivery = await deliveries.record(event, preview)
        assert delivery is not None
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE billing_sponsorships SET revoked_at=now() WHERE tenant_id=:tenant"),
                {"tenant": tenant},
            )
            if deadline_elapsed:
                await connection.execute(
                    text("UPDATE editorial_proposals SET expires_at=now()-interval '1 day' WHERE id=:id"),
                    {"id": proposal},
                )
                await connection.execute(
                    text("UPDATE media_previews SET expires_at=now()-interval '1 day' WHERE id=:id"),
                    {"id": preview},
                )
                await connection.execute(
                    text("UPDATE content_deliveries SET expires_at=now()-interval '1 day' WHERE id=:id"),
                    {"id": delivery},
                )
        previews = MediaPreviewService(cfg, owner)
        assert [item.id for item in await previews.list(tenant, business, actor)] == [preview]
        assert await previews.file_key(tenant, business, actor, preview, review=True)
        assert (await deliveries.list(tenant, business, actor))[0].id == delivery
        with pytest.raises(AuthError, match="PREVIEW_SCRIPT_EXPIRED" if deadline_elapsed else "PLAN_REQUIRED"):
            await previews.request_candidate(
                tenant, business, actor, PreviewRequest(operation_id=uuid4(), proposal_id=proposal)
            )
        with pytest.raises(AuthError, match="CANDIDATE_EXPIRED" if deadline_elapsed else "PLAN_REQUIRED"):
            await deliveries.decide(
                tenant, business, actor, delivery, ContentDecision(operation_id=uuid4(), decision="approve")
            )
        assert await claim_publications(worker, uuid4()) == []
        async with admin.begin() as connection:
            await connection.execute(
                text("UPDATE memberships SET active=false WHERE tenant_id=:tenant AND actor_id=:actor"),
                {"tenant": tenant, "actor": actor},
            )
        with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
            await previews.file_key(tenant, business, actor, preview, review=True)
    finally:
        await worker.close()
        await owner.close()


@pytest.mark.parametrize("change", ["script_version", "script_rejected"])
async def test_historical_preview_cannot_create_delivery_for_changed_script(admin, seeded, settings, change):
    cfg, owner, worker, tenant, business, actor, proposal, event, preview = await _candidate_case(
        admin, seeded, settings
    )
    try:
        async with admin.begin() as connection:
            if change == "script_version":
                await connection.execute(
                    text("""UPDATE editorial_proposals SET script_version=script_version+1,
                  document=jsonb_set(document,'{script,0,on_screen_text}',to_jsonb(CAST(:caption AS text)))
                  WHERE id=:id"""),
                    {"caption": "Uma nova legenda que não pertence à arte anterior", "id": proposal},
                )
            else:
                await connection.execute(
                    text("UPDATE editorial_proposals SET review_state='changes_requested' WHERE id=:id"),
                    {"id": proposal},
                )
        assert await MediaPreviewService(cfg, owner).file_key(tenant, business, actor, preview, review=True)
        deliveries = ContentDeliveryService(cfg, owner, worker)
        assert await deliveries.record(event, preview) is None
        assert await deliveries.list(tenant, business, actor) == []
        assert await claim_publications(worker, uuid4()) == []
    finally:
        await worker.close()
        await owner.close()
