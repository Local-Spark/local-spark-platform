"""Owner-scoped encrypted trace of the actual prepared visual request."""

import hashlib
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr

from app.services.auth import AuthError
from app.services.brand_kits import MANIFEST
from app.services.visual_kit_reference import load_kit_example
from app.services.visual_references import VisualReferenceSource
from app.services.visual_request_trace import VisualRequestTraceService, decrypt_visual_trace, encrypt_visual_trace


def prepared():
    return SimpleNamespace(
        skill_id="instagram-story-v1",
        skill_sha256="e" * 64,
        context=SimpleNamespace(
            proposal_id=uuid4(), briefing_id=uuid4(), context_version=1, script_version=2, brand_kit_version=3
        ),
        request=SimpleNamespace(
            prompt="Peça sintética com preço confirmado",
            model="synthetic",
            quality="medium",
            size="1024x1280",
            output_format="png",
            background=None,
            request_id=uuid4(),
            references=(SimpleNamespace(mime_type="image/png"),),
        ),
        sources=(VisualReferenceSource("source_photo", uuid4(), 1, "a" * 64, "b" * 64),),
    )


def configured(settings):
    return settings.model_copy(update={"meta_encryption_key": SecretStr(Fernet.generate_key().decode())})


def test_visual_trace_round_trip_keeps_exact_prompt_and_reference_without_plaintext(settings):
    cfg, original = configured(settings), prepared()
    ciphertext = encrypt_visual_trace(cfg, original)
    assert original.request.prompt not in ciphertext
    trace = decrypt_visual_trace(cfg, ciphertext)
    assert trace["prompt"] == original.request.prompt
    assert trace["client_request_id"] == str(original.request.request_id)
    assert trace["references"][0]["normalized_sha256"] == "b" * 64
    assert trace["references"][0]["id"] == str(original.sources[0].id)
    assert trace["skill_id"] == "instagram-story-v1" and trace["skill_sha256"] == "e" * 64
    assert trace["context"]["brand_kit_version"] == 3
    assert trace["http"]["method"] == "POST"
    assert trace["http"]["path"] == "/v1/images/edits"
    assert trace["http"]["json_without_images"] == {
        "model": original.request.model,
        "prompt": original.request.prompt,
        "quality": original.request.quality,
        "size": original.request.size,
        "output_format": original.request.output_format,
        "n": 1,
    }
    assert trace["http"]["images_field"] == "images"


def test_visual_trace_records_generation_endpoint_without_references(settings):
    original = prepared()
    original.sources = ()
    original.request.references = ()
    cfg = configured(settings)
    trace = decrypt_visual_trace(cfg, encrypt_visual_trace(cfg, original))
    assert trace["http"]["path"] == "/v1/images/generations"
    assert trace["http"]["images_field"] is None
    assert trace["references"] == []


def test_visual_trace_records_all_five_references_without_image_bytes(settings):
    cfg, original = configured(settings), prepared()
    kit_id = uuid4()
    original.sources += tuple(
        VisualReferenceSource(kind, uuid4(), 1, "c" * 64, "d" * 64)
        for kind in ("item_photo", "space_photo", "brand_logo")
    )
    original.sources += (
        VisualReferenceSource("kit_example", kit_id, 2, "e" * 64, "f" * 64, "cafe-pausas", "assets/example.jpg"),
    )
    original.request.references += tuple(SimpleNamespace(mime_type="image/png") for _ in range(4))
    trace = decrypt_visual_trace(cfg, encrypt_visual_trace(cfg, original))
    assert len(trace["references"]) == 5
    assert trace["references"][-1] == {
        "kind": "kit_example",
        "id": str(kit_id),
        "version": 2,
        "source_sha256": "e" * 64,
        "normalized_sha256": "f" * 64,
        "mime_type": "image/png",
        "catalog_id": "cafe-pausas",
        "asset_path": "assets/example.jpg",
    }
    assert all(
        set(reference) == {"kind", "id", "version", "source_sha256", "normalized_sha256", "mime_type"}
        for reference in trace["references"][:-1]
    )


