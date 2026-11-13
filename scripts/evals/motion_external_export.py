"""Offline export through product builders. No env, database, provider IO or rendering."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import zipfile
from dataclasses import replace
from pathlib import Path
from typing import Any, Literal
from uuid import NAMESPACE_URL, uuid5

import httpx

from app.adapters.motion_ai import OpenAIMotionProvider, request_bytes
from app.adapters.motion_html_renderer import ASSET_ID, RenderAsset, RenderedFrame
from app.adapters.motion_inputs import FONTS, PreparedMotionInput
from app.schemas.brand_kits import BrandKitVersion
from app.schemas.motion_production import MotionRequest
from app.schemas.motion_scene_direction import MotionSceneDirection
from app.schemas.motion_speech import MotionSpeechTiming
from app.services.motion_context import capture_motion_guidance
from app.services.motion_elements import ROOT as ELEMENTS_ROOT
from app.services.motion_elements import elements_hash, runtime_bytes
from app.services.motion_generation import asset_informed_enabled, decode_construction_plan, staged_generation_enabled
from app.services.motion_illustrations import validate_declarations
from app.services.motion_materials import prepare_implementation_materials
from app.services.motion_movement import movement_bytes, movement_hash
from app.services.motion_protocols import MotionModelRequest
from app.services.motion_repertoire import load_repertoire_images
from app.services.motion_speech import speech_context

ROOT = Path(__file__).resolve().parents[2]
FACTUAL_FIELDS = frozenset(
    {
        "schema",
        "kit",
        "context_version",
        "preferences",
        "confirmed_facts",
        "reference_context",
        "source",
        "authorized_audio",
        "output",
        "transcript",
        "limitations",
    }
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pretty(value: Any, *, sort_keys: bool = True) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=sort_keys) + "\n").encode()


def offline_provider(model: str, limit: int) -> OpenAIMotionProvider:
    def forbidden(_: httpx.Request) -> httpx.Response:
        raise RuntimeError("OFFLINE_EXPORT_NETWORK_FORBIDDEN")

    # Required constructor placeholder, never a credential or an authorized tariff/budget.
    return OpenAIMotionProvider(
        "offline-placeholder",
        model=model,
        max_output_tokens=limit,
        input_usd_micros_per_million_tokens=1,
        output_usd_micros_per_million_tokens=1,
        transport=httpx.MockTransport(forbidden),
    )


def prepare_case(
    prior_payload: Path,
    source_path: Path,
    direction_path: Path,
    brief_path: Path,
    speech_timing_path: Path | None = None,
    repertoire_id: Literal["business-reel-v1", "business-reel-v2", "business-reel-v3"] = "business-reel-v1",
    illustration_generation: dict[str, Any] | None = None,
) -> tuple[MotionModelRequest, dict[str, Any]]:
    """Replay verified media/context from this recorded proof; never claim fresh DB admission."""
    archived_bytes = prior_payload.read_bytes()
    archived = json.loads(archived_bytes)
    blocks = archived["input"][0]["content"]
    recorded = json.loads(blocks[0]["text"])
    prior = recorded["authorized_context"]
    # This slice intentionally supports the existing proof without new facts, images or external context.
    if prior["confirmed_facts"] or prior["reference_context"]:
        raise ValueError("EXPORT_CASE_REQUIRES_REVIEW")
    kit = BrandKitVersion.model_validate(prior["kit"])
    if kit.state != "confirmed" or kit.overrides.logo_asset_id is not None:
        raise ValueError("EXPORT_CASE_KIT_UNSUPPORTED")
    if prior["source"]["asset_id"] != "assets/source.mp4" or prior["source"]["sha256"] != sha(source_path.read_bytes()):
        raise ValueError("EXPORT_SOURCE_CHANGED")
    direction = MotionSceneDirection.model_validate_json(direction_path.read_bytes())
    seed = sha(archived_bytes) + sha(direction_path.read_bytes()) + sha(brief_path.read_bytes()) + repertoire_id
    if illustration_generation is not None:
        seed += sha(pretty(illustration_generation))
    timing = MotionSpeechTiming.model_validate_json(speech_timing_path.read_bytes()) if speech_timing_path else None
    if timing is not None:
        seed += sha(pretty(timing.model_dump(mode="json")))
    body = MotionRequest(
        operation_id=uuid5(NAMESPACE_URL, "offline-motion-export/" + seed),
        source_asset_id=uuid5(NAMESPACE_URL, "offline-motion-source/" + prior["source"]["sha256"]),
        instruction=brief_path.read_text().strip(),
        storyboard=True,
        repertoire_id=repertoire_id,
        scene_direction=direction,
        speech_timing=timing,
    )
    context = {key: prior[key] for key in FACTUAL_FIELDS}
    # Fresh product guidance, not a hand-maintained prompt or a mutation of the historical request.
    context.update(capture_motion_guidance(body, illustration_generation=illustration_generation))
    if timing is not None:
        context["transcript"] = speech_context(context, context["source"])
        context["limitations"] = [
            "Owner-reviewed timing supplied, not automatic listening; preserve the entire original audio.",
            "Source sampling does not show continuous movement.",
        ]
    elif prior["transcript"] is not None:
        transcript = prior["transcript"]
        timing_fields = set(MotionSpeechTiming.model_fields)
        recorded_timing = MotionSpeechTiming.model_validate({key: transcript[key] for key in timing_fields})
        if recorded_timing.provenance != "local_asr_unreviewed":
            raise ValueError("EXPORT_SPEECH_PROVENANCE_UNSUPPORTED")
        context["speech_result"] = recorded_timing.model_dump(mode="json")
        context["transcript"] = speech_context(context, context["source"])
        if context["transcript"] != transcript:
            raise ValueError("EXPORT_SPEECH_CONTEXT_CHANGED")
    expected_assets = {
        "assets/source.mp4": ("video/mp4", source_path),
        "assets/DejaVuSans.ttf": ("font/ttf", FONTS / "DejaVuSans.ttf"),
        "assets/DejaVuSerif.ttf": ("font/ttf", FONTS / "DejaVuSerif.ttf"),
    }
    if {a["id"] for a in recorded["assets"]} != set(expected_assets):
        raise ValueError("EXPORT_CASE_ASSETS_UNSUPPORTED")
    assets = []
    for item in recorded["assets"]:
        mime, path = expected_assets[item["id"]]
        data = path.read_bytes()
        if mime != item["mime_type"] or sha(data) != item["sha256"]:
            raise ValueError("EXPORT_ASSET_CHANGED")
        assets.append(RenderAsset(item["id"], mime, data, sha(data)))
    frames = []
    if len(blocks) < 13 or len(blocks) % 2 != 1:
        raise ValueError("EXPORT_SOURCE_SAMPLES_REQUIRED")
    for label, image in zip(blocks[1::2], blocks[2::2], strict=True):
        meta = json.loads(label["text"])
        if label["type"] != "input_text" or image["type"] != "input_image":
            raise ValueError("EXPORT_SOURCE_SAMPLE_INVALID")
        prefix, encoded = image["image_url"].split(",", 1)
        png = base64.b64decode(encoded, validate=True)
        if "finish_reference" in meta:
            reference = meta["finish_reference"]
            if prefix != "data:image/jpeg;base64" or sha(png) != reference["sha256"]:
                raise ValueError("EXPORT_REFERENCE_SAMPLE_INVALID")
            continue  # Historical references are replaced by the newly selected product repertoire.
        if meta.get("version") != "source":
            raise ValueError("EXPORT_SOURCE_SAMPLE_INVALID")
        if prefix != "data:image/png;base64" or sha(png) != meta["sha256"]:
            raise ValueError("EXPORT_SOURCE_SAMPLE_INVALID")
        frames.append(RenderedFrame(meta["at_ms"], png, meta["sha256"]))
    times = [f.ms for f in frames]
    if (
        len(times) != 6
        or times != sorted(set(times))
        or min(times) < 0
        or max(times) >= context["source"]["duration_ms"]
    ):
        raise ValueError("EXPORT_SOURCE_SAMPLE_INVALID")
    job = MotionModelRequest(
        uuid5(body.operation_id, "generate:0"),
        "generate",
        context,
        assets=tuple(assets),
        source_frames=tuple(frames),
        reference_images=load_repertoire_images(context),
    )
    provenance = {
        "recorded_payload_sha256": sha(archived_bytes),
        "direction_sha256": sha(direction_path.read_bytes()),
        "brief_sha256": sha(brief_path.read_bytes()),
        "model": archived["model"],
        "max_output_tokens": archived["max_output_tokens"],
        "origin": "Contexto factual e seis quadros da prova Café Pausa registrada; não houve nova consulta ao banco.",
        "changes": [
            "Briefing e direção fornecidos para esta preparação; sem alegação de aceite dos quadros/vídeo.",
            "Contratos, skill e repertório montados nas versões atuais pelo mesmo assembler do produto.",
            "IDs operacionais substituídos por identificadores locais sem vínculo de execução no banco.",
            (
                "Política de ilustração explicitamente fornecida para exportação offline; não autoriza gasto."
                if illustration_generation is not None
                else "Geração de ilustrações desabilitada nesta entrada; nenhum orçamento anterior reutilizado."
            ),
            "Vídeo, fontes, metadados e seis amostras preservados por hash; sem extração ou render novos.",
        ],
    }
    return job, provenance


def implementation_job(
    job: MotionModelRequest, output: str, resolved_assets: tuple[RenderAsset, ...] = ()
) -> MotionModelRequest:
    """Validate a complete planning response locally; never repair partial JSON or dispatch."""
    if not staged_generation_enabled(job.context):
        raise ValueError("EXPORT_STAGED_CONTRACT_REQUIRED")
    plan = decode_construction_plan(output, job.context)
    prepared = PreparedMotionInput(
        job.context,
        job.assets,
        job.source_frames,
        job.context["output"]["duration_ms"],
        job.context["authorized_audio"],
        job.asset_previews,
        job.reference_images,
    )
    validate_declarations(plan, prepared)
    if plan.audio.model_dump(mode="json") != prepared.audio:
        raise ValueError("EXPORT_ORIGINAL_AUDIO_CHANGED")
    if asset_informed_enabled(job.context):
        declared = {item.asset_id for item in plan.illustrations}
        if (
            {asset.id for asset in resolved_assets} != declared
            or len(resolved_assets) != len(declared)
            or any(asset.mime_type != "image/png" or sha(asset.data) != asset.sha256 for asset in resolved_assets)
        ):
            raise ValueError("EXPORT_RESOLVED_MATERIALS_REQUIRED")
        prepared = replace(
            prepared,
            assets=prepared.assets + resolved_assets,
            context={
                **prepared.context,
                "available_materials": [
                    *prepared.context.get("available_materials", []),
                    *[
                        {
                            "asset_id": asset.id,
                            "sha256": asset.sha256,
                            "role": "offline_supplied_illustration",
                            "identity_rule": "Proveniência fornecida offline; não é foto documental.",
                        }
                        for asset in resolved_assets
                    ],
                ],
            },
        )
        prepared = prepare_implementation_materials(plan, prepared)
    elif resolved_assets:
        raise ValueError("EXPORT_RESOLVED_MATERIALS_UNEXPECTED")
    return replace(
        job,
        operation_id=uuid5(job.operation_id, "implementation"),
        construction_plan=plan,
        context=prepared.context,
        assets=prepared.assets,
        asset_previews=prepared.asset_previews,
    )


def read_resolved_materials(path: Path) -> tuple[RenderAsset, ...]:
    """Read explicitly supplied local PNGs, requiring their declared digests; no generation or IO to a provider."""
    entries = json.loads(path.read_bytes())
    if not isinstance(entries, list) or len(entries) > 2:
        raise ValueError("EXPORT_RESOLVED_MATERIALS_INVALID")
    result = []
    for item in entries:
        if not isinstance(item, dict) or set(item) != {"asset_id", "path", "sha256"}:
            raise ValueError("EXPORT_RESOLVED_MATERIALS_INVALID")
        source = Path(item["path"])
        if not 0 < source.stat().st_size <= 8 * 1024 * 1024:
            raise ValueError("EXPORT_RESOLVED_MATERIALS_INVALID")
        data = source.read_bytes()
        if not ASSET_ID.fullmatch(item["asset_id"]) or sha(data) != item["sha256"]:
            raise ValueError("EXPORT_RESOLVED_MATERIALS_INVALID")
        result.append(RenderAsset(item["asset_id"], "image/png", data, item["sha256"]))
    return tuple(result)


def read_illustration_policy(path: Path) -> dict[str, Any]:
    """Explicit offline policy only; reject extra fields that could carry credentials."""
    policy = json.loads(path.read_bytes())
    fields = {
        "version",
        "model",
        "quality",
        "size",
        "output_format",
        "background",
        "max_images",
        "reservation_usd_micros",
        "budget_usd_micros",
        "cost_policy",
        "rules",
    }
    if (
        not isinstance(policy, dict)
        or set(policy) != fields
        or policy.get("version") != "motion-illustrations-v1"
        or policy.get("output_format") != "png"
        or policy.get("background") != "transparent"
        or type(policy.get("max_images")) is not int
        or not 1 <= policy["max_images"] <= 2
        or any(
            type(policy.get(key)) is not int or policy[key] <= 0
            for key in ("reservation_usd_micros", "budget_usd_micros")
        )
        or policy["reservation_usd_micros"] > policy["budget_usd_micros"]
        or any(
            not isinstance(policy.get(key), str) or not 0 < len(policy[key]) <= 4000
            for key in ("model", "quality", "size", "cost_policy", "rules")
        )
    ):
        raise ValueError("EXPORT_ILLUSTRATION_POLICY_INVALID")
    return policy


def assemble_files(job: MotionModelRequest, provenance: dict[str, Any]) -> dict[str, bytes]:
    model = offline_provider(provenance["model"], provenance["max_output_tokens"])
    payload = model.build_request(job)
    files = {
        "generation-request.json": request_bytes(payload),
        "instructions.txt": payload["instructions"].encode(),
        "context.json": pretty(job.context),
        "motion-request.json": pretty(job.context["request"]),
        "output-contract.json": pretty(payload["text"]["format"], sort_keys=False),
        "parameters.json": pretty({k: v for k, v in payload.items() if k not in {"input", "instructions", "text"}}),
    }
    if job.context["request"].get("scene_direction") is not None:
        files["scene-direction.json"] = pretty(job.context["request"]["scene_direction"])
    prompt = ["# Entrada integral — projeção legível do payload\n", "## instructions\n", payload["instructions"]]
    images: list[dict[str, Any]] = []
    metadata: dict[str, Any] = {}
    for index, block in enumerate(payload["input"][0]["content"]):
        if block["type"] == "input_text":
            prompt.extend([f"\n## input[0].content[{index}] — texto literal\n", block["text"]])
            metadata = json.loads(block["text"])
        else:
            prefix, encoded = block["image_url"].split(",", 1)
            data = base64.b64decode(encoded, validate=True)
            ext = "jpg" if prefix == "data:image/jpeg;base64" else "png"
            name = f"input/image-{len(images) + 1:02d}.{ext}"
            files[name] = data
            role = (
                "finish_reference_only"
                if "finish_reference" in metadata
                else "material"
                if "material_asset_id" in metadata
                else metadata["version"]
            )
            images.append(
                {
                    "file": name,
                    "content_index": index,
                    "role": role,
                    "label": metadata,
                    "sha256": sha(data),
                    "detail": block["detail"],
                }
            )
            prompt.append(f"\n## input[0].content[{index}] — imagem\nAnexo: {name}; detail={block['detail']}.\n")
    prompt.extend(
        [
            "\n## text.format — contrato de saída completo\n",
            pretty(payload["text"]["format"], sort_keys=False).decode(),
            "\n## Parâmetros da chamada proposta\n",
            files["parameters.json"].decode(),
        ]
    )
    files["PROMPT-INTEGRAL.md"] = "\n".join(prompt).encode()
    files["input/order.json"] = pretty(images)
    for asset in job.assets:
        if not ASSET_ID.fullmatch(asset.id) or sha(asset.data) != asset.sha256:
            raise ValueError("EXPORT_ASSET_INVALID")
        files["execution/" + asset.id] = asset.data
    movement, elements = movement_bytes(movement_hash(job.context) or ""), runtime_bytes()
    if sha(movement) != movement_hash(job.context) or sha(elements) != elements_hash(job.context):
        raise ValueError("EXPORT_RUNTIME_CHANGED")
    files["execution/libraries/movement-v1.js"] = movement
    files["execution/libraries/elements-v1.js"] = elements
    files["execution/libraries/LICENSE.maestro.md"] = (ELEMENTS_ROOT / "LICENSE.maestro.md").read_bytes()
    files["execution/assets/LICENSE-fonts.txt"] = (FONTS / "LICENSE.txt").read_bytes()
    repertoire = job.context.get("repertoire")
    if repertoire is not None:
        for item in repertoire["examples"] + repertoire["licenses"]:
            files["repertoire/" + item["file"]] = item["content"].encode()
        files["repertoire/manifest.json"] = pretty(repertoire)
    files["skill.md"] = job.context["skill"]["instructions"].encode()
    stage = (
        ("implementation" if job.construction_plan is not None else "plan")
        if staged_generation_enabled(job.context)
        else "complete"
    )
    if job.construction_plan is not None:
        files["construction-plan.json"] = pretty(job.construction_plan.model_dump(mode="json"))
    files["LEIA-ME.md"] = readme(images, stage=stage).encode()
    manifest = {
        "version": "motion-external-export-v1",
        "purpose": "Teste manual externo, sem execução no produto",
        "builders": [
            "app.services.motion_context.capture_motion_guidance",
            "app.adapters.motion_ai.OpenAIMotionProvider.build_request",
        ],
        "provenance": provenance,
        "images": images,
        "runtime_only": [name for name in files if name.startswith("execution/")],
        "model_receives": "instructions, input (texto/imagens), text.format e parâmetros em generation-request.json",
        "execution_materials": (
            "Vídeo/fontes/runtimes não são anexados pela API de geração; constam aqui para uso posterior."
        ),
        "paid_calls_authorized": False,
        "construction_stage": stage,
        "network_calls": 0,
        "rendered": False,
        "token_count": None,
        "cost_estimate": None,
        "credentials_included": False,
        "files": [{"path": name, "bytes": len(data), "sha256": sha(data)} for name, data in sorted(files.items())],
    }
    files["manifest.json"] = pretty(manifest)
    return files


def readme(images: list[dict[str, Any]], *, stage: str = "complete") -> str:
    order = "\n".join(
        f"{i}. `{item['file']}` — {item['role']}; rótulo e instante em `input/order.json`."
        for i, item in enumerate(images, 1)
    )
    return f"""# Teste externo — Café Pausa

