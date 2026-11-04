"""Versioned owner characteristics and retirement of the legacy facts area."""

from uuid import uuid4

import pytest
from sqlalchemy import text

from app.tests.integration.test_reference_discovery import create_business
from app.tests.unit.test_core import access_token

pytestmark = pytest.mark.integration


async def test_characteristics_legacy_clients_restore_replay_and_facts(admin, api, seeded, settings):
    tenant, actor = seeded["t1"], seeded["a1"]
    business = await create_business(admin, tenant)
    url = f"/api/v1/organizations/{tenant}/businesses/{business}/editorial-context"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    viewer = {"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"}
    legacy = {"expected_version": 0, "operation_id": str(uuid4()), "preferences": {"business_terms": ["Café"]}}
    first = await api.put(url, headers=owner, json=legacy)
    assert first.status_code == 200
    async with admin.begin() as conn:
        await conn.execute(
            text("""UPDATE business_context_versions SET document=jsonb_set(
              document,'{facts}',CAST(:facts AS jsonb))
              WHERE tenant_id=:tenant AND business_id=:business AND version=1"""),
            {
                "tenant": tenant,
                "business": business,
                "facts": '[{"id":"00000000-0000-4000-8000-000000000001","kind":"product",'
                '"statement":"Dado antigo","source_detail":"Titular"}]',
            },
        )
    put = {
        "expected_version": 1,
        "operation_id": str(uuid4()),
        "preferences": {"business_characteristics": " Atendimento acolhedor "},
    }
    assert (await api.put(url, headers=viewer, json=put)).status_code == 403
    saved = await api.put(url, headers=owner, json=put)
    assert saved.status_code == 200, saved.text
    assert saved.json()["facts"] == []
    assert saved.json()["preferences"]["business_terms"] == ["Café"]
    assert saved.json()["preferences"]["business_characteristics"] == "Atendimento acolhedor"
    assert (await api.put(url, headers=owner, json=put)).json() == saved.json()
    legacy_edit = {"expected_version": 2, "operation_id": str(uuid4()), "preferences": {"tone": "friendly"}}
    result = await api.put(url, headers=owner, json=legacy_edit)
    assert (
        result.status_code == 200
        and result.json()["preferences"]["business_characteristics"] == "Atendimento acolhedor"
    )
    restored = await api.post(
        url + "/restore", headers=owner, json={"expected_version": 3, "target_version": 1, "operation_id": str(uuid4())}
    )
    assert restored.status_code == 200 and restored.json()["facts"] == []
    # Historical snapshots that predate the field keep the present owner choice.
    # The generated test's first snapshot has the current field explicitly empty.
    cleared = await api.put(
        url,
        headers=owner,
        json={"expected_version": 4, "operation_id": str(uuid4()), "preferences": {"business_characteristics": ""}},
    )
    assert cleared.status_code == 200 and cleared.json()["preferences"]["business_characteristics"] is None