@pytest.mark.parametrize("format", ["photo", "story"])
def test_kit_trace_identifies_real_pinned_catalog_asset_and_normalized_bytes(settings, format):
    cfg, original = configured(settings), prepared()
    source, reference = load_kit_example(cfg, {"kit_id": "cafe-pausas", "kit_version": 1}, format)
    original.sources = (source,)
    original.request.references = (reference,)
    trace = decrypt_visual_trace(cfg, encrypt_visual_trace(cfg, original))["references"][0]
    assert trace["catalog_id"] == "cafe-pausas" and trace["version"] == 1
    asset = MANIFEST.parent / trace["asset_path"]
    assert hashlib.sha256(asset.read_bytes()).hexdigest() == trace["source_sha256"]
    assert hashlib.sha256(reference.content).hexdigest() == trace["normalized_sha256"]


def test_trace_requires_valid_key_and_complete_reference_binding(settings):
    with pytest.raises(AuthError, match="VISUAL_TRACE_KEY_REQUIRED"):
        encrypt_visual_trace(settings, prepared())
    with pytest.raises(AuthError, match="VISUAL_TRACE_KEY_REQUIRED"):
        decrypt_visual_trace(settings, "x")
    invalid_key = settings.model_copy(update={"meta_encryption_key": SecretStr("invalid")})
    with pytest.raises(AuthError, match="VISUAL_TRACE_KEY_INVALID"):
        encrypt_visual_trace(invalid_key, prepared())
    cfg = configured(settings)
    missing = prepared()
    missing.request.references = ()
    with pytest.raises(AuthError, match="VISUAL_TRACE_INVALID"):
        encrypt_visual_trace(cfg, missing)
    missing_skill_hash = prepared()
    missing_skill_hash.skill_sha256 = None
    with pytest.raises(AuthError, match="VISUAL_TRACE_INVALID"):
        encrypt_visual_trace(cfg, missing_skill_hash)
    with pytest.raises(AuthError, match="VISUAL_TRACE_UNAVAILABLE"):
        decrypt_visual_trace(cfg, "not-authenticated")
    wrong_version = Fernet(cfg.meta_encryption_key.get_secret_value().encode()).encrypt(b'{"version":2}').decode()
    with pytest.raises(AuthError, match="VISUAL_TRACE_UNAVAILABLE"):
        decrypt_visual_trace(cfg, wrong_version)
    non_object = Fernet(cfg.meta_encryption_key.get_secret_value().encode()).encrypt(b"[]").decode()
    with pytest.raises(AuthError, match="VISUAL_TRACE_UNAVAILABLE"):
        decrypt_visual_trace(cfg, non_object)


@pytest.mark.asyncio
async def test_owner_can_read_exact_trace_others_are_rejected(settings, monkeypatch):
    tenant, business, actor, preview = (uuid4() for _ in range(4))
    cfg, original = configured(settings), prepared()
    result = SimpleNamespace(
        mappings=lambda: SimpleNamespace(
            one_or_none=lambda: {
                "operation_id": uuid4(),
                "request_hash": "c" * 64,
                "ciphertext": encrypt_visual_trace(cfg, original),
                "created_at": "fixture",
                "sha256": "d" * 64,
                "preview_state": "failed",
                "preview_error_code": "VISUAL_OUTCOME_UNCERTAIN",
            }
        )
    )
    session = SimpleNamespace(execute=AsyncMock(return_value=result))

    @asynccontextmanager
    async def transaction(*args):
        assert args == (tenant, actor)
        yield session

    authorize = AsyncMock()
    monkeypatch.setattr("app.services.visual_request_trace.WhatsAppMaterialsService._require_owner", authorize)
    service = VisualRequestTraceService(cfg, SimpleNamespace(transaction=transaction))
    trace = await service.read(tenant, business, actor, preview)
    assert trace["preview_id"] == str(preview) and trace["request"]["prompt"] == original.request.prompt
    assert trace["trace_status"] == "prepared" and trace["preview_error_code"] == "VISUAL_OUTCOME_UNCERTAIN"
    authorize.assert_awaited_once_with(session, tenant, business, actor)
    authorize.side_effect = AuthError("BUSINESS_OWNER_REQUIRED", 403)
    with pytest.raises(AuthError, match="BUSINESS_OWNER_REQUIRED"):
        await service.read(tenant, business, actor, preview)
    assert session.execute.await_count == 1
    authorize.side_effect = None
    session.execute.return_value = SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: None))
    with pytest.raises(AuthError, match="VISUAL_TRACE_NOT_FOUND"):
        await service.read(tenant, business, actor, preview)