Este pacote prepara a geração da composição. Nada foi enviado a um modelo,
renderizado ou aprovado. A direção fornecida é uma proposta para inspeção;
a qualidade da execução ainda não foi avaliada.

Etapa deste pacote: **{stage}**. Nos contratos v3/v4, `plan` devolve somente o plano,
sem HTML/JavaScript. Salve a resposta JSON completa e execute novamente o exportador
com os mesmos argumentos, acrescentando `--plan-output caminho/plano.json` e um
novo diretório `--output`. Ele valida o plano e monta o pacote `implementation`
pelo mesmo builder do produto. A resposta v3 contém `plan_sha256`, `html` e
`scene_init`; v4 inclui status e motivo opcional para solicitar revisão do plano.
O produto incorpora o plano preservado. Nenhuma etapa é
chamada automaticamente por este exportador. Não tente renderizar a resposta `plan`.
No contrato v4, uma implementação com ilustrações declaradas também exige
`--resolved-materials` com JSON local que identifique cada PNG e SHA-256. O arquivo
é material já resolvido, não autorização de gerar imagens ou reutilizar orçamento.
Para preparar direção com ilustração habilitada, informe ainda uma política
explícita em `--illustration-policy` (JSON sem credenciais). Essas opções não
acionam provedor nem transformam reservas históricas em autorização.

