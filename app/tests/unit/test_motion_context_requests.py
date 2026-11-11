"""Private factual projection and fail-closed request guards at service boundaries."""

import json
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4, uuid5

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr

from app.schemas.brand_kits import BrandKitState, BrandKitVersion
from app.schemas.editorial_context import ConfirmedFact, ContextRead
from app.schemas.motion_production import MotionRequest
from app.services import motion_context as context_module
from app.services.auth import AuthError
from app.services.motion_context import MotionContext
from app.services.motion_requests import MotionRequestService
from app.services.reference_generation_context import ReferenceGenerationSnapshot
from app.tests.unit.test_motion_direction_input import kit


def result(value):
    return SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: value, all=lambda: value))


@pytest.fixture
def context_case(settings, monkeypatch):
    tenant, business, source, logo = (uuid4() for _ in range(4))
    body = MotionRequest(operation_id=uuid4(), source_asset_id=source, instruction="Synthetic request")
    version = BrandKitVersion(
        version=4,
        state="confirmed",
        kit_id="synthetic",
        kit_version=1,
        overrides=kit(logo),
        created_at=datetime(2026, 11, 1, tzinfo=UTC),
    )
    state = AsyncMock(return_value=BrandKitState(head_version=4, confirmed=version))
    monkeypatch.setattr(context_module.BrandKitService, "_state", state)
    context = ContextRead(
        version=7,
        facts=[
            ConfirmedFact(
                id=uuid4(),
                kind="price",
                statement="Preço vigente fictício",
                source_detail="Private provenance",
                valid_until=date(2026, 11, 10),
            ),
            ConfirmedFact(
                id=uuid4(),
                kind="offer",
                statement="Oferta antiga fictícia",
                source_detail="Private provenance",
                valid_until=date(2026, 11, 8),
            ),
            ConfirmedFact(
                id=uuid4(), kind="other", statement="Fato permanente fictício", source_detail="Private provenance"
            ),
        ],
    )
    monkeypatch.setattr(context_module.EditorialContextService, "_version", AsyncMock(return_value=object()))
    monkeypatch.setattr(context_module.EditorialContextService, "_present", lambda _: context)
    monkeypatch.setattr(
        context_module,
        "capture_generation_context",
        AsyncMock(return_value=ReferenceGenerationSnapshot(version=1, selected=(), learnings=())),
    )
    monkeypatch.setattr(context_module, "resolve_motion_skill", lambda _: ("skill", "a" * 64, "creative instructions"))
    card = {"sources": [{"path": "/private/origin", "ref": "private-reference", "license": "MIT"}]}
    monkeypatch.setattr(
        context_module,
        "list_motion_styles",
        lambda: [SimpleNamespace(id="style", version=1, sha256="b" * 64, content=json.dumps(card))],
    )
    source_row = {
        "id": source,
        "kind": "video",
        "object_key": "private/source",
        "mime_type": "video/mp4",
        "size_bytes": 100,
        "sha256": "c" * 64,
    }
    logo_row = {
        "id": logo,
        "object_key": "private/logo",
        "mime_type": "image/png",
        "size_bytes": 10,
        "sha256": "d" * 64,
    }
    session = AsyncMock()
    session.scalar.return_value = date(2026, 11, 9)
    session.execute.side_effect = [result(source_row), result(logo_row)]
    return SimpleNamespace(
        service=MotionContext(settings),
        session=session,
        tenant=tenant,
        business=business,
        body=body,
        source=source_row,
        logo=logo_row,
        state=state,
    )


