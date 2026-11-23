"""T1–T3 admission and execution supplement, opt-in through immutable capture."""

import hashlib
import json
from pathlib import Path
from typing import Any

from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan
from app.services.auth import AuthError
from app.services.motion_photo_energy import _state, energetic

POLISH_PATH = Path(__file__).resolve().parents[1] / "assets/motion_photo/photo-polish-v4.js"
V4_POLISH_PATH = POLISH_PATH.with_name("photo-polish-v3.js")
V3_POLISH_PATH = POLISH_PATH.with_name("photo-polish-v2.js")
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


PHOTO_POLISH_CONTRACT_V3 = {
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


PHOTO_POLISH_CONTRACT_V4 = {
    **PHOTO_POLISH_CONTRACT_V2,
    "version": "motion-photo-polish-v4",
    "dom_guard_sha256": "a7d4949c427cb65ccdb1ec10e149e99a06d1a3947a73f01dd76b86cbb2c11c5c",
    "rules": PHOTO_POLISH_CONTRACT_V2["rules"]
    + (
        " U1 restringe T2: prefira região já escura da foto, depois scrim local suave, depois sombra discreta. "
        "Posição sozinha não comprova contraste: mantenha proteção T2. Use uma única sombra preta opaca "
        "com blur entre 2 e 4px e offsets absolutos <=2px. Não empilhe sombras nem use glow/box-shadow/filtro. "
        "Scrim apenas retangular preto sólido/translúcido, alpha <=0.8, sem radial/gradiente/mancha/raio; "
        "margens externas ao retângulo do texto <=16px por lado, largura <95% e altura <40% do frame. "
        "Para substituir sombra, fundo no texto/ancestral deve manter alpha >=0.75; suporte irmão "
        "<id-do-texto>-scrim vazio pode ter alpha menor mas não dispensa T2 nem CTA v3. "
        "Mantenha família/pesos tipográficos coerentes entre frases. Texto integralmente visível durante "
        "TODO enter/transform/exit, inclusive endpoints: sem máscara/revelação, opacity <0.95 ou hidden. "
        "CTA >=1500ms sem saída durante leitura; finish-v1 e proibição de faixa full-width intactos. "
        "U2: além de O2/Q2, foto PRIMÁRIA deve ter transforms lineares contínuos em >=80% de cada cena, "
        "sem lacuna >500ms inclusive bordas. No mesmo eixo: scale >=0.01/s OU x_pct/y_pct >=0.5/s (N2). "
        "Texto energético não substitui essa continuidade da foto. Exemplo: cena 5000ms, foto transform "
        "linear 0–5000ms scale=1.04 até 1.09: 100% de continuidade N2; texto relacionado ainda precisa "
        "cobrir O2/Q2 como no exemplo anterior. Confira crop v5 nos extremos, não acelere foto insegura. "
        "Sem holds de ~2s no miolo; se crop inviabilizar movimento, selecione outra foto/revise plano. "
        "U3: ordene ambiente elegível e detalhes como progressão do lugar à pausa, não loop de closes. "
        "Revise TODO inventário pelos previews e justifique cada exclusão; >=min(3,elegíveis) primárias "
        "e ambiente elegível por >=1500ms exclusivos permanecem obrigatórios. Não invente imagens, "
        "não marque ambiente inviável só para repetir produto; S3/crop v5 prevalecem. "
        "Preserve tom suave e aconchegante, sem hard-sell, A5b, Music/mix, TTS ou avatar."
    ),
}


TIMING_PATH = POLISH_PATH.with_name("photo-timing-v1.js")
PHOTO_POLISH_CONTRACT_V5 = {
    **PHOTO_POLISH_CONTRACT_V4,
    "version": "motion-photo-polish-v5",
    "timing_sha256": "f32be2f98c207d96f77b0098240a19eb7cf3442dfc867f8ea6cce3391fc77b08",
    "rules": PHOTO_POLISH_CONTRACT_V4["rules"]
    + (
        " Timing v1: PhotoTimingV1 já é instalado antes de scene_init; não o redefina. "
        "Use PhotoTimingV1.textVisible(t,start,end) para display de texto E seu wrapper: "
        "é inclusivo nos dois endpoints (t>=start && t<=end), também no exit. "
        "Exemplo: exit 13200–13400 permanece display:block em 13400; esconda só em t>13400. "
        "Não reutilize janelas half-open de fotos para texto. Agrupe beats contíguos do texto "
        "numa janela do primeiro start ao último end; CTA permanece até duration_ms. "
        "Use PhotoTimingV1.photoVisible(t,start,end,duration_ms) para wrappers de fotos. "
        "Dissolução: declare phase=exit na foto de origem e staging.transition com a MESMA "
        "janela contida na interseção das cenas, duração >0 e <=500ms. "
        "Exemplo: origem 0–5200, destino 5000–11200: transition 5000–5200, nunca 4900–5200. "
        "Preparação narrativa anterior ao overlap não pertence a transition.start_ms. "
        "Só wrapper da origem usa PhotoTimingV1.outgoingOpacity(t,start,end); destino fica "
        "opaco/cover desde seu start. Sem overlap, corte seco sem fade. Não esconda texto "
        "dentro de wrapper fotográfico que dissolve. Teste seeks start,end,end+1 e reversos."
    ),
}


PHOTO_POLISH_CONTRACT = {
    **PHOTO_POLISH_CONTRACT_V5,
    "version": "motion-photo-polish-v6",
    "dom_guard_sha256": "dee896303ba595fda012f54b29ec4137b83dcc90c89521771c1923144e2e050e",
    "rules": PHOTO_POLISH_CONTRACT_V5["rules"]
    + (
        " V1 cover+energia restringe a exceção contain_blur de S1 e o piso de cobertura U2: "
        "todas as cenas, do primeiro ao último frame, devem declarar photo_layout.mode=cover. "
        "Proibido Stories/letterbox, janela horizontal com blur, mesmo por 1ms ou foto paisagem. "
        "IMG primária com object-fit:cover ocupa todo 9:16; ancestrais não recortam uma janela. "
        "Se cover não preservar região essencial/crop v5, escolha outro material elegível ou "
        "requires_plan_revision; nunca invente fotos. Ambiente somente se elegível no inventário. "
        "Foto primária: transforms N2 lineares por 100% da cena, sem holds nem lacunas, "
        "estados contíguos iguais nos encontros dos beats. Única exceção: exit de dissolução "
        "validado por timing v1; destino já entra cover opaco e em movimento desde start. "
        "Exemplo: cena 0–5000, transform scale=1.04 até 1.09 em 0–5000, sem enter/hold; "
        "confira crop nos extremos. Não anime só wrapper, texto ou foto escondida; aplique "
        "o transform à IMG declarada e mantenha geometria CSS estável, sem compensar movimento. "
        "O2/Q2 continuam separados e obrigatórios. Viés de conversão: cover imediato, ritmo "
        "suave contínuo, frases curtas legíveis e convite CTA no fecho, respeitando intenção "
        "e tom do pedido original. Aconchegante não significa estático nem autoriza hard-sell. "
        "Não reescreva briefing, não invente oferta/urgência. Preserve U1, Music e demais gates."
    ),
}


def polish_enabled(context: dict[str, Any]) -> bool:
    contract = context.get("photo_polish_contract")
    if contract is None:
        return False
    if contract not in (
        PHOTO_POLISH_CONTRACT_V1,
        PHOTO_POLISH_CONTRACT_V2,
        PHOTO_POLISH_CONTRACT_V3,
        PHOTO_POLISH_CONTRACT_V4,
        PHOTO_POLISH_CONTRACT_V5,
        PHOTO_POLISH_CONTRACT,
    ):
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

    if context["photo_polish_contract"] in (PHOTO_POLISH_CONTRACT_V4, PHOTO_POLISH_CONTRACT_V5, PHOTO_POLISH_CONTRACT):
        for scene in plan.scenes:
            primary = next(
                (e for e in scene.elements if scene.photo_layout and e.id == scene.photo_layout.primary_element_id),
                None,
            )
            intervals = (
                []
                if primary is None
                else [
                    (max(scene.start_ms, b.start_ms), min(scene.end_ms, b.end_ms))
                    for b in primary.beats
                    if energetic(b) and b.end_ms > scene.start_ms and b.start_ms < scene.end_ms
                ]
            )
            covered, active = scene.start_ms, 0
            for start, end in sorted(intervals) + [(scene.end_ms, scene.end_ms)]:
                if start - covered > 500:
                    raise AuthError("MOTION_PHOTO_CONTINUITY_REQUIRED", 409)
                active += max(0, end - max(start, covered))
                covered = max(covered, end)
            if active * 5 < (scene.end_ms - scene.start_ms) * 4:
                raise AuthError("MOTION_PHOTO_CONTINUITY_REQUIRED", 409)

    if context["photo_polish_contract"] in (PHOTO_POLISH_CONTRACT_V5, PHOTO_POLISH_CONTRACT):
        assert artifact.staging is not None
        for scene in plan.scenes:
            for element in scene.elements:
                if scene.photo_layout is None or element.id != scene.photo_layout.primary_element_id:
                    continue
                exits = [b for b in element.beats if b.phase == "exit"]
                for beat in exits:
                    transition = next((m.transition for m in artifact.staging.moments if m.scene_id == scene.id), None)
                    destination = next(
                        (s for s in plan.scenes if transition and s.id == transition.next_scene_id), None
                    )
                    if (
                        transition is None
                        or destination is None
                        or not 0 < transition.end_ms - transition.start_ms <= 500
                        or not max(scene.start_ms, destination.start_ms)
                        <= transition.start_ms
                        < transition.end_ms
                        <= min(scene.end_ms, destination.end_ms)
                        or (beat.start_ms, beat.end_ms) != (transition.start_ms, transition.end_ms)
                    ):
                        raise AuthError("MOTION_PHOTO_HANDOFF_WINDOW_INVALID", 409)

    if context["photo_polish_contract"] == PHOTO_POLISH_CONTRACT:
        for scene in plan.scenes:
            if scene.photo_layout is None or scene.photo_layout.mode != "cover":
                raise AuthError("MOTION_PHOTO_FULL_BLEED_REQUIRED", 409)
            primary = next(e for e in scene.elements if e.id == scene.photo_layout.primary_element_id)
            end = min(
                [scene.end_ms] + [b.start_ms for b in primary.beats if b.phase == "exit" and b.end_ms == scene.end_ms]
            )
            covered = scene.start_ms
            previous = None
            for beat in sorted((b for b in primary.beats if energetic(b)), key=lambda b: b.start_ms):
                if beat.start_ms > covered or (previous is not None and _state(beat.start_state) != previous):
                    raise AuthError("MOTION_PHOTO_CONTINUOUS_TRANSFORM_REQUIRED", 409)
                covered = beat.end_ms
                previous = _state(beat.end_state)
            if covered < end:
                raise AuthError("MOTION_PHOTO_CONTINUOUS_TRANSFORM_REQUIRED", 409)


def polish_scene_init(composition: HTMLMotionComposition, context: dict[str, Any], scene_init: str) -> str:
    if not polish_enabled(context):
        return scene_init
    contract = context["photo_polish_contract"]
    path = (
        POLISH_PATH
        if contract == PHOTO_POLISH_CONTRACT
        else V4_POLISH_PATH
        if contract in (PHOTO_POLISH_CONTRACT_V4, PHOTO_POLISH_CONTRACT_V5)
        else V3_POLISH_PATH
        if contract == PHOTO_POLISH_CONTRACT_V3
        else LEGACY_POLISH_PATH
    )
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != contract["dom_guard_sha256"]:
        raise AuthError("MOTION_PHOTO_POLISH_GUARD_CHANGED", 409)
    assert composition.motion_plan is not None
    payload = json.dumps(
        {
            **(
                {
                    "cover": [
                        {"id": s.photo_layout.primary_element_id, "start": s.start_ms, "end": s.end_ms}
                        for s in composition.motion_plan.scenes
                        if s.photo_layout
                    ],
                    "end": composition.motion_plan.duration_ms,
                }
                if contract == PHOTO_POLISH_CONTRACT
                else {}
            ),
            "images": sorted({e.id for s in composition.motion_plan.scenes for e in s.elements if e.role == "image"}),
            "texts": sorted({e.id for s in composition.motion_plan.scenes for e in s.elements if e.role == "text"}),
            **(
                {
                    "continuity": [
                        {
                            "id": e.id,
                            "start": b.start_ms,
                            "end": b.end_ms,
                            "a": _state(b.start_state),
                            "z": _state(b.end_state),
                        }
                        for s in composition.motion_plan.scenes
                        for e in s.elements
                        if s.photo_layout and e.id == s.photo_layout.primary_element_id
                        for b in e.beats
                        if energetic(b)
                    ]
                }
                if contract in (PHOTO_POLISH_CONTRACT_V4, PHOTO_POLISH_CONTRACT_V5, PHOTO_POLISH_CONTRACT)
                else {}
            ),
        }
    )
    if contract in (PHOTO_POLISH_CONTRACT_V5, PHOTO_POLISH_CONTRACT):
        timing = TIMING_PATH.read_bytes()
        if hashlib.sha256(timing).hexdigest() != contract["timing_sha256"]:
            raise AuthError("MOTION_PHOTO_TIMING_CHANGED", 409)
        scene_init = timing.decode() + "\n" + scene_init
    return scene_init + "\n;(" + source.decode() + ")(" + payload + ");"