## Uso em um chat externo

1. Extraia o ZIP. Anexe `PROMPT-INTEGRAL.md` e as {len(images)} imagens de `input/`, na ordem
   abaixo. O prompt contém instruções, contexto integral, rótulos e schema de saída.
2. Peça: “Leia integralmente o prompt e os {len(images)} anexos, mantendo sua associação na
   ordem indicada. Entregue o JSON completo do contrato. Informe se algum anexo
   não puder ser lido. Não gere novos assets nem renderize sem minha autorização.”
3. Salve a resposta integral correspondente ao schema da etapa deste pacote.
   Se generation_contract=provided-direction-output-v1/v2, a direção já está em
   scene-direction.json/context.json: não a peça novamente ao modelo. O produto
   a incorpora pela função decode_provided_output antes das validações e do render.
   Na v2 essa função também expande as chaves compactas dos beats e curvas nomeadas;
   o plano persistido e o runtime conservam o formato completo.
   Informe o modelo usado, anexos efetivamente lidos e eventuais mudanças de entrada.
4. Devolva a resposta e sua avaliação. Uma imagem bonita não prova movimento ou
   preservação da voz; saída externa não será executada automaticamente no produto.

{order}

Se o chat limitar anexos, envie-os em lotes com os nomes/rótulos e peça para esperar
até receber todos. Se não aceitar Markdown, cole o conteúdo integral do prompt.
Não substitua silenciosamente as {len(images)} imagens por vídeo, colagem ou resumo.

