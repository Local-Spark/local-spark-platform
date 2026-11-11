"""Image effects stay private, budgeted and one-shot; local synthetic pixels only."""

import hashlib
import io
import json
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4, uuid5

import pytest
from PIL import Image, ImageDraw
from pydantic import ValidationError

from app.adapters.motion_inputs import PreparedMotionInput
from app.adapters.visual_ai import VisualAIError, VisualRequest, VisualResult, _validate, visual_request_http_parts
from app.schemas.motion_production import HTMLMotionComposition, MotionIllustration
from app.services.auth import AuthError
from app.services.motion_illustration_policy import MODEL, illustration_policy, image_estimate
from app.services.motion_illustrations import MotionIllustrations, verified_preview
from app.tests.unit.test_motion_plan import context, planned
from app.tests.unit.test_motion_runtime import configured


def image_result(*, alpha=True, usage=True):
    image = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0 if alpha else 255))
    ImageDraw.Draw(image).ellipse((100, 100, 900, 900), fill="#244739")
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    png = buffer.getvalue()
    return VisualResult(
        png,
        "image/png",
        hashlib.sha256(png).hexdigest(),
        1024,
        1024,
        {"input_tokens": 100, "output_tokens": 200} if usage else None,
        "synthetic-request",
    )


def art_settings(settings):
    return configured(settings, "openai").model_copy(
        update={
            "motion_illustrations_enabled": True,
            "motion_illustration_reservation_usd_micros": 10000,
            "motion_illustration_budget_usd_micros": 20000,
            "motion_request_budget_usd_micros": 21000,
        }
    )


def composition_with_art():
    data = planned().model_dump(mode="json")
    spec = {
        "asset_id": "assets/illustration-cup.png",
        "description": "Xícara ilustrada com vapor em curva.",
        "purpose": "Representar a pausa, sem simular o produto real.",
    }
    data["illustrations"] = [spec]
    data["motion_plan"]["scenes"][0]["elements"][0].update(role="image", asset_id=spec["asset_id"])
    data["scene_direction"]["scenes"][0]["elements"][0]["construction"] = "generated_asset"
    return HTMLMotionComposition.model_validate(data)


@pytest.fixture
def art_case(settings):
    settings = art_settings(settings)
    ctx = context()
    ctx["illustration_generation"] = illustration_policy(settings)
    ctx["kit"] = {"overrides": {"palette": {"primary": "#244739"}, "brand_name": "Não criar logo"}}
    prepared = PreparedMotionInput(ctx, (), (), 1000, {"mode": "silent", "tracks": []})
    effects = SimpleNamespace(
        requests=SimpleNamespace(settings=settings),
        capacity=AsyncMock(return_value=True),
        reserve_submission=AsyncMock(return_value=SimpleNamespace(id=uuid4())),
        received=AsyncMock(),
        claim=AsyncMock(),
        ledger=SimpleNamespace(finish=AsyncMock()),
    )
    result = image_result()
    provider = SimpleNamespace(generate=AsyncMock(return_value=result))
    store = SimpleNamespace(single_attempt_put=True, put=AsyncMock(), get_image=AsyncMock(return_value=result.content))
    row = {key: uuid4() for key in ("tenant_id", "business_id", "actor_id", "id", "operation_id")}
    return SimpleNamespace(
        settings=settings,
        row=row,
        token=uuid4(),
        prepared=prepared,
        effects=effects,
        store=store,
        provider=provider,
        service=MotionIllustrations(effects, store, provider),
        composition=composition_with_art(),
    )


async def test_declared_art_flows_to_private_storage_render_assets_and_review_payload(art_case):
    from app.tests.unit.test_motion_ai import provider, request

    c = art_case
    value = await c.service.prepare(c.row, c.token, c.prepared, c.composition)
    assert len(value.assets) == len(value.asset_previews) == 1
    assert c.prepared.assets == ()
    assert c.effects.reserve_submission.await_args.args[2] == uuid5(
        c.row["operation_id"], "illustration:assets/illustration-cup.png"
    )
    c.effects.capacity.assert_awaited_once_with(c.row, c.token, 10100)
    sent = c.provider.generate.await_args.args[0]
    assert sent.model == MODEL and sent.background == "transparent" and sent.references == ()
    assert "#244739" in sent.prompt and "Não criar logo" not in sent.prompt
    assert c.effects.received.await_args_list[0].args[-1] == 6500
    assert c.effects.ledger.finish.await_args.kwargs == {"actual_usd_micros": None}
    assert str(c.row["tenant_id"]) in c.store.put.await_args.args[0]
    assert c.store.put.await_args.args[1].data == value.assets[0].data
    assert "object_key" not in str(value.context)
    payload = provider().build_request(
        replace(request(), context=value.context, assets=value.assets, asset_previews=value.asset_previews)
    )
    assert any(item["type"] == "input_image" for item in payload["input"][0]["content"])
    assert value.context["available_materials"][0]["role"] == "generated_illustration"


