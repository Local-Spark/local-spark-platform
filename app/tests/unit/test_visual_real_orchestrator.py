"""The isolated visual orchestration fails closed around external effects."""

import asyncio
import hashlib
import io
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import NAMESPACE_URL, uuid4, uuid5

import pytest
from PIL import Image, ImageChops, ImageStat

from app.adapters.brand_overlay import BrandOverlayError
from app.adapters.material_media import FetchedMedia
from app.adapters.visual_ai import VisualAIError, VisualResult
from app.services.auth import AuthError
from app.services.editorial_consent_scope import current_visual_run
from app.services.visual_provider_execution import VisualSubmissionError
from app.services.visual_real_orchestrator import (
    VisualRealOrchestrator,
    VisualRunError,
    VisualRunScope,
    _encode_preview,
    _verify_finished,
)


@pytest.fixture
def case(monkeypatch):
    ids = [uuid4() for _ in range(6)]
    tenant, business, actor, preview, proposal, operation = ids
    scope = VisualRunScope(tenant, business, actor, preview, proposal, operation, 2, True, "a" * 64)
    context = SimpleNamespace(
        tenant_id=tenant, business_id=business, proposal_id=proposal, fingerprint=scope.fingerprint
    )
    prepared = SimpleNamespace(context=context, request=SimpleNamespace(request_id=operation), request_hash="b" * 64)
    brand_data = SimpleNamespace(request=prepared)
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(buffer, format="PNG")
    data = buffer.getvalue()
    sha = hashlib.sha256(data).hexdigest()
    media = FetchedMedia(data, "image/png", sha)
    result = VisualResult(data, "image/png", sha, 8, 8, None, None)
    brand = SimpleNamespace(prepare=AsyncMock(return_value=brand_data), finish=AsyncMock(return_value=media))
    guard = SimpleNamespace(
        admit=AsyncMock(return_value=True),
        authorize=AsyncMock(return_value=object()),
        current=AsyncMock(return_value=True),
        commit=AsyncMock(return_value=True),
        finish=AsyncMock(),
    )
    store = SimpleNamespace(put=AsyncMock(), delete=AsyncMock())
    submit = AsyncMock(return_value=result)
    monkeypatch.setattr("app.services.visual_real_orchestrator.execute_visual_submission", submit)
    service = VisualRealOrchestrator(
        guard=guard, brand=brand, provider=object(), ledger=object(), claims=object(), store=store, signing_key="key"
    )
    return SimpleNamespace(
        scope=scope,
        prepared=prepared,
        guard=guard,
        brand=brand,
        store=store,
        submit=submit,
        result=result,
        media=media,
        service=service,
    )


async def test_success_requires_admission_revalidation_and_commit(case):
    c = case
    assert await c.service.run(c.scope) == "completed"
    c.guard.admit.assert_awaited_once_with(c.scope)
    c.guard.authorize.assert_awaited_once()
    assert c.guard.current.await_count == 3
    c.guard.commit.assert_awaited_once()
    c.guard.finish.assert_awaited_once_with(c.scope, completed=True, effect_resolved=True)
    c.submit.assert_awaited_once()
    key, stored = c.store.put.await_args.args
    assert key.startswith(f"previews/{c.scope.tenant}/{c.scope.business}/{c.scope.preview}/attempt-2/")
    assert key.endswith(f"{stored.sha256}.jpg")
    assert stored.mime_type == "image/jpeg"
    assert stored.sha256 == hashlib.sha256(stored.data).hexdigest()
    with Image.open(io.BytesIO(stored.data)) as image:
        assert image.format == "JPEG" and image.size == (8, 8)
    assert c.guard.commit.await_args.args[2] == stored
    c.store.delete.assert_not_awaited()


