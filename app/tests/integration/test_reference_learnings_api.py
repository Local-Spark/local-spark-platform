"""Owner HTTP reads persisted patterns without creating provider effects."""

from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import text

from app.adapters.jev_reference_post_analysis import JevReferencePostAnalysis
from app.services.reference_learning_store import ReferenceLearningStore
from app.services.reference_pattern_vocabulary import aggregate_pattern_choices
from app.services.reference_post_analysis_guard import DatabasePostAnalysisGuard, PostGuardContext
from app.tests.integration.test_reference_learning import canonical_feed_fixture, canonical_learning_fixture
from app.tests.unit.test_core import access_token
from app.tests.unit.test_jev_reference_post_analysis import response_for

pytestmark = pytest.mark.integration


async def _counts(admin):
    async with admin.connect() as conn:
        return tuple(
            [
                await conn.scalar(text(f"SELECT count(*) FROM {table}"))
                for table in (
                    "reference_feed_windows",
                    "reference_learning_associations",
                    "reference_learning_results",
                    "reference_cost_reservations",
                    "outbox_events",
                    "audit_events",
                )
            ]
        )


async def test_learnings_http_reports_waiting_and_enforces_active_owner(admin, api, seeded, settings):
    event, base, headers, reference = await canonical_learning_fixture(admin, api, seeded, settings)
    before = await _counts(admin)
    response = await api.get(base + "/reference-learnings", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json() == {
        "references": [
            {
                "reference_id": str(reference),
                "association_version": 1,
                "source": "owner",
                "instagram_handle": "fixture_profile",
                "profile_name": None,
                "analysis_status": "not_requested",
                "update_status": "waiting",
                "last_analyzed_at": None,
                "next_analysis_at": response.json()["references"][0]["next_analysis_at"],
                "patterns": [],
            }
        ]
    }
    viewer_headers = {"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"}
    denied = await api.get(base + "/reference-learnings", headers=viewer_headers)
    assert denied.status_code == 403
    other = await api.get(
        base.replace(event.tenant_id, str(seeded["t2"])) + "/reference-learnings",
        headers={"Authorization": f"Bearer {access_token(settings, seeded['a2'])}"},
    )
    assert other.status_code == 403
    assert (await api.get(base + "/reference-learnings")).status_code == 401
    assert await _counts(admin) == before


async def test_learnings_http_shares_only_persisted_patterns_and_profile_name(admin, api, seeded, settings):
    worker, window, feed, token, _ = await canonical_feed_fixture(admin, api, seeded, settings)
    try:
        tariff = "jev-" + uuid4().hex
        async with admin.begin() as conn:
            await conn.execute(
                text("""INSERT INTO reference_provider_tariffs(version,provider,field_mask,
                  minimum_reserved_usd_micros,active) VALUES(:v,'jev','jev-model:jev-1.14.0',1,true)"""),
                {"v": tariff},
            )
        context = PostGuardContext(
            window.tenant,
            window.business,
            window.actor,
            window.window,
            window.reference,
            1,
            feed.effect,
            token,
            uuid4(),
            "b" * 64,
            feed.pilot,
            feed.key,
            "test-key",
            tariff,
            "test-credential",
            5,
            caption_mac="a" * 64,
        )
        guard = DatabasePostAnalysisGuard(worker, context)
        model = JevReferencePostAnalysis(
            SecretStr("synthetic"),
            "jev-1.14.0",
            guard,
            enabled=True,
            transport=httpx.MockTransport(lambda request: httpx.Response(200, json=response_for(request))),
        )
        result = await model.analyze(caption="Synthetic private caption", image=None, operation_id=context.effect)
        await guard.record(result)
        patterns = aggregate_pattern_choices((result.choices,))
        await ReferenceLearningStore(worker).finish(
            window,
            feed.effect,
            token,
            patterns=patterns,
            status="partial",
            posts=1,
            images=0,
            coverage="partial",
            profile_name="Café de demonstração",
        )
        base = f"/api/v1/organizations/{window.tenant}/businesses/{window.business}"
        headers = {"Authorization": f"Bearer {access_token(settings, window.actor)}"}
        before = await _counts(admin)
        first = await api.get(base + "/reference-learnings", headers=headers)
        assert first.status_code == 200, first.text
        value = first.json()["references"][0]
        assert value["analysis_status"] == "partial" and value["update_status"] == "scheduled"
        assert value["profile_name"] == "Café de demonstração"
        assert value["patterns"] == [pattern.model_dump() for pattern in patterns]
        assert value["last_analyzed_at"] and value["next_analysis_at"]
        assert "Synthetic private caption" not in first.text
        async with admin.begin() as conn:
            await conn.execute(
                text("UPDATE memberships SET role='owner' WHERE tenant_id=:tenant AND actor_id=:actor"),
                {"tenant": window.tenant, "actor": seeded["viewer"]},
            )
        second = await api.get(
            base + "/reference-learnings",
            headers={"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"},
        )
        assert second.status_code == 200 and second.json() == first.json()
        assert await _counts(admin) == before
    finally:
        await worker.close()
