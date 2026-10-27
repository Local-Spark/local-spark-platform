"""BL02: owner-only draft/confirm, CAS, private logos and frozen F03 kit."""

import asyncio
import base64
import io
from uuid import uuid4

import pytest
from PIL import Image
from sqlalchemy import text

from app.schemas.brand_kits import BrandKitLogoUpload
from app.services.auth import AuthError
from app.services.brand_kits import BrandKitService
from app.tests.unit.test_core import access_token

pytestmark = pytest.mark.integration


async def _business(admin, seeded, name="A"):
    business = uuid4()
    async with admin.begin() as connection:
        await connection.execute(
            text("INSERT INTO businesses(id,tenant_id,name,timezone) VALUES(:id,:tenant,:name,'UTC')"),
            {"id": business, "tenant": seeded["t1"], "name": name},
        )
        await connection.execute(
            text("""INSERT INTO business_profiles
              (tenant_id,business_id,category,city,description,phone,brand_color)
              VALUES(:tenant,:business,'Food','Rio','Test','+5511999999999','#6557ed')"""),
            {"tenant": seeded["t1"], "business": business},
        )
        await connection.execute(
            text("""INSERT INTO billing_sponsorships(id,tenant_id,actor_id,idempotency_key,reason)
              VALUES(:id,:tenant,:actor,:key,'Brand kit test')"""),
            {"id": uuid4(), "tenant": seeded["t1"], "actor": seeded["a1"], "key": str(uuid4())},
        )
    return business


def _overrides(name="A"):
    return {
        "palette": {"primary": "#244739", "background": "#F5F0E7", "accent": "#BB7A48"},
        "heading_font": "DejaVu Serif",
        "body_font": "DejaVu Sans",
        "brand_name": name,
        "tagline": "",
        "cta": "Saiba mais",
        "formats": {
            "feed": {"layout": "photo_focus", "image_position": "center"},
            "story": {"layout": "photo_focus", "image_position": "center"},
            "reel_cover": {"layout": "photo_focus", "image_position": "center"},
        },
        "logo_asset_id": None,
    }


def _draft(expected, overrides=None, operation=None):
    return {
        "operation_id": str(operation or uuid4()),
        "expected_version": expected,
        "kit_id": "cafe-pausas",
        "kit_version": 1,
        "overrides": overrides or _overrides(),
    }


