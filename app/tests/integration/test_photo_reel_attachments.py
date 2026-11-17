"""The no-video material query keeps private photos inside their run and RLS scope."""

from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text

from app.schemas.motion_production import MotionRequest
from app.services.auth import AuthError
from app.services.creation_lab_motion_context import LabMotionContext
from app.services.motion_context import MotionContext

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def synthetic_encryption(settings, monkeypatch):
    monkeypatch.setattr(settings, "meta_encryption_key", SecretStr(Fernet.generate_key().decode()))


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


@pytest.mark.parametrize("origin", ["lab", "whatsapp"])
async def test_shared_photo_snapshot_uses_material_evidence_and_origin_approval(
    admin, database, seeded, settings, monkeypatch, origin
):
    from app.schemas.creation_lab import LabStart
    from app.services.creation_lab_motion_requests import LabMotionRequests
    from app.services.motion_context import capture_motion_guidance

    actor, tenant = seeded["a1"], seeded["t1"]
    business, run, photo = uuid4(), uuid4(), uuid4()
    requests = LabMotionRequests(settings, database, run, administrative=origin == "lab")

    async def factual_capture(self, session, tenant, business, request, **kwargs):
        return {"source": None, **capture_motion_guidance(request)}

    # Real shared request assembler + restricted attachment SQL; no provider or storage IO.
    monkeypatch.setattr(MotionContext, "capture", factual_capture)
    encrypted = requests.context.seal({"instruction": "Reel de 15 segundos com estas fotos"})
    async with admin.begin() as session:
        if origin == "lab":
            await session.execute(text("INSERT INTO platform_staff(actor_id) VALUES(:actor)"), {"actor": actor})
        await session.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,'Photo','America/Sao_Paulo')"),
            {"id": business, "tenant": tenant},
        )
        await session.execute(
            text("""INSERT INTO creation_lab_runs
            (id,actor_id,tenant_id,business_id,operation_id,request_hash,format,mode,
             instruction_ciphertext,budget_usd_micros,flow_version,origin)
            VALUES(:run,:actor,:tenant,:business,:run,:hash,'reel','automatic',:cipher,3000000,2,:origin)"""),
            {
                "run": run,
                "actor": actor,
                "tenant": tenant,
                "business": business,
                "hash": "b" * 64,
                "cipher": encrypted,
                "origin": origin,
            },
        )
        await session.execute(
            text("""INSERT INTO creation_lab_attachments
            (id,run_id,operation_id,request_hash,name_ciphertext,object_key,kind,mime_type,
             sha256,byte_size,rights_confirmed,state)
            VALUES(:id,:run,:id,:hash,:name,:key,'image','image/png',:hash,100,true,'ready')"""),
            {
                "id": photo,
                "run": run,
                "hash": "b" * 64,
                "name": requests.context.seal({"name": "Synthetic photo"}),
                "key": f"synthetic/{photo}.png",
            },
        )
    async with database.transaction(tenant, actor) as session:
        await session.execute(text("SELECT set_config('app.creation_lab_run_id',:run,true)"), {"run": str(run)})
        snapshot = await requests.build_snapshot(
            session,
            {
                "id": run,
                "origin": origin,
                "flow_version": 2,
                "tenant_id": tenant,
                "business_id": business,
                "instruction_ciphertext": encrypted,
            },
            LabStart(operation_id=run),
        )
    body = MotionRequest.model_validate(snapshot["request"])
    assert not body.review_checkpoints
    assert not body.storyboard
    assert body.automatic_plan
    assert body.preparation.evidence[0].asset_id == f"assets/photo-{photo}.png"
    assert snapshot["photo_intent_contract"]["version"] == "motion-photo-intent-v2"
    assert snapshot["skill"]["id"] == "instagram-reel-photo-v14"
    assert snapshot["repertoire"]["id"] == "business-reel-v6"
    assert "makePhotoReelMotion" in snapshot["repertoire"]["examples"][-1]["content"]
    assert snapshot["staging_contract"]["version"] == "motion-staging-photo-v2"
    assert snapshot["photo_motion"]["music_policy"] == "elevenlabs-music-v1"
    assert snapshot["sound_library"]["id"] == "public-cc0-v1"
    assert {item["id"] for item in snapshot["sound_library"]["items"]} == {"coffee-pour", "cup-contact"}
    async with database.transaction(tenant, actor) as session:
        assert (
            await session.scalar(text("SELECT count(*) FROM outbox_events WHERE event_type='motion.plan_approved'"))
            == 0
        )