async def test_context_preserves_owner_provenance_and_filters_expired_facts(context_case):
    c = context_case
    captured = await c.service.capture(c.session, c.tenant, c.business, c.body)
    assert [fact["statement"] for fact in captured["confirmed_facts"]] == [
        "Preço vigente fictício",
        "Fato permanente fictício",
    ]
    assert all(fact["provenance"] == {"kind": "owner_context", "version": 7} for fact in captured["confirmed_facts"])
    assert "source_detail" not in json.dumps(captured)
    assert captured["logo"]["object_key"] == "private/logo"
    assert captured["styles"][0]["card"]["sources"] == [{"license": "MIT"}]
    assert captured["execution"]["mode"] == "disabled"
    assert captured["creative_contract"]["version"] == "reel-creative-v6"
    assert captured["creative_contract"]["scene_direction_version"] == "scene-direction-v1"
    assert len(captured["creative_contract"]["requirements"]) == 4
    altered = {**captured, "creative_contract": {"version": "other"}}
    cipher_context = MotionContext(
        c.service.settings.model_copy(update={"meta_encryption_key": SecretStr(Fernet.generate_key().decode())})
    )
    assert cipher_context.fingerprint(captured) != cipher_context.fingerprint(altered)


async def test_unconfigured_logo_is_distinct_from_a_missing_configured_logo(context_case):
    c = context_case
    state = c.state.return_value
    c.state.return_value = state.model_copy(
        update={"confirmed": state.confirmed.model_copy(update={"overrides": kit()})}
    )
    c.session.execute.side_effect = [result(c.source)]
    captured = await c.service.capture(c.session, c.tenant, c.business, c.body)
    assert captured["logo"] is None


@pytest.mark.parametrize(
    "missing,code",
    [
        ("source", "MOTION_SOURCE_UNAVAILABLE"),
        ("kit", "MOTION_CONFIRMED_KIT_REQUIRED"),
        ("logo", "MOTION_LOGO_UNAVAILABLE"),
    ],
)
async def test_missing_authoritative_inputs_do_not_become_model_assumptions(context_case, missing, code):
    c = context_case
    if missing == "source":
        c.session.execute.side_effect = [result(None)]
    elif missing == "kit":
        c.state.return_value = BrandKitState(head_version=0)
    else:
        c.session.execute.side_effect = [result(c.source), result(None)]
    with pytest.raises(AuthError, match=code):
        await c.service.capture(c.session, c.tenant, c.business, c.body)


@pytest.mark.parametrize(
    "guard,code",
    [
        ("settings", "MOTION_EXECUTION_NOT_CONFIGURED"),
        ("plan", "PLAN_REQUIRED"),
        ("consent", "VISUAL_AI_CONSENT_REQUIRED"),
        ("pending", "VISUAL_CHANGE_PENDING"),
    ],
)
async def test_admission_stops_at_the_failed_authority(settings, monkeypatch, guard, code):
    session = AsyncMock()
    service = MotionRequestService(settings, object())
    monkeypatch.setattr(type(settings), "motion_execution_ready", lambda _: guard != "settings")
    session.scalar.return_value = guard != "plan"
    service.gate._state = AsyncMock(return_value="revoked" if guard == "consent" else "active")
    monkeypatch.setattr(
        "app.services.motion_requests.VisualPendingChanges.has_pending_in_session",
        AsyncMock(return_value=guard == "pending"),
    )
    with pytest.raises(AuthError, match=code):
        await service._admission(session, uuid4(), uuid4())


async def test_status_projection_does_not_expose_ciphertext_or_execution_token(settings, monkeypatch):
    tenant, business, actor, identifier, operation = (uuid4() for _ in range(5))
    public = {
        "id": identifier,
        "operation_id": operation,
        "format": "reel",
        "state": "queued",
        "piece_id": None,
        "failure_code": None,
    }
    session = AsyncMock()
    session.execute.return_value = result([public])

    @asynccontextmanager
    async def transaction(*_args):
        yield session

    service = MotionRequestService(settings, SimpleNamespace(transaction=transaction))
    monkeypatch.setattr("app.services.motion_requests.WhatsAppMaterialsService._require_owner", AsyncMock())
    assert (await service.list(tenant, business, actor))[0].model_dump() == public
    session.execute.return_value = result({**public, "snapshot_ciphertext": "private", "execution_token": uuid4()})
    assert (await service.get(tenant, business, actor, identifier)).model_dump() == public
    session.execute.return_value = result(None)
    with pytest.raises(AuthError, match="MOTION_REQUEST_NOT_FOUND"):
        await service.get(tenant, business, actor, identifier)


