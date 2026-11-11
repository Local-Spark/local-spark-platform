"""No-network proof of grounded review and a single paid-transport attempt."""

import base64
import hashlib
import io
import json
from dataclasses import replace
from unittest.mock import patch
from uuid import uuid4

import httpx
import pytest
from PIL import Image
from pydantic import ValidationError

from app.adapters import motion_ai
from app.adapters.motion_ai import MotionAIError, OpenAIMotionProvider
from app.adapters.motion_html_renderer import RenderAsset, RenderedFrame
from app.schemas.motion_production import HTMLMotionComposition, MotionAudio, MotionReview
from app.services.motion_protocols import MotionModelRequest
from app.services.motion_review import MotionReviewError, validate_review


def frame(ms=0, color="red"):
    out = io.BytesIO()
    Image.new("RGB", (64, 64), color).save(out, "PNG")
    data = out.getvalue()
    return RenderedFrame(ms, data, hashlib.sha256(data).hexdigest())


def composition():
    return HTMLMotionComposition(
        html="<main>Texto autorizado</main>",
        scene_init="window.seek=()=>{}",
        concept="Convite",
        source_usage="Material autorizado",
        audio={"mode": "silent", "tracks": []},
    )


def review_data(*, current=None, previous=None, revise=False):
    current = current or frame()
    evidence = {"version": "current", "at_ms": current.ms, "sha256": current.sha256}
    refs = [evidence]
    if previous:
        refs.append({"version": "previous", "at_ms": previous.ms, "sha256": previous.sha256})
    return {
        "verdict": "needs_revision" if revise else "adequate",
        "criteria": [
            {
                "name": name,
                "status": "uncertain" if name == "audio" else "fail" if name == "legibility" and revise else "pass",
                "observation": "Quadro amostrado" if name != "audio" else "Sem escuta",
                "evidence": [] if name == "audio" else [evidence],
            }
            for name in ("factuality", "brand", "legibility", "composition", "motion", "technical", "audio")
        ],
        "preferred": "current",
        "preference_reason": "Leitura observada",
        "preference_evidence": refs,
        "issues": [
            {
                "severity": "major",
                "criterion": "legibility",
                "actionable": True,
                "at_ms": current.ms,
                "evidence_sha256": current.sha256,
                "problem": "Título cortado",
                "correction": "Reposicionar título",
            }
        ]
        if revise
        else [],
        "limitations": ["Quadros não comprovam todo o movimento; áudio não ouvido."],
    }


def response_data(document=None, **updates):
    return {
        "status": "completed",
        "output": [
            {
                "type": "message",
                "content": [
                    {"type": "output_text", "text": json.dumps(document or composition().model_dump(mode="json"))}
                ],
            }
        ],
        "usage": {"input_tokens": 100, "output_tokens": 15},
        **updates,
    }


def provider(handler=None, **updates):
    return OpenAIMotionProvider(
        "private-test-credential",
        model="configured-model",
        input_usd_micros_per_million_tokens=2500000,
        output_usd_micros_per_million_tokens=10000000,
        transport=httpx.MockTransport(handler or (lambda _: httpx.Response(200, json=response_data()))),
        **updates,
    )


def request(kind="generate", **updates):
    return MotionModelRequest(uuid4(), kind, {"instruction": "Um convite", "facts": ["Café"]}, **updates)


async def test_exact_context_schema_and_one_request_without_storage_tools_or_credentials():
    seen = []

    def handler(sent):
        seen.append(sent)
        return httpx.Response(200, json=response_data(), headers={"x-request-id": "provider-123"})

    client = provider(handler)
    job = request(
        assets=(RenderAsset("assets/photo.png", "image/png", frame().png, frame().sha256),), frames=(frame(),)
    )
    payload = client.build_request(job)
    assert payload["store"] is False and "tools" not in payload
    assert "private-test-credential" not in json.dumps(payload)
    assert payload["input"][0]["content"][0]["text"].find("Um convite") >= 0
    assert payload["text"]["format"]["strict"] is True
    result = await client.submit(job, payload)
    assert result.composition == composition() and result.review is None
    assert result.estimated_usd_micros == 400 and result.http_status == 200
    assert result.provider_request_id == "provider-123" and result.raw_response
    assert len(seen) == 1 and seen[0].headers["x-client-request-id"] == str(job.operation_id)
    assert json.loads(seen[0].content) == payload


