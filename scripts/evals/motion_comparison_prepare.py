"""Prepare a reviewable comparison through product builders; never dispatch or authorize it."""

import argparse
import json
from pathlib import Path
from typing import Any

from app.adapters.motion_ai import _format
from app.adapters.motion_html_renderer import IMAGE
from app.schemas.motion_generation import CompactProvidedDirectionOutput, MotionImplementationOutputV4
from app.schemas.motion_production import HTMLMotionComposition
from app.services.motion_budget import MAX_INPUT_TOKENS, cost_bound, validate_tariff
from app.services.motion_corrections import correction_enabled
from app.services.motion_generation import asset_informed_enabled
from app.services.motion_protocols import MotionModelRequest
from app.services.motion_review import review_wire_model
from scripts.evals import motion_external_export as export

DIMENSIONS = ("Sentido e ação", "Gravação", "Espaço e objeto", "Ritmo e acabamento", "Som", "Identidade")


def budget_proposal(model: str, output_limit: int, image_policy: dict[str, Any] | None) -> dict[str, Any]:
    """A new proposed reservation, not historical consent, a token estimate or an invoice."""
    input_rate, output_rate, reserve = 2_500_000, 10_000_000, 1_250_000
    validate_tariff(model, input_rate, output_rate)
    ceiling = cost_bound(MAX_INPUT_TOKENS, output_limit, input_rate, output_rate)
    if ceiling["maximum_usd_micros"] > reserve:
        raise ValueError("COMPARISON_OUTPUT_EXCEEDS_PROPOSED_RESERVE")
    images = image_policy["max_images"] if image_policy else 0
    if images > 1:
        raise ValueError("COMPARISON_SUPPORTS_ONE_IMAGE")
    image_reserve = image_policy["reservation_usd_micros"] if image_policy else 0
    return {
        "version": "motion-comparison-budget-proposal-v1",
        "authorized": False,
        "source": "New proposal; no prior budget, approval or reservation is reused.",
        "model": model,
        "per_model_call_reserve_usd_micros": reserve,
        "initial_model_calls": 3,
        "conditional_correction_model_calls": 2,
        "max_corrections": 1,
        "max_images": images,
        "per_image_reserve_usd_micros": image_reserve,
        "initial_reserves_usd_micros": 3 * reserve + images * image_reserve,
        "maximum_reserves_usd_micros": 5 * reserve + images * image_reserve,
        "input_tokens": None,
        "estimated_cost_usd_micros": None,
        "rate_basis": "Existing project admission policy, not independently refreshed supplier pricing.",
        "input_usd_micros_per_million": input_rate,
        "output_usd_micros_per_million": output_rate,
        "construction_output_limit": output_limit,
        "review_output_limit": min(8000, output_limit),
        "qualified_input_limit": MAX_INPUT_TOKENS,
        "construction_bound_at_input_limit": ceiling,
        "local_work": ["ASR if needed", "storyboard", "up to two complete renders", "local correction guard"],
        "conditions": [
            "New explicit owner authorization and configured per-request/monthly/global balances.",
            "Real token count and cost admission before each submitted model call; no remote count done here.",
            "One attempt per effect; uncertainty, invalid output or failed preflight stops without extra calls.",
            "One correction only if explicitly included; no new image in correction.",
            "Image policy is a proposal, not an image-generation permit.",
        ],
    }


