"""Pinned art components; selection serves meaning, not a mandatory visual template."""

import hashlib
import json
from pathlib import Path
from typing import Any

from app.services.auth import AuthError

ROOT = Path(__file__).resolve().parents[1] / "assets/motion_elements/v1"
VERSION = "motion-elements-v1"


def runtime_bytes() -> bytes:
    catalog = json.loads((ROOT / "catalog.json").read_text())
    return (
        (ROOT / "runtime.js")
        .read_bytes()
        .replace(b"__MOTION_ELEMENTS_CATALOG__", json.dumps(catalog, ensure_ascii=True, separators=(",", ":")).encode())
    )


def elements_contract() -> dict[str, Any]:
    catalog = json.loads((ROOT / "catalog.json").read_text())
    return {
        "version": VERSION,
        "sha256": hashlib.sha256(runtime_bytes()).hexdigest(),
        "items": [{"id": item["id"], "tags": item["tags"], "parts": list(item["parts"])} for item in catalog["items"]],
        "api": (
            "MotionElementsV1.mount(document.getElementById(element_id), component_id, "
            "{color: kit.palette.primary, strokeWidth:1.5}) cria SVG e retorna {svg,parts}. "
            "Use a cor hexadecimal do kit confirmado, nunca copie a paleta Maestro. "
            "Monte uma vez, dimensione/posicione o wrapper e anime com MotionV1. "
            "MotionElementsV1.reveal(parts.outline, MotionV1.progress(ms,inicio,fim,curva)) desenha o traço; "
            "use os nomes de partes do catálogo, sem supor outline nos objetos multipartes. "
            "MotionElementsV1.node(host, component_id, {color,background,font,label}) compõe objeto e rótulo "
            "em um nó; background/font também vêm do kit. Dimensione o wrapper e defina fontSize legível. "
            "MotionElementsV1.connector(host, [[x1,y1],[x2,y2],...], {color}) desenha uma conexão em pixels "
            "locais e retorna parts.line; use reveal para construir o percurso. Conectores são construction=code. "
            "Crie diagramas/colagens combinando wrappers, conectores e texto; não use um ícone como cena inteira "
            "por padrão. Selecione pelo significado, não por mera disponibilidade. Registre component_id em "
            "scene_direction com construction=component. Elementos próprios podem usar construction=code e "
            "component_id=null: SVG/Canvas/HTML originais são permitidos, sem importar bibliotecas. "
            "Fotos do acervo usam construction=authorized_asset e o asset_id fornecido. "
            "Não transforme ilustração genérica em afirmação sobre produto, serviço ou local real."
        ),
    }


def elements_hash(context: dict[str, Any]) -> str | None:
    contract = context.get("creative_contract")
    descriptor = contract.get("element_library") if isinstance(contract, dict) else None
    if descriptor is None:
        return None
    expected = elements_contract()
    if descriptor != expected:
        raise AuthError("MOTION_ELEMENTS_VERSION_UNAVAILABLE", 409)
    return str(expected["sha256"])