async def test_concrete_brand_finish_is_applied_before_private_commit(case, settings):
    from app.schemas.brand_kits import BrandKitOverrides
    from app.services.visual_brand_finish import PreparedBrandScene, VisualBrandFinishService
    from app.tests.integration.test_brand_kits import _overrides

    c = case
    buffer = io.BytesIO()
    Image.new("RGB", (1024, 1280), "navy").save(buffer, format="PNG")
    data = buffer.getvalue()
    result = VisualResult(data, "image/png", hashlib.sha256(data).hexdigest(), 1024, 1280, None, None)
    c.submit.return_value = result
    # The finish service re-reads the same verified brand inputs before and
    # after applying the real overlay; no real provider or DB is contacted.
    c.prepared.context.format = "photo"
    scene = PreparedBrandScene(c.prepared, BrandKitOverrides.model_validate(_overrides()), "Croissant.", "Confira.")
    brand = VisualBrandFinishService(settings, object(), c.store)
    brand.prepare = AsyncMock(return_value=scene)
    c.service.brand = brand
    assert await c.service.run(c.scope) == "completed"
    brand.prepare.assert_awaited()
    assert brand.prepare.await_count == 3
    output = c.store.put.await_args.args[1]
    assert output.mime_type == "image/jpeg" and output.sha256 == hashlib.sha256(output.data).hexdigest()
    assert output.data != data
    c.guard.commit.assert_awaited_once()


async def test_admission_denial_never_reads_or_calls_provider(case):
    c = case
    c.guard.admit.return_value = False
    assert await c.service.run(c.scope) == "not_started"
    c.brand.prepare.assert_not_awaited()
    c.submit.assert_not_awaited()
    c.guard.finish.assert_not_awaited()


@pytest.mark.parametrize("field", ["tenant_id", "business_id", "proposal_id", "fingerprint", "request_id"])
async def test_changed_scope_is_discarded_before_reserving(case, field):
    c = case
    if field == "request_id":
        c.prepared.request.request_id = uuid4()
    else:
        setattr(c.prepared.context, field, "c" * 64 if field == "fingerprint" else uuid4())
    assert await c.service.run(c.scope) == "stale"
    c.guard.authorize.assert_not_awaited()
    c.submit.assert_not_awaited()
    c.guard.finish.assert_awaited_once_with(c.scope, completed=False, effect_resolved=False)


@pytest.mark.parametrize("check", [0, 1, 2])
async def test_changed_context_before_or_after_upload_never_becomes_visible(case, check):
    c = case
    c.guard.current.side_effect = [True] * check + [False]
    assert await c.service.run(c.scope) == "stale"
    c.guard.commit.assert_not_awaited()
    assert c.store.put.await_count == int(check == 2)
    assert c.store.delete.await_count == int(check == 2)
    c.guard.finish.assert_awaited_once_with(c.scope, completed=False, effect_resolved=True)


async def test_expired_fence_discards_only_its_own_object(case):
    c = case
    c.guard.commit.return_value = False
    assert await c.service.run(c.scope) == "stale"
    key = c.store.put.await_args.args[0]
    c.store.delete.assert_awaited_once_with(key)
    c.guard.finish.assert_awaited_once_with(c.scope, completed=False, effect_resolved=True)


@pytest.mark.parametrize(
    "exception,expected,finish",
    [
        (VisualSubmissionError("replayed"), "uncertain", False),
        (VisualAIError("timeout", uncertain=True), "uncertain", False),
        (VisualAIError("invalid", uncertain=False), "not_started", True),
    ],
)
async def test_external_failure_is_never_retried(case, exception, expected, finish):
    c = case
    c.submit.side_effect = exception
    assert await c.service.run(c.scope) == expected
    c.submit.assert_awaited_once()
    assert c.guard.finish.await_count == int(finish)
    c.store.put.assert_not_awaited()


async def test_pre_call_failure_closes_admission_but_cancellation_does_not(case):
    c = case
    c.brand.prepare.side_effect = ValueError("synthetic")
    with pytest.raises(ValueError):
        await c.service.run(c.scope)
    c.guard.finish.assert_awaited_once_with(c.scope, completed=False, effect_resolved=False)
    c.guard.finish.reset_mock()
    c.brand.prepare.side_effect = None
    c.submit.side_effect = asyncio.CancelledError
    with pytest.raises(asyncio.CancelledError):
        await c.service.run(c.scope)
    c.guard.finish.assert_not_awaited()