def comparison_files(
    job: MotionModelRequest,
    provenance: dict[str, Any],
    *,
    prior_payload: Path,
    baseline_video: Path,
    baseline_sha256: str,
    baseline_composition: Path,
    executor_image: str | None = None,
) -> dict[str, bytes]:
    if not asset_informed_enabled(job.context) or not correction_enabled(job.context) or job.construction_plan:
        raise ValueError("COMPARISON_CURRENT_PLANNING_CONTRACT_REQUIRED")
    if job.context.get("authorized_soundtrack") or job.context["request"].get("sound_events"):
        raise ValueError("COMPARISON_AUDIO_MATERIALS_REQUIRE_SEPARATE_PREPARATION")
    if executor_image is not None and IMAGE.fullmatch(executor_image) is None:
        raise ValueError("COMPARISON_EXECUTOR_DIGEST_REQUIRED")
    video = baseline_video.read_bytes()
    if export.sha(video) != baseline_sha256 or video[4:8] != b"ftyp":
        raise ValueError("COMPARISON_BASELINE_CHANGED")
    archived = json.loads(prior_payload.read_bytes())
    old = json.loads(archived["input"][0]["content"][0]["text"])["authorized_context"]
    base = HTMLMotionComposition.model_validate_json(baseline_composition.read_bytes())
    preserved = {
        key: old[key] == job.context[key] for key in ("source", "kit", "authorized_audio", "output", "transcript")
    }
    preserved["baseline_composition_audio"] = base.audio.model_dump(mode="json") == job.context["authorized_audio"]
    preserved["model"] = archived["model"] == provenance["model"]
    preserved["max_output_tokens"] = archived["max_output_tokens"] == provenance["max_output_tokens"]
    if not all(preserved.values()):
        raise ValueError("COMPARISON_BASELINE_CONTEXT_CHANGED")
    files = export.assemble_files(job, provenance)
    budget = budget_proposal(
        provenance["model"], provenance["max_output_tokens"], job.context.get("illustration_generation")
    )
    pipeline = [
        {"stage": "planning", "state": "prepared_not_sent", "exact_payload": "generation-request.json"},
        {"stage": "materials", "state": "pending_validated_plan", "exact_payload": None},
        {"stage": "implementation", "state": "pending_plan_and_material_pixels", "exact_payload": None},
        {"stage": "storyboard", "state": "pending_code_and_owner_decision", "exact_payload": None},
        {"stage": "render", "state": "pending_storyboard_approval", "exact_payload": None},
        {"stage": "review", "state": "pending_rendered_evidence", "exact_payload": None},
        {"stage": "correction", "state": "conditional_on_authorization_and_localized_issue", "exact_payload": None},
        {"stage": "correction_review", "state": "conditional_on_local_regression_guard", "exact_payload": None},
    ]
    files.update(
        {
            "baseline/video.mp4": video,
            "baseline/composition.json": export.pretty(base.model_dump(mode="json")),
            "pipeline.json": export.pretty(pipeline),
            "budget-proposal.json": export.pretty(budget),
            "contracts/implementation.json": export.pretty(_format(MotionImplementationOutputV4)),
            "contracts/review.json": export.pretty(_format(review_wire_model(job.context))),
            "contracts/correction.json": export.pretty(_format(CompactProvidedDirectionOutput)),
            "rubric.json": export.pretty(
                {
                    "owner_acceptance": None,
                    "dimensions": [
                        {"name": name, "verdict": "not_evaluated", "reason": "No new piece exists.", "evidence": []}
                        for name in DIMENSIONS
                    ],
                }
            ),
            "comparison.json": export.pretty(
                {
                    "version": "motion-comparison-preparation-v1",
                    "execution_ready": False,
                    "executor_image": executor_image,
                    "executor_qualified": False,
                    "baseline_video_sha256": baseline_sha256,
                    "preserved": preserved,
                    "source_sha256": job.context["source"]["sha256"],
                    "source_samples": len(job.source_frames),
                    "finish_references": len(job.reference_images),
                    "source_duration_ms": job.context["source"]["duration_ms"],
                    "audio": "Original recording only; supplemental-audio A/B not available in this preparation.",
                    "differences": [
                        "Brief and direction revised; skill/repertoire/temporal/material/correction contracts updated.",
                        "Storyboard is an owner gate before MP4; baseline ran without that gate.",
                        "One conditional bounded correction proposed; baseline ran without corrections.",
                        "Cup pixels from baseline are not included; "
                        "current representation follows scene-direction.json.",
                    ],
                    "blockers": [
                        "Explicit owner authorization and new budget absent.",
                        (
                            "Rebuilt executor digest supplied; runtime qualification still pending."
                            if executor_image
                            else "Executor image must contain stage 5/6 changes and pass qualification."
                        ),
                        "Fresh API/Temporal admission and asset availability have not been checked against dev.",
                        "ASR is archived and unreviewed; actual run must record its source/timing and any differences.",
                        "Later exact prompts depend on actual responses; no synthetic response is substituted.",
                    ],
                    "causal_claim": "Comparison of the combined changes; not an isolated experiment per feature.",
                    "visual_quality_validated": False,
                    "network_calls": 0,
                    "rendered": False,
                }
            ),
            "manual-interventions.json": export.pretty(
                {
                    "preparation": provenance["changes"],
                    "generated_code_edits": [],
                    "new_piece": None,
                }
            ),
        }
    )
    files["LEIA-ME.md"] = (
        "# Comparação de qualidade motion — preparação\n\n"
        "Entrada de plano montada pelo produto; nenhuma chamada, peça ou aprovação nova. "
        "Não execute via chat manual: a rodada deve usar API/Temporal e o dev existente, com autorização nova.\n\n"
        "`generation-request.json` contém o payload exato disponível; `PROMPT-INTEGRAL.md` é sua projeção legível. "
        "Schemas futuros em `contracts/` não são prompts executados. `pipeline.json` declara dependências "
        "sem inventar plano, ilustração, implementação, crítica ou correção.\n\n"
        "`comparison.json` declara invariantes, diferenças e bloqueios. `baseline/video.mp4` é cópia íntegra "
        "da base, não uma nova peça. Não existe candidata ou comparação lado a lado ainda. "
        "`rubric.json` permanece não avaliada até evidência real e parecer do titular.\n\n"
        "`budget-proposal.json` é reserva máxima proposta, não estimativa, fatura ou autorização. "
        "Sem transações no ledger; não usa aprovações históricas. Aprovar storyboard antes do MP4; "
        "no máximo uma correção se incluída expressamente. Os cinco serviços interrompidos permanecem parados.\n\n"
        "Verificar: `.venv/bin/python -m scripts.evals.motion_external_export --verify CAMINHO`.\n"
    ).encode()
    manifest = json.loads(files.pop("manifest.json"))
    manifest.update(
        purpose="Preparação de comparação pelo produto; execução pendente de autorização",
        comparison_preparation=True,
        files=[{"path": name, "bytes": len(data), "sha256": export.sha(data)} for name, data in sorted(files.items())],
    )
    files["manifest.json"] = export.pretty(manifest)
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("prior-payload", "source", "direction", "brief", "baseline-video", "baseline-composition", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--baseline-sha256", required=True)
    parser.add_argument("--illustration-policy", type=Path)
    parser.add_argument("--executor-image", help="Digest of rebuilt image; does not assert runtime qualification")
    args = parser.parse_args()
    policy = export.read_illustration_policy(args.illustration_policy) if args.illustration_policy else None
    job, provenance = export.prepare_case(
        args.prior_payload,
        args.source,
        args.direction,
        args.brief,
        repertoire_id="business-reel-v2",
        illustration_generation=policy,
    )
    files = comparison_files(
        job,
        provenance,
        prior_payload=args.prior_payload,
        baseline_video=args.baseline_video,
        baseline_sha256=args.baseline_sha256,
        baseline_composition=args.baseline_composition,
        executor_image=args.executor_image,
    )
    archive = export.write_export(args.output, files)
    print(
        json.dumps(
            {
                "folder": str(args.output),
                "archive": str(archive),
                "network_calls": 0,
                "execution_ready": False,
                "manifest_sha256": export.sha(files["manifest.json"]),
            }
        )
    )


if __name__ == "__main__":
    main()
