"""Versioned movement capabilities captured in a request, with immutable browser bytes."""

import hashlib
from pathlib import Path
from typing import Any

from app.services.auth import AuthError

VERSION = "motion-movement-v3"
SOURCE = Path(__file__).resolve().parents[1] / "assets/motion_html_renderer/movement-v3.js"
LEGACY_SOURCE = SOURCE.with_name("movement-v1.js")
V2_SOURCE = SOURCE.with_name("movement-v2.js")
SOURCES = {"motion-movement-v1": LEGACY_SOURCE, "motion-movement-v2": V2_SOURCE, VERSION: SOURCE}
V2_API = (
    "window.MotionV1 está disponível antes de scene_init, sem imports. "
    "Use MotionV1.timeline(tracks) uma vez e chame timeline.seek(ms) dentro de window.seek(ms), "
    "junto do seek assíncrono do vídeo original. tracks: [{id,initial,beats}]; id é o ID do elemento DOM "
    "e deve corresponder ao elemento do motion_plan. beats: [{start_ms,end_ms,to,curve}]. "
    "Cada track exige de 1 a 12 beats; nunca envie beats:[]. Para um elemento estático, use um beat "
    "de hold cobrindo sua cena, com to igual a initial e curva linear, ou mantenha-o fora da timeline. "
    "initial/to são estados numéricos parciais: x/y em px (0), scaleX/scaleY (1), rotate em graus (0), "
    "opacity (1), clipTop/Right/Bottom/Left em % (0), radius em px (0). Valores entre parênteses são defaults. "
    "Cada beat parte do estado final anterior; entre beats mantém estado. Antes do primeiro usa initial. "
    "Use initial.opacity=0 para elementos que surgem depois. Tempos absolutos, sem sobreposição por elemento. "
    "curve:{kind,parameters} usa o contrato motion_plan: linear/ease_in/ease_out/ease_in_out com [], "
    "cubic_bezier [x1,y1,x2,y2], spring [rigidez,amortecimento,massa]. As curvas nomeadas são cúbicas; "
    "spring é resposta física normalizada para terminar continuamente no alvo na duração escolhida. "
    "MotionV1.stagger(tracks,step_ms) desloca todos os beats do item i por i*step_ms, sem mutar os inputs. "
    "Registre no motion_plan os tempos finais após stagger. Use múltiplas tracks com tempos coordenados "
    "para revelar/transformar composições; segmente texto em spans no HTML quando a direção pedir. "
    "MotionV1.progress(ms,start_ms,end_ms,curve) fornece progresso para outros grafismos determinísticos. "
    "timeline controla transform, opacity e border-radius; só controla clip-path quando initial ou algum to "
    "declara clipTop/Right/Bottom/Left explicitamente; sem esses campos preserva o CSS, sem criar máscara; "
    "use wrappers para "
    "compor transforms/máscaras com layout fixo. Mantenha identidade, conteúdo e CSS conforme kit. "
    "Não use CSS animations/transitions nem relógio real; preserve leitura e holds. "
    "Exemplo: const t=MotionV1.timeline([{id:'titulo',initial:{y:40,opacity:0},beats:["
    "{start_ms:0,end_ms:500,to:{y:0,opacity:1},curve:{kind:'ease_out',parameters:[]}}]}]); "
    "window.seek=async(ms)=>{t.seek(ms); /* aguardar também o seek do vídeo se houver */}; "
    "A biblioteca não executa o motion_plan textual automaticamente nem comprova qualidade."
)


API = V2_API.replace(
    "timeline controla transform, opacity e border-radius; só controla clip-path",
    "timeline controla transform e opacity; só controla border-radius quando initial ou algum to declara "
    "radius explicitamente (inclusive zero); sem radius preserva o arredondamento CSS. Só controla clip-path",
)


def movement_v2_contract() -> dict[str, str]:
    """Exact descriptor used by the previous registered construction snapshots."""
    return {
        "version": "motion-movement-v2",
        "sha256": hashlib.sha256(V2_SOURCE.read_bytes()).hexdigest(),
        "api": V2_API,
    }


