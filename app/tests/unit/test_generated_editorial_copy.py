"""Generated text is preserved, source-bound, and never replaced on failure."""

from uuid import UUID, uuid4

import pytest

from app.core.editorial_creative import creative_experiment_enabled
from app.schemas.editorial_proposals import ProposalDraft
from app.services.editorial_proposals import EditorialProposalService, _catalog_price_fact, generated_copy_matches_fact


def _snapshot(amount=1990, deadline="2027-12-31", promotions=None):
    return {
        "offering": {
            "id": str(uuid4()),
            "version": 1,
            "kind": "product",
            "name": "Croissant",
            "price": {"status": "valid", "amount_minor": amount, "valid_until": deadline, "currency": "BRL"},
        },
        "promotions": [] if promotions is None else promotions,
    }


@pytest.mark.parametrize(
    "environment,enabled,expected",
    [("development", True, True), ("testing", True, True), ("production", True, False), ("testing", False, False)],
)
def test_experimental_copy_only_enabled_in_development_and_testing(settings, environment, enabled, expected):
    config = settings.model_copy(update={"environment": environment, "editorial_creative_experimental": enabled})
    assert creative_experiment_enabled(config) is expected


def _draft(fact_id):
    return ProposalDraft(
        title="Conheça croissant",
        format="photo",
        angle="Conheça croissant por R$ 19,90",
        fact_ids=[fact_id],
        hypotheses=[],
        questions=[],
        scene_plan=["fact", "cta"],
        art_text="Croissant por R$ 19,90",
        caption="Sua pausa com croissant por R$ 19,90",
        cta="Envie mensagem",
    )


def test_catalog_price_fact_is_source_bound_and_uses_integer_arithmetic():
    snapshot = _snapshot()
    fact = _catalog_price_fact(snapshot)
    assert fact is not None
    assert fact["statement"] == "Croissant por R$ 19,90"
    assert _catalog_price_fact(snapshot) == fact
    for amount, expected in ((0, "0,00"), (100000, "1000,00"), (1000000000, "10000000,00")):
        other = _snapshot(amount)
        assert _catalog_price_fact(other)["statement"] == f"Croissant por R$ {expected}"
    snapshot["offering"]["price"]["amount_minor"] = 2000
    assert _catalog_price_fact(snapshot)["id"] != fact["id"]
    snapshot["offering"]["price"]["valid_until"] = "2028-12-31"
    assert _catalog_price_fact(snapshot)["id"] != fact["id"]


@pytest.mark.parametrize("amount", [-1, 1000000001, True, "1990", None])
def test_invalid_price_does_not_become_evidence(amount):
    assert _catalog_price_fact(_snapshot(amount)) is None


@pytest.mark.parametrize("deadline", [None, "2027-99-01", "20271231"])
def test_invalid_deadline_does_not_become_evidence(deadline):
    assert _catalog_price_fact(_snapshot(deadline=deadline)) is None


@pytest.mark.parametrize("field,value", [("status", "expired"), ("status", "not_set"), ("currency", "USD")])
def test_noncurrent_or_wrong_currency_price_does_not_become_evidence(field, value):
    snapshot = _snapshot()
    snapshot["offering"]["price"][field] = value
    assert _catalog_price_fact(snapshot) is None


def test_price_is_not_inferred_when_promotions_exist_or_snapshot_invalid():
    assert _catalog_price_fact(_snapshot(promotions=[{"title": "promo"}])) is None
    assert _catalog_price_fact({}) is None
    snapshot = _snapshot()
    snapshot["offering"]["price"] = None
    assert _catalog_price_fact(snapshot) is None


def test_generated_copy_keeps_model_text_and_binds_one_confirmed_fact():
    fact = _catalog_price_fact(_snapshot())
    fact_id = UUID(fact["id"])
    data = {
        "confirmed_facts": [fact],
        "preferences": {"avoided_topics": []},
        "material_kind": "text",
        "source_asset_id": None,
        "requested_format": "photo",
        "eligible_formats": ["photo", "story"],
    }
    draft = _draft(fact_id)
    assert EditorialProposalService._safe_generated(draft, data, {fact_id})
    grounded = EditorialProposalService._ground_generated(draft, data)
    assert (grounded.art_text, grounded.caption, grounded.cta) == (draft.art_text, draft.caption, draft.cta)
    assert grounded.script[0].on_screen_text == "Croissant por R$ 19,90."
    assert grounded.script[0].fact_ids == [fact_id]
    assert grounded.script[1].on_screen_text == draft.cta
    assert not EditorialProposalService._safe_generated(draft, data, set())
    assert not EditorialProposalService._safe_generated(draft, {**data, "confirmed_facts": []}, {fact_id})
    assert not EditorialProposalService._safe_generated(draft.model_copy(update={"format": "story"}), data, {fact_id})
    assert not EditorialProposalService._safe_generated(
        draft, {**data, "preferences": {"avoided_topics": ["pausa"]}}, {fact_id}
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("art_text", None),
        ("caption", None),
        ("cta", None),
        ("art_text", "Croissant por R$ 29,90"),
        ("caption", "Croissant vegano"),
        ("cta", "Envie mensagem hoje"),
    ],
)
def test_generated_copy_rejects_missing_or_unsupported_claims(field, value):
    fact_id = uuid4()
    assert not generated_copy_matches_fact(
        _draft(fact_id).model_copy(update={field: value}), "Croissant por R$ 19,90", []
    )


def test_generated_copy_rejects_money_misassociation_and_avoided_topics():
    draft = _draft(uuid4())
    assert not generated_copy_matches_fact(draft, "Croissant por R$ 19,90", ["croissant"])
    assert not generated_copy_matches_fact(draft.model_copy(update={"fact_ids": []}), "Croissant por R$ 19,90", [])
    assert not generated_copy_matches_fact(
        draft.model_copy(update={"art_text": "Croissant por R$ 1.000,00"}), "Croissant por R$ 1000,00", []
    )


@pytest.mark.parametrize(
    "name,amount,fmt",
    [
        ("Croissant", 1800, "photo"),
        ("Cachorro-quente", 1990, "story"),
        ("Alongamento acrílico decorado", 9500, "story"),
    ],
)
def test_three_business_price_cases_can_keep_model_copy(name, amount, fmt):
    snapshot = _snapshot(amount)
    snapshot["offering"]["name"] = name
    fact = _catalog_price_fact(snapshot)
    assert fact is not None
    statement = fact["statement"]
    draft = ProposalDraft(
        title=f"Conheça {name}",
        format=fmt,
        angle=f"Conheça {statement}",
        fact_ids=[UUID(fact["id"])],
        hypotheses=[],
        questions=[],
        art_text=statement,
        caption=f"Conheça {statement}",
        cta="Envie mensagem",
    )
    assert generated_copy_matches_fact(draft, statement, [])