async def test_begin_rejects_an_event_for_a_different_request_owner(settings):
    tenant, business, actor, operation = (uuid4() for _ in range(4))
    session = AsyncMock()
    session.scalar.return_value = True

    @asynccontextmanager
    async def transaction(*_args):
        yield session

    service = MotionRequestService(settings, SimpleNamespace(transaction=transaction))
    service.gate._lock = AsyncMock()
    service.row = AsyncMock(return_value={"actor_id": uuid4()})
    with pytest.raises(AuthError, match="MOTION_OWNER_CHANGED"):
        await service.begin(tenant, business, actor, operation, uuid5(operation, "motion.requested"))
    session.execute.assert_not_awaited()
    session.scalar.return_value = False
    with pytest.raises(AuthError, match="MOTION_EVENT_MISMATCH"):
        await service.begin(tenant, business, actor, operation, uuid5(operation, "motion.requested"))


async def test_explicit_financial_revocation_and_run_token_are_revalidated(settings):
    tenant, business, actor, source = (uuid4() for _ in range(4))
    body = MotionRequest(operation_id=uuid4(), instruction="Synthetic", source_asset_id=source)
    row = {
        "tenant_id": tenant,
        "business_id": business,
        "actor_id": actor,
        "source_asset_id": source,
        "snapshot_ciphertext": "ciphertext",
        "source_fingerprint": "fingerprint",
        "admitted_at": None,
        "id": uuid4(),
    }
    service = MotionRequestService(settings, object())
    service.context = SimpleNamespace(
        require_qualification=lambda *args: None,
        open=lambda _: {"request": body.model_dump()},
        capture=AsyncMock(return_value={}),
        fingerprint=lambda _: "fingerprint",
    )
    session = AsyncMock()
    session.scalar.return_value = True
    with pytest.raises(AuthError, match="MOTION_ACCESS_REVOKED"):
        await service.current(session, row)
    service.gate._lock = AsyncMock()
    service.row = AsyncMock(return_value={"state": "uncertain", "execution_token": uuid4()})
    with pytest.raises(AuthError, match="MOTION_EXECUTION_FENCED"):
        await service.locked_running(session, row, uuid4())
    service.row.return_value = {"state": "running", "execution_token": uuid4()}
    with pytest.raises(AuthError, match="MOTION_EXECUTION_FENCED"):
        await service.locked_running(session, row, uuid4())


@pytest.mark.parametrize("available", [True, False])
async def test_collection_selection_is_owner_scoped_and_revalidates_active_rights(context_case, available):
    c = context_case
    photo_id = uuid4()
    body = c.body.model_copy(update={"collection_photo_ids": (photo_id,)})
    photo = {
        "id": photo_id,
        "version": 2,
        "title": "Foto",
        "item_id": uuid4(),
        "object_key": "private/photo",
        "mime_type": "image/png",
        "size_bytes": 20,
        "sha256": "e" * 64,
        "space_kind": None,
    }
    c.session.execute.side_effect = [result(c.source), result(photo if available else None), result(c.logo)]
    previous = {"creative_contract": {"version": "reel-creative-v3"}}
    if not available:
        with pytest.raises(AuthError, match="MOTION_COLLECTION_PHOTO_UNAVAILABLE"):
            await c.service.capture(c.session, c.tenant, c.business, body, previous=previous)
    else:
        value = await c.service.capture(c.session, c.tenant, c.business, body, previous=previous)
        assert value["collection_photos"][0]["version"] == 2
        assert value["creative_contract"] == previous["creative_contract"]
    query, params = c.session.execute.await_args_list[1].args
    assert params == {"tenant": c.tenant, "business": c.business, "photo": photo_id}
    for required in (
        "tenant_id=:tenant",
        "business_id=:business",
        "state='ready'",
        "status='active'",
        "rights_scope='business_collection_confirmed'",
        "delete_owner IS NULL",
        "FOR SHARE",
    ):
        assert required in str(query)


