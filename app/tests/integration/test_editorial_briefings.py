"""Durable owner-scoped context used by the experimental inbound flow."""

from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from sqlalchemy import text

from app.db.session import Database
from app.schemas.business_catalog import CatalogUpdate
from app.services.auth import AuthError
from app.services.business_catalog import BusinessCatalogService
from app.services.creative_catalog_resolution import CatalogIntent
from app.services.editorial_dispatch import claim_proposals, finish_proposal_dispatch
from app.services.editorial_proposals import EditorialProposalService
from app.services.media_previews import MediaPreviewService
from app.tests.integration.test_business_catalog import _payload
from app.tests.integration.test_editorial_proposals import _asset, _business
from app.workflows.content_activities import ContentCandidateActivities

pytestmark = pytest.mark.integration


async def _enable(admin, tenant, business, actor):
    async with admin.begin() as conn:
        await conn.execute(
            text("""INSERT INTO whatsapp_processing_consents(tenant_id,business_id,actor_id,accepted_at)
          VALUES(:tenant,:business,:actor,now()-interval '1 minute')"""),
            {"tenant": tenant, "business": business, "actor": actor},
        )
        await conn.execute(
            text("""INSERT INTO whatsapp_channel_links
          (tenant_id,business_id,actor_id,sender_hash,proof_event_id,linked_at)
          VALUES(:tenant,:business,:actor,:sender,:proof,now()-interval '1 minute')"""),
            {"tenant": tenant, "business": business, "actor": actor, "sender": "b" * 64, "proof": uuid4()},
        )
        await conn.execute(
            text("""INSERT INTO editorial_ai_consents(tenant_id,business_id,actor_id)
          VALUES(:tenant,:business,:actor)"""),
            {"tenant": tenant, "business": business, "actor": actor},
        )


async def test_inbound_catalog_briefing_is_durable_scoped_and_revalidated(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr(key)})
    source = await _asset(admin, tenant, business, key, body="Crie uma imagem do croissant")
    catalog = _payload()
    await BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
    item = UUID(catalog["offerings"][0]["id"])
    interpreter = SimpleNamespace(interpret=AsyncMock(return_value=CatalogIntent("selected", item)))
    worker = Database(cfg, correlator=True)
    try:
        activity = ContentCandidateActivities(cfg, database, worker, interpreter=interpreter)
        first = await activity.request_candidate_proposal(str(source))
        proposal_id = UUID(first)
        assert await activity.request_candidate_proposal(str(source)) == first
        assert interpreter.interpret.await_count == 1
        owner = EditorialProposalService(cfg, database)
        summary = (await owner.list(tenant, business, actor))[0].briefing
        assert summary is not None and summary.status == "prepared" and summary.offering.name == "Croissant"
        assert "Assado" not in str(summary)
        async with database.transaction(seeded["t2"], seeded["a2"]) as session:
            assert await session.scalar(text("SELECT count(*) FROM editorial_briefings")) == 0
        with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
            await owner.list(tenant, business, seeded["viewer"])
        async with worker.sessions() as session, session.begin():
            row = (
                (await session.execute(text("SELECT * FROM editorial_proposals WHERE id=:id"), {"id": proposal_id}))
                .mappings()
                .one()
            )
            data, _ = await EditorialProposalService(cfg, worker, owner_database=database)._inputs(session, row)
            assert data["catalog_context"]["name"] == "Croissant"
            assert "description" not in data["catalog_context"]
            with pytest.raises(AuthError, match="BRIEFING_PREVIEW_NOT_READY"):
                await MediaPreviewService(cfg, worker)._inputs(session, row)
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE whatsapp_material_assets SET ciphertext=:body WHERE id=:id"),
                {"id": source, "body": Fernet(key.encode()).encrypt(b"Outro pedido").decode()},
            )
        assert (await owner.list(tenant, business, actor))[0].briefing.status == "context_changed"
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE whatsapp_material_assets SET ciphertext=:body WHERE id=:id"),
                {"id": source, "body": Fernet(key.encode()).encrypt(b"Crie uma imagem do croissant").decode()},
            )
        assert (await owner.list(tenant, business, actor))[0].briefing.status == "prepared"
        claims = await claim_proposals(worker, uuid4())
        await finish_proposal_dispatch(worker, claims[0], True)
        # An acervo item is context, not a fabricated business_context fact.
        assert await EditorialProposalService(cfg, worker, owner_database=database).run(proposal_id) == "rejected"
        async with admin.connect() as conn:
            assert (
                await conn.scalar(text("SELECT error_code FROM editorial_proposals WHERE id=:id"), {"id": proposal_id})
                == "EDITORIAL_FACTS_REQUIRED"
            )
        async with admin.begin() as conn:
            await conn.execute(text("UPDATE business_offerings SET name='Alterado' WHERE id=:id"), {"id": item})
        assert (await owner.list(tenant, business, actor))[0].briefing.status == "context_changed"
        async with admin.begin() as conn:
            await conn.execute(text("DELETE FROM editorial_briefings WHERE tenant_id=:tenant"), {"tenant": tenant})
        async with worker.sessions() as session, session.begin():
            row = (
                (await session.execute(text("SELECT * FROM editorial_proposals WHERE id=:id"), {"id": proposal_id}))
                .mappings()
                .one()
            )
            assert row["briefing_id"] is None and row["briefing_required"]
            assert await EditorialProposalService(cfg, worker, owner_database=database)._inputs(session, row) is None
    finally:
        await worker.close()


