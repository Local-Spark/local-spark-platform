"""Read existing owner context and export the real recovery input; never dispatch or submit."""

import argparse
import asyncio
import json
from pathlib import Path
from uuid import UUID

from app.adapters.material_media import MaterialStore
from app.adapters.motion_inputs import MotionInputLoader
from app.core.config import get_settings
from app.db.session import Database
from app.schemas.motion_production import MotionRequest
from app.schemas.motion_speech import MotionSpeechTiming
from app.services.motion_context import MotionContext
from app.services.motion_protocols import MotionModelRequest
from app.services.motion_speech import speech_context
from scripts.evals.motion_comparison_prepare import comparison_files
from scripts.evals.motion_external_export import pretty, sha, verify_export, write_export


async def prepare(args: argparse.Namespace) -> dict[str, object]:
    body = MotionRequest.model_validate_json(args.request.read_bytes())
    if body.evolution is None:
        raise ValueError("RECOVERY_EVOLUTION_REQUIRED")
    # Configure only capture, not execution/budgets/providers. No worker or API is invoked.
    cfg = get_settings().model_copy(update={"motion_storyboard_enabled": True, "motion_illustrations_enabled": False})
    if cfg.environment != "development":
        raise ValueError("RECOVERY_EXISTING_DEVELOPMENT_REQUIRED")
    context = MotionContext(cfg)
    database = Database(cfg)
    try:
        async with database.transaction(args.tenant, args.actor) as session:
            # Product capture uses SELECT FOR SHARE; this is a read with locks, no DML.
            snapshot = await context.capture(session, args.tenant, args.business, body)
        prepared = await MotionInputLoader(MaterialStore(cfg), context).prepare(snapshot)
        old = json.loads(args.prior_payload.read_bytes())
        archived = json.loads(old["input"][0]["content"][0]["text"])["authorized_context"]
        timing = MotionSpeechTiming.model_validate(
            {
                key: archived["transcript"][key]
                for key in MotionSpeechTiming.model_fields
                if key in archived["transcript"]
            }
        )
        if timing.source_sha256 != prepared.context["source"]["sha256"] or timing.provenance != "local_asr_unreviewed":
            raise ValueError("RECOVERY_SPEECH_SOURCE_CHANGED")
        ctx = {**prepared.context, "speech_result": timing.model_dump(mode="json")}
        ctx["transcript"] = speech_context(ctx, ctx["source"])
        job = MotionModelRequest(
            body.operation_id,
            "generate",
            ctx,
            prepared.assets,
            source_frames=prepared.source_frames,
            asset_previews=prepared.asset_previews,
            reference_images=prepared.reference_images,
            baseline_frames=prepared.baseline_frames,
        )
        provenance = {
            "model": old["model"],
            "max_output_tokens": old["max_output_tokens"],
            "changes": [
                "Explicit historical baseline and preservation matrix; reused original illustration.",
                "Recorded unreviewed ASR for preparation; live admission/ASR must be checked again.",
            ],
        }
        files = comparison_files(
            job,
            provenance,
            prior_payload=args.prior_payload,
            baseline_video=args.baseline_video,
            baseline_sha256=body.evolution.baseline_video_sha256,
            baseline_composition=args.baseline_composition,
        )
        files["request-body.json"] = pretty(body.model_dump(mode="json"))
        comparison = json.loads(files["comparison.json"])
        comparison["differences"][-1] = (
            "Original baseline illustration is included, hash-verified, as an authorized asset."
        )
        comparison["blockers"][2] = (
            "Existing owner context and material availability verified; fresh API/Temporal admission still pending."
        )
        comparison["provider_calls"] = comparison.pop("network_calls")
        comparison["preparation_io"] = "Existing owner-scoped database/storage reads and decoding existing videos only."
        files["comparison.json"] = pretty(comparison)
        files["recovery.json"] = pretty(
            {
                "version": "motion-recovery-preparation-v1",
                "authorized": False,
                "execution_ready": False,
                "baseline_frames": len(prepared.baseline_frames),
                "reused_images": len(body.evolution.reuse_illustration_ids),
                "reference_context": prepared.context.get("reference_context"),
                "collection_photos_selected": len(snapshot.get("collection_photos", [])),
                "reference_images": len(prepared.reference_images),
                "available_materials": prepared.context.get("available_materials", []),
                "generation_calls": 0,
                "renders": 0,
                "blockers": [
                    "New explicit budget authorization",
                    "Full CI/qualified executor before execution",
                    "Fresh admission and actual ASR/input verification",
                    "Owner storyboard approval before MP4",
                ],
            }
        )
        manifest = json.loads(files.pop("manifest.json"))
        manifest["files"] = [
            {"path": name, "bytes": len(data), "sha256": sha(data)} for name, data in sorted(files.items())
        ]
        files["manifest.json"] = pretty(manifest)
        write_export(args.output, files)
        verify_export(args.output)
        return {
            "folder": str(args.output),
            "baseline_frames": len(prepared.baseline_frames),
            "generation_calls": 0,
            "renders": 0,
            "authorized": False,
            "manifest_sha256": sha(files["manifest.json"]),
        }
    finally:
        await database.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("tenant", "business", "actor"):
        parser.add_argument("--" + name, type=UUID, required=True)
    for name in ("request", "prior-payload", "baseline-video", "baseline-composition", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    print(json.dumps(asyncio.run(prepare(parser.parse_args()))))


if __name__ == "__main__":
    main()
