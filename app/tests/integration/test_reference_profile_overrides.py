"""Owner corrections are versioned, shared, replayable and do not fetch profiles."""

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.tests.integration.test_reference_discovery import access_token
from app.tests.integration.test_reference_real_selection import _result, _seed

pytestmark = pytest.mark.integration


async def _setup(admin, seeded):
    tenant, business, actor, cycle = await _seed(admin, seeded)
    result, candidates, places = await _result(admin, tenant, business, actor, cycle, 5)
    async with admin.begin() as conn:
        await conn.execute(
            text("""INSERT INTO reference_provider_profile_options
          (tenant_id,business_id,result_id,candidate_id,instagram_handle,source_position,is_primary,source,association_status)
          VALUES(:t,:b,:r,:c,'provider_suggestion',1,false,'apify','unverified')"""),
            {"t": tenant, "b": business, "r": result, "c": candidates[0]},
        )
    base = f"/api/v1/organizations/{tenant}/businesses/{business}/reference-results"
    payload = {
        "operation_id": str(uuid4()),
        "expected_version": 0,
        "result_id": str(result),
        "candidate_id": str(candidates[0]),
        "instagram_handle": "@Correct_Profile",
    }
    return tenant, business, actor, cycle, result, candidates[0], places[0], base, payload


async def test_correction_overrides_apify_preserves_history_and_replays_without_new_effect(
    admin, seeded, api, settings
):
    t, b, actor, cycle, result, candidate, place, base, payload = await _setup(admin, seeded)
    headers = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    before = (await api.get(base, headers=headers)).json()["searches"][0]["candidates"][0]
    assert before["profile_source"] == "apify" and before["profile_version"] == 0
    url = base + f"/profiles/{place}"
    first, replay = await asyncio.gather(
        api.put(url, headers=headers, json=payload), api.put(url, headers=headers, json=payload)
    )
    assert first.status_code == 200 and replay.json() == first.json()
    assert first.json()["version"] == 1 and first.json()["instagram_handle"] == "correct_profile"
    after = (await api.get(base, headers=headers)).json()
    assert after["selected"] == []
    item = after["searches"][0]["candidates"][0]
    assert (
        item["profile_source"] == "owner"
        and item["profile_version"] == 1
        and item["instagram_handle"] == "correct_profile"
    )
    assert item["reputation_score"] == before["reputation_score"]
    unchanged = {**payload, "operation_id": str(uuid4()), "expected_version": 1}
    assert (await api.put(url, headers=headers, json=unchanged)).json() == first.json()
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM reference_profile_overrides")) == 1
        assert await conn.scalar(text("SELECT count(*) FROM reference_profile_override_operations")) == 2
        assert (
            await conn.scalar(text("SELECT count(*) FROM outbox_events WHERE event_type='reference.profile_changed'"))
            == 1
        )
        event = await conn.scalar(
            text("SELECT payload::text FROM outbox_events WHERE event_type='reference.profile_changed'")
        )
        assert "correct_profile" not in event and "provider_suggestion" not in event
        assert await conn.scalar(text("SELECT count(*) FROM reference_provider_effects")) == 0
    bad = {**payload, "instagram_handle": "different"}
    assert (await api.put(url, headers=headers, json=bad)).json()[
        "error_code"
    ] == "REFERENCE_PROFILE_OPERATION_CONFLICT"
    stale = {**bad, "operation_id": str(uuid4())}
    assert (await api.put(url, headers=headers, json=stale)).json()[
        "error_code"
    ] == "REFERENCE_PROFILE_VERSION_CONFLICT"


async def test_two_owners_share_correction_but_other_tenant_and_revoked_owner_cannot_edit(admin, seeded, api, settings):
    t, b, actor, cycle, result, candidate, place, base, payload = await _setup(admin, seeded)
    url = base + f"/profiles/{place}"
    original = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    first = await api.put(url, headers=original, json=payload)
    assert first.status_code == 200
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE memberships SET role='owner' WHERE tenant_id=:t AND actor_id=:a"),
            {"t": t, "a": seeded["viewer"]},
        )
    other = {"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"}
    changed = {**payload, "operation_id": str(uuid4()), "expected_version": 1, "instagram_handle": "another_profile"}
    second = await api.put(url, headers=other, json=changed)
    assert second.status_code == 200 and second.json()["version"] == 2
    assert (await api.put(url, headers=original, json=payload)).json() == first.json()
    item = (await api.get(base, headers=original)).json()["searches"][0]["candidates"][0]
    assert item["instagram_handle"] == "another_profile" and item["profile_version"] == 2
    outsider = {"Authorization": f"Bearer {access_token(settings, seeded['a2'])}"}
    assert (await api.put(url, headers=outsider, json=changed)).status_code == 403
    async with admin.begin() as conn:
        await conn.execute(
            text("UPDATE memberships SET active=false WHERE tenant_id=:t AND actor_id=:a"), {"t": t, "a": actor}
        )
    assert (await api.put(url, headers=original, json=payload)).status_code == 403
    async with admin.connect() as conn:
        assert await conn.scalar(text("SELECT count(*) FROM reference_profile_overrides")) == 2


async def test_only_current_or_still_selected_published_occurrences_can_be_corrected(admin, seeded, api, settings):
    t, b, actor, cycle, result, candidate, place, base, payload = await _setup(admin, seeded)
    headers = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    url = base + f"/profiles/{place}"
    bad = {**payload, "candidate_id": str(uuid4())}
    assert (await api.put(url, headers=headers, json=bad)).json()[
        "error_code"
    ] == "REFERENCE_PROFILE_OCCURRENCE_INVALID"
    new = uuid4()
    async with admin.begin() as conn:
        await conn.execute(
            text("INSERT INTO reference_real_cycles(tenant_id,business_id,id) VALUES(:t,:b,:id)"),
            {"t": t, "b": b, "id": new},
        )
        await conn.execute(
            text("UPDATE reference_real_heads SET cycle_id=:id WHERE tenant_id=:t AND business_id=:b"),
            {"t": t, "b": b, "id": new},
        )
    assert (await api.put(url, headers=headers, json=payload)).json()[
        "error_code"
    ] == "REFERENCE_PROFILE_OCCURRENCE_INVALID"
    async with admin.begin() as conn:
        await conn.execute(
            text("INSERT INTO reference_real_selected VALUES(:t,:b,:p,:r,:c)"),
            {"t": t, "b": b, "p": place, "r": result, "c": candidate},
        )
    assert (await api.put(url, headers=headers, json=payload)).status_code == 200
    assert (await api.get(base, headers=headers)).json()["selected"][0]["instagram_handle"] == "correct_profile"
    for change in ({"instagram_handle": "invalid/profile"}, {"reputation_score": "10"}, {"expected_version": True}):
        assert (await api.put(url, headers=headers, json={**payload, **change})).status_code == 422
