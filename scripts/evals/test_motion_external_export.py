"""Synthetic offline proof: exact payload, all attachments, no network or customer media."""

import base64
import json
import zipfile
from dataclasses import replace

import pytest

from app.adapters.motion_ai import request_bytes
from app.schemas.brand_kits import BrandKitVersion
from app.services.motion_elements import runtime_bytes
from app.tests.conftest import settings  # noqa: F401
from app.tests.unit.test_motion_ai import frame
from app.tests.unit.test_motion_direction_input import kit
from app.tests.unit.test_motion_generation import compact_wire
from app.tests.unit.test_motion_illustrations import art_case  # noqa: F401
from app.tests.unit.test_motion_plan import direction_data
from scripts.evals import motion_external_export as export


@pytest.fixture
def recorded_case(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-appear-in-export")
    source = tmp_path / "source.mp4"
    source.write_bytes(b"synthetic-media-placeholder-no-render")
    context = {
        "schema": "html-motion-context-v1",
        "kit": BrandKitVersion(
            version=1,
            state="confirmed",
            kit_id="synthetic",
            kit_version=1,
            overrides=kit(),
            created_at="2026-11-10T12:00:00Z",
        ).model_dump(mode="json"),
        "context_version": 0,
        "preferences": {},
        "confirmed_facts": [],
        "reference_context": [],
        "source": {"asset_id": "assets/source.mp4", "sha256": export.sha(source.read_bytes()), "duration_ms": 1000},
        "authorized_audio": {"mode": "silent", "tracks": []},
        "output": {"width": 720, "height": 1280, "fps": 30, "duration_ms": 1000},
        "transcript": None,
        "limitations": ["Synthetic fixture, not a customer source."],
        "execution": {"api_key": "must-not-appear-in-export"},
        "request": {"instruction": "old briefing must not appear", "operation_id": "private-old-id"},
        "illustration_generation": {"budget_usd_micros": 999999},
        "private_extra": "must-not-appear-in-export",
    }
    assets = [
        {"id": "assets/source.mp4", "mime_type": "video/mp4", "sha256": context["source"]["sha256"]},
        *(
            {"id": f"assets/{name}", "mime_type": "font/ttf", "sha256": export.sha((export.FONTS / name).read_bytes())}
            for name in ("DejaVuSans.ttf", "DejaVuSerif.ttf")
        ),
    ]
    blocks = [{"type": "input_text", "text": json.dumps({"authorized_context": context, "assets": assets})}]
    for ms in [0, 180, 360, 540, 720, 900]:
        item = frame(ms)
        blocks.extend(
            [
                {"type": "input_text", "text": json.dumps({"version": "source", "at_ms": ms, "sha256": item.sha256})},
                {
                    "type": "input_image",
                    "image_url": "data:image/png;base64," + base64.b64encode(item.png).decode(),
                    "detail": "high",
                },
            ]
        )
    prior = tmp_path / "prior.json"
    prior.write_text(
        json.dumps(
            {
                "model": "local-synthetic-model",
                "max_output_tokens": 64000,
                "instructions": "must-not-appear-in-export",
                "input": [{"role": "user", "content": blocks}],
            }
        )
    )
    direction = tmp_path / "direction.json"
    direction.write_text(json.dumps(direction_data()))
    brief = tmp_path / "brief.txt"
    brief.write_text("Synthetic business Reel; preserve original material and kit.")
    return prior, source, direction, brief


def test_second_stage_export_binds_complete_plan_and_keeps_schema_order(recorded_case):
    from app.tests.unit.test_motion_construction import plan_wire

    job, provenance = export.prepare_case(*recorded_case)
    data = plan_wire()
    data["motion_plan"]["style_id"] = None
    for scene in data["motion_plan"]["scenes"]:
        scene["keyframe_ms"] = (scene["start_ms"] + scene["end_ms"]) // 2
    built = export.implementation_job(job, json.dumps(data))
    files = export.assemble_files(built, provenance)
    assert json.loads(files["manifest.json"])["construction_stage"] == "implementation"
    assert list(json.loads(files["output-contract.json"])["schema"]["properties"]) == [
        "plan_sha256",
        "status",
        "html",
        "scene_init",
        "revision_reason",
    ]
    assert json.loads(files["construction-plan.json"])["scene_direction"] == job.context["request"]["scene_direction"]
    assert len(json.loads(files["input/order.json"])) == 12
    assert b"--plan-output" in files["LEIA-ME.md"]
    with pytest.raises(ValueError):
        export.implementation_job(job, '{"concept":"interrupted')
    data["audio"] = {
        "mode": "mix",
        "tracks": [
            {"asset_id": "assets/source.mp4", "offset_ms": 0, "trim_start_ms": 0, "trim_end_ms": 1000, "volume": 1}
        ],
    }
    with pytest.raises(ValueError, match="ORIGINAL_AUDIO_CHANGED"):
        export.implementation_job(job, json.dumps(data))
    legacy = replace(job, context={k: v for k, v in job.context.items() if k != "generation_contract"})
    with pytest.raises(ValueError, match="STAGED_CONTRACT_REQUIRED"):
        export.implementation_job(legacy, json.dumps(data))


def test_exact_product_payload_and_every_attachment_are_exported_without_secrets_or_calls(recorded_case, tmp_path):
    job, provenance = export.prepare_case(*recorded_case)
    archived = recorded_case[0].read_bytes()
    files = export.assemble_files(job, provenance)
    payload = export.offline_provider(provenance["model"], provenance["max_output_tokens"]).build_request(job)
    assert files["generation-request.json"] == request_bytes(payload)
    assert json.loads(files["manifest.json"])["construction_stage"] == "plan"
    assert list(json.loads(files["output-contract.json"])["schema"]["properties"]) == list(
        payload["text"]["format"]["schema"]["properties"]
    )
    assert b"must-not-appear-in-export" not in b"".join(files.values())
    assert b"private-old-id" not in b"".join(files.values())
    assert b"old briefing must not appear" not in b"".join(files.values())
    assert "illustration_generation" not in job.context
    assert job.context["review_contract"]["version"] == "motion-review-v3"
    assert job.context["skill"]["id"] == "instagram-reel-v13"
    assert job.context["creative_contract"]["version"] == "reel-creative-v7"
    assert files["execution/assets/source.mp4"] == recorded_case[1].read_bytes()
    assert files["execution/libraries/elements-v1.js"] == runtime_bytes()
    assert b"__MOTION_ELEMENTS_CATALOG__" not in files["execution/libraries/elements-v1.js"]
    manifest = json.loads(files["manifest.json"])
    assert len(manifest["images"]) == 12
    assert [image["role"] for image in manifest["images"]] == ["finish_reference_only"] * 6 + ["source"] * 6
    for block in payload["input"][0]["content"]:
        if block["type"] == "input_text":
            assert block["text"].encode() in files["PROMPT-INTEGRAL.md"]
    assert payload["instructions"].encode() in files["PROMPT-INTEGRAL.md"]
    assert json.loads(files["output-contract.json"]) == payload["text"]["format"]
    destination = tmp_path / "package"
    archive = export.write_export(destination, files)
    export.verify_export(destination)
    with zipfile.ZipFile(archive) as zipped:
        assert set(zipped.namelist()) == {"package/" + name for name in files}
        for name, data in files.items():
            assert zipped.read("package/" + name) == data
    assert recorded_case[0].read_bytes() == archived
    assert export.assemble_files(*export.prepare_case(*recorded_case)) == files
    with pytest.raises(ValueError, match="DESTINATION_EXISTS"):
        export.write_export(destination, files)


@pytest.mark.parametrize(
    "change",
    ["source", "asset", "extra_asset", "sample_hash", "sample_kind", "sample_time", "missing_sample", "facts", "logo"],
)
def test_changed_or_unsupported_inputs_stop_before_export(recorded_case, change):
    prior, source, _, _ = recorded_case
    document = json.loads(prior.read_bytes())
    blocks = document["input"][0]["content"]
    data = json.loads(blocks[0]["text"])
    if change == "source":
        source.write_bytes(b"changed")
    elif change == "asset":
        data["assets"][1]["sha256"] = "0" * 64
    elif change == "extra_asset":
        data["assets"].append({"id": "assets/unknown.png"})
    elif change in {"sample_hash", "sample_kind", "sample_time"}:
        meta = json.loads(blocks[1]["text"])
        meta[{"sample_hash": "sha256", "sample_kind": "version", "sample_time": "at_ms"}[change]] = {
            "sample_hash": "0" * 64,
            "sample_kind": "current",
            "sample_time": 2000,
        }[change]
        blocks[1]["text"] = json.dumps(meta)
    elif change == "missing_sample":
        blocks.pop()
    elif change == "facts":
        data["authorized_context"]["confirmed_facts"] = ["unreviewed fact"]
    else:
        data["authorized_context"]["kit"]["overrides"]["logo_asset_id"] = "00000000-0000-4000-8000-000000000001"
    blocks[0]["text"] = json.dumps(data)
    prior.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="EXPORT_"):
        export.prepare_case(*recorded_case)


