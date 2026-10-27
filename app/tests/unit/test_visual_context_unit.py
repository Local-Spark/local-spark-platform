"""The capture checks live consent/context and never calls a media provider."""

from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import SecretStr

from app.services.auth import AuthError
from app.services.visual_context import VisualContextService


class Database:
    def __init__(self, session):
        self.session = session
        self.calls = []

    @asynccontextmanager
    async def transaction(self, tenant, actor):
        self.calls.append((tenant, actor))
        yield self.session


class Session:
    def __init__(self, proposal, kit, source):
        self.proposal, self.kit, self.source = proposal, kit, source
        self.consent, self.source_kind, self.context_version, self.logo_hash = True, "text", 0, "logo-hash"
        self.source_image_hash = "a" * 64
        self.consent_dates = {
            "whatsapp_processing_consents": "w1",
            "intent_jev_consents": "j1",
            "editorial_ai_consents": "e1",
            "whatsapp_channel_links": "l1",
        }

    async def scalar(self, statement, params):
        sql = str(statement)
        if "visual_ai_consents" in sql:
            return self.consent
        for name, value in self.consent_dates.items():
            if name in sql:
                return value
        if "FROM editorial_briefings" in sql:
            return self.source
        if "whatsapp_material_assets" in sql:
            return self.source_image_hash if "SELECT sha256" in sql else self.source_kind
        if "business_context_heads" in sql:
            return self.context_version
        if "business_brand_kit_logos" in sql:
            return self.logo_hash
        raise AssertionError(sql)

    async def execute(self, statement, params):
        sql = str(statement)
        if "FROM editorial_proposals" in sql:
            row = self.proposal
        elif "FROM business_brand_kit_heads" in sql:
            row = self.kit
        else:
            raise AssertionError(sql)
        return SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: row))


@pytest.fixture
def setup_case(settings, monkeypatch):
    ids = [uuid4() for _ in range(6)]
    tenant, business, actor, proposal_id, briefing_id, source = ids
    document = {
        "title": "Uma ideia",
        "format": "photo",
        "angle": "Apresentar o produto",
        "fact_ids": [],
        "hypotheses": [],
        "questions": [],
        "script": [],
    }
    kit_doc = {"kit_id": "cafe-pausas", "overrides": {"logo_asset_id": None}}
    proposal = {
        "id": proposal_id,
        "state": "completed",
        "document": document,
        "review_state": "accepted",
        "expires_at": datetime.now(UTC) + timedelta(hours=1),
        "briefing_required": True,
        "briefing_id": briefing_id,
        "source_asset_id": source,
        "brand_kit_version": 1,
        "brand_kit_document": kit_doc,
        "context_version": 0,
        "script_version": 1,
    }
    session = Session(proposal, {"version": 1, "document": kit_doc}, source)
    database = Database(session)
    cfg = settings.model_copy(update={"visual_ai_mode": "openai", "meta_encryption_key": SecretStr("test-key")})
    owner = AsyncMock()
    briefing = AsyncMock(return_value=("prepared", {"catalog_version": 1, "offering": {"name": "Croissant"}}))
    monkeypatch.setattr("app.services.visual_context.WhatsAppMaterialsService._require_owner", owner)
    monkeypatch.setattr("app.services.visual_context.EditorialBriefingService.read_valid", briefing)
    return SimpleNamespace(
        ids=ids,
        session=session,
        db=database,
        service=VisualContextService(cfg, database),
        owner=owner,
        briefing=briefing,
        cfg=cfg,
    )


async def test_capture_is_owner_scoped_and_only_exposes_ids_and_keyed_fingerprint(setup_case):
    c = setup_case
    tenant, business, actor, proposal, briefing, source = c.ids
    result = await c.service.capture(tenant, business, actor, proposal)
    assert (result.tenant_id, result.business_id, result.briefing_id, result.source_asset_id) == (
        tenant,
        business,
        briefing,
        source,
    )
    assert result.format == "photo" and len(result.fingerprint) == 64
    assert "Croissant" not in repr(result) and "Uma ideia" not in repr(result)
    assert c.db.calls == [(tenant, actor)]
    c.owner.assert_awaited_once_with(c.session, tenant, business, actor)
    c.briefing.assert_awaited_once()
    # Changing content changes the HMAC without returning that content.
    c.session.proposal["document"]["title"] = "Outra ideia"
    changed = await c.service.capture(tenant, business, actor, proposal)
    assert result.fingerprint != changed.fingerprint