async def test_review_prefers_only_evidence_actually_sent_and_minor_does_not_force_regeneration():
    current, previous = frame(33, "blue"), frame(0)
    data = review_data(current=current, previous=previous)
    client = provider(lambda _: httpx.Response(200, json=response_data(data)))
    job = request(
        "review",
        composition=composition(),
        frames=(current,),
        incumbent_composition=composition(),
        incumbent_frames=(previous,),
    )
    result = await client.submit(job, client.build_request(job))
    assert result.review.mandatory_pass
    assert result.review.preferred == "current"
    data["issues"] = [{**review_data(current=current, revise=True)["issues"][0], "severity": "minor"}]
    assert MotionReview.model_validate(data).verdict == "adequate"


async def test_original_source_is_sent_and_grounded_separately_from_compared_versions():
    source, current, previous = frame(0, "green"), frame(33, "blue"), frame(0)
    reference = {"version": "source", "at_ms": source.ms, "sha256": source.sha256}
    data = review_data(current=current, previous=previous)
    data["criteria"][1]["evidence"].append(reference)
    data["preference_evidence"].append(reference)
    client = provider(lambda _: httpx.Response(200, json=response_data(data)))
    job = request(
        "review",
        composition=composition(),
        frames=(current,),
        incumbent_composition=composition(),
        incumbent_frames=(previous,),
        source_frames=(source,),
    )
    payload = client.build_request(job)
    content = payload["input"][0]["content"]
    assert [json.loads(content[index]["text"])["version"] for index in (1, 3, 5)] == [
        "source",
        "current",
        "previous",
    ]
    assert [content[index]["image_url"] for index in (2, 4, 6)] == [
        "data:image/png;base64," + base64.b64encode(item.png).decode() for item in (source, current, previous)
    ]
    result = await client.submit(job, payload)
    assert result.review.mandatory_pass
    data["criteria"][0]["evidence"] = [reference]
    with pytest.raises(ValidationError):
        MotionReview.model_validate(data)
    data["criteria"][0]["evidence"] = [{"version": "current", "at_ms": current.ms, "sha256": current.sha256}]
    bad_source = request("review", composition=composition(), frames=(current,), incumbent_frames=(previous,))
    with pytest.raises(MotionReviewError, match="UNSENT_EVIDENCE"):
        validate_review(bad_source, MotionReview.model_validate(data))


async def test_correction_keeps_audio_and_uses_prior_critique():
    client = provider()
    job = request(
        "correct",
        composition=composition(),
        review=MotionReview.model_validate(review_data(revise=True)),
        frames=(frame(),),
    )
    payload = client.build_request(job)
    assert "Reposicionar título" in payload["input"][0]["content"][0]["text"]
    assert (await client.submit(job, payload)).composition.audio == composition().audio
    changed = composition().model_dump(mode="json")
    changed["audio"] = {
        "mode": "mix",
        "tracks": [
            {"asset_id": "assets/voice.wav", "offset_ms": 0, "trim_start_ms": 0, "trim_end_ms": 10, "volume": 1}
        ],
    }
    other = provider(lambda _: httpx.Response(200, json=response_data(changed)))
    with pytest.raises(MotionAIError, match="RESPONSE_INVALID"):
        await other.submit(job, other.build_request(job))


