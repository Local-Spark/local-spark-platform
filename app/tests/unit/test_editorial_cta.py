import hashlib
import json
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.editorial_context import ContextContent, ContextUpdate, EditorialPreferences
from app.schemas.editorial_proposals import ProposalDraft
from app.services.editorial_context import _digest
from app.services.editorial_cta import public_action_matches_destination


def _draft(caption: str) -> ProposalDraft:
    return ProposalDraft(
        title="Uma pausa para o café",
        format="story",
        angle="Apresentar o produto",
        fact_ids=[uuid4()],
        hypotheses=[],
        questions=[],
        scene_plan=["fact", "cta"],
        art_text="Croissant por R$ 18,00",
        caption=caption,
        cta="Saiba mais",
    )


def test_destination_is_opt_in_versioned_and_strips_value() -> None:
    old = ContextContent.model_validate({"preferences": {}})
    assert old.preferences.cta_destination is None
    value = EditorialPreferences.model_validate(
        {"cta_destination": {"type": "whatsapp", "value": "  +55 11 99999-9999  "}}
    )
    assert value.cta_destination is not None
    assert value.cta_destination.value == "+55 11 99999-9999"
    assert ContextContent.model_validate({"preferences": value.model_dump()}).preferences == value
    for destination in ({"type": "whatsapp", "value": "   "}, {"type": "unknown", "value": "x"}):
        with pytest.raises(ValidationError):
            EditorialPreferences.model_validate({"cta_destination": destination})


def test_old_context_request_digest_stays_stable_when_destination_is_unset() -> None:
    payload = ContextUpdate(expected_version=1, operation_id=uuid4())
    original = payload.model_dump(mode="json")
    original["preferences"].pop("cta_destination")
    encoded = json.dumps(original, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    assert _digest(payload) == hashlib.sha256(encoded.encode()).hexdigest()
    with_destination = payload.model_copy(
        update={
            "preferences": EditorialPreferences.model_validate({"cta_destination": {"type": "ifood", "value": "Loja"}})
        }
    )
    assert _digest(with_destination) != _digest(payload)


@pytest.mark.parametrize(
    ("text", "destination", "expected"),
    [
        ("Conheça nosso croissant.", None, True),
        ("Peça pelo WhatsApp.", None, False),
        ("Peça pelo WhatsApp.", {"type": "whatsapp", "value": "+55 11 99999-9999"}, True),
        ("Peça pelo iFood.", {"type": "whatsapp", "value": "+55 11 99999-9999"}, False),
        ("Peça pelo iFood.", {"type": "ifood", "value": "Café do Cedro"}, True),
        ("Ligue para encomendar.", {"type": "phone", "value": "+55 11 99999-9999"}, True),
        ("Mande uma mensagem no direct.", {"type": "instagram_direct", "value": "@cafe"}, True),
        ("Mande uma mensagem para @cafe.", {"type": "instagram_direct", "value": "@cafe"}, True),
        ("Mande uma mensagem para @outro.", {"type": "instagram_direct", "value": "@cafe"}, False),
        ("Visite a nossa loja.", None, False),
        ("Visite a nossa loja.", {"type": "physical_location", "value": "Rua das Flores, 10"}, True),
        ("Peça pelo link.", None, False),
        ("Peça no site https://cafe.example.com.", {"type": "order_link", "value": "https://cafe.example.com"}, True),
        ("Peça no site https://outro.example.com.", {"type": "order_link", "value": "https://cafe.example.com"}, False),
        ("Acesse exemplo.com/pedidos.", None, False),
        ("Toque em Saiba mais.", {"type": "booking_link", "value": "https://cafe.example.com"}, False),
        ("Acesse o link na bio.", {"type": "order_link", "value": "https://cafe.example.com"}, False),
    ],
)
def test_public_action_requires_confirmed_channel_and_never_assumes_tap(
    text: str, destination: dict[str, str] | None, expected: bool
) -> None:
    assert public_action_matches_destination(_draft(text), {"cta_destination": destination}) is expected
