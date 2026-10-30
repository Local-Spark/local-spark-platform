"""Real RLS and atomic trace/reservation boundaries, with no network effects."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.db.session import Database
from app.services.auth import AuthError
from app.services.visual_attempts import VisualAttemptService
from app.services.visual_request_trace import VisualRequestTraceService, encrypt_visual_trace
from app.tests.integration.test_visual_attempts import preview
from app.tests.integration.test_visual_cost_ledger import _business

pytestmark = pytest.mark.integration


async def test_encrypted_visual_trace_is_atomic_owner_scoped_and_bound_to_attempt(admin, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, tenant)
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO business_profiles
              (tenant_id,business_id,category,city,description,phone,brand_color)
              VALUES(:tenant,:business,'Food','Rio','Test','+5511999999999','#6557ed')"""),
            {"tenant": tenant, "business": business},
        )
    item, operation = await preview(admin, tenant, business, actor), uuid4()
    cfg = settings.model_copy(
        update={
            "meta_encryption_key": SecretStr(Fernet.generate_key().decode()),
            "visual_ai_monthly_budget_usd_micros": 200,
        }
    )
    worker, owner = Database(cfg, correlator=True), Database(cfg)
    request = SimpleNamespace(
        prompt="Mensagem fictícia privada da peça",
        model="synthetic",
        quality="medium",
        size="1024x1280",
        output_format="png",
        request_id=uuid4(),
        references=(),
    )
    prepared = SimpleNamespace(
        request=request,
        sources=(),
        skill_id="instagram-feed-v1",
        skill_sha256="d" * 64,
        context=SimpleNamespace(
            proposal_id=uuid4(), briefing_id=uuid4(), context_version=1, script_version=1, brand_kit_version=1
        ),
    )
    ciphertext = encrypt_visual_trace(cfg, prepared)
    service = VisualAttemptService(cfg, worker)
    args = (tenant, business, actor, item, 1, operation, "fake", "synthetic", "a" * 64, 70)
    try:
        first = await service.reserve(*args, trace_ciphertext=ciphertext)
        replay = await service.reserve(*args, trace_ciphertext=ciphertext)
        assert first.created and not replay.created
        async with admin.connect() as connection:
            rows = (
                await connection.execute(
                    text("SELECT ciphertext,request_hash FROM visual_request_traces WHERE preview_id=:id"),
                    {"id": item},
                )
            ).all()
        assert len(rows) == 1 and rows[0].request_hash == "a" * 64
        assert request.prompt not in rows[0].ciphertext
        trace = await VisualRequestTraceService(cfg, owner).read(tenant, business, actor, item)
        assert trace["request"]["prompt"] == request.prompt
        assert trace["request"]["skill_id"] == "instagram-feed-v1"
        assert trace["request"]["skill_sha256"] == "d" * 64
        assert trace["request_hash"] == "a" * 64
        async with owner.transaction(seeded["t2"], seeded["a2"]) as session:
            assert await session.scalar(text("SELECT count(*) FROM visual_request_traces")) == 0
        with pytest.raises(AuthError):
            await VisualRequestTraceService(cfg, owner).read(tenant, business, seeded["a2"], item)
        untraced = await preview(admin, tenant, business, actor)
        another_operation = uuid4()
        await service.reserve(
            tenant, business, actor, untraced, 1, another_operation, "fake", "synthetic", "b" * 64, 70
        )
        async with worker.transaction(tenant, actor) as session:
            with pytest.raises(IntegrityError):
                await session.execute(
                    text("""INSERT INTO visual_request_traces
                      (tenant_id,business_id,preview_id,actor_id,operation_id,request_hash,ciphertext)
                      VALUES(:tenant,:business,:preview,:actor,:operation,:hash,:ciphertext)"""),
                    {
                        "tenant": tenant,
                        "business": business,
                        "preview": untraced,
                        "actor": actor,
                        "operation": another_operation,
                        "hash": "c" * 64,
                        "ciphertext": ciphertext,
                    },
                )
    finally:
        await owner.close()
        await worker.close()