def test_recorded_asr_and_new_repertoire_use_product_builders(recorded_case):
    from app.services.motion_speech import speech_context

    prior, source, direction, brief = recorded_case
    document = json.loads(prior.read_bytes())
    blocks = document["input"][0]["content"]
    data = json.loads(blocks[0]["text"])
    context = data["authorized_context"]
    context["source"]["has_audio"] = True
    result = {
        "version": "motion-speech-v1",
        "source_sha256": context["source"]["sha256"],
        "provenance": "local_asr_unreviewed",
        "alignment": "word",
        "cues": [{"id": "cue-1", "text": "Olá", "start_ms": 0, "end_ms": 200, "confidence": 0.9}],
        "focus_cue_ids": [],
    }
    context["transcript"] = speech_context({"speech_result": result}, context["source"])
    blocks[0]["text"] = json.dumps(data)
    prior.write_text(json.dumps(document))
    job, provenance = export.prepare_case(prior, source, direction, brief, repertoire_id="business-reel-v2")
    files = export.assemble_files(job, provenance)
    assert job.context["speech_result"] == result
    assert job.context["transcript"] == context["transcript"]
    images = json.loads(files["input/order.json"])
    assert sum(item["role"] == "finish_reference_only" for item in images) == 5
    assert "11 imagens" in files["LEIA-ME.md"].decode()
    assert job.context["repertoire"]["id"] == "business-reel-v2"
    context["transcript"]["text"] = "modified"
    blocks[0]["text"] = json.dumps(data)
    prior.write_text(json.dumps(document))
    with pytest.raises(ValueError, match="EXPORT_SPEECH_CONTEXT_CHANGED"):
        export.prepare_case(prior, source, direction, brief, repertoire_id="business-reel-v2")


