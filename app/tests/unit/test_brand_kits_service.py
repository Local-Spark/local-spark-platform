"""BL02 service decisions exercised without SQLAlchemy's async greenlet tracer."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.adapters.material_media import FetchedMedia, MaterialError
from app.schemas.brand_kits import BrandKitConfirmRequest, BrandKitDraftRequest, BrandKitLogoUpload, BrandKitState
from app.schemas.editorial_proposals import ProposalRequest
from app.services import brand_kits as kits
from app.services.auth import AuthError
from app.services.editorial_proposals import EditorialProposalService
from app.services.whatsapp_materials import WhatsAppMaterialsService


class Rows:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = rows or []

    def mappings(self):
        return self

    def one_or_none(self):
        return self.row

    def all(self):
        return self.rows


class Session:
    def __init__(self, *, results=(), scalars=()):
        self.results = iter(results)
        self.scalars = iter(scalars)
        self.statements = []

    async def execute(self, statement, params=None):
        self.statements.append((str(statement), params))
        return next(self.results, Rows())

    async def scalar(self, statement, params=None):
        self.statements.append((str(statement), params))
        return next(self.scalars, None)


class Database:
    def __init__(self, session):
        self.session = session

    @asynccontextmanager
    async def transaction(self, tenant, actor):
        yield self.session


def _service(session=None, *, environment="testing", store=None):
    session = session or Session()
    store = store or SimpleNamespace(
        put=AsyncMock(), signed_url=AsyncMock(return_value="https://private.invalid/logo"), delete=AsyncMock()
    )
    service = kits.BrandKitService(SimpleNamespace(environment=environment), Database(session), store)
    return service, session, store


def _draft(*, logo=None):
    overrides = kits._default_overrides("Café da Ana", kits._manifest())
    if logo is not None:
        overrides = overrides.model_copy(update={"logo_asset_id": logo})
    return BrandKitDraftRequest(
        operation_id=uuid4(), expected_version=0, kit_id=kits.KIT_ID, kit_version=1, overrides=overrides
    )


def _logo():
    return BrandKitLogoUpload(
        operation_id=uuid4(), mime_type="image/png", content_base64="A" * 16, rights_confirmed=True
    )


def _row(version=1, state="draft"):
    return {
        "version": version,
        "state": state,
        "document": {
            "kit_id": kits.KIT_ID,
            "kit_version": 1,
            "overrides": kits._default_overrides("Café da Ana", kits._manifest()).model_dump(mode="json"),
        },
        "created_at": datetime.now(UTC),
    }


def _ids():
    return uuid4(), uuid4(), uuid4()


def _owner(monkeypatch):
    monkeypatch.setattr(kits.BrandKitService, "_owner", AsyncMock())


async def test_empty_kit_state_and_versioned_history(monkeypatch):
    _owner(monkeypatch)
    tenant, business, actor = _ids()
    service, _, _ = _service(Session(results=[Rows()]))
    assert await service.read(tenant, business, actor) == BrandKitState(head_version=0)
    session = Session(
        results=[
            Rows({"version": 3, "confirmed_version": 2}),
            Rows(rows=[_row(3, "draft"), _row(2, "confirmed")]),
            Rows(rows=[_row(3, "draft"), _row(2, "confirmed")]),
        ]
    )
    service, _, _ = _service(session)
    state = await service.read(tenant, business, actor)
    assert (state.head_version, state.draft.version, state.confirmed.version) == (3, 3, 2)
    assert [(item.version, item.state) for item in await service.history(tenant, business, actor)] == [
        (3, "draft"),
        (2, "confirmed"),
    ]


@pytest.mark.parametrize(
    "row,expected",
    [
        (None, None),
        ({"request_hash": "other", "response": None}, "BRAND_KIT_OPERATION_CONFLICT"),
        ({"request_hash": "same", "response": None}, "BRAND_KIT_OPERATION_INCOMPLETE"),
        ({"request_hash": "same", "response": {"head_version": 4}}, 4),
    ],
)
async def test_replay_returns_exact_response_or_explicit_error(row, expected):
    session = Session(results=[Rows(row)])
    tenant, business, _ = _ids()
    if isinstance(expected, str):
        with pytest.raises(AuthError) as failure:
            await kits.BrandKitService._replay(session, tenant, business, uuid4(), "same")
        assert failure.value.code == expected
    else:
        result = await kits.BrandKitService._replay(session, tenant, business, uuid4(), "same")
        assert (result.head_version if result else None) == expected


async def test_draft_replay_and_public_demo_gate(monkeypatch):
    _owner(monkeypatch)
    body, (tenant, business, actor) = _draft(), _ids()
    replay = BrandKitState(head_version=7)
    monkeypatch.setattr(kits.BrandKitService, "_replay", AsyncMock(return_value=replay))
    service, _, _ = _service()
    assert await service.draft(tenant, business, actor, body) == replay
    monkeypatch.setattr(kits.BrandKitService, "_replay", AsyncMock(return_value=None))
    service, _, _ = _service(environment="production")
    with pytest.raises(AuthError) as failure:
        await service.draft(tenant, business, actor, body)
    assert failure.value.code == "BRAND_KIT_NOT_SELECTABLE"


async def test_draft_requires_ready_logo_and_cas(monkeypatch):
    _owner(monkeypatch)
    monkeypatch.setattr(kits.BrandKitService, "_replay", AsyncMock(return_value=None))
    tenant, business, actor = _ids()
    service, _, _ = _service(Session(scalars=[None]))
    with pytest.raises(AuthError) as failure:
        await service.draft(tenant, business, actor, _draft(logo=uuid4()))
    assert failure.value.code == "BRAND_KIT_LOGO_NOT_FOUND"
    service, _, _ = _service(Session(scalars=[None]))
    with pytest.raises(AuthError) as failure:
        await service.draft(tenant, business, actor, _draft())
    assert failure.value.code == "BRAND_KIT_VERSION_CONFLICT"


async def test_draft_cas_race_replays_winner_and_success_saves_response(monkeypatch):
    _owner(monkeypatch)
    tenant, business, actor = _ids()
    state = BrandKitState(head_version=1)
    replay = AsyncMock(side_effect=[None, state])
    monkeypatch.setattr(kits.BrandKitService, "_replay", replay)
    service, _, _ = _service(Session(scalars=[None]))
    assert await service.draft(tenant, business, actor, _draft()) == state
    monkeypatch.setattr(kits.BrandKitService, "_replay", AsyncMock(return_value=None))
    monkeypatch.setattr(kits.BrandKitService, "_state", AsyncMock(return_value=state))
    record, save = AsyncMock(), AsyncMock()
    monkeypatch.setattr(kits.BrandKitService, "_record", record)
    monkeypatch.setattr(kits.BrandKitService, "_save_response", save)
    service, _, _ = _service(Session(scalars=[1]))
    assert await service.draft(tenant, business, actor, _draft()) == state
    record.assert_awaited_once()
    save.assert_awaited_once()


async def test_confirm_requires_a_real_draft_and_cas(monkeypatch):
    _owner(monkeypatch)
    tenant, business, actor = _ids()
    body = BrandKitConfirmRequest(operation_id=uuid4(), expected_version=1)
    monkeypatch.setattr(kits.BrandKitService, "_replay", AsyncMock(return_value=BrandKitState(head_version=2)))
    service, _, _ = _service()
    assert (await service.confirm(tenant, business, actor, body)).head_version == 2
    monkeypatch.setattr(kits.BrandKitService, "_replay", AsyncMock(return_value=None))
    service, _, _ = _service(environment="production")
    with pytest.raises(AuthError) as failure:
        await service.confirm(tenant, business, actor, body)
    assert failure.value.code == "BRAND_KIT_NOT_SELECTABLE"
    for row in (None, {"state": "confirmed", "document": {}}):
        service, _, _ = _service(Session(results=[Rows(row)]))
        with pytest.raises(AuthError) as failure:
            await service.confirm(tenant, business, actor, body)
        assert failure.value.code == "BRAND_KIT_DRAFT_REQUIRED"
    service, _, _ = _service(
        Session(results=[Rows({"state": "draft", "document": _row()["document"]})], scalars=[None])
    )
    with pytest.raises(AuthError) as failure:
        await service.confirm(tenant, business, actor, body)
    assert failure.value.code == "BRAND_KIT_VERSION_CONFLICT"


async def test_confirm_cas_replay_and_success(monkeypatch):
    _owner(monkeypatch)
    tenant, business, actor = _ids()
    body = BrandKitConfirmRequest(operation_id=uuid4(), expected_version=1)
    state = BrandKitState(head_version=2)
    monkeypatch.setattr(kits.BrandKitService, "_replay", AsyncMock(side_effect=[None, state]))
    session = Session(results=[Rows({"state": "draft", "document": _row()["document"]})], scalars=[None])
    service, _, _ = _service(session)
    assert await service.confirm(tenant, business, actor, body) == state
    monkeypatch.setattr(kits.BrandKitService, "_replay", AsyncMock(return_value=None))
    monkeypatch.setattr(kits.BrandKitService, "_state", AsyncMock(return_value=state))
    monkeypatch.setattr(kits.BrandKitService, "_record", AsyncMock())
    monkeypatch.setattr(kits.BrandKitService, "_save_response", AsyncMock())
    session = Session(results=[Rows({"state": "draft", "document": _row()["document"]})], scalars=[2])
    service, _, _ = _service(session)
    assert await service.confirm(tenant, business, actor, body) == state


async def test_logo_rejects_unavailable_demo_and_deleted_intent(monkeypatch):
    _owner(monkeypatch)
    tenant, business, actor = _ids()
    service, _, _ = _service(environment="production")
    with pytest.raises(AuthError) as failure:
        await service.upload_logo(tenant, business, actor, _logo())
    assert failure.value.code == "BRAND_KIT_NOT_SELECTABLE"
    monkeypatch.setattr(kits.BrandKitService, "reconcile_pending_logos", AsyncMock(return_value=0))
    monkeypatch.setattr(kits, "_normalize_logo", lambda body: (FetchedMedia(b"one", "image/png", "a" * 64), "b" * 64))
    body = _logo()
    row = {
        "id": uuid4(),
        "request_hash": kits._digest({"sha256": "b" * 64, "mime_type": "image/png", "rights_confirmed": True}),
        "object_key": "private/logo.png",
        "mime_type": "image/png",
        "state": "deleting",
    }
    service, _, _ = _service(Session(results=[Rows(row)]))
    with pytest.raises(AuthError) as failure:
        await service.upload_logo(tenant, business, actor, body)
    assert failure.value.code == "BRAND_KIT_LOGO_EXPIRED"


async def test_logo_conflicting_insert_and_expired_reservation(monkeypatch):
    _owner(monkeypatch)
    monkeypatch.setattr(kits.BrandKitService, "reconcile_pending_logos", AsyncMock(return_value=0))
    monkeypatch.setattr(kits, "_normalize_logo", lambda body: (FetchedMedia(b"one", "image/png", "a" * 64), "b" * 64))
    tenant, business, actor = _ids()
    body = _logo()
    # A concurrent request can win the deterministic PK before this insert.
    service, _, _ = _service(
        Session(results=[Rows(), Rows({"request_hash": "different", "state": "ready"})], scalars=[None])
    )
    with pytest.raises(AuthError) as failure:
        await service.upload_logo(tenant, business, actor, body)
    assert failure.value.code == "BRAND_KIT_OPERATION_CONFLICT"
    row = {
        "id": uuid4(),
        "request_hash": kits._digest({"sha256": "b" * 64, "mime_type": "image/png", "rights_confirmed": True}),
        "object_key": "private/logo.png",
        "mime_type": "image/png",
        "state": "pending",
    }
    service, _, _ = _service(Session(results=[Rows(row)], scalars=[None]))
    with pytest.raises(AuthError) as failure:
        await service.upload_logo(tenant, business, actor, body)
    assert failure.value.code == "BRAND_KIT_LOGO_EXPIRED"


@pytest.mark.parametrize("state,expected", [("ready", None), ("deleting", "BRAND_KIT_LOGO_EXPIRED")])
async def test_logo_insert_conflict_reads_committed_winner(monkeypatch, state, expected):
    _owner(monkeypatch)
    monkeypatch.setattr(kits.BrandKitService, "reconcile_pending_logos", AsyncMock(return_value=0))
    monkeypatch.setattr(kits, "_normalize_logo", lambda body: (FetchedMedia(b"one", "image/png", "a" * 64), "b" * 64))
    tenant, business, actor = _ids()
    body = _logo()
    row = {
        "id": uuid4(),
        "request_hash": kits._digest({"sha256": "b" * 64, "mime_type": "image/png", "rights_confirmed": True}),
        "object_key": "private/winner.png",
        "mime_type": "image/png",
        "state": state,
    }
    # Initial SELECT misses while the other transaction is committing; INSERT conflicts, then reselect sees it.
    service, _, store = _service(Session(results=[Rows(), Rows(row)], scalars=[None]))
    if expected is None:
        assert (await service.upload_logo(tenant, business, actor, body)).id == row["id"]
        store.put.assert_not_awaited()
    else:
        with pytest.raises(AuthError) as failure:
            await service.upload_logo(tenant, business, actor, body)
        assert failure.value.code == expected


async def test_new_logo_intent_uploads_once_and_becomes_ready(monkeypatch):
    _owner(monkeypatch)
    monkeypatch.setattr(kits.BrandKitService, "reconcile_pending_logos", AsyncMock(return_value=0))
    monkeypatch.setattr(kits, "_normalize_logo", lambda body: (FetchedMedia(b"one", "image/png", "a" * 64), "b" * 64))
    record = AsyncMock()
    monkeypatch.setattr(kits.BrandKitService, "_record", record)
    tenant, business, actor = _ids()
    session = Session(results=[Rows()], scalars=[uuid4(), uuid4(), uuid4()])
    service, _, store = _service(session)
    result = await service.upload_logo(tenant, business, actor, _logo())
    assert result.preview_url == "https://private.invalid/logo"
    store.put.assert_awaited_once()
    record.assert_awaited_once()


async def test_logo_ready_replay_and_finalize_race(monkeypatch):
    _owner(monkeypatch)
    monkeypatch.setattr(kits.BrandKitService, "reconcile_pending_logos", AsyncMock(return_value=0))
    monkeypatch.setattr(kits, "_normalize_logo", lambda body: (FetchedMedia(b"one", "image/png", "a" * 64), "b" * 64))
    tenant, business, actor = _ids()
    body = _logo()
    row = {
        "id": uuid4(),
        "request_hash": kits._digest({"sha256": "b" * 64, "mime_type": "image/png", "rights_confirmed": True}),
        "object_key": "private/logo.png",
        "mime_type": "image/png",
        "state": "ready",
    }
    service, _, store = _service(Session(results=[Rows(row)]))
    assert (await service.upload_logo(tenant, business, actor, body)).id == row["id"]
    store.put.assert_not_awaited()
    row["state"] = "pending"
    service, _, store = _service(Session(results=[Rows(row)], scalars=[row["id"], None, None]))
    with pytest.raises(AuthError) as failure:
        await service.upload_logo(tenant, business, actor, body)
    assert failure.value.code == "BRAND_KIT_LOGO_NOT_READY"
    store.put.assert_awaited_once()


async def test_logo_missing_reference_and_cleanup_failures(monkeypatch):
    _owner(monkeypatch)
    tenant, business, actor = _ids()
    service, _, _ = _service(Session(results=[Rows()]))
    with pytest.raises(AuthError) as failure:
        await service.logo_url(tenant, business, actor, uuid4())
    assert failure.value.code == "BRAND_KIT_LOGO_NOT_FOUND"
    first, second = uuid4(), uuid4()
    rows = [
        {"id": first, "object_key": "private/one", "delete_fencing_token": 2},
        {"id": second, "object_key": "private/two", "delete_fencing_token": 3},
    ]
    store = SimpleNamespace(delete=AsyncMock(side_effect=[MaterialError("unavailable"), None]))
    service, _, _ = _service(Session(results=[Rows(rows=rows)], scalars=[None]), store=store)
    assert await service.reconcile_pending_logos(tenant, business, actor) == 0
    assert store.delete.await_count == 2


async def test_editorial_proposal_blocks_demo_kit_in_production(monkeypatch):
    monkeypatch.setattr(WhatsAppMaterialsService, "_require_owner", AsyncMock())
    tenant, business, actor = _ids()
    session = Session(
        results=[Rows(), Rows({"version": 2, "document": _row(2, "confirmed")["document"]})],
        scalars=[True, 0],
    )
    settings = SimpleNamespace(environment="production", editorial_ai_mode="deterministic")
    service = EditorialProposalService(settings, Database(session), provider=object())
    with pytest.raises(AuthError) as failure:
        await service.request(tenant, business, actor, ProposalRequest(operation_id=uuid4()))
    assert failure.value.code == "BRAND_KIT_NOT_APPROVED"


@pytest.mark.parametrize("environment,expected", [("testing", "snapshot"), ("production", "blocked")])
async def test_editorial_worker_uses_frozen_brand_text_and_demo_gate(monkeypatch, environment, expected):
    tenant, business, _ = _ids()
    service = EditorialProposalService(
        SimpleNamespace(environment=environment, meta_encryption_key=None), Database(Session()), provider=object()
    )
    monkeypatch.setattr(service, "_source", lambda asset: "Crie um post do café")
    row = {
        "tenant_id": tenant,
        "business_id": business,
        "source_asset_id": uuid4(),
        "context_version": 0,
        "brand_kit_version": 2,
        "brand_kit_document": _row(2, "confirmed")["document"],
    }
    session = Session(results=[Rows({"kind": "text"})])
    result = await service._inputs(session, row)
    if expected == "blocked":
        assert result is None
    else:
        assert result is not None
        brand = result[0]["brand_kit"]
        assert brand["applied_version"] == 2
        assert brand["brand_name"] == "Café da Ana"
        assert brand["cta"] == "Saiba mais"
        assert brand["formats"]["feed"]["layout"] == "photo_focus"
