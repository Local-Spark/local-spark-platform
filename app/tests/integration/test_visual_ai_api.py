"""The public request names the paid mode and never downgrades missing authority."""

from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import text

from app.main import create_app
from app.schemas.editorial_proposals import ScriptReview
from app.services.editorial_proposals import EditorialProposalService
from app.services.service_agreement import SERVICE_AGREEMENT_HASH, SERVICE_AGREEMENT_VERSION, ServiceAgreementService
from app.tests.integration.test_visual_admission import _ready
from app.tests.unit.test_core import access_token

pytestmark = pytest.mark.integration


async def test_public_visual_ai_request_requires_configuration_contract_and_owner_and_is_idempotent(
    admin, database, seeded, settings
):
    tenant, business, actor, _, admission = await _ready(admin, database, seeded, settings)
    # The public manual-preview route remains a DEV lab tool for a reviewed
    # script. The automatic customer journey is tested through Temporal.
    await EditorialProposalService(admission.settings, database).review_script(
        tenant, business, actor, admission.proposal, ScriptReview(operation_id=uuid4(), decision="accepted")
    )
    cfg = admission.settings.model_copy(
        update={
            "visual_ai_mode": "openai",
            "visual_ai_execution_enabled": True,
            "visual_ai_reservation_usd_micros": 70,
            "visual_ai_monthly_budget_usd_micros": 100,
            "visual_ai_global_monthly_budget_usd_micros": 100,
            "openai_api_key": SecretStr("synthetic-unused-key"),
            "service_agreement_required": True,
        }
    )
    app = create_app(cfg, database)
    path = f"/api/v1/organizations/{tenant}/businesses/{business}/media-previews"
    owner = {"Authorization": f"Bearer {access_token(cfg, actor)}"}
    payload = {"operation_id": str(uuid4()), "proposal_id": str(admission.proposal), "generation_mode": "visual_ai"}
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client,
    ):
        cfg.visual_ai_execution_enabled = False
        blocked = await client.post(path, headers=owner, json=payload)
        assert blocked.status_code == 409 and blocked.json()["error_code"] == "VISUAL_EXECUTION_DISABLED"
        cfg.visual_ai_execution_enabled = True
        blocked = await client.post(path, headers=owner, json=payload)
        assert blocked.status_code == 409 and blocked.json()["error_code"] == "SERVICE_AGREEMENT_REQUIRED"
        await ServiceAgreementService(cfg, database).accept(
            tenant, business, actor, SERVICE_AGREEMENT_VERSION, SERVICE_AGREEMENT_HASH
        )
        for other in (seeded["viewer"], seeded["a2"]):
            denied = await client.post(
                path, headers={"Authorization": f"Bearer {access_token(cfg, other)}"}, json=payload
            )
            assert denied.status_code == 403
        first = await client.post(path, headers=owner, json=payload)
        assert first.status_code == 202, first.text
        row = first.json()
        assert row["state"] == "pending" and row["generation_mode"] == "visual_ai"
        replay = await client.post(path, headers=owner, json=payload)
        assert replay.status_code == 202 and replay.json()["id"] == row["id"]
        legacy = await client.post(path, headers=owner, json={**payload, "generation_mode": "local"})
        assert legacy.status_code == 409 and legacy.json()["error_code"] == "PREVIEW_OPERATION_CONFLICT"
        fake = await client.post(path, headers=owner, json={**payload, "generation_mode": "visual_fake"})
        assert fake.status_code == 409 and fake.json()["error_code"] == "VISUAL_FAKE_DISABLED"
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM media_previews")) == 1
        assert await connection.scalar(text("SELECT count(*) FROM visual_ai_attempts")) == 0
        assert await connection.scalar(text("SELECT count(*) FROM visual_cost_reservations")) == 0
        assert await connection.scalar(text("SELECT count(*) FROM visual_consent_runs")) == 0
        assert (
            await connection.scalar(text("SELECT count(*) FROM audit_events WHERE action='media.preview_requested'"))
            == 1
        )