async def test_kit_catalog_draft_confirm_replay_cas_and_snapshot(admin, api, database, seeded, settings):
    business = await _business(admin, seeded)
    tenant, actor = seeded["t1"], seeded["a1"]
    base = f"/api/v1/organizations/{tenant}/businesses/{business}/brand-kit"
    owner = {"Authorization": f"Bearer {access_token(settings, actor)}"}
    viewer = {"Authorization": f"Bearer {access_token(settings, seeded['viewer'])}"}
    other = {"Authorization": f"Bearer {access_token(settings, seeded['a2'])}"}

    catalog = await api.get(base + "/catalog", headers=owner)
    assert catalog.status_code == 200, catalog.text
    kit = catalog.json()["kits"][0]
    assert kit["status"] == "public_demo" and kit["selectable"]
    assert kit["default_overrides"]["brand_name"] == "A"
    assert all("post-" not in value for value in kit["preview_images"].values())
    assert kit["options"]["layouts"]["feed"] == ["photo_focus", "offer_focus"]
    assert (await api.get(base, headers=owner)).json() == {"head_version": 0, "confirmed": None, "draft": None}
    assert (await api.get(base, headers=viewer)).status_code == 403
    assert (await api.get(base, headers=other)).status_code == 403

    initial = _draft(0)
    wrong = {
        **initial,
        "overrides": {
            **initial["overrides"],
            "palette": {"primary": "#FFFFFF", "background": "#FAFAFA", "accent": "#BB7A48"},
        },
    }
    assert (await api.put(base + "/draft", headers=owner, json=wrong)).status_code == 422
    assert (await api.put(base + "/draft", headers=viewer, json=initial)).status_code == 403
    first = await api.put(base + "/draft", headers=owner, json=initial)
    assert first.status_code == 200, first.text
    assert first.json()["head_version"] == 1
    assert first.json()["draft"]["version"] == 1
    assert first.json()["confirmed"] is None

    confirm = {"operation_id": str(uuid4()), "expected_version": 1}
    accepted = await api.post(base + "/confirm", headers=owner, json=confirm)
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["head_version"] == 2
    assert accepted.json()["confirmed"]["version"] == 2
    assert accepted.json()["draft"] is None
    assert (await api.post(base + "/confirm", headers=owner, json=confirm)).json() == accepted.json()

    edited = _overrides()
    edited["formats"]["feed"]["layout"] = "offer_focus"
    edited["tagline"] = "Uma pausa especial"
    next_draft = _draft(2, edited)
    saved = await api.put(base + "/draft", headers=owner, json=next_draft)
    assert saved.status_code == 200
    assert saved.json()["head_version"] == 3
    assert saved.json()["confirmed"]["version"] == 2
    assert saved.json()["draft"]["overrides"]["formats"]["feed"]["layout"] == "offer_focus"
    assert (await api.put(base + "/draft", headers=owner, json=initial)).json() == first.json()
    assert (await api.put(base + "/draft", headers=owner, json={**initial, "expected_version": 3})).json()[
        "error_code"
    ] == "BRAND_KIT_OPERATION_CONFLICT"
    assert (await api.put(base + "/draft", headers=owner, json=_draft(0))).json()[
        "error_code"
    ] == "BRAND_KIT_VERSION_CONFLICT"
    assert (await api.post(base + "/confirm", headers=owner, json={**confirm, "expected_version": 3})).json()[
        "error_code"
    ] == "BRAND_KIT_OPERATION_CONFLICT"
    missing_draft = await api.post(
        base + "/confirm", headers=owner, json={"operation_id": str(uuid4()), "expected_version": 2}
    )
    assert missing_draft.json()["error_code"] == "BRAND_KIT_DRAFT_REQUIRED"
    assert [row["version"] for row in (await api.get(base + "/history", headers=owner)).json()] == [3, 2, 1]

    proposal_base = f"/api/v1/organizations/{tenant}/businesses/{business}/editorial-proposals"
    proposal = await api.post(proposal_base, headers=owner, json={"operation_id": str(uuid4())})
    assert proposal.status_code == 202, proposal.text
    assert proposal.json()["brand_kit_version"] == 2
    async with admin.connect() as connection:
        row = (
            (
                await connection.execute(
                    text("SELECT brand_kit_version,brand_kit_document FROM editorial_proposals WHERE id=:id"),
                    {"id": proposal.json()["id"]},
                )
            )
            .mappings()
            .one()
        )
        assert row["brand_kit_version"] == 2
        assert row["brand_kit_document"]["overrides"]["tagline"] == ""
        brand_events = await connection.scalar(
            text("SELECT count(*) FROM outbox_events WHERE event_type='brand_kit.changed'")
        )
        assert brand_events == 3
    confirmed_edit = await api.post(
        base + "/confirm", headers=owner, json={"operation_id": str(uuid4()), "expected_version": 3}
    )
    assert confirmed_edit.status_code == 200, confirmed_edit.text
    assert confirmed_edit.json()["confirmed"]["version"] == 4
    later_proposal = await api.post(proposal_base, headers=owner, json={"operation_id": str(uuid4())})
    assert later_proposal.status_code == 202, later_proposal.text
    assert later_proposal.json()["brand_kit_version"] == 4
    async with admin.connect() as connection:
        snapshots = (
            (
                await connection.execute(
                    text("""SELECT brand_kit_version,brand_kit_document FROM editorial_proposals
                      WHERE id IN (:old,:new) ORDER BY brand_kit_version"""),
                    {"old": proposal.json()["id"], "new": later_proposal.json()["id"]},
                )
            )
            .mappings()
            .all()
        )
        assert [row["brand_kit_version"] for row in snapshots] == [2, 4]
        assert [row["brand_kit_document"]["overrides"]["tagline"] for row in snapshots] == ["", "Uma pausa especial"]
    async with database.transaction(seeded["t2"], seeded["a2"]) as session:
        assert await session.scalar(text("SELECT count(*) FROM business_brand_kit_versions")) == 0


async def test_kit_concurrent_drafts_only_one_wins(admin, api, seeded, settings):
    business = await _business(admin, seeded)
    base = f"/api/v1/organizations/{seeded['t1']}/businesses/{business}/brand-kit"
    owner = {"Authorization": f"Bearer {access_token(settings, seeded['a1'])}"}
    first, second = await asyncio.gather(
        api.put(base + "/draft", headers=owner, json=_draft(0)),
        api.put(base + "/draft", headers=owner, json=_draft(0)),
    )
    assert sorted([first.status_code, second.status_code]) == [200, 409]