@pytest.mark.parametrize("status", [301, 400, 429, 500])
async def test_error_response_is_preserved_without_retry_or_redirect(status):
    calls = []

    def handler(sent):
        calls.append(sent)
        return httpx.Response(
            status, content=b"private-provider-response", headers={"location": "https://elsewhere.invalid"}
        )

    client, job = provider(handler), request()
    with pytest.raises(MotionAIError, match="HTTP_FAILED") as caught:
        await client.submit(job, client.build_request(job))
    assert len(calls) == 1
    assert caught.value.raw_response == b"private-provider-response"
    assert "private-provider-response" not in str(caught.value)


async def test_transport_failure_is_uncertain_single_attempt():
    calls = []

    def handler(sent):
        calls.append(sent)
        raise httpx.ReadTimeout("sensitive request")

    client, job = provider(handler), request()
    with pytest.raises(MotionAIError, match="UNCERTAIN") as caught:
        await client.submit(job, client.build_request(job))
    assert len(calls) == 1 and caught.value.raw_response is None


async def test_truncated_output_preserves_known_usage_without_parsing_partial_code_or_retry():
    calls = []
    data = response_data(
        status="incomplete",
        incomplete_details={"reason": "max_output_tokens"},
        usage={"input_tokens": 9428, "output_tokens": 16000},
        output=[{"content": [{"type": "output_text", "text": "{partial private code"}]}],
    )

    def handler(sent):
        calls.append(sent)
        return httpx.Response(200, json=data, headers={"x-request-id": "limited-response"})

    client, job = provider(handler), request()
    with pytest.raises(MotionAIError, match="OUTPUT_LIMIT") as caught:
        await client.submit(job, client.build_request(job))
    assert len(calls) == 1
    assert caught.value.estimated_usd_micros == 183570
    assert caught.value.usage == {"input_tokens": 9428, "output_tokens": 16000}
    assert caught.value.provider_request_id == "limited-response"
    assert json.loads(caught.value.raw_response) == data
    assert "private" not in str(caught.value)


@pytest.mark.parametrize(
    "usage", [{}, {"input_tokens": True, "output_tokens": 10}, {"input_tokens": 10, "output_tokens": -1}]
)
async def test_incomplete_output_cannot_invent_cost_from_invalid_usage(usage):
    data = response_data(status="incomplete", incomplete_details={"reason": "max_output_tokens"}, usage=usage)
    client, job = provider(lambda _: httpx.Response(200, json=data)), request()
    with pytest.raises(MotionAIError, match="RESPONSE_INVALID") as caught:
        await client.submit(job, client.build_request(job))
    assert caught.value.estimated_usd_micros is None


@pytest.mark.parametrize(
    "data",
    [
        {"status": "incomplete"},
        response_data(status="incomplete", incomplete_details={"reason": "other"}),
        {"status": "completed", "output": []},
        response_data(usage={"input_tokens": True, "output_tokens": 0}),
        response_data(usage={"input_tokens": -1, "output_tokens": 0}),
        response_data(output=[{"content": [{"type": "refusal"}]}]),
        response_data(output=[{"content": [{"type": "output_text", "text": "invalid"}]}]),
        response_data(output=[None]),
        None,
    ],
)
async def test_invalid_response_preserved_and_never_repaired_by_second_call(data):
    client, job = provider(lambda _: httpx.Response(200, content=json.dumps(data).encode())), request()
    with pytest.raises(MotionAIError, match="RESPONSE_INVALID") as caught:
        await client.submit(job, client.build_request(job))
    assert caught.value.raw_response == json.dumps(data).encode()


async def test_bounded_response_and_request_identity(monkeypatch):
    client, job = provider(lambda _: httpx.Response(200, content=b"x" * 70000)), request()
    payload = client.build_request(job)
    with pytest.raises(MotionAIError, match="REQUEST_CHANGED"):
        await client.submit(job, {**payload, "store": True})
    monkeypatch.setattr(motion_ai, "MAX_RESPONSE_BYTES", 65536)
    with pytest.raises(MotionAIError, match="RESPONSE_TOO_LARGE") as caught:
        await client.submit(job, payload)
    assert len(caught.value.raw_response) == 65536