@pytest.mark.parametrize(
    "failure",
    ["disabled", "duplicate", "unused", "no_plan", "foreign_path", "budget", "policy", "storage_mode", "replay"],
)
async def test_invalid_or_unfunded_art_stops_before_provider(art_case, failure):
    c = art_case
    value, prepared = c.composition, c.prepared
    if failure == "disabled":
        prepared = replace(
            prepared, context={k: v for k, v in prepared.context.items() if k != "illustration_generation"}
        )
    elif failure == "duplicate":
        value = value.model_copy(update={"illustrations": value.illustrations * 2})
    elif failure == "unused":
        value = value.model_copy(update={"motion_plan": planned().motion_plan})
    elif failure == "no_plan":
        value = value.model_copy(update={"motion_plan": None})
    elif failure == "foreign_path":
        data = value.model_dump(mode="json")
        data["motion_plan"]["scenes"][1]["elements"][0].update(role="image", asset_id="assets/missing.png")
        data["scene_direction"]["scenes"][1]["elements"][0]["construction"] = "authorized_asset"
        value = HTMLMotionComposition.model_validate(data)
    elif failure == "budget":
        c.effects.capacity.return_value = False
    elif failure == "policy":
        c.settings.motion_illustration_reservation_usd_micros = 9999
    elif failure == "storage_mode":
        c.store.single_attempt_put = False
    else:
        c.effects.reserve_submission.side_effect = AuthError("MOTION_EFFECT_ALREADY_CLAIMED", 409)
    with pytest.raises(AuthError):
        await c.service.prepare(c.row, c.token, prepared, value)
    c.provider.generate.assert_not_awaited()
    c.store.put.assert_not_awaited()


@pytest.mark.parametrize("failure", ["transport", "usage", "cost", "opaque", "storage", "revoked"])
async def test_paid_uncertainty_retains_hold_and_never_regenerates(art_case, failure):
    c = art_case
    if failure == "transport":
        c.provider.generate.side_effect = VisualAIError("VISUAL_PROVIDER_UNCERTAIN", uncertain=True)
    elif failure == "usage":
        c.provider.generate.return_value = image_result(usage=False)
    elif failure == "cost":
        c.provider.generate.return_value = replace(image_result(), usage={"input_tokens": 1, "output_tokens": 10000})
    elif failure == "opaque":
        c.provider.generate.return_value = image_result(alpha=False)
    elif failure == "storage":
        c.store.get_image.return_value = b"changed"
    else:
        c.effects.claim.side_effect = AuthError("MOTION_ACCESS_REVOKED", 409)
    with pytest.raises((AuthError, VisualAIError)):
        await c.service.prepare(c.row, c.token, c.prepared, c.composition)
    c.provider.generate.assert_awaited_once()
    c.effects.ledger.finish.assert_awaited_once()
    assert c.effects.ledger.finish.await_args.kwargs["actual_usd_micros"] is None
    if failure not in ("transport",):
        assert c.effects.received.await_count >= 1


async def test_no_art_does_not_require_budget_or_add_any_call(art_case):
    c = art_case
    value = await c.service.prepare(c.row, c.token, c.prepared, planned())
    assert value is c.prepared
    c.effects.capacity.assert_not_awaited()
    c.provider.generate.assert_not_awaited()