LEGACY_API = (
    "window.MotionV1 está disponível antes de scene_init, sem imports. Use MotionV1.timeline(tracks)"
    " uma vez e chame timeline.seek(ms) dentro de window.seek(ms), junto do seek assíncrono do vídeo"
    " original. tracks: [{id,initial,beats}]; id é o ID do elemento DOM e deve corresponder ao eleme"
    "nto do motion_plan. beats: [{start_ms,end_ms,to,curve}]. Cada track exige de 1 a 12 beats; nunc"
    "a envie beats:[]. Para um elemento estático, use um beat de hold cobrindo sua cena, com to igua"
    "l a initial e curva linear, ou mantenha-o fora da timeline. initial/to são estados numéricos pa"
    "rciais: x/y em px (0), scaleX/scaleY (1), rotate em graus (0), opacity (1), clipTop/Right/Botto"
    "m/Left em % (0), radius em px (0). Valores entre parênteses são defaults. Cada beat parte do es"
    "tado final anterior; entre beats mantém estado. Antes do primeiro usa initial. Use initial.opac"
    "ity=0 para elementos que surgem depois. Tempos absolutos, sem sobreposição por elemento. curve:"
    "{kind,parameters} usa o contrato motion_plan: linear/ease_in/ease_out/ease_in_out com [], cubic"
    "_bezier [x1,y1,x2,y2], spring [rigidez,amortecimento,massa]. As curvas nomeadas são cúbicas; sp"
    "ring é resposta física normalizada para terminar continuamente no alvo na duração escolhida. Mo"
    "tionV1.stagger(tracks,step_ms) desloca todos os beats do item i por i*step_ms, sem mutar os inp"
    "uts. Registre no motion_plan os tempos finais após stagger. Use múltiplas tracks com tempos coo"
    "rdenados para revelar/transformar composições; segmente texto em spans no HTML quando a direção"
    " pedir. MotionV1.progress(ms,start_ms,end_ms,curve) fornece progresso para outros grafismos det"
    "erminísticos. timeline controla integralmente transform, opacity, clip-path e border-radius; us"
    "e wrappers para compor transforms/máscaras com layout fixo. Mantenha identidade, conteúdo e CSS"
    " conforme kit. Não use CSS animations/transitions nem relógio real; preserve leitura e holds. E"
    "xemplo: const t=MotionV1.timeline([{id:'titulo',initial:{y:40,opacity:0},beats:[{start_ms:0,end"
    "_ms:500,to:{y:0,opacity:1},curve:{kind:'ease_out',parameters:[]}}]}]); window.seek=async(ms)=>{"
    "t.seek(ms); /* aguardar também o seek do vídeo se houver */}; A biblioteca não executa o motion"
    "_plan textual automaticamente nem comprova qualidade."
)


def movement_contract(*, legacy: bool = False) -> dict[str, str]:
    source = LEGACY_SOURCE if legacy else SOURCE
    return {
        "version": "motion-movement-v1" if legacy else VERSION,
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "api": LEGACY_API if legacy else API,
    }


def movement_bytes(expected_hash: str) -> bytes:
    """Resolve the exact captured runtime; never upgrade old compositions implicitly."""
    for source in SOURCES.values():
        data = source.read_bytes()
        if hashlib.sha256(data).hexdigest() == expected_hash:
            return data
    raise AuthError("MOTION_MOVEMENT_VERSION_UNAVAILABLE", 409)


def movement_hash(context: dict[str, Any]) -> str | None:
    contract = context.get("creative_contract")
    if contract is None:
        return None
    if not isinstance(contract, dict):
        raise AuthError("MOTION_MOVEMENT_VERSION_UNAVAILABLE", 409)
    descriptor = contract.get("movement_runtime")
    if descriptor is None:
        return None
    if not isinstance(descriptor, dict) or descriptor.get("version") not in SOURCES:
        raise AuthError("MOTION_MOVEMENT_VERSION_UNAVAILABLE", 409)
    expected_hash = hashlib.sha256(SOURCES[descriptor["version"]].read_bytes()).hexdigest()
    if descriptor.get("sha256") != expected_hash:
        raise AuthError("MOTION_MOVEMENT_VERSION_UNAVAILABLE", 409)
    return expected_hash