async def test_image_capability_is_captured_but_not_retroactive_on_old_snapshots(context_case):
    from app.services.motion_illustration_policy import MODEL
    from app.tests.unit.test_motion_illustrations import art_settings

    c = context_case
    c.service.settings = art_settings(c.service.settings)
    value = await c.service.capture(c.session, c.tenant, c.business, c.body)
    assert value["illustration_generation"]["model"] == MODEL
    c.session.execute.side_effect = [result(c.source), result(c.logo)]
    historic = await c.service.capture(
        c.session, c.tenant, c.business, c.body, previous={"creative_contract": {"version": "reel-creative-v3"}}
    )
    assert "illustration_generation" not in historic
    c.service.settings.motion_illustrations_enabled = False
    c.session.execute.side_effect = [result(c.source), result(c.logo)]
    disabled = await c.service.capture(c.session, c.tenant, c.business, c.body, previous=value)
    assert "illustration_generation" not in disabled  # Different fingerprint fences a previously enabled run.


async def test_storyboard_request_fails_before_context_io_unless_explicitly_enabled(context_case):
    c = context_case
    with pytest.raises(AuthError, match="STORYBOARD_NOT_CONFIGURED"):
        await c.service.capture(c.session, c.tenant, c.business, c.body.model_copy(update={"storyboard": True}))
    c.session.execute.assert_not_awaited()


async def test_selected_repertoire_is_captured_and_recaptured_without_retroactive_selection(context_case):
    from app.services.motion_repertoire import capture_repertoire

    c = context_case
    historic = await c.service.capture(c.session, c.tenant, c.business, c.body)
    assert "repertoire" not in historic and "repertoire_id" not in historic["request"]
    selected = c.body.model_copy(update={"repertoire_id": "business-reel-v1"})
    c.session.execute.side_effect = [result(c.source), result(c.logo)]
    captured = await c.service.capture(c.session, c.tenant, c.business, selected)
    assert captured["repertoire"] == capture_repertoire("business-reel-v1")
    assert captured["reference_context"] == historic["reference_context"]
    for body, snapshot in ((selected, captured), (c.body, historic)):
        c.session.execute.side_effect = [result(c.source), result(c.logo)]
        assert await c.service.capture(c.session, c.tenant, c.business, body, previous=snapshot) == snapshot


async def test_direction_is_captured_before_code_without_changing_existing_snapshots(context_case):
    from app.tests.unit.test_motion_plan import direction_data

    c = context_case
    historic = await c.service.capture(c.session, c.tenant, c.business, c.body)
    selected = MotionRequest.model_validate({**c.body.model_dump(), "scene_direction": direction_data()})
    c.session.execute.side_effect = [result(c.source), result(c.logo)]
    captured = await c.service.capture(c.session, c.tenant, c.business, selected)
    assert captured["request"]["scene_direction"] == direction_data()
    assert captured["creative_contract"]["version"] == "reel-creative-v7"
    assert historic["creative_contract"]["version"] == "reel-creative-v6"
    assert "scene_direction" not in historic["request"]
    assert context_module.digest(captured) != context_module.digest(historic)
    for body, snapshot in ((selected, captured), (c.body, historic)):
        c.session.execute.side_effect = [result(c.source), result(c.logo)]
        assert await c.service.capture(c.session, c.tenant, c.business, body, previous=snapshot) == snapshot