@pytest.mark.parametrize(
    "updates",
    [
        {"motion_illustration_budget_usd_micros": 0},
        {"motion_ai_mode": "fake"},
        {"motion_request_budget_usd_micros": 200},
        {"openai_api_key": None},
    ],
)
def test_activation_requires_explicit_compatible_budget_and_credentials(settings, updates):
    assert illustration_policy(settings) is None
    with pytest.raises(AuthError, match="NOT_CONFIGURED"):
        illustration_policy(art_settings(settings).model_copy(update=updates))


@pytest.mark.parametrize(
    "usage,expected",
    [
        (None, None),
        ({}, None),
        ({"input_tokens": True, "output_tokens": 1}, None),
        ({"input_tokens": -1, "output_tokens": 1}, None),
        ({"input_tokens": 100, "output_tokens": 200}, 6500),
        (
            {
                "input_tokens": 100,
                "output_tokens": 200,
                "input_tokens_details": {"image_tokens": 20, "text_tokens": 80},
            },
            6560,
        ),
        ({"input_tokens": 1, "output_tokens": 1, "input_tokens_details": {"image_tokens": 2}}, None),
        ({"input_tokens": 1, "output_tokens": 1, "input_tokens_details": {"text_tokens": 2}}, None),
    ],
)
def test_estimate_uses_actual_reported_usage_without_claiming_invoice(usage, expected):
    assert image_estimate(usage) == expected


def test_illustration_ids_cannot_escape_canonical_paths():
    for path in ("https://outside/image.png", "assets/../logo.png", "assets/source.mp4"):
        with pytest.raises(ValidationError):
            MotionIllustration(asset_id=path, description="Objeto", purpose="Conceito")
    assert "illustrations" not in planned().model_dump()


def test_native_alpha_is_opt_in_and_keeps_old_visual_request_identical():
    old = VisualRequest("Objeto", MODEL, "medium", "1024x1024", "png", uuid4())
    assert "background" not in visual_request_http_parts(old)[1]
    new = replace(old, background="transparent")
    assert _validate(new) == (1024, 1024)
    assert visual_request_http_parts(new)[1]["background"] == "transparent"
    with pytest.raises(VisualAIError):
        _validate(replace(new, output_format="jpeg"))
    with pytest.raises(AuthError):
        verified_preview(replace(image_result(), sha256="0" * 64))


async def test_realistic_cutout_uses_existing_image_pipeline_and_retains_conceptual_provenance(art_case):
    from pathlib import Path

    from app.schemas.motion_production import MotionRequest
    from app.services.motion_context import capture_motion_guidance
    from app.services.motion_visual_direction import supplied_direction

    c = art_case
    root = Path(__file__).resolve().parents[3] / "docs" / "evals"
    spec = MotionIllustration.model_validate_json(
        (root / "ilustracao-cafe-pausa-objeto-realista-2026-11-10.json").read_bytes()
    )
    direction = json.loads((root / "direcao-cafe-pausa-objeto-realista-2026-11-10.json").read_bytes())
    body = MotionRequest(
        operation_id=uuid4(), source_asset_id=uuid4(), instruction="Realistic object", scene_direction=direction
    )
    with pytest.raises(AuthError, match="MOTION_VISUAL_DIRECTION_ILLUSTRATION_UNAVAILABLE"):
        capture_motion_guidance(body)
    policy = c.prepared.context["illustration_generation"]
    ctx = capture_motion_guidance(body, illustration_generation=policy)
    ctx["illustration_generation"] = policy
    ctx["request"] = body.model_dump(mode="json")
    assert supplied_direction(ctx).model_dump(mode="json") == direction
    data = c.composition.model_dump(mode="json")
    data["illustrations"] = [spec.model_dump()]
    data["motion_plan"]["scenes"][0]["elements"][0]["asset_id"] = spec.asset_id
    composition = HTMLMotionComposition.model_validate(data)
    value = await c.service.prepare(c.row, c.token, c.prepared, composition)
    sent = c.provider.generate.await_args.args[0]
    assert spec.description in sent.prompt and spec.purpose in sent.prompt
    assert "nunca fotografia documental" in sent.prompt
    assert sent.background == "transparent"
    assert len(value.assets) == len(value.asset_previews) == 1
    assert value.assets[0].id == spec.asset_id
    assert value.context["available_materials"][0]["role"] == "generated_illustration"
    assert "não foto real do negócio" in value.context["available_materials"][0]["identity_rule"]
    c.provider.generate.assert_awaited_once()
