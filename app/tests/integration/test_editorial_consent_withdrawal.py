"""Editorial requests cannot be revived after a consent withdrawal."""

import asyncio
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.db.session import Database
from app.schemas.editorial_proposals import ProposalRequest
from app.services.auth import AuthError
from app.services.editorial_dispatch import claim_proposals, finish_proposal_dispatch
from app.services.editorial_proposals import EditorialProposalService
from app.tests.integration.test_editorial_briefings import _enable
from app.tests.integration.test_editorial_proposals import _business, _fact

pytestmark = pytest.mark.integration


async def test_withdrawal_and_regrant_never_replay_an_old_request(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    cfg = settings.model_copy(update={"editorial_ai_mode": "openai"})
    consent = EditorialProposalService(cfg, database)
    payload = ProposalRequest(operation_id=uuid4())
    proposal = await consent.request(tenant, business, actor, payload)
    await consent.set_consent(tenant, business, actor, False)
    await consent.set_consent(tenant, business, actor, True)
    with pytest.raises(AuthError, match="EDITORIAL_REQUEST_CANCELLED"):
        await consent.request(tenant, business, actor, payload)
    worker = Database(cfg, correlator=True)
    provider = AsyncMock()
    try:
        claim = (await claim_proposals(worker, uuid4()))[0]
        await finish_proposal_dispatch(worker, claim, True)
        assert (
            await EditorialProposalService(cfg, worker, provider, owner_database=database).run(proposal.id)
            == "rejected"
        )
        provider.propose.assert_not_awaited()
        async with admin.connect() as connection:
            code = await connection.scalar(
                text("SELECT error_code FROM editorial_proposals WHERE id=:id"), {"id": proposal.id}
            )
        assert code == "EDITORIAL_REQUEST_CANCELLED"
    finally:
        await worker.close()


async def test_request_racing_with_withdrawal_cannot_be_replayed_after_regrant(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    cfg = settings.model_copy(update={"editorial_ai_mode": "openai"})
    consent = EditorialProposalService(cfg, database)
    payload = ProposalRequest(operation_id=uuid4())
    requested, withdrawn = await asyncio.gather(
        consent.request(tenant, business, actor, payload),
        consent.set_consent(tenant, business, actor, False),
        return_exceptions=True,
    )
    assert not isinstance(withdrawn, Exception)
    await consent.set_consent(tenant, business, actor, True)
    if isinstance(requested, AuthError):
        assert requested.code in {"EDITORIAL_AI_CONSENT_REQUIRED", "EDITORIAL_WITHDRAWAL_PENDING"}
    else:
        with pytest.raises(AuthError, match="EDITORIAL_REQUEST_CANCELLED"):
            await consent.request(tenant, business, actor, payload)


async def test_legacy_queued_proposal_without_consent_epoch_is_not_sent(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    cfg = settings.model_copy(update={"editorial_ai_mode": "openai"})
    owner = EditorialProposalService(cfg, database)
    proposal = await owner.request(tenant, business, actor, ProposalRequest(operation_id=uuid4()))
    async with admin.begin() as connection:
        await connection.execute(
            text("UPDATE editorial_proposals SET consent_generation=NULL WHERE id=:id"), {"id": proposal.id}
        )
    worker = Database(cfg, correlator=True)
    provider = AsyncMock()
    try:
        claim = (await claim_proposals(worker, uuid4()))[0]
        await finish_proposal_dispatch(worker, claim, True)
        assert (
            await EditorialProposalService(cfg, worker, provider, owner_database=database).run(proposal.id)
            == "rejected"
        )
        provider.propose.assert_not_awaited()
    finally:
        await worker.close()


async def test_withdrawal_does_not_cancel_local_baseline_work(admin, database, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await _business(admin, seeded)
    await _enable(admin, tenant, business, actor)
    await _fact(admin, tenant, business, actor)
    owner = EditorialProposalService(settings, database)
    payload = ProposalRequest(operation_id=uuid4())
    proposal = await owner.request(tenant, business, actor, payload)
    await owner.set_consent(tenant, business, actor, False)
    await owner.set_consent(tenant, business, actor, True)
    assert (await owner.request(tenant, business, actor, payload)).id == proposal.id
    worker = Database(settings, correlator=True)
    try:
        claim = (await claim_proposals(worker, uuid4()))[0]
        await finish_proposal_dispatch(worker, claim, True)
        assert await EditorialProposalService(settings, worker, owner_database=database).run(proposal.id) == "completed"
    finally:
        await worker.close()