@pytest.mark.parametrize(
    "changed",
    [
        "visual_ai_consents",
        "whatsapp_processing_consents",
        "intent_jev_consents",
        "editorial_ai_consents",
        "whatsapp_channel_links",
    ],
)
async def test_withdraw_and_regrant_or_relink_invalidates_old_fingerprint(setup_case, changed):
    c = setup_case
    before = await c.service.capture(*c.ids[:4])
    if changed == "visual_ai_consents":
        c.session.consent = "new grant"
    else:
        c.session.consent_dates[changed] = "new grant"
    after = await c.service.capture(*c.ids[:4])
    assert before.fingerprint != after.fingerprint


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        ("no_consent", "VISUAL_AI_CONSENT_REQUIRED"),
        ("no_proposal", "PROPOSAL_NOT_FOUND"),
        ("not_accepted", "PREVIEW_SCRIPT_NOT_ACCEPTED"),
        ("expired", "PREVIEW_SCRIPT_EXPIRED"),
        ("no_briefing", "VISUAL_BRIEFING_REQUIRED"),
        ("video", "VISUAL_FORMAT_UNSUPPORTED"),
        ("briefing_changed", "VISUAL_BRIEFING_CHANGED"),
        ("source_changed", "VISUAL_SOURCE_CHANGED"),
        ("image", "VISUAL_SOURCE_NOT_NORMALIZED"),
        ("kit_changed", "VISUAL_KIT_CHANGED"),
        ("context_changed", "VISUAL_CONTEXT_CHANGED"),
        ("logo_changed", "VISUAL_LOGO_CHANGED"),
    ],
)
async def test_capture_fails_closed(setup_case, mutation, code):
    c = setup_case
    s, p = c.session, c.session.proposal
    if mutation == "no_consent":
        s.consent = False
    if mutation == "no_proposal":
        s.proposal = None
    if mutation == "not_accepted":
        p["review_state"] = None
    if mutation == "expired":
        p["expires_at"] = datetime.now(UTC) - timedelta(seconds=1)
    if mutation == "no_briefing":
        p["briefing_required"] = False
    if mutation == "video":
        p["document"]["format"] = "short_video"
    if mutation == "briefing_changed":
        c.briefing.return_value = ("context_changed", None)
    if mutation == "source_changed":
        s.source = uuid4()
    if mutation == "image":
        s.source_kind = "video"
    if mutation == "kit_changed":
        s.kit = None
    if mutation == "context_changed":
        s.context_version = 1
    if mutation == "logo_changed":
        p["brand_kit_document"]["overrides"]["logo_asset_id"] = str(uuid4())
        s.logo_hash = None
    with pytest.raises(AuthError) as exc:
        await c.service.capture(*c.ids[:4])
    assert exc.value.code == code


async def test_candidate_and_configuration_guards(setup_case):
    c = setup_case
    c.session.proposal["review_state"] = None
    assert (await c.service.capture(*c.ids[:4], candidate=True)).format == "photo"
    c.service.settings = c.cfg.model_copy(update={"visual_ai_mode": "disabled"})
    with pytest.raises(AuthError, match="VISUAL_AI_DISABLED"):
        await c.service.capture(*c.ids[:4])
    c.service.settings = c.cfg.model_copy(update={"meta_encryption_key": None})
    with pytest.raises(AuthError, match="VISUAL_CONTEXT_KEY_REQUIRED"):
        await c.service.capture(*c.ids[:4])


async def test_capture_includes_current_authorized_logo_hash(setup_case):
    c = setup_case
    c.session.proposal["brand_kit_document"]["overrides"]["logo_asset_id"] = str(uuid4())
    before = await c.service.capture(*c.ids[:4])
    c.session.logo_hash = "different-logo-hash"
    after = await c.service.capture(*c.ids[:4])
    assert before.fingerprint != after.fingerprint


async def test_capture_binds_whatsapp_image_hash_and_requires_ready_source(setup_case):
    c = setup_case
    c.session.source_kind = "image"
    before = await c.service.capture(*c.ids[:4])
    c.session.source_image_hash = "b" * 64
    assert before.fingerprint != (await c.service.capture(*c.ids[:4])).fingerprint
    c.session.source_image_hash = None
    with pytest.raises(AuthError, match="VISUAL_SOURCE_NOT_READY"):
        await c.service.capture(*c.ids[:4])