async def test_html_context_serializes_compatible_contract_and_preserves_historic_snapshots(context_case, monkeypatch):
    """The actual model payload gets the new projection without rewriting old requests."""
    from app.adapters.motion_ai import OpenAIMotionProvider
    from app.services.motion_protocols import MotionModelRequest
    from app.services.motion_skills import load_motion_skill, resolve_motion_skill
    from app.services.motion_styles import list_motion_styles

    c = context_case
    monkeypatch.setattr(context_module, "resolve_motion_skill", resolve_motion_skill)
    monkeypatch.setattr(context_module, "list_motion_styles", list_motion_styles)
    captured = await c.service.capture(c.session, c.tenant, c.business, c.body)

    provider = OpenAIMotionProvider(
        "test-only", model="local-test", input_usd_micros_per_million_tokens=1, output_usd_micros_per_million_tokens=1
    )
    payload = provider.build_request(MotionModelRequest(uuid4(), "generate", captured))
    transmitted = json.loads(payload["input"][0]["content"][0]["text"])["authorized_context"]
    assert transmitted == captured
    assert transmitted["executor_contract"]["version"] == "html-motion-executor-v2"
    capabilities = transmitted["executor_contract"]["capabilities"]
    assert all(term in capabilities for term in ("HTML", "JavaScript", "SVG", "Canvas", "misturar", "cut/fade"))
    assert "não exige vídeo sempre visível" in transmitted["executor_contract"]["integration_policy"]
    assert transmitted["skill"]["id"] == "instagram-reel-v11"
    assert "escolha os trechos" not in transmitted["skill"]["instructions"]
    for item in transmitted["styles"]:
        assert item["projection"] == "html-executor-style-v1"
        assert "current_visual_subset" not in item["card"]
        assert "execution_restrictions" not in item["card"]
    serialized = json.dumps(transmitted, ensure_ascii=False)
    assert "HTML, CSS, JavaScript, comandos, caminhos e URLs não são saída executável" not in serialized
    assert "executor visual experimental não mistura áudio" not in serialized
    assert "composição HTML" in payload["instructions"]
    assert "Preserve o plano de áudio autorizado e sua voz original" in payload["instructions"]

    c.session.execute.side_effect = [result(c.source), result(c.logo)]
    assert await c.service.capture(c.session, c.tenant, c.business, c.body, previous=captured) == captured

    # Construct the shape persisted before this change from the immutable files.
    old_skill_hash = "4ed6a1307437b492cf423612855645752fda331e206920abfcf155c198271ec7"
    historic = dict(captured)
    historic.pop("executor_contract")
    historic["skill"] = {
        "id": "instagram-reel-v1",
        "sha256": old_skill_hash,
        "instructions": load_motion_skill("instagram-reel-v1", old_skill_hash, "reel"),
    }
    historic["styles"] = []
    for style in list_motion_styles():
        card = json.loads(style.content)
        for source in card["sources"]:
            source.pop("path", None)
            source.pop("ref", None)
        historic["styles"].append({"id": style.id, "version": style.version, "sha256": style.sha256, "card": card})
    c.session.execute.side_effect = [result(c.source), result(c.logo)]
    assert await c.service.capture(c.session, c.tenant, c.business, c.body, previous=historic) == historic


@pytest.mark.parametrize(
    "skill_id,skill_hash",
    [
        ("instagram-reel-v2", "4401257fd8a4e73352ed55aa5985a9a636612a84f1efb5ce3d315661bc8edcab"),
        ("instagram-reel-v3", "40c7fbd49864507ba6b76c945af456fc159694e2611f829af6abb78865345661"),
        ("instagram-reel-v4", "45c20abcfad7bcac5892f24eb435c4e0f216ff219872d98895b2e0bae906cda6"),
        ("instagram-reel-v6", "5fa1aa1f7044c523b519e31cf766bb2d01adf238f17e23625c30d868c9283432"),
    ],
)
async def test_html_recapture_preserves_the_exact_construction_skill(context_case, skill_id, skill_hash):
    from app.services.motion_skills import load_motion_skill

    c = context_case
    captured = await c.service.capture(c.session, c.tenant, c.business, c.body)
    captured["skill"] = {
        "id": skill_id,
        "sha256": skill_hash,
        "instructions": load_motion_skill(skill_id, skill_hash, "reel"),
    }
    c.session.execute.side_effect = [result(c.source), result(c.logo)]
    recaptured = await c.service.capture(c.session, c.tenant, c.business, c.body, previous=captured)
    assert recaptured == captured
    assert context_module.digest(recaptured) == context_module.digest(captured)