## Fidelidade e diferenças do chat

`generation-request.json` é o corpo exato produzido por build_request, com imagens
base64, instruções, parâmetros e schema. Não contém headers/credenciais. O arquivo
legível só acrescenta títulos e caminhos no lugar dos blocos base64; os textos
originais estão completos. `context.json`, `instructions.txt`, `parameters.json`
e `output-contract.json` são cópias separadas para conferência, não prompts extras.

Um chat pode não reproduzir papéis, schema estrito, esforço de raciocínio, limites
ou ferramentas da API. Registre essas diferenças. O modelo indicado no JSON é o
parâmetro da comparação proposta; não limita sua escolha de modelo externo.
Nenhuma contagem remota de tokens ou nova autorização de orçamento foi feita.

## Materiais para execução, separados da chamada

`execution/assets/source.mp4` é a fonte efetivamente usada na prova anterior,
verificada por SHA; não é um novo render. A API recebe apenas suas seis amostras,
sem escuta de áudio. A transcrição e sua proveniência, quando presentes, constam em
`context.json`; ASR local não revisado continua sendo uma estimativa. A revisão
humana, quando declarada, não é comprovada pelo exportador. Anexar o vídeo ao chat fornece evidência adicional e deve
ser registrado como variação. As fontes e licenças estão na mesma pasta.