async def test_negation_never_selects_even_with_fake_interpreter(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr(key)})
    source = await _asset(admin, tenant, business, key, body="Não quero croissant")
    catalog = _payload()
    await BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
    interpreter = SimpleNamespace(
        interpret=AsyncMock(return_value=CatalogIntent("selected", UUID(catalog["offerings"][0]["id"])))
    )
    worker = Database(cfg, correlator=True)
    try:
        activity = ContentCandidateActivities(cfg, database, worker, interpreter=interpreter)
        assert await activity.request_candidate_proposal(str(source)) == "briefing_needs_clarification"
        interpreter.interpret.assert_not_awaited()
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT count(*) FROM editorial_proposals")) == 0
    finally:
        await worker.close()


@pytest.mark.parametrize("change", ["text", "consent"])
async def test_change_during_interpretation_invalidates_snapshot(admin, database, seeded, settings, change):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr(key)})
    source = await _asset(admin, tenant, business, key, body="Crie uma imagem do croissant")
    catalog = _payload()
    await BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
    item = UUID(catalog["offerings"][0]["id"])

    async def mutate(*args):
        async with admin.begin() as conn:
            if change == "text":
                await conn.execute(
                    text("UPDATE whatsapp_material_assets SET ciphertext=:body WHERE id=:id"),
                    {"id": source, "body": Fernet(key.encode()).encrypt(b"Outro pedido").decode()},
                )
            else:
                await conn.execute(
                    text(
                        "UPDATE whatsapp_processing_consents SET revoked_at=now() "
                        "WHERE tenant_id=:tenant AND business_id=:business"
                    ),
                    {"tenant": tenant, "business": business},
                )
        return CatalogIntent("selected", item)

    interpreter = SimpleNamespace(interpret=AsyncMock(side_effect=mutate))
    worker = Database(cfg, correlator=True)
    try:
        activity = ContentCandidateActivities(cfg, database, worker, interpreter=interpreter)
        result = await activity.request_candidate_proposal(str(source))
        assert result == ("briefing_needs_clarification" if change == "text" else "briefing_unavailable")
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT count(*) FROM editorial_proposals")) == 0
            assert await conn.scalar(text("SELECT catalog_snapshot FROM editorial_briefings")) is None
    finally:
        await worker.close()


async def test_concurrent_replay_never_runs_interpreter_twice(admin, database, seeded, settings):
    import asyncio

    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr(key)})
    source = await _asset(admin, tenant, business, key, body="Crie uma imagem do croissant")
    catalog = _payload()
    await BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
    entered, release = asyncio.Event(), asyncio.Event()

    async def wait(*args):
        entered.set()
        await release.wait()
        return CatalogIntent("selected", UUID(catalog["offerings"][0]["id"]))

    interpreter = SimpleNamespace(interpret=AsyncMock(side_effect=wait))
    worker = Database(cfg, correlator=True)
    try:
        activity = ContentCandidateActivities(cfg, database, worker, interpreter=interpreter)
        task = asyncio.create_task(activity.request_candidate_proposal(str(source)))
        await asyncio.wait_for(entered.wait(), timeout=5)
        assert await activity.request_candidate_proposal(str(source)) == "briefing_unavailable"
        release.set()
        UUID(await asyncio.wait_for(task, timeout=5))
        assert interpreter.interpret.await_count == 1
    finally:
        await worker.close()


async def test_audio_requires_transcript_and_preexisting_consent(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr(key)})
    catalog = _payload()
    await BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
    interpreter = SimpleNamespace(
        interpret=AsyncMock(return_value=CatalogIntent("selected", UUID(catalog["offerings"][0]["id"])))
    )
    worker = Database(cfg, correlator=True)
    try:
        activity = ContentCandidateActivities(cfg, database, worker, interpreter=interpreter)
        audio = await _asset(admin, tenant, business, key, kind="audio", body="Crie uma imagem do croissant")
        assert await activity.request_candidate_proposal(str(audio)) == "briefing_needs_clarification"
        interpreter.interpret.assert_not_awaited()
        transcribed = await _asset(admin, tenant, business, key, kind="audio", body="unused")
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE whatsapp_material_assets SET transcript_ciphertext=:transcript WHERE id=:id"),
                {
                    "id": transcribed,
                    "transcript": Fernet(key.encode()).encrypt(b"Crie uma imagem do croissant").decode(),
                },
            )
        UUID(await activity.request_candidate_proposal(str(transcribed)))
        stale = await _asset(admin, tenant, business, key, body="Crie uma imagem do croissant")
        async with admin.begin() as conn:
            await conn.execute(
                text(
                    "UPDATE whatsapp_processing_consents SET accepted_at=now()+interval '1 minute' "
                    "WHERE tenant_id=:tenant AND business_id=:business"
                ),
                {"tenant": tenant, "business": business},
            )
        assert await activity.request_candidate_proposal(str(stale)) == "skipped"
    finally:
        await worker.close()