def test_export_v4_resolved_synthetic_image_reproduces_product_payload(recorded_case, art_case, tmp_path):  # noqa: F811
    from app.services.motion_generation import construction_plan_hash

    c = art_case
    prior, source, direction, brief = recorded_case
    direction.write_text(c.composition.scene_direction.model_dump_json())
    policy_path = tmp_path / "explicit-policy.json"
    policy_path.write_text(json.dumps(c.prepared.context["illustration_generation"]))
    policy = export.read_illustration_policy(policy_path)
    job, provenance = export.prepare_case(prior, source, direction, brief, illustration_generation=policy)
    data = c.composition.model_dump(mode="json", exclude={"html", "scene_init", "scene_direction"})
    data["motion_plan"]["style_id"] = None
    for scene in data["motion_plan"]["scenes"]:
        scene["keyframe_ms"] = (scene["start_ms"] + scene["end_ms"]) // 2
    output = json.dumps(compact_wire(data))
    with pytest.raises(ValueError, match="RESOLVED_MATERIALS_REQUIRED"):
        export.implementation_job(job, output)
    image = c.provider.generate.return_value
    image_path = tmp_path / "existing.png"
    image_path.write_bytes(image.content)
    material_path = tmp_path / "materials.json"
    material_path.write_text(
        json.dumps(
            [{"asset_id": c.composition.illustrations[0].asset_id, "path": str(image_path), "sha256": image.sha256}]
        )
    )
    built = export.implementation_job(job, output, export.read_resolved_materials(material_path))
    files = export.assemble_files(built, provenance)
    payload = export.offline_provider(provenance["model"], provenance["max_output_tokens"]).build_request(built)
    assert files["generation-request.json"] == request_bytes(payload)
    assert json.loads(files["manifest.json"])["construction_stage"] == "implementation"
    sent = json.loads(payload["input"][0]["content"][0]["text"])
    assert sent["plan_sha256"] == construction_plan_hash(built.construction_plan)
    assert sent["authorized_context"]["implementation_materials"][0]["sha256"] == image.sha256
    assert any(item["role"] == "material" for item in json.loads(files["input/order.json"]))
    policy_path.write_text(json.dumps({**policy, "api_key": "forbidden"}))
    with pytest.raises(ValueError, match="POLICY_INVALID"):
        export.read_illustration_policy(policy_path)