@pytest.mark.parametrize("kind", ["generate", "review", "correct"])
async def test_construction_skill_reaches_the_exact_counted_request(context_case, kind):
    from dataclasses import replace

    import httpx

    from app.schemas.motion_production import MotionReview
    from app.services.motion_repertoire import load_repertoire_images
    from app.tests.unit.test_motion_ai import frame, provider, request, review_data
    from app.tests.unit.test_motion_plan import direction_data, planned

    c = context_case
    body = c.body.model_copy(update={"repertoire_id": "business-reel-v1", "scene_direction": planned().scene_direction})
    captured = await c.service.capture(c.session, c.tenant, c.business, body)
    sent = []

    def transport(call):
        sent.append(json.loads(call.content))
        return httpx.Response(200, json={"object": "response.input_tokens", "input_tokens": 11000})

    model = provider(transport)
    job = replace(
        request(
            kind, composition=planned(), frames=(frame(),), review=MotionReview.model_validate(review_data(revise=True))
        ),
        context=captured,
        reference_images=load_repertoire_images(captured),
    )
    payload = model.build_request(job)
    authorized = json.loads(payload["input"][0]["content"][0]["text"])["authorized_context"]
    assert authorized == captured
    assert authorized["request"]["scene_direction"] == direction_data()
    instructions = authorized["skill"]["instructions"]
    assert authorized["skill"]["id"] == "instagram-reel-v11"
    assert "function makeCompositionPassage" in instructions
    assert "function makeReadingReveal" in instructions
    assert "MotionV1.stagger" in instructions
    assert "makeCutoutObject" in instructions
    assert "makeNarrativeBackdrop" in instructions
    assert "makeVideoFrameTreatment" in instructions
    assert "Na revisão," in instructions  # Instructions are not render evidence.
    assert "Coreografia ligada ao sentido da mensagem" in instructions
    assert "Crítica da interação solicitada" in instructions
    assert "não trate esse texto como transcrição" in instructions.replace("\n", " ")
    assert len(authorized["repertoire"]["examples"]) == 3
    assert await model.count_input_tokens(job, payload) == 11000
    assert sent == [{key: payload[key] for key in ("model", "input", "instructions", "text", "reasoning")}]


async def test_review_policy_is_captured_but_not_added_to_historical_requests(context_case):
    from app.services.motion_review import review_contract

    c = context_case
    captured = await c.service.capture(c.session, c.tenant, c.business, c.body)
    assert captured["review_contract"] == review_contract()
    for historical in (False, True):
        snapshot = dict(captured)
        if historical:
            snapshot.pop("review_contract")
        c.session.execute.side_effect = [result(c.source), result(c.logo)]
        assert await c.service.capture(c.session, c.tenant, c.business, c.body, previous=snapshot) == snapshot


