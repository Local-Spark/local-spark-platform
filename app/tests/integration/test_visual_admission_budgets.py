"""Owner admissions and restricted OpenAI ledger reservations, without provider IO."""

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.db.session import Database
from app.services.visual_attempts import VisualAttemptService
from app.services.visual_consent_gate import VisualConsentGate
from app.services.visual_cost_ledger import VisualCostError, VisualCostLedger
from app.tests.integration.test_visual_admission import _ready
from app.tests.integration.test_visual_attempts import preview as create_preview

pytestmark = pytest.mark.integration


async def _admitted(admin, database, context):
    tenant, business, actor, _, admission = context
    preview = await create_preview(admin, tenant, business, actor)
    operation = uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("""UPDATE media_previews SET proposal_id=:proposal,generation_mode='visual_fake',
              visual_fingerprint=:fingerprint
              WHERE id=:preview"""),
            {"proposal": admission.proposal, "preview": preview, "fingerprint": admission.fingerprint},
        )
    assert await VisualConsentGate(database).admit(tenant, business, actor, preview, operation, 1, admission=admission)
    return tenant, business, actor, preview, operation


async def _reserve(service, admitted, amount):
    tenant, business, actor, preview, operation = admitted
    # Selecting the ledger's OpenAI category never constructs or calls an
    # adapter. The identities and amounts here are entirely synthetic.
    return await service.reserve(
        tenant, business, actor, preview, 1, operation, "openai", "synthetic-model", "a" * 64, amount
    )


@pytest.mark.parametrize("ceiling", ["tenant", "aggregate"])
async def test_concurrent_admissions_cannot_overspend_or_duplicate_a_rejected_reservation(
    admin, database, seeded, settings, ceiling
):
    first_context = await _ready(admin, database, seeded, settings)
    second_context = first_context
    if ceiling == "aggregate":
        # Shared single-tenant fixtures use one synthetic sender. Give the
        # first business its own source identity before creating tenant two.
        async with admin.begin() as connection:
            params = {"tenant": first_context[0], "sender": "a" * 64}
            await connection.execute(
                text("UPDATE whatsapp_channel_links SET sender_hash=:sender WHERE tenant_id=:tenant"), params
            )
            await connection.execute(
                text("UPDATE whatsapp_material_events SET sender_hash=:sender WHERE tenant_id=:tenant"), params
            )
        second_context = await _ready(admin, database, {**seeded, "t1": seeded["t2"], "a1": seeded["a2"]}, settings)
    contexts = (first_context, second_context)
    admissions = [await _admitted(admin, database, context) for context in contexts]
    cfg = settings.model_copy(
        update={
            "visual_ai_monthly_budget_usd_micros": 100,
            "visual_ai_global_monthly_budget_usd_micros": 100 if ceiling == "aggregate" else 1000,
        }
    )
    worker = Database(cfg, correlator=True)
    try:
        service = VisualAttemptService(cfg, worker)
        outcomes = await asyncio.gather(
            *(_reserve(service, admitted, 70) for admitted in admissions), return_exceptions=True
        )
        assert sum(not isinstance(result, Exception) for result in outcomes) == 1
        rejected = next(index for index, result in enumerate(outcomes) if isinstance(result, Exception))
        expected = "VISUAL_GLOBAL_BUDGET_EXCEEDED" if ceiling == "aggregate" else "VISUAL_BUDGET_EXCEEDED"
        assert isinstance(outcomes[rejected], VisualCostError) and str(outcomes[rejected]) == expected
        with pytest.raises(VisualCostError, match=expected):
            await _reserve(service, admissions[rejected], 70)
        tenant, business, actor, preview, operation = admissions[rejected]
        assert not await VisualConsentGate(database).admit(
            tenant, business, actor, preview, operation, 1, admission=contexts[rejected][-1]
        )
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT count(*) FROM visual_consent_runs")) == 2
            assert await connection.scalar(text("SELECT count(*) FROM visual_ai_attempts")) == 1
            assert await connection.scalar(text("SELECT count(*) FROM visual_cost_reservations")) == 1
            assert await connection.scalar(text("SELECT committed_usd_micros FROM visual_global_monthly_budget")) == 70
            assert await connection.scalar(text("SELECT count(*) FROM visual_cost_events WHERE action='reserved'")) == 1
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM visual_ai_attempts WHERE preview_id=:preview"), {"preview": preview}
                )
                == 0
            )
    finally:
        await worker.close()


async def test_uncertain_admitted_attempt_keeps_hold_and_late_cost_releases_only_proven_difference(
    admin, database, seeded, settings
):
    context = await _ready(admin, database, seeded, settings)
    admissions = [await _admitted(admin, database, context) for _ in range(3)]
    tenant, _, actor, _, _ = admissions[0]
    cfg = settings.model_copy(
        update={"visual_ai_monthly_budget_usd_micros": 100, "visual_ai_global_monthly_budget_usd_micros": 100}
    )
    worker = Database(cfg, correlator=True)
    try:
        service, ledger = VisualAttemptService(cfg, worker), VisualCostLedger(cfg, worker)
        first = await _reserve(service, admissions[0], 70)
        uncertain = await ledger.finish(tenant, actor, first.reservation.id, actual_usd_micros=None)
        assert uncertain.state == "uncertain" and uncertain.actual_usd_micros is None
        assert not (await _reserve(service, admissions[0], 70)).created
        with pytest.raises(VisualCostError, match="VISUAL_BUDGET_EXCEEDED"):
            await _reserve(service, admissions[1], 70)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT committed_usd_micros FROM visual_global_monthly_budget")) == 70
            assert await connection.scalar(text("SELECT count(*) FROM visual_ai_attempts")) == 1
        # Trusted late reconciliation proves a cost of 30. Only its difference
        # from the original hold is freed; replay cannot free that credit twice.
        completed = await ledger.finish(tenant, actor, first.reservation.id, actual_usd_micros=30)
        assert completed.state == "completed" and completed.actual_usd_micros == 30
        assert (await ledger.finish(tenant, actor, first.reservation.id, actual_usd_micros=30)) == completed
        second = await _reserve(service, admissions[1], 70)
        assert second.created
        with pytest.raises(VisualCostError, match="VISUAL_BUDGET_EXCEEDED"):
            await _reserve(service, admissions[2], 1)
        with pytest.raises(VisualCostError, match="RESERVATION_OUTCOME_CONFLICT"):
            await ledger.finish(tenant, actor, first.reservation.id, actual_usd_micros=20)
        async with admin.connect() as connection:
            assert await connection.scalar(text("SELECT committed_usd_micros FROM visual_global_monthly_budget")) == 100
            assert await connection.scalar(text("SELECT count(*) FROM visual_ai_attempts")) == 2
            assert await connection.scalar(text("SELECT count(*) FROM visual_cost_reservations")) == 2
            assert (
                await connection.scalar(text("SELECT count(*) FROM visual_cost_events WHERE action='uncertain'")) == 1
            )
            assert (
                await connection.scalar(text("SELECT count(*) FROM visual_cost_events WHERE action='completed'")) == 1
            )
            # Settling money is not proof that generation finished, and cannot
            # silently close an owner admission or apply a pending source change.
            assert (
                await connection.scalar(text("SELECT count(*) FROM visual_consent_runs WHERE state='in_flight'")) == 3
            )
    finally:
        await worker.close()
