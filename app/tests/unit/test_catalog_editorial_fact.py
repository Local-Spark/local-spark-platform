"""A catalog name is usable only with a stable, valid source and no price claim."""

from uuid import uuid4

import pytest

from app.services.editorial_proposals import EditorialProposalService, _catalog_fact


def test_fact_id_is_bound_to_item_version_and_name_only():
    offering = {"id": str(uuid4()), "version": 3, "kind": "product", "name": "Croissant", "price": "R$ 20"}
    fact = _catalog_fact({"offering": offering})
    assert fact is not None and fact["statement"] == "Croissant" and "R$" not in str(fact)
    assert _catalog_fact({"offering": offering}) == fact
    assert _catalog_fact({"offering": {**offering, "version": 4}})["id"] != fact["id"]


@pytest.mark.parametrize(
    "offering",
    [
        None,
        {},
        {"id": "bad", "version": 1, "kind": "product", "name": "Croissant"},
        {"id": str(uuid4()), "version": 1, "kind": "product", "name": "Croissant R$ 20"},
        {"id": str(uuid4()), "version": 1, "kind": "product", "name": ""},
        {"id": str(uuid4()), "version": 1, "kind": "other", "name": "Croissant"},
        {"id": str(uuid4()), "version": True, "kind": "product", "name": "Croissant"},
    ],
)
def test_never_uses_malformed_or_unverified_commercial_claims(offering):
    assert _catalog_fact({"offering": offering}) is None


@pytest.mark.parametrize(
    "requested,kind,expected", [("photo", "text", "photo"), ("story", "image", "story"), (None, "audio", "story")]
)
def test_requested_and_allowed_format_reaches_baseline(requested, kind, expected):
    item = uuid4()
    data = {
        "confirmed_facts": [{"id": str(item), "statement": "Croissant"}],
        "preferences": {"avoided_topics": []},
        "material_kind": kind,
        "source_asset_id": None,
        "requested_format": requested,
        "eligible_formats": ["photo", "story"],
    }
    draft = EditorialProposalService._baseline(data)
    assert draft.format == expected and EditorialProposalService._safe(draft, data, {item})
    assert not EditorialProposalService._safe(draft.model_copy(update={"format": "short_video"}), data, {item})
    if requested:
        other = "story" if requested == "photo" else "photo"
        assert not EditorialProposalService._safe(draft.model_copy(update={"format": other}), data, {item})
