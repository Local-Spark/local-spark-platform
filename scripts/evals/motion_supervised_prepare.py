"""Read existing scoped product context, export its real input, never admit or execute a request."""

import argparse
import asyncio
import json
from dataclasses import replace
from pathlib import Path
from uuid import UUID, uuid5

from sqlalchemy import make_url, text

from app.adapters.material_media import MaterialStore
from app.adapters.motion_inputs import MotionInputLoader
from app.core.config import get_settings
from app.db.session import Database
from app.schemas.motion_production import MotionRequest
from app.schemas.motion_speech import MotionSpeechTiming
from app.services.auth import AuthError
from app.services.motion_context import MotionContext
from app.services.motion_protocols import MotionModelRequest
from app.services.motion_quality import require_quality_readiness
from app.services.motion_speech import speech_context
from app.services.whatsapp_materials import WhatsAppMaterialsService
from scripts.evals.motion_external_export import assemble_files, pretty, sha, verify_export, write_export
from scripts.evals.motion_preparation_speech import prepare_speech


def reuse_speech(prepared, timing):
    if prepared.context.get("quality_contract") is not None:
        raise ValueError("PRODUCTION_PREPARATION_ARCHIVED_SPEECH_FORBIDDEN")
    value = MotionSpeechTiming.model_validate(timing)
    if value.source_sha256 != prepared.context["source"]["sha256"]:
        raise ValueError("PREPARATION_SPEECH_SOURCE_CHANGED")
    context = {**prepared.context, "speech_result": value.model_dump(mode="json")}
    context["transcript"] = speech_context(context, context["source"])
    context["limitations"] = [
        "ASR histórico da mesma fonte/hash reutilizado, sem nova transcrição ou escuta.",
        "Quadros da fonte e base não demonstram movimento contínuo nem qualidade sonora.",
        "Interpretação da mensagem e direção ainda serão propostas pelo modelo, após orçamento novo.",
    ]
    return replace(prepared, context=context)