@pytest.mark.parametrize("change", ["bytes", "extra_file", "symlink", "image_mapping"])
def test_package_verifier_rejects_tampering(recorded_case, tmp_path, change):
    files = export.assemble_files(*export.prepare_case(*recorded_case))
    destination = tmp_path / "package"
    export.write_export(destination, files)
    if change == "bytes":
        (destination / "context.json").write_bytes(b"changed")
    elif change == "extra_file":
        (destination / "extra.txt").write_text("untracked")
    elif change == "symlink":
        path = destination / "context.json"
        path.unlink()
        path.symlink_to(recorded_case[0])
    else:
        manifest = json.loads((destination / "manifest.json").read_bytes())
        manifest["images"][0]["file"] = manifest["images"][-1]["file"]
        (destination / "manifest.json").write_bytes(export.pretty(manifest))
    with pytest.raises(ValueError, match="EXPORT_"):
        export.verify_export(destination)


def test_unsafe_destination_member_and_invalid_assets_are_rejected(recorded_case, tmp_path):
    with pytest.raises(ValueError, match="PATH_INVALID"):
        export.write_export(tmp_path / "unsafe", {"../outside": b"invalid"})
    job, provenance = export.prepare_case(*recorded_case)
    changed = replace(job.assets[0], sha256="0" * 64)
    with pytest.raises(ValueError, match="ASSET_INVALID"):
        export.assemble_files(replace(job, assets=(changed, *job.assets[1:])), provenance)


async def test_offline_transport_cannot_submit_even_with_accidental_method_call(recorded_case):
    job, provenance = export.prepare_case(*recorded_case)
    model = export.offline_provider(provenance["model"], provenance["max_output_tokens"])
    with pytest.raises(RuntimeError, match="NETWORK_FORBIDDEN"):
        await model.submit(job, model.build_request(job))


def test_reviewed_speech_export_uses_product_context_and_rejects_another_recording(recorded_case, tmp_path):
    from app.services.auth import AuthError
    from app.tests.unit.test_motion_speech import timing_data

    prior = json.loads(recorded_case[0].read_bytes())
    block = prior["input"][0]["content"][0]
    original = json.loads(block["text"])
    original["authorized_context"]["source"]["has_audio"] = True
    original["authorized_context"]["authorized_audio"] = {
        "mode": "mix",
        "tracks": [
            {"asset_id": "assets/source.mp4", "offset_ms": 0, "trim_start_ms": 0, "trim_end_ms": 1000, "volume": 1.0}
        ],
    }
    block["text"] = json.dumps(original)
    recorded_case[0].write_text(json.dumps(prior))
    timing = timing_data()
    timing["source_sha256"] = export.sha(recorded_case[1].read_bytes())
    timing_path = tmp_path / "speech.json"
    timing_path.write_text(json.dumps(timing))
    job, provenance = export.prepare_case(*recorded_case, speech_timing_path=timing_path)
    assert job.context["transcript"]["cues"] == timing["cues"]
    files = export.assemble_files(job, provenance)
    payload = json.loads(files["generation-request.json"])
    sent = json.loads(payload["input"][0]["content"][0]["text"])["authorized_context"]
    assert sent["transcript"] == job.context["transcript"]
    assert sent["request"]["speech_timing"] == timing
    assert b"owner_reviewed" in files["PROMPT-INTEGRAL.md"]
    timing["source_sha256"] = "f" * 64
    timing_path.write_text(json.dumps(timing))
    with pytest.raises(AuthError, match="MOTION_SPEECH_SOURCE_CHANGED"):
        export.prepare_case(*recorded_case, speech_timing_path=timing_path)