def test_full_historical_html_guidance_keeps_executor_review_skill_and_runtime():
    from app.services.motion_context import HTML_EXECUTOR_CONTRACT, capture_motion_guidance
    from app.services.motion_creative import provided_direction_contract
    from app.services.motion_review import REVIEW_CONTRACT
    from app.services.motion_skills import load_motion_skill
    from app.tests.unit.test_motion_plan import direction_data

    body = MotionRequest.model_validate(
        {
            "operation_id": uuid4(),
            "source_asset_id": uuid4(),
            "instruction": "Historical request",
            "scene_direction": direction_data(),
        }
    )
    current = capture_motion_guidance(body)
    old = {
        **current,
        "creative_contract": provided_direction_contract(),
        "executor_contract": HTML_EXECUTOR_CONTRACT,
        "review_contract": REVIEW_CONTRACT,
    }
    old_hash = "c8c9e83de74053e3156c325bc7e599c1594977ede53e90d0552d6ca119e7345b"
    old["skill"] = {
        "id": "instagram-reel-v5",
        "sha256": old_hash,
        "instructions": load_motion_skill("instagram-reel-v5", old_hash, "reel"),
    }
    assert capture_motion_guidance(body, previous=old) == old
    assert current["creative_contract"]["movement_runtime"]["version"] == "motion-movement-v3"
    assert old["creative_contract"]["movement_runtime"]["version"] == "motion-movement-v1"
    assert current["executor_contract"]["version"] == "html-motion-executor-v2"


def test_new_guidance_coordinates_background_video_and_objects_without_new_capabilities():
    from app.services.motion_context import capture_motion_guidance

    body = MotionRequest(operation_id=uuid4(), source_asset_id=uuid4(), instruction="Elaborated motion")
    guidance = capture_motion_guidance(body)
    assert guidance["skill"]["id"] == "instagram-reel-v11"
    text = guidance["skill"]["instructions"]
    assert "Fundo vivo significa participação na narrativa" in text
    assert "mesma janela de tamanho fixo" in text
    assert "não prometa geometria 3D" in text
    assert "illustration_generation" not in guidance


def test_v7_with_v2_movement_recaptures_without_upgrading_historical_frames():
    from copy import deepcopy

    from app.services.motion_context import capture_motion_guidance
    from app.services.motion_movement import movement_v2_contract
    from app.services.motion_skills import load_motion_skill

    body = MotionRequest(operation_id=uuid4(), source_asset_id=uuid4(), instruction="Frame treatment")
    current = capture_motion_guidance(body)
    previous = deepcopy(current)
    digest = "f067fbd60372c8c291f9df28753d89af665a73dbaa280b2ea6e54facc49a9996"
    previous["skill"] = {
        "id": "instagram-reel-v7",
        "sha256": digest,
        "instructions": load_motion_skill("instagram-reel-v7", digest, "reel"),
    }
    previous["creative_contract"]["movement_runtime"] = movement_v2_contract()
    assert capture_motion_guidance(body, previous=previous) == previous
    assert current["skill"]["id"] == "instagram-reel-v11"
    assert "makeVideoFrameTreatment" in current["skill"]["instructions"]


def test_background_skill_recapture_preserves_the_previous_video_treatment_version():
    from copy import deepcopy

    from app.services.motion_context import capture_motion_guidance
    from app.services.motion_skills import load_motion_skill

    body = MotionRequest(operation_id=uuid4(), source_asset_id=uuid4(), instruction="Narrative background")
    current = capture_motion_guidance(body)
    previous = deepcopy(current)
    digest = "5050e1c0a4c523e28187eb393effde5f2e6be3e8a1ea0e502ed179a5d46c81fe"
    previous["skill"] = {
        "id": "instagram-reel-v8",
        "sha256": digest,
        "instructions": load_motion_skill("instagram-reel-v8", digest, "reel"),
    }
    assert capture_motion_guidance(body, previous=previous) == previous
    assert "makeNarrativeBackdrop" in current["skill"]["instructions"]
    assert "makeVideoFrameTreatment" in current["skill"]["instructions"]
    assert "makeNarrativeBackdrop" not in previous["skill"]["instructions"]
    for key in ("creative_contract", "review_contract", "executor_contract"):
        assert current[key] == previous[key]