async def prepare(args):
    body = MotionRequest.model_validate_json(args.request.read_bytes())
    if not body.propose_direction or not body.review_checkpoints or body.evolution is not None:
        raise ValueError("SUPERVISED_PROPOSAL_REQUIRED")
    identity = json.loads(args.identity.read_bytes())["ids"]
    tenant, business, actor = (UUID(identity[key]) for key in ("tenant", "business", "actor"))
    cfg = get_settings().model_copy(update={"motion_storyboard_enabled": True, "motion_illustrations_enabled": False})
    if cfg.environment != "development" or make_url(cfg.database_url.get_secret_value()).database != args.database_name:
        raise ValueError("PREPARATION_EXISTING_DEVELOPMENT_DATABASE_REQUIRED")
    ctx, db = MotionContext(cfg), Database(cfg)
    try:
        async with db.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            snapshot = await ctx.capture(session, tenant, business, body)
            revision = await session.scalar(text("SELECT version_num FROM alembic_version"))
        # All storage reads and media decoding occur after releasing SQL locks.
        prepared = await MotionInputLoader(MaterialStore(cfg), ctx).prepare(snapshot)
        if args.speech_timing is not None:
            prepared = reuse_speech(prepared, json.loads(args.speech_timing.read_bytes()))
        prepared = await prepare_speech(
            prepared, cfg, body.operation_id, args.output.with_name(args.output.name + "-speech")
        )
        readiness_issue = None
        try:
            require_quality_readiness(prepared.context)
        except AuthError as exc:
            readiness_issue = exc.code
        job = MotionModelRequest(
            uuid5(body.operation_id, "generate:plan:0"),
            "generate",
            prepared.context,
            prepared.assets,
            source_frames=prepared.source_frames,
            baseline_frames=prepared.baseline_frames,
            asset_previews=prepared.asset_previews,
            reference_images=prepared.reference_images,
        )
        provenance = {
            "model": args.model,
            "max_output_tokens": args.max_output_tokens,
            "changes": [
                "Scoped existing product context, no admission or provider IO.",
                "Natural client message; direction/functions/sound choices await planning and review.",
            ],
        }
        files = assemble_files(job, provenance)
        files["snapshot.json"] = pretty(snapshot)
        files["request.json"] = pretty(body.model_dump(mode="json"))
        listening_reports = [item.id for item in body.preparation.evidence if item.kind == "audio"]
        report = {
            "state": "prepared_with_gaps_not_for_submission" if readiness_issue else "prepared_before_new_budget",
            "database_revision": revision,
            "runtime_mode": cfg.motion_ai_mode,
            "proposed_model": args.model,
            "proposed_max_output_tokens": args.max_output_tokens,
            "request_admitted": False,
            "model_calls": 0,
            "paid_calls": 0,
            "renders": 0,
            "client_message": body.preparation.client_message,
            "direction": "pending_model_proposal_then_exact_plan_approval",
            "source_frames": len(prepared.source_frames),
            "source_times_ms": [f.ms for f in prepared.source_frames],
            "baseline_frames": len(prepared.baseline_frames),
            "reference_images": len(prepared.reference_images),
            "material_previews": len(prepared.asset_previews),
            "sound_candidates": len(prepared.context.get("sound_library", {}).get("items", [])),
            "selected_sound_events": 0,
            "sound_listening": "human_reports_bound_to_files" if listening_reports else "pending",
            "human_listening_evidence": listening_reports,
            "quality_validated": False,
            "payload_sha256": sha(files["generation-request.json"]),
            "submission_authorized": False,
            "planning_readiness_issue": readiness_issue,
            "speech": {
                "policy": prepared.context.get("speech_recognition"),
                "provenance": prepared.context.get("speech_result", {}).get("provenance"),
                "words": len(prepared.context.get("speech_result", {}).get("cues", [])),
                "new_local_transcription": prepared.context.get("speech_result") is not None,
                "journal": args.output.name + "-speech",
            },
            "quality_profile": prepared.context.get("quality_contract", {}).get("version"),
            "pending": [
                "Revisar esta entrada e definir/autorizar orçamento novo antes da primeira chamada paga.",
                "Revisar por cena o plano recebido antes de aprovar implementação.",
                "Eventos, cortes, ganhos e inteligibilidade da mistura dependem do plano e de escuta futura.",
                *([] if listening_reports else ["Adequação dos arquivos sonoros ainda depende de escuta."]),
                "Parar no checkpoint de código, antes de qualquer render, inclusive storyboard.",
                *body.preparation.unresolved,
                *([readiness_issue] if readiness_issue else []),
            ],
        }
        files["preparation-report.json"] = pretty(report)
        files["LEIA-ME.md"] = (
            "# Preparação pelo produto — ainda não enviada\n\n"
            "Entrada exata: generation-request.json; leitura: PROMPT-INTEGRAL.md; contexto: context.json.\n"
            "MotionContext.capture → MotionInputLoader.prepare → OpenAIMotionProvider.build_request, com transporte "
            "offline que rejeita rede. Apenas leitura do negócio existente; sem admissão, gasto ou render.\n\n"
            "Mensagem é simulada. Negócio/kit/fatos/materiais vieram do produto. Direção e som ainda serão "
            "propostos no plano, com orçamento novo. Relatos humanos de escuta, quando fornecidos, "
            "ficam vinculados aos hashes dos arquivos em preparation_evidence; não são escuta do servidor "
            "nem aprovação de eventos ou mistura. "
            "Oito prints retirados; exemplos de código e evidências da fonte/base preservados.\n\n"
            "Novas peças usam os critérios de qualidade do produto, sem frames, composição ou material "
            "recuperado de peças anteriores. Históricos do ensaio continuam fora desta entrada. "
            "No modo de produção, ASR arquivado não é injetado pelo exportador. Havendo política local configurada, "
            "o mesmo serviço/adapter do runtime executa ASR novo, com claim/recibo privados desta preparação. "
            "Eventuais lacunas de fala "
            "ou preparação são explícitas no relatório e impedem gastar com o plano.\n\n"
            "Revisar por cena fala, gravação, objeto, fundo, texto, transição e som nos tempos do plano. "
            "Aprovação exata de plan permite gerar código. Parar em awaiting_render: não aprovar render "
            "nem storyboard nesta rodada. Nenhum orçamento anterior autoriza envio.\n"
        ).encode()
        manifest = json.loads(files.pop("manifest.json"))
        manifest.update(
            purpose="Product preparation, no paid IO or render",
            files=[{"path": key, "bytes": len(value), "sha256": sha(value)} for key, value in sorted(files.items())],
        )
        files["manifest.json"] = pretty(manifest)
        write_export(args.output, files)
        verify_export(args.output)
        return report
    finally:
        await db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--identity", type=Path, required=True)
    parser.add_argument("--database-name", required=True)
    parser.add_argument("--speech-timing", type=Path)
    parser.add_argument("--model", required=True, help="Offline proposal; never enables execution")
    parser.add_argument("--max-output-tokens", type=int, default=54000)
    parser.add_argument("--output", type=Path, required=True)
    report = asyncio.run(prepare(parser.parse_args()))
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