async def test_briefing_gates_replay_expiration_and_missing_sources(admin, database, seeded, settings):
    from app.services.editorial_briefings import EditorialBriefingService

    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr(key)})
    source = await _asset(admin, tenant, business, key, body="Crie uma imagem do croissant")
    catalog = _payload()
    await BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
    fake = SimpleNamespace(
        interpret=AsyncMock(return_value=CatalogIntent("selected", UUID(catalog["offerings"][0]["id"])))
    )
    service = EditorialBriefingService(cfg, database, fake)
    op = uuid4()
    async with database.transaction(tenant, actor) as session:
        assert await service.read_valid(session, tenant, business, actor, uuid4()) == ("unavailable", None)
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE billing_sponsorships SET revoked_at=now() WHERE tenant_id=:tenant"), {"tenant": tenant}
        )
    with pytest.raises(AuthError, match="PLAN_REQUIRED"):
        await service.prepare(tenant, business, actor, source, op)
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE billing_sponsorships SET revoked_at=NULL WHERE tenant_id=:tenant"), {"tenant": tenant}
        )
        await conn.execute(
            text("UPDATE editorial_ai_consents SET revoked_at=now() WHERE tenant_id=:tenant"), {"tenant": tenant}
        )
    with pytest.raises(AuthError, match="EDITORIAL_AI_CONSENT_REQUIRED"):
        await service.prepare(tenant, business, actor, source, op)
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE editorial_ai_consents SET revoked_at=NULL WHERE tenant_id=:tenant"), {"tenant": tenant}
        )
    result = await service.prepare(tenant, business, actor, source, op)
    with pytest.raises(AuthError, match="BRIEFING_OPERATION_CONFLICT"):
        await service.prepare(tenant, business, actor, source, uuid4())
    async with admin.begin() as conn:
        await conn.execute(
            text(
                "UPDATE editorial_briefings SET state='submitted',catalog_snapshot=NULL, "
                "updated_at=now()-interval '6 minutes' WHERE id=:id"
            ),
            {"id": result.id},
        )
    assert (await service.prepare(tenant, business, actor, source, op)).state == "uncertain"
    async with database.transaction(tenant, actor) as session:
        assert await service.read_valid(session, tenant, business, actor, result.id) == ("unavailable", None)
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE editorial_briefings SET state='needs_clarification' WHERE id=:id"), {"id": result.id}
        )
    async with database.transaction(tenant, actor) as session:
        assert await service.read_valid(session, tenant, business, actor, result.id) == ("needs_clarification", None)
    with pytest.raises(AuthError, match="BRIEFING_INTERPRETER_DISABLED"):
        await EditorialBriefingService(cfg, database).prepare(tenant, business, actor, source, uuid4())
    with pytest.raises(ValueError, match="development and testing"):
        EditorialBriefingService(cfg.model_copy(update={"environment": "production"}), database, fake)


@pytest.mark.parametrize("failure", ["unavailable", "invalid", "exception", "deleted", "catalog_changed"])
async def test_interpreter_failures_do_not_persist_snapshot(admin, database, seeded, settings, failure):
    from app.services.creative_catalog_resolution import CatalogInterpreterUnavailable

    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    key = Fernet.generate_key().decode()
    cfg = settings.model_copy(update={"meta_encryption_key": SecretStr(key)})
    source = await _asset(admin, tenant, business, key, body="Crie uma imagem do croissant")
    catalog = _payload()
    await BusinessCatalogService(database).update(tenant, business, actor, CatalogUpdate.model_validate(catalog))
    item = UUID(catalog["offerings"][0]["id"])

    async def fail(*args):
        if failure == "unavailable":
            raise CatalogInterpreterUnavailable()
        if failure == "invalid":
            return object()
        if failure == "exception":
            raise RuntimeError("synthetic fault")
        async with admin.begin() as conn:
            if failure == "deleted":
                await conn.execute(text("DELETE FROM editorial_briefings WHERE tenant_id=:tenant"), {"tenant": tenant})
            else:
                await conn.execute(
                    text(
                        "UPDATE business_catalog_heads SET version=version+1 "
                        "WHERE tenant_id=:tenant AND business_id=:business"
                    ),
                    {"tenant": tenant, "business": business},
                )
        return CatalogIntent("selected", item)

    fake = SimpleNamespace(interpret=AsyncMock(side_effect=fail))
    worker = Database(cfg, correlator=True)
    try:
        activity = ContentCandidateActivities(cfg, database, worker, interpreter=fake)
        result = await activity.request_candidate_proposal(str(source))
        if failure == "deleted":
            assert result == "skipped"
        elif failure == "catalog_changed":
            assert result == "briefing_needs_clarification"
        else:
            assert result == "briefing_unavailable"
        async with admin.connect() as conn:
            assert await conn.scalar(text("SELECT count(*) FROM editorial_proposals")) == 0
            assert await conn.scalar(text("SELECT catalog_snapshot FROM editorial_briefings")) is None
    finally:
        await worker.close()