`execution/libraries/movement-v1.js` e `elements-v1.js` são os bytes que o renderer
fornece antes de scene_init; o segundo já contém seu catálogo expandido. A API
recebe as APIs/hashes desses runtimes, não seus arquivos integrais. Enviá-los ao
chat também amplia a entrada; registre isso. Os três exemplos adaptáveis em
`repertoire/` e os exemplos em `skill.md` já estão integralmente no prompt.
Eles não são novos motores instalados nem autorização para criar imagens.

A futura execução precisa manter caminhos `assets/`, carregar os runtimes antes
de scene_init e chamar window.seek(ms) aguardando o seek do vídeo. O plano de áudio
é separado e deve preservar a faixa original. Este pacote não inclui um comando
que execute automaticamente código recebido de outro modelo.

As referências de acabamento não são assets a incorporar na peça. Fontes,
licenças, tempos aproximados e limites estão no manifesto do repertório quando
houver seleção. Kit e materiais autorizados prevalecem sobre identidade dos
exemplos. PNGs de ilustração presentes são materiais fornecidos para a montagem,
não novos assets gerados por este exportador nem fotos documentais do negócio.

## Verificação local

Na raiz do projeto: `.venv/bin/python -m scripts.evals.motion_external_export --verify CAMINHO_DO_PACOTE`.
Isso verifica hashes/arquivos sem provedor ou render. `manifest.json` registra a
origem, as diferenças de entrada e quais arquivos pertencem somente à execução.
"""


def verify_export(folder: Path) -> None:
    manifest = json.loads((folder / "manifest.json").read_bytes())
    expected = {item["path"] for item in manifest["files"]} | {"manifest.json"}
    if {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()} != expected:
        raise ValueError("EXPORT_FILES_CHANGED")
    for item in manifest["files"]:
        path = folder / item["path"]
        if path.is_symlink() or not path.resolve().is_relative_to(folder.resolve()):
            raise ValueError("EXPORT_PATH_INVALID")
        data = path.read_bytes()
        if len(data) != item["bytes"] or sha(data) != item["sha256"]:
            raise ValueError("EXPORT_FILE_CHANGED")
    payload = json.loads((folder / "generation-request.json").read_bytes())
    for item in manifest["images"]:
        block = payload["input"][0]["content"][item["content_index"]]
        if base64.b64decode(block["image_url"].split(",", 1)[1], validate=True) != (folder / item["file"]).read_bytes():
            raise ValueError("EXPORT_IMAGE_CHANGED")


def write_export(folder: Path, files: dict[str, bytes]) -> Path:
    archive = folder.with_suffix(".zip")
    if folder.exists() or archive.exists():
        raise ValueError("EXPORT_DESTINATION_EXISTS")
    if any(Path(name).is_absolute() or ".." in Path(name).parts for name in files):
        raise ValueError("EXPORT_PATH_INVALID")
    folder.mkdir(parents=True, mode=0o700)
    for name, data in files.items():
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(data)
        path.chmod(0o600)
    verify_export(folder)
    with archive.open("xb") as handle, zipfile.ZipFile(handle, "w", zipfile.ZIP_DEFLATED) as bundle:
        for name in sorted(files):
            bundle.write(folder / name, arcname=folder.name + "/" + name)
    archive.chmod(0o600)
    return archive


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", type=Path)
    parser.add_argument(
        "--prior-payload",
        type=Path,
        default=ROOT / ".local/evals/reel-storyboard-composition-20261109/generation-request.json",
    )
    parser.add_argument(
        "--source", type=Path, default=ROOT / ".local/evals/reel-integrated-creative-proof-20261109/source.mp4"
    )
    parser.add_argument("--direction", type=Path, default=ROOT / "docs/evals/direcao-cafe-pausa-2026-11-10.json")
    parser.add_argument("--speech-timing", type=Path, help="Reviewed motion-speech-v1 JSON bound to the source SHA")
    parser.add_argument(
        "--repertoire", choices=("business-reel-v1", "business-reel-v2", "business-reel-v3"), default="business-reel-v1"
    )
    parser.add_argument(
        "--plan-output", type=Path, help="Complete v3 planning JSON; validates and exports implementation"
    )
    parser.add_argument("--resolved-materials", type=Path, help="JSON de PNGs locais resolvidos e seus hashes")
    parser.add_argument("--illustration-policy", type=Path, help="Política explícita para montagem offline; sem gastos")
    parser.add_argument("--brief", type=Path, default=ROOT / "docs/evals/brief-cafe-pausa-2026-11-10.txt")
    parser.add_argument("--output", type=Path, default=ROOT / ".local/exports/motion-cafe-pausa-20261110")
    args = parser.parse_args()
    if args.verify:
        verify_export(args.verify)
        print("EXPORT_VERIFIED")
        return
    illustration_policy = read_illustration_policy(args.illustration_policy) if args.illustration_policy else None
    job, provenance = prepare_case(
        args.prior_payload,
        args.source,
        args.direction,
        args.brief,
        args.speech_timing,
        args.repertoire,
        illustration_policy,
    )
    if args.resolved_materials and not args.plan_output:
        raise ValueError("EXPORT_PLAN_REQUIRED_FOR_MATERIALS")
    if args.plan_output:
        resolved = read_resolved_materials(args.resolved_materials) if args.resolved_materials else ()
        job = implementation_job(job, args.plan_output.read_text(), resolved)
    archive = write_export(args.output, assemble_files(job, provenance))
    print(json.dumps({"folder": str(args.output), "archive": str(archive), "network_calls": 0, "rendered": False}))


if __name__ == "__main__":
    main()
