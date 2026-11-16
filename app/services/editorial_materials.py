"""Model-facing material labels, separate from storage names and provenance IDs."""

from typing import Any

_LABELS = {
    "space_photo": "Foto de ambiente",
    "item_photo": "Foto do produto ou serviço",
    "source_photo": "Foto anexada ao pedido",
    "brand_logo": "Logo do negócio",
}


def editorial_material_reference(source: dict[str, Any]) -> dict[str, Any]:
    """Call only for sources already authorized and captured in the snapshot.

    Original titles/hashes stay in that snapshot. An illustrative declaration is
    preserved, but absence of that declaration does not prove a photo is real.
    """
    illustrative = "ilustrativ" in str(source.get("title") or "").casefold()
    label = _LABELS.get(source["role"], "Material visual")
    return {
        "role": source["role"],
        "title": label + (" (imagem ilustrativa)" if illustrative else ""),
        "declared_illustrative": illustrative,
        "authorized": True,
    }