@pytest.mark.parametrize(
    "job,code",
    [
        (request("review"), "COMPOSITION_REQUIRED"),
        (request("correct", composition=composition()), "CORRECTION_NOT_JUSTIFIED"),
        (
            request("correct", composition=composition(), review=MotionReview.model_validate(review_data())),
            "CORRECTION_NOT_JUSTIFIED",
        ),
        (request("review", composition=composition()), "EVIDENCE_REQUIRED"),
        (request(frames=(frame(),) * 65), "EVIDENCE_TOO_LARGE"),
        (request(frames=(replace(frame(), sha256="0" * 64),)), "EVIDENCE_INVALID"),
        (request(frames=(replace(frame(), png=b"not-png"),)), "EVIDENCE_INVALID"),
    ],
)
def test_build_rejects_unqualified_inputs_before_transport(job, code):
    with pytest.raises(MotionAIError, match=code):
        provider().build_request(job)


def test_request_size_cap_and_constructor_guards(monkeypatch):
    monkeypatch.setattr(motion_ai, "MAX_REQUEST_BYTES", 10)
    with pytest.raises(MotionAIError, match="REQUEST_TOO_LARGE"):
        provider().build_request(request())
    for changes in (
        {"api_key": ""},
        {"model": ""},
        {"max_output_tokens": 0},
        {"input_usd_micros_per_million_tokens": 0},
        {"output_usd_micros_per_million_tokens": 0},
    ):
        kwargs = {
            "api_key": "private",
            "model": "model",
            "input_usd_micros_per_million_tokens": 1,
            "output_usd_micros_per_million_tokens": 1,
            **changes,
        }
        with pytest.raises(MotionAIError):
            OpenAIMotionProvider(**kwargs)


@pytest.mark.parametrize("change", ["unknown_reference", "unknown_issue", "missing_previous", "current_without_both"])
def test_unfounded_comparison_is_rejected(change):
    current, previous = frame(33, "blue"), frame(0)
    data = review_data(current=current, previous=previous, revise=change == "unknown_issue")
    job = request("review", composition=composition(), frames=(current,), incumbent_frames=(previous,))
    if change == "unknown_reference":
        data["criteria"][0]["evidence"][0]["sha256"] = "0" * 64
    elif change == "unknown_issue":
        data["issues"][0]["evidence_sha256"] = "0" * 64
    elif change == "missing_previous":
        job = replace(job, incumbent_frames=())
        data = review_data(current=current)
        data["preferred"] = "previous"
    else:
        data["preference_evidence"] = [data["preference_evidence"][0]]
    with pytest.raises(MotionReviewError):
        validate_review(job, MotionReview.model_validate(data))


def test_previous_and_undetermined_are_valid_without_improvement_claim():
    job = request("review", composition=composition(), frames=(frame(),), incumbent_frames=(frame(33),))
    for preferred in ("previous", "undetermined"):
        data = {**review_data(), "preferred": preferred, "preference_evidence": []}
        validate_review(job, MotionReview.model_validate(data))


@pytest.mark.parametrize(
    "change",
    [
        "audio_pass",
        "pass_without_evidence",
        "pass_only_previous",
        "duplicate_criterion",
        "adequate_major",
        "needs_without_issue",
        "issue_pass",
        "audio_actionable",
    ],
)
def test_review_contract_rejects_unsupported_verdicts(change):
    data = review_data(revise=change in {"adequate_major", "issue_pass", "audio_actionable"})
    if change == "audio_pass":
        data["criteria"][-1]["status"] = "pass"
    elif change == "pass_without_evidence":
        data["criteria"][0]["evidence"] = []
    elif change == "pass_only_previous":
        data["criteria"][0]["evidence"][0]["version"] = "previous"
    elif change == "duplicate_criterion":
        data["criteria"][-1] = data["criteria"][0]
    elif change == "adequate_major":
        data["verdict"] = "adequate"
    elif change == "needs_without_issue":
        data["verdict"] = "needs_revision"
    elif change == "issue_pass":
        data["criteria"][2]["status"] = "pass"
    else:
        data["issues"][0]["criterion"] = "audio"
    with pytest.raises(ValidationError):
        MotionReview.model_validate(data)