@pytest.mark.parametrize("error", [RuntimeError("lost reservation acknowledgement"), AuthError("OWNER_LOST", 403)])
async def test_authorization_failure_does_not_claim_a_resolved_financial_effect(case, error):
    c = case
    c.guard.authorize.side_effect = error
    if isinstance(error, AuthError):
        assert await c.service.run(c.scope) == "stale"
    else:
        with pytest.raises(RuntimeError, match="lost reservation acknowledgement"):
            await c.service.run(c.scope)
    c.guard.finish.assert_awaited_once_with(c.scope, completed=False, effect_resolved=False)
    c.submit.assert_not_awaited()
    c.store.put.assert_not_awaited()


@pytest.mark.parametrize("failure", [None, "prepare", "authorize", "provider"])
async def test_admitted_context_is_available_throughout_execution_and_always_resets(case, failure):
    c = case
    expected_operation = uuid5(NAMESPACE_URL, f"visual-preview:{c.scope.preview}")
    before = current_visual_run()
    observed = []

    def check(stage):
        actual = current_visual_run()
        assert actual is not None
        assert (actual.tenant, actual.business, actual.actor, actual.operation, actual.fence) == (
            c.scope.tenant,
            c.scope.business,
            c.scope.actor,
            expected_operation,
            c.scope.fence,
        )
        observed.append(stage)

    brand_data = c.brand.prepare.return_value

    async def prepare(*_args, **_kwargs):
        check("prepare")
        if failure == "prepare":
            raise RuntimeError("synthetic failure")
        return brand_data

    async def authorize(*_args):
        check("authorize")
        if failure == "authorize":
            raise RuntimeError("synthetic failure")
        return object()

    async def provider(**_kwargs):
        check("provider")
        if failure == "provider":
            raise asyncio.CancelledError
        return c.result

    async def finish(*_args, **_kwargs):
        check("finish")

    c.brand.prepare.side_effect = prepare
    c.guard.authorize.side_effect = authorize
    c.submit.side_effect = provider
    c.guard.finish.side_effect = finish
    if failure is None:
        assert await c.service.run(c.scope) == "completed"
        assert observed == ["prepare", "authorize", "provider", "finish"]
    else:
        with pytest.raises(asyncio.CancelledError if failure == "provider" else RuntimeError):
            await c.service.run(c.scope)
        if failure == "provider":
            c.guard.finish.assert_not_awaited()
        else:
            assert observed[-1] == "finish"
    assert current_visual_run() is before


async def test_failed_upload_attempts_cleanup_without_claiming_completion(case):
    c = case
    c.store.put.side_effect = RuntimeError("synthetic")
    c.store.delete.side_effect = RuntimeError("synthetic")
    with pytest.raises(RuntimeError):
        await c.service.run(c.scope)
    c.store.delete.assert_awaited_once()
    c.guard.finish.assert_awaited_once_with(c.scope, completed=False, effect_resolved=True)


@pytest.mark.parametrize("check", [0, 1, 2])
async def test_failed_revalidation_after_provider_finishes_admission(case, check):
    c = case
    c.guard.current.side_effect = [True] * check + [RuntimeError("synthetic")]
    with pytest.raises(RuntimeError, match="synthetic"):
        await c.service.run(c.scope)
    c.guard.finish.assert_awaited_once_with(c.scope, completed=False, effect_resolved=True)
    assert c.store.delete.await_count == int(check == 2)


@pytest.mark.parametrize("error", [RuntimeError("synthetic"), AuthError("synthetic", 409)])
async def test_unknown_commit_retains_object_and_admission_for_reconciliation(case, error):
    c = case
    c.guard.commit.side_effect = error
    with pytest.raises(type(error)):
        await c.service.run(c.scope)
    c.store.put.assert_awaited_once()
    c.store.delete.assert_not_awaited()
    c.guard.finish.assert_not_awaited()


async def test_resolved_rejected_commit_finishes_even_when_cleanup_fails(case):
    c = case
    c.guard.commit.return_value = False
    c.store.delete.side_effect = RuntimeError("synthetic")
    with pytest.raises(RuntimeError, match="synthetic"):
        await c.service.run(c.scope)
    c.guard.finish.assert_awaited_once_with(c.scope, completed=False, effect_resolved=True)


