"""T1–T3 admission and execution supplement, opt-in through immutable capture."""

import hashlib
import json
from pathlib import Path
from typing import Any

from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan
from app.services.auth import AuthError

POLISH_PATH = Path(__file__).resolve().parents[1] / "assets/motion_photo/photo-polish-v2.js"
LEGACY_POLISH_PATH = POLISH_PATH.with_name("photo-polish-v1.js")
PHOTO_POLISH_CONTRACT_V1 = {
    "version": "motion-photo-polish-v1",
    "dom_guard_sha256": "7cfc699866299ebdcb4d6956253ce533f8d0b001f6f3e8750cb32b84a0cc6ba6",
    "rules": (
        "T1–T3: preserve o briefing aconchegante, movimento suave e frases curtas sobre pausa; não hard-sell. "
        "Sem mudar crop v5, intent v10, finish-v1, readability-v1 ou CTA >=1500 ms. "
        "T1: staging.photo_material_reviews deve inspecionar TODO o inventário assets/photo-*, "
        "inclusive fotos não selecionadas: {asset_id, subject:environment|detail|people|other, "
        "identity:clean|third_party|uncertain, crop_safe:boolean, evidence}. Observe os previews; "
        "evidence explica assunto, identidade e viabilidade de crop v5. Não marque inviável só para "
        "reduzir variedade. Só clean e crop_safe são elegíveis. Use >=min(3,elegíveis) fotos distintas "
        "como primárias por >=1500 ms exclusivos cada; se houver environment elegível, inclua um "
        "beat de salão/balcão/mesa ampla por >=1500 ms exclusivos. Sem material suficiente use todos "
        "os elegíveis, sem inventar fotos ou relaxar S3/crop; sem elegíveis, requires_plan_revision. "
        "T2: todas as frases, não apenas CTA, precisam de texto claro >=24px com sombra(s) preta(s) "
        "opaca(s), ao menos uma com blur >=2px, ou fundo preto local com alpha >=0.75 "
        "no texto ou ancestral que o contenha. "
        "Scrim deve cobrir o texto, largura <95% do frame; nunca faixa full-width. Prefira posição "
        "escura, mas só posição não comprova contraste. Checar cada seek visível, inclusive fecho. "
        "T3: nesta fatia use apenas fotos, logo do kit e tipografia com scrim CSS local. Sem elementos "
        "graphic, cantoneiras, crop marks, linhas-guia, bordas, outlines, SVG/canvas ou pseudo-elementos "
        "decorativos. Não acrescente acentos laranja como UI residual. Não alterar Music/mix."
    ),
}


PHOTO_POLISH_CONTRACT_V2 = {
    **PHOTO_POLISH_CONTRACT_V1,
    "version": "motion-photo-polish-v2",
    "rules": PHOTO_POLISH_CONTRACT_V1["rules"]
    + (
        " Planejamento O2/Q2: antes de responder, calcule a união dos intervalos energéticos por cena "
        "e depois globalmente. Conte SOMENTE beats phase=transform, curve.kind=linear, de foto ou "
        "text relacionado pela foto em related_element_ids. Enter/exit NÃO contam nessa união, "
        "mesmo quando têm deslocamento grande; logo também não conta como candidato O2. "
        "No mesmo eixo, delta absoluto de scale precisa ser >=max(0.04,0.02*duracao_em_segundos), "
        "OU delta de x_pct/y_pct >=max(2,1*duracao_em_segundos). Some a união, não beats sobrepostos. "
        "Cada cena precisa de cobertura >=80% e nenhuma lacuna global >500ms, incluindo início/fim. "
        "O mínimo S2 de 0.01 scale/s no fecho NÃO satisfaz sozinho O2/Q2. Movimento suave ainda "
        "precisa desses números; não conte zoom lento como energia qualificada. "
        "Exemplo numérico sem impor crop: cena de 5000ms, texto relacionado entra em 0–250ms, "
        "transforma linearmente em 250–4750ms com scale=1 x_pct=0 y_pct=0 até "
        "scale=1 x_pct=0 y_pct=-4.5, sai em 4750–5000ms: cobertura 90%, lacuna de 500ms entre "
        "duas cenas adjacentes iguais. É exemplo de agenda, não substituição automática dos beats. "
        "No fecho, mantenha CTA visível até end e >=1500ms de leitura; não aplique a saída do exemplo "
        "ao CTA. Se depender de duas frases, evite lacunas entre seus transforms >500ms e confira "
        "80% na união. Use somente tipografia/scrim, sem reintroduzir graphic. Nunca aumente zoom/pan "
        "de foto violando crop v5: reorganize texto/tempos ou selecione outra foto. Preserve o tom "
        "aconchegante e a legibilidade; não transformar a peça em hard-sell."
    ),
}