class _Store:
    def __init__(self):
        self.objects = {}
        self.puts = 0

    async def put(self, key, media):
        self.puts += 1
        await asyncio.sleep(0)
        self.objects[key] = media.data

    async def signed_url(self, key, mime):
        assert key in self.objects and mime == "image/png"
        return f"https://storage.test/{key}"

    async def delete(self, key):
        self.objects.pop(key, None)


def _logo(color=(12, 40, 30, 220)):
    output = io.BytesIO()
    Image.new("RGBA", (16, 16), color).save(output, format="PNG")
    return base64.b64encode(output.getvalue()).decode()


async def test_logo_intent_replay_private_reference_and_concurrent_upload(admin, database, seeded, settings):
    business = await _business(admin, seeded)
    store = _Store()
    service = BrandKitService(settings, database, store)
    tenant, actor = seeded["t1"], seeded["a1"]
    body = BrandKitLogoUpload(
        operation_id=uuid4(), mime_type="image/png", content_base64=_logo(), rights_confirmed=True
    )
    first, second = await asyncio.gather(
        service.upload_logo(tenant, business, actor, body),
        service.upload_logo(tenant, business, actor, body),
    )
    assert first.id == second.id
    assert first.preview_url == second.preview_url
    assert await service.logo_url(tenant, business, actor, first.id)
    assert (await service.upload_logo(tenant, business, actor, body)).id == first.id
    assert len(store.objects) == 1
    with pytest.raises(AuthError, match="BRAND_KIT_OPERATION_CONFLICT"):
        await service.upload_logo(
            tenant,
            business,
            actor,
            body.model_copy(update={"content_base64": _logo((80, 20, 30, 220))}),
        )
    conflicting_operation = uuid4()
    divergent = [
        body.model_copy(update={"operation_id": conflicting_operation, "content_base64": _logo((20, 60, 90, 220))}),
        body.model_copy(update={"operation_id": conflicting_operation, "content_base64": _logo((90, 60, 20, 220))}),
    ]
    results = await asyncio.gather(
        *(service.upload_logo(tenant, business, actor, item) for item in divergent),
        return_exceptions=True,
    )
    assert sum(not isinstance(result, Exception) for result in results) == 1
    conflicts = [result for result in results if isinstance(result, AuthError)]
    assert len(conflicts) == 1 and conflicts[0].code == "BRAND_KIT_OPERATION_CONFLICT"
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await service.logo_url(seeded["t2"], business, seeded["a2"], first.id)
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM business_brand_kit_logos WHERE state='ready'")) == 2
        brand_events = await connection.scalar(
            text("SELECT count(*) FROM outbox_events WHERE event_type='brand_kit.changed'")
        )
        assert brand_events == 2


async def test_logo_pending_reconcile_is_owner_scoped(admin, database, seeded, settings):
    business = await _business(admin, seeded)
    tenant, actor, logo_id = seeded["t1"], seeded["a1"], uuid4()
    key = f"brand-kit-logos/{tenant}/{business}/{logo_id}.png"
    async with admin.begin() as connection:
        await connection.execute(
            text("""INSERT INTO business_brand_kit_logos
              (id,tenant_id,business_id,operation_id,actor_id,request_hash,object_key,
               sha256,mime_type,size_bytes,state,rights_scope,created_at,upload_lease_until)
              VALUES(:id,:tenant,:business,:operation,:actor,:hash,:key,:hash,'image/png',
                     3,'pending','business_brand_confirmed',now()-interval '2 hours',
                     now()-interval '1 hour')"""),
            {
                "id": logo_id,
                "tenant": tenant,
                "business": business,
                "operation": uuid4(),
                "actor": actor,
                "hash": "a" * 64,
                "key": key,
            },
        )
    store = _Store()
    store.objects[key] = b"old"
    service = BrandKitService(settings, database, store)
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await service.reconcile_pending_logos(seeded["t2"], business, seeded["a2"])
    assert await service.reconcile_pending_logos(tenant, business, actor) == 1
    assert key not in store.objects
    assert await service.reconcile_pending_logos(tenant, business, actor) == 0
    async with admin.connect() as connection:
        assert await connection.scalar(text("SELECT count(*) FROM business_brand_kit_logos")) == 0
        assert (
            await connection.scalar(text("SELECT count(*) FROM audit_events WHERE action='brand_kit.logo_reconciled'"))
            == 1
        )
