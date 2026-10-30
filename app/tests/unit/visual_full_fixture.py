"""Shared owner-scoped full-piece test data; all inputs are fictional."""

from types import SimpleNamespace
from uuid import uuid4

from cryptography.fernet import Fernet
from pydantic import SecretStr

from app.services.editorial_consent_scope import VisualRunScope
from app.services.visual_brand_finish import FULL_RECIPE
from app.services.visual_skills import select_visual_skill


def result(row):
    return SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: row))


def configure_full(case, *, logo=False):
    key = Fernet.generate_key().decode()
    case.service.settings = case.service.settings.model_copy(
        update={"meta_encryption_key": SecretStr(key), "visual_skill_experiment_enabled": True}
    )
    case.row["document"].update(
        art_text="Croissant R$ 18,00",
        caption="Croissant por R$ 18,00",
        cta="Faça seu pedido",
        creative_brief={
            "objective": "Divulgar croissant",
            "concept": "Pausa com sabor",
            "visual_direction": "Valorizar foto e produto",
            "hierarchy": "Produto, preço e chamada",
            "photo_use": "Usar foto como foco",
        },
        editorial_skill_id="instagram-feed-v1",
        editorial_skill_sha256=select_visual_skill(case.service.settings, "instagram-feed-v1", "photo"),
    )
    message = "Mostre nosso croissant por R$ 18,00 no feed"
    source = {"ciphertext": Fernet(key.encode()).encrypt(message.encode()).decode(), "transcript_ciphertext": None}
    selected = {"visual_skill_id": None, "visual_skill_sha256": None, "visual_recipe": FULL_RECIPE}
    rows = [result(selected), result(case.row), result(source)]
    mark = None
    if logo:
        from app.tests.unit.test_visual_brand_finish_unit import picture

        mark = picture(color="red")
        case.row["brand_kit_document"]["overrides"]["logo_asset_id"] = str(uuid4())
        rows.append(result({"object_key": "private/logo", "sha256": mark.sha256, "mime_type": "image/png"}))
        case.store.get_image.return_value = mark.data
    case.session.execute.side_effect = rows
    tenant, business, actor, _, _ = case.ids
    scope = VisualRunScope(tenant, business, actor, uuid4(), 1, uuid4(), visual_recipe=FULL_RECIPE)
    return scope, message, mark