PHOTO_POLISH_CONTRACT = {
    **PHOTO_POLISH_CONTRACT_V2,
    "version": "motion-photo-polish-v3",
    "dom_guard_sha256": "9de1d5ff1c7f5a0e2f7b0169a66f77f7e0481b456f0589934a4b7e9e88f0e124",
    "rules": PHOTO_POLISH_CONTRACT_V2["rules"]
    + (
        " Scrim local irmão pode usar id exato <id-do-texto>-scrim, vinculado a um text do plano. "
        "Deve conter geometricamente o texto visível, ter largura <95% e altura <40% do frame, "
        "ser vazio, sem filhos, bordas, outline, pseudo-elementos, box-shadow, filtros ou máscaras. "
        "Pintura permitida: preto sólido/translúcido ou radial-gradient(ellipse,...) só com stops "
        "pretos (alpha variável). Nenhum URL, imagem ou acento colorido. Nome sozinho não autoriza "
        "um adorno. Scrim irmão não dispensa a proteção T2 do próprio texto/sombra, nem o CTA v3. "
        "S2 no fecho: o texto com enter/exit numérico precisa estar integralmente visível em TODOS "
        "os seeks do beat, incluindo início e fim. Não use clip-path de revelação, máscara, opacity "
        "abaixo de 0.95 ou visibility hidden nele/ancestrais nesse intervalo. Anime o transform "
        "declarado sem esconder o texto; saída do CTA continua proibida durante sua janela de leitura."
    ),
}


def polish_enabled(context: dict[str, Any]) -> bool:
    contract = context.get("photo_polish_contract")
    if contract is None:
        return False
    if contract not in (PHOTO_POLISH_CONTRACT_V1, PHOTO_POLISH_CONTRACT_V2, PHOTO_POLISH_CONTRACT):
        raise AuthError("MOTION_PHOTO_POLISH_CONTRACT_CHANGED", 409)
    return True


def validate_photo_polish(
    artifact: HTMLMotionComposition | MotionConstructionPlan, context: dict[str, Any], *, asset_ids: set[str]
) -> None:
    if not polish_enabled(context):
        return
    plan = artifact.motion_plan
    assert plan is not None
    # Photo inputs are normalized PNGs; photo-music.mp3 shares the prefix
    # but is an authorized soundtrack, never a photographic review candidate.
    inventory = {a for a in asset_ids if a.startswith("assets/photo-") and a.endswith(".png")}
    reviews = artifact.staging.photo_material_reviews if artifact.staging else None
    if (
        reviews is None
        or len(reviews) != len(inventory)
        or {r.asset_id for r in reviews} != inventory
        or any(not r.evidence.strip() for r in reviews)
    ):
        raise AuthError("MOTION_PHOTO_INVENTORY_REVIEW_REQUIRED", 409)
    eligible = {r.asset_id for r in reviews if r.identity == "clean" and r.crop_safe}
    environment = {r.asset_id for r in reviews if r.asset_id in eligible and r.subject == "environment"}
    selected: set[str] = set()
    for scene in plan.scenes:
        if any(e.role == "graphic" for e in scene.elements):
            raise AuthError("MOTION_PHOTO_DECORATION_FORBIDDEN", 409)
        photos = {e.id: e.asset_id for e in scene.elements if (e.asset_id or "").startswith("assets/photo-")}
        if not set(photos.values()) <= eligible:
            raise AuthError("MOTION_PHOTO_MATERIAL_INELIGIBLE", 409)
        layout = scene.photo_layout
        if layout is not None and layout.primary_element_id in photos:
            # An asset flashed during overlap does not constitute a distinct atmosphere beat.
            start = max([scene.start_ms] + [s.end_ms for s in plan.scenes if s.start_ms < scene.start_ms])
            end = min([scene.end_ms] + [s.start_ms for s in plan.scenes if s.start_ms > scene.start_ms])
            if end - start >= 1500:
                selected.add(str(photos[layout.primary_element_id]))
    if not eligible or len(selected) < min(3, len(eligible)):
        raise AuthError("MOTION_PHOTO_DIVERSITY_REQUIRED", 409)
    if environment and not selected & environment:
        raise AuthError("MOTION_PHOTO_ENVIRONMENT_BEAT_REQUIRED", 409)


def polish_scene_init(composition: HTMLMotionComposition, context: dict[str, Any], scene_init: str) -> str:
    if not polish_enabled(context):
        return scene_init
    contract = context["photo_polish_contract"]
    path = POLISH_PATH if contract == PHOTO_POLISH_CONTRACT else LEGACY_POLISH_PATH
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != contract["dom_guard_sha256"]:
        raise AuthError("MOTION_PHOTO_POLISH_GUARD_CHANGED", 409)
    assert composition.motion_plan is not None
    payload = json.dumps(
        {
            "images": sorted({e.id for s in composition.motion_plan.scenes for e in s.elements if e.role == "image"}),
            "texts": sorted({e.id for s in composition.motion_plan.scenes for e in s.elements if e.role == "text"}),
        }
    )
    return scene_init + "\n;(" + source.decode() + ")(" + payload + ");"