async def test_kit_change_after_provider_response_discards_and_finishes(case):
    c = case
    c.brand.finish.side_effect = AuthError("VISUAL_KIT_CHANGED", 409)
    assert await c.service.run(c.scope) == "stale"
    c.submit.assert_awaited_once()
    c.store.put.assert_not_awaited()
    c.guard.finish.assert_awaited_once_with(c.scope, completed=False, effect_resolved=True)


async def test_local_finish_error_finishes_but_unknown_provider_error_does_not(case):
    c = case
    c.brand.finish.side_effect = BrandOverlayError("BRAND_COPY_TOO_LONG")
    with pytest.raises(BrandOverlayError):
        await c.service.run(c.scope)
    c.guard.finish.assert_awaited_once_with(c.scope, completed=False, effect_resolved=True)
    c.guard.finish.reset_mock()
    c.brand.finish.side_effect = None
    c.submit.side_effect = AuthError("synthetic", 409)
    with pytest.raises(AuthError):
        await c.service.run(c.scope)
    c.guard.finish.assert_not_awaited()
    c.submit.side_effect = BrandOverlayError("synthetic")
    with pytest.raises(BrandOverlayError):
        await c.service.run(c.scope)
    c.guard.finish.assert_not_awaited()


async def test_failed_output_validation_never_persists_and_finishes(case):
    c = case
    c.brand.finish.return_value = FetchedMedia(b"bad", "image/png", "a" * 64)
    with pytest.raises(VisualRunError, match="VISUAL_OUTPUT_INVALID"):
        await c.service.run(c.scope)
    c.store.put.assert_not_awaited()
    c.guard.finish.assert_awaited_once_with(c.scope, completed=False, effect_resolved=True)


@pytest.mark.parametrize("fence,fingerprint", [(0, "a" * 64), (1, "bad"), (1, "z" * 64)])
async def test_invalid_scope_rejected_before_admission(case, fence, fingerprint):
    from dataclasses import replace

    with pytest.raises(VisualRunError, match="VISUAL_SCOPE_INVALID"):
        await case.service.run(replace(case.scope, fence=fence, fingerprint=fingerprint))
    case.guard.admit.assert_not_awaited()


def test_invalid_output_is_not_accepted(case):
    bad_data = FetchedMedia(b"bad", "image/png", hashlib.sha256(b"bad").hexdigest())
    for media in (
        FetchedMedia(case.media.data, "image/jpeg", case.media.sha256),
        FetchedMedia(case.media.data, "image/png", "a" * 64),
        bad_data,
    ):
        with pytest.raises(VisualRunError, match="VISUAL_OUTPUT_INVALID"):
            _verify_finished(media, (8, 8))
    with pytest.raises(VisualRunError, match="VISUAL_OUTPUT_INVALID"):
        _verify_finished(case.media, (9, 8))


def test_preview_encoding_rejects_malformed_input():
    media = FetchedMedia(b"invalid", "image/png", hashlib.sha256(b"invalid").hexdigest())
    with pytest.raises(VisualRunError, match="VISUAL_OUTPUT_INVALID"):
        _encode_preview(media)


def test_preview_encoding_strips_metadata_and_preserves_synthetic_gradient():
    image = Image.new("RGB", (128, 128))
    image.putdata([(x * 2, y * 2, (x + y)) for y in range(128) for x in range(128)])
    exif = Image.Exif()
    exif[270] = "private synthetic metadata"
    original = io.BytesIO()
    image.save(original, format="PNG", exif=exif, icc_profile=b"private synthetic profile")
    data = original.getvalue()
    result = _encode_preview(FetchedMedia(data, "image/png", hashlib.sha256(data).hexdigest()))
    with Image.open(io.BytesIO(result.data)) as encoded:
        assert encoded.format == "JPEG"
        assert not encoded.getexif()
        assert "icc_profile" not in encoded.info
        assert max(ImageStat.Stat(ImageChops.difference(image, encoded.convert("RGB"))).mean) < 2


@pytest.mark.parametrize("length", [0, 15 * 1024 * 1024 + 1])
def test_preview_encoding_rejects_empty_or_oversized_output(case, monkeypatch, length):
    def save(_image, output, **_kwargs):
        output.write(b"x" * length)

    monkeypatch.setattr(Image.Image, "save", save)
    with pytest.raises(VisualRunError, match="VISUAL_OUTPUT_INVALID"):
        _encode_preview(case.media)
