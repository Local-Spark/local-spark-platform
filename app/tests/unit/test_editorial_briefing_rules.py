"""Briefing revocation, source integrity and stale-state failures; no database/network."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.schemas.editorial_proposals import ProposalRead
from app.services.auth import AuthError
from app.services.editorial_briefings import EditorialBriefingService
from app.services.editorial_proposals import EditorialProposalService


def mapped(row):
    result = MagicMock()
    result.mappings.return_value.one_or_none.return_value = row
    return result


class MemoryDatabase:
    def __init__(self, session):
        self.session = session

    @asynccontextmanager
    async def transaction(self, *args):
        yield self.session


@pytest.fixture
def ids():
    return [uuid4() for _ in range(5)]


def test_digest_is_missing_without_message_or_encryption_key(settings):
    service = EditorialBriefingService(settings.model_copy(update={"meta_encryption_key": None}), MagicMock())
    assert service._source_digest("mensagem") is None
    assert service._source_digest(None) is None
    configured = settings.model_copy(update={"meta_encryption_key": SecretStr("test-key")})
    service = EditorialBriefingService(configured, MagicMock())
    assert service._source_digest(None) is None
    assert service._source_digest("mensagem") != service._source_digest("outra")


async def test_prepare_rejects_snapshot_changed_during_interpretation(settings, ids, monkeypatch):
    tenant, business, actor, source, operation = ids
    briefing = uuid4()

    async def execute(statement, params=None):
        sql = str(statement)
        if "INSERT INTO editorial_briefings" in sql:
            return mapped({"id": briefing})
        if "UPDATE editorial_briefings" in sql:
            assert params["state"] == "needs_clarification"
            assert params["snapshot"] is None
            return mapped({"id": briefing, "state": "needs_clarification"})
        return mapped(None)

    session = SimpleNamespace(execute=AsyncMock(side_effect=execute))
    database = MemoryDatabase(session)
    interpreter = SimpleNamespace(interpret=AsyncMock())
    service = EditorialBriefingService(settings, database, interpreter)
    monkeypatch.setattr(service, "_source", AsyncMock(return_value="Crie croissant"))
    monkeypatch.setattr(
        "app.services.editorial_briefings.resolve_catalog_context",
        AsyncMock(return_value=SimpleNamespace(status="resolved", snapshot={"catalog_version": 1})),
    )
    monkeypatch.setattr(
        "app.services.editorial_briefings.validate_catalog_snapshot", AsyncMock(return_value="catalog_changed")
    )
    result = await service.prepare(tenant, business, actor, source, operation)
    assert result.id == briefing and result.state == "needs_clarification"


async def test_read_valid_denies_revoked_or_missing_source(settings, ids, monkeypatch):
    tenant, business, actor, source, briefing = ids
    row = {"id": briefing, "source_asset_id": source, "source_digest": "x", "state": "prepared", "catalog_snapshot": {}}
    session = SimpleNamespace(execute=AsyncMock(return_value=mapped(row)))
    service = EditorialBriefingService(settings, MemoryDatabase(session))
    monkeypatch.setattr("app.services.whatsapp_materials.WhatsAppMaterialsService._require_owner", AsyncMock())
    monkeypatch.setattr(service, "_source", AsyncMock(side_effect=AuthError("MATERIAL_NOT_FOUND", 404)))
    assert await service.read_valid(session, tenant, business, actor, briefing) == ("unavailable", None)


@pytest.mark.parametrize(
    "state,expected",
    [("needs_clarification", "needs_clarification"), ("uncertain", "unavailable"), ("submitted", "unavailable")],
)
async def test_read_valid_never_reads_sources_for_incomplete_briefings(settings, ids, monkeypatch, state, expected):
    tenant, business, actor, source, briefing = ids
    row = {"id": briefing, "source_asset_id": source, "source_digest": None, "state": state, "catalog_snapshot": None}
    session = SimpleNamespace(execute=AsyncMock(return_value=mapped(row)))
    service = EditorialBriefingService(settings, MemoryDatabase(session))
    monkeypatch.setattr("app.services.whatsapp_materials.WhatsAppMaterialsService._require_owner", AsyncMock())
    source_check = AsyncMock()
    monkeypatch.setattr(service, "_source", source_check)
    assert await service.read_valid(session, tenant, business, actor, briefing) == (expected, None)
    source_check.assert_not_awaited()


@pytest.mark.parametrize(
    "briefing_id,required,environment,expected",
    [
        (None, False, "testing", None),
        (None, True, "testing", "unavailable"),
        (uuid4(), True, "production", "unavailable"),
    ],
)
async def test_proposal_presentation_fails_closed_when_briefing_missing_or_not_supported(
    settings, ids, monkeypatch, briefing_id, required, environment, expected
):
    tenant, business, actor, _, _ = ids
    monkeypatch.setattr(
        "app.services.editorial_proposals._present", lambda row: ProposalRead.model_construct(id=uuid4())
    )
    service = EditorialProposalService(settings.model_copy(update={"environment": environment}), MagicMock())
    shown = await service._present_with_briefing(
        MagicMock(), {"briefing_id": briefing_id, "briefing_required": required}, tenant, business, actor
    )
    if expected is None:
        assert shown.briefing is None
    else:
        assert shown.briefing.status == expected


@pytest.mark.parametrize("status", ["needs_clarification", "context_changed", "unavailable"])
async def test_proposal_presentation_shows_nonprepared_state(settings, ids, monkeypatch, status):
    tenant, business, actor, _, briefing = ids
    monkeypatch.setattr(
        "app.services.editorial_proposals._present", lambda row: ProposalRead.model_construct(id=uuid4())
    )
    monkeypatch.setattr(EditorialBriefingService, "read_valid", AsyncMock(return_value=(status, None)))
    shown = await EditorialProposalService(settings, MagicMock())._present_with_briefing(
        MagicMock(), {"briefing_id": briefing}, tenant, business, actor
    )
    assert shown.briefing.status == status and shown.briefing.offering is None


async def test_proposal_presentation_only_reveals_safe_catalog_summary(settings, ids, monkeypatch):
    tenant, business, actor, _, briefing = ids
    monkeypatch.setattr(
        "app.services.editorial_proposals._present", lambda row: ProposalRead.model_construct(id=uuid4())
    )
    snapshot = {
        "offering": {"name": "Croissant", "kind": "product", "description": "dado privado"},
        "item_photo": {"id": "private"},
        "space_photo": None,
    }
    monkeypatch.setattr(EditorialBriefingService, "read_valid", AsyncMock(return_value=("prepared", snapshot)))
    shown = await EditorialProposalService(settings, MagicMock())._present_with_briefing(
        MagicMock(),
        {"briefing_id": briefing, "brand_kit_document": {"overrides": {"brand_name": "Café"}}},
        tenant,
        business,
        actor,
    )
    assert shown.briefing.offering.name == "Croissant"
    assert shown.briefing.brand_name == "Café" and shown.briefing.has_item_photo and not shown.briefing.has_space_photo
    assert "dado privado" not in str(shown.briefing)


@pytest.mark.parametrize(
    "status,snapshot,source_matches",
    [
        ("context_changed", None, True),
        ("prepared", None, True),
        ("prepared", {"offering": {}}, False),
    ],
)
async def test_proposal_rejects_unready_or_foreign_source_briefing(
    settings, ids, monkeypatch, status, snapshot, source_matches
):
    from app.schemas.editorial_proposals import ProposalRequest

    tenant, business, actor, source, operation = ids
    briefing = uuid4()
    session = SimpleNamespace(
        execute=AsyncMock(return_value=mapped(None)),
        scalar=AsyncMock(side_effect=[True, True, source if source_matches else uuid4()]),
    )
    database = MemoryDatabase(session)
    monkeypatch.setattr("app.services.whatsapp_materials.WhatsAppMaterialsService._require_owner", AsyncMock())
    monkeypatch.setattr(EditorialBriefingService, "read_valid", AsyncMock(return_value=(status, snapshot)))
    with pytest.raises(AuthError, match="BRIEFING_NOT_READY"):
        await EditorialProposalService(settings, database).request(
            tenant,
            business,
            actor,
            ProposalRequest(operation_id=operation, source_asset_id=source),
            briefing_id=briefing,
        )


def context_row(ids):
    return {
        "source_asset_id": None,
        "tenant_id": ids[0],
        "business_id": ids[1],
        "actor_id": ids[2],
        "context_version": 1,
        "briefing_id": ids[3],
        "briefing_required": True,
    }


def confirmed_context():
    return {
        "facts": [{"id": str(uuid4()), "kind": "product", "statement": "Croissant", "source_detail": "Dono confirmou"}],
        "preferences": {},
    }


@pytest.mark.parametrize("owner_available,environment", [(False, "testing"), (True, "production")])
async def test_proposal_inputs_block_briefing_without_owner_database_or_in_production(
    settings, ids, owner_available, environment
):
    session = SimpleNamespace(scalar=AsyncMock(return_value=confirmed_context()))
    owner = MemoryDatabase(session) if owner_available else None
    service = EditorialProposalService(
        settings.model_copy(update={"environment": environment}), MagicMock(), owner_database=owner
    )
    assert await service._inputs(session, context_row(ids)) is None


@pytest.mark.parametrize("status,snapshot", [("context_changed", None), ("prepared", None)])
async def test_proposal_inputs_reject_unavailable_or_inconsistent_briefing(
    settings, ids, monkeypatch, status, snapshot
):
    session = SimpleNamespace(scalar=AsyncMock(return_value=confirmed_context()))
    owner = MemoryDatabase(session)
    monkeypatch.setattr(EditorialBriefingService, "read_valid", AsyncMock(return_value=(status, snapshot)))
    service = EditorialProposalService(settings, MagicMock(), owner_database=owner)
    assert await service._inputs(session, context_row(ids)) is None
