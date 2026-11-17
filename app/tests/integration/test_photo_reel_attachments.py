"""The no-video material query keeps private photos inside their run and RLS scope."""

from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text

from app.schemas.motion_production import MotionRequest
from app.services.auth import AuthError
from app.services.creation_lab_motion_context import LabMotionContext
from app.services.motion_context import MotionContext

pytestmark = pytest.mark.integration


async def test_photo_reel_without_video_reads_only_its_authorized_run(admin, database, seeded, settings, monkeypatch):
    operator, other = seeded["a1"], seeded["a2"]
    business, run, other_run, photo, other_photo = [uuid4() for _ in range(5)]
    context = LabMotionContext(settings, run)
    # Exercise the real restricted SQL material reader; factual context has separate coverage.
    monkeypatch.setattr(MotionContext, "capture", AsyncMock(side_effect=lambda *args, **kwargs: {"source": None}))
    async with admin.begin() as session:
        for actor in (operator, other):
            await session.execute(text("INSERT INTO platform_staff(actor_id) VALUES(:actor)"), {"actor": actor})
        await session.execute(
            text(
                "INSERT INTO businesses(id,tenant_id,name,timezone) "
                "VALUES(:id,:tenant,'Photo reel','America/Sao_Paulo')"
            ),
            {"id": business, "tenant": seeded["t1"]},
        )
        for run_id, photo_id, actor in ((run, photo, operator), (other_run, other_photo, other)):
            await session.execute(
                text("""INSERT INTO creation_lab_runs
                (id,actor_id,tenant_id,business_id,operation_id,request_hash,format,mode,
                 instruction_ciphertext,budget_usd_micros,flow_version)
                VALUES(:run,:actor,:tenant,:business,:run,:hash,'reel','automatic',:cipher,3000000,2)"""),
                {
                    "run": run_id,
                    "actor": actor,
                    "tenant": seeded["t1"],
                    "business": business,
                    "hash": "a" * 64,
                    "cipher": context.seal({"instruction": "Reel com fotos"}),
                },
            )
            await session.execute(
                text("""INSERT INTO creation_lab_attachments
                (id,run_id,operation_id,request_hash,name_ciphertext,object_key,kind,mime_type,
                 sha256,byte_size,rights_confirmed,state)
                VALUES(:id,:run,:id,:hash,:name,:key,'image','image/png',:hash,100,true,'ready')"""),
                {
                    "id": photo_id,
                    "run": run_id,
                    "hash": "a" * 64,
                    "name": context.seal({"name": "Synthetic photo"}),
                    "key": f"synthetic/{photo_id}.png",
                },
            )
    request = MotionRequest(
        operation_id=run, instruction="Reel com fotos", source_asset_id=None, photo_duration_ms=15000
    )
    async with database.transaction(UUID(int=0), operator) as session:
        snapshot = await context.capture(session, seeded["t1"], business, request)
        assert [p["id"] for p in snapshot["collection_photos"]] == [str(photo)]
    async with database.transaction(UUID(int=0), other) as session:
        with pytest.raises(AuthError, match="MOTION_PHOTOS_REQUIRED"):
            await context.capture(session, seeded["t1"], business, request)