async def test_default_transport_is_created_with_retries_disabled():
    # Substitute the default transport constructor, preserving the real request path.
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json=response_data()))
    with patch.object(httpx, "AsyncHTTPTransport", return_value=transport) as factory:
        client = OpenAIMotionProvider(
            "key", model="model", input_usd_micros_per_million_tokens=1, output_usd_micros_per_million_tokens=1
        )
        job = request()
        await client.submit(job, client.build_request(job))
        factory.assert_called_once_with(retries=0, trust_env=False)


@pytest.mark.parametrize(
    "audio",
    [
        {"mode": "mix", "tracks": []},
        {
            "mode": "mix",
            "tracks": [
                {"asset_id": "assets/voice.wav", "offset_ms": 0, "trim_start_ms": 20, "trim_end_ms": 10, "volume": 1}
            ],
        },
    ],
)
def test_invalid_audio_is_rejected_before_rendering(audio):
    with pytest.raises(ValidationError):
        MotionAudio.model_validate(audio)


@pytest.mark.parametrize("failure", [None, "unknown", "duplicate", "hash"])
def test_material_previews_enter_the_same_counted_model_payload(failure):
    image = frame()
    asset_id = "assets/product.png"
    asset = RenderAsset(asset_id, "image/png", image.png, image.sha256)
    previews = ((asset_id, image),)
    if failure == "unknown":
        previews = (("assets/unknown.png", image),)
    elif failure == "duplicate":
        previews *= 2
    elif failure == "hash":
        previews = ((asset_id, replace(image, sha256="0" * 64)),)
    job = replace(request(), assets=(asset,), asset_previews=previews)
    if failure:
        with pytest.raises(MotionAIError, match="ASSET_PREVIEW_INVALID"):
            provider().build_request(job)
        return
    content = provider().build_request(job)["input"][0]["content"]
    assert json.loads(content[1]["text"]) == {"material_asset_id": asset_id, "preview_sha256": image.sha256}
    assert base64.b64decode(content[2]["image_url"].split(",")[1]) == image.png


@pytest.mark.parametrize("failure", ["invalid_json", "refusal", "unknown_evidence", "wrong_audio"])
async def test_rejected_complete_response_preserves_usage_cost_request_id_without_retry(failure):
    calls = []
    job = request()
    data = response_data()
    if failure == "invalid_json":
        data["output"][0]["content"][0]["text"] = "{broken"
    elif failure == "refusal":
        data["output"][0]["content"] = [{"type": "refusal"}]
    elif failure == "unknown_evidence":
        job = request("review", composition=composition(), frames=(frame(),))
        review = review_data()
        review["criteria"][0]["evidence"][0]["sha256"] = "0" * 64
        data = response_data(review)
    else:
        job = request(
            "correct", composition=composition(), review=MotionReview.model_validate(review_data(revise=True))
        )
        doc = composition().model_dump(mode="json")
        doc["audio"] = {
            "mode": "mix",
            "tracks": [
                {"asset_id": "assets/source.mp4", "offset_ms": 0, "trim_start_ms": 0, "trim_end_ms": 1000, "volume": 1}
            ],
        }
        data = response_data(doc)

    def handler(sent):
        calls.append(sent)
        return httpx.Response(200, json=data, headers={"x-request-id": "rejected-known-usage"})

    client = provider(handler)
    with pytest.raises(MotionAIError, match="RESPONSE_INVALID") as caught:
        await client.submit(job, client.build_request(job))
    assert len(calls) == 1
    assert caught.value.usage == {"input_tokens": 100, "output_tokens": 15}
    assert caught.value.estimated_usd_micros == 400
    assert caught.value.provider_request_id == "rejected-known-usage"
    assert json.loads(caught.value.raw_response) == data
