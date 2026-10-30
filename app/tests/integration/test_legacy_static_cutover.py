"""Retired static generation stops; completed previews and other formats survive."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.db.session import Database
from app.schemas.media_previews import PreviewRequest
from app.services.auth import AuthError
from app.services.media_dispatch import claim_previews
from app.services.media_previews import MediaPreviewService
from app.tests.integration.test_media_previews import _accepted_case

pytestmark = pytest.mark.integration


async def test_legacy_static_requests_and_claims_are_stopped_without_deleting_history(admin, seeded, settings):
    tenant, business, actor, _, proposal, _ = await _accepted_case(admin, seeded)
    owner, worker = Database(settings), Database(settings, correlator=True)
    pending_image, completed_image, pending_video = uuid4(), uuid4(), uuid4()
    try:
        with pytest.raises(AuthError, match="PREVIEW_LEGACY_CREATION_DISABLED"):
            await MediaPreviewService(settings, owner).request(
                tenant,
                business,
                actor,
                PreviewRequest(operation_id=uuid4(), proposal_id=proposal, generation_mode="local"),
            )
        async with admin.begin() as connection:
            for item, state, mime in (
                (pending_image, "pending", "image/jpeg"),
                (completed_image, "completed", "image/jpeg"),
                (pending_video, "pending", "video/mp4"),
            ):
                await connection.execute(
                    text("""INSERT INTO media_previews
                      (id,tenant_id,business_id,proposal_id,actor_id,operation_id,request_hash,render_key,
                       context_version,script_version,fact_ids,state,object_key,sha256,expires_at,mime_type)
                      VALUES(:id,:tenant,:business,:proposal,:actor,:operation,:hash,:render,
                        1,1,'[]'::jsonb,:state,:key,:sha,now()+interval '1 day',:mime)"""),
                    {
                        "id": item,
                        "tenant": tenant,
                        "business": business,
                        "proposal": proposal,
                        "actor": actor,
                        "operation": uuid4(),
                        "hash": "a" * 64,
                        "render": item.hex * 2,
                        "state": state,
                        "key": "private/existing.jpg" if state == "completed" else None,
                        "sha": "c" * 64 if state == "completed" else None,
                        "mime": mime,
                    },
                )
        claims = await claim_previews(worker, uuid4())
        assert [claim.id for claim in claims] == [pending_video]
        visible = await MediaPreviewService(settings, owner).list(tenant, business, actor)
        assert next(item for item in visible if item.id == completed_image).sha256 == "c" * 64

        # A worker that had already received an old local image must not render
        # it either, even though this job predates the dispatch filter.
        async with admin.begin() as connection:
            await connection.execute(
                text("""UPDATE media_previews SET state='rendering',dispatch_fence=1,
                  dispatch_lease_until=now()+interval '3 minutes' WHERE id=:id"""),
                {"id": pending_image},
            )
        store = AsyncMock()
        assert await MediaPreviewService(settings, worker, store, owner).render(pending_image, 1) == "failed"
        store.put.assert_not_awaited()
        async with admin.connect() as connection:
            row = (
                (
                    await connection.execute(
                        text("SELECT state,error_code FROM media_previews WHERE id=:id"), {"id": pending_image}
                    )
                )
                .mappings()
                .one()
            )
        assert row["state"] == "failed" and row["error_code"] == "PREVIEW_LEGACY_CREATION_DISABLED"
    finally:
        await worker.close()
        await owner.close()