def test_realistic_object_guidance_preserves_v9_snapshot_and_does_not_grant_image_generation():
    from copy import deepcopy

    from app.services.motion_context import capture_motion_guidance
    from app.services.motion_skills import load_motion_skill

    body = MotionRequest(operation_id=uuid4(), source_asset_id=uuid4(), instruction="Realistic object")
    current = capture_motion_guidance(body)
    previous = deepcopy(current)
    digest = "49a0cb2b52b5870c3f2e3a020abc3501b7701ab3521bad709054b92c0e4678a8"
    previous["skill"] = {
        "id": "instagram-reel-v9",
        "sha256": digest,
        "instructions": load_motion_skill("instagram-reel-v9", digest, "reel"),
    }
    assert capture_motion_guidance(body, previous=previous) == previous
    assert "makeCutoutObject" in current["skill"]["instructions"]
    assert "makeCutoutObject" not in previous["skill"]["instructions"]
    assert "illustration_generation" not in current
    for key in ("creative_contract", "executor_contract", "review_contract"):
        assert current[key] == previous[key]


async def test_timed_speech_is_captured_immutably_and_wrong_source_is_rejected(context_case):
    from app.schemas.motion_speech import MotionSpeechTiming
    from app.tests.unit.test_motion_speech import timing_data

    c = context_case
    timing = timing_data()
    timing["source_sha256"] = c.source["sha256"]
    body = c.body.model_copy(update={"speech_timing": MotionSpeechTiming.model_validate(timing)})
    captured = await c.service.capture(c.session, c.tenant, c.business, body)
    assert captured["request"]["speech_timing"] == timing
    c.session.execute.side_effect = [result(c.source), result(c.logo)]
    assert await c.service.capture(c.session, c.tenant, c.business, body, previous=captured) == captured
    timing["source_sha256"] = "f" * 64
    body = body.model_copy(update={"speech_timing": MotionSpeechTiming.model_validate(timing)})
    c.session.execute.side_effect = [result(c.source)]
    with pytest.raises(AuthError, match="MOTION_SPEECH_SOURCE_CHANGED"):
        await c.service.capture(c.session, c.tenant, c.business, body)


def test_speech_skill_keeps_v10_snapshots_unchanged():
    from copy import deepcopy

    from app.services.motion_context import capture_motion_guidance
    from app.services.motion_skills import load_motion_skill

    body = MotionRequest(operation_id=uuid4(), source_asset_id=uuid4(), instruction="Speech timing")
    current = capture_motion_guidance(body)
    previous = deepcopy(current)
    digest = "3ae3bb49051b9b0b42e9268eb75ebd5b7d80b8ce3bd41c994fb4c36480b47722"
    previous["skill"] = {
        "id": "instagram-reel-v10",
        "sha256": digest,
        "instructions": load_motion_skill("instagram-reel-v10", digest, "reel"),
    }
    assert capture_motion_guidance(body, previous=previous) == previous
    assert "speech_cue_id" in current["skill"]["instructions"]
    assert "speech_cue_id" not in previous["skill"]["instructions"]


async def test_local_speech_policy_is_captured_only_for_new_or_previously_enabled_requests(context_case, tmp_path):
    c = context_case
    historical = await c.service.capture(c.session, c.tenant, c.business, c.body)
    c.service.settings.motion_speech_mode = "local"
    c.service.settings.motion_speech_model_directory = str(tmp_path)
    c.service.settings.motion_speech_model_sha256 = "a" * 64
    c.session.execute.side_effect = [result(c.source), result(c.logo)]
    assert await c.service.capture(c.session, c.tenant, c.business, c.body, previous=historical) == historical
    c.session.execute.side_effect = [result(c.source), result(c.logo)]
    current = await c.service.capture(c.session, c.tenant, c.business, c.body)
    assert current["speech_recognition"]["backend"] == "faster-whisper"
    assert str(tmp_path) not in str(current)
    c.session.execute.side_effect = [result(c.source), result(c.logo)]
    assert await c.service.capture(c.session, c.tenant, c.business, c.body, previous=current) == current
