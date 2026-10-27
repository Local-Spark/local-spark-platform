"""Catalog input keeps prices, service fields and promotion confirmations unambiguous."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.business_catalog import CatalogContent, Offering, OfferingPromotion


def offering(**overrides):
    return {"id": uuid4(), "kind": "product", "name": " Croissant ", **overrides}


def promotion(item, **overrides):
    return {
        "id": uuid4(),
        "offering_id": item["id"],
        "title": "Oferta da tarde",
        "starts_at": "2026-10-01T13:00:00-03:00",
        "ends_at": "2026-10-31T18:00:00-03:00",
        **overrides,
    }


@pytest.mark.parametrize(
    "changes",
    [
        {"name": " "},
        {"name": "x" * 121},
        {"kind": "unknown"},
        {"state": "confirmed"},
        {"aliases": [" "]},
        {"aliases": ["x" * 121]},
        {"aliases": ["Café", " café "]},
        {"price_minor": 1800},
        {"price_valid_until": "2026-10-31"},
        {"price_minor": -1, "price_valid_until": "2026-10-31"},
        {"price_minor": True, "price_valid_until": "2026-10-31"},
        {"price_minor": 18.5, "price_valid_until": "2026-10-31"},
        {"currency": "USD"},
        {"duration_minutes": 30},
        {"booking_instructions": "Envie uma mensagem"},
        {"kind": "service", "duration_minutes": 0},
        {"kind": "service", "duration_minutes": True},
        {"position": -1},
        {"unrecognized": "field"},
    ],
)
def test_offering_rejects_invalid_or_ambiguous_values(changes):
    with pytest.raises(ValidationError):
        Offering.model_validate(offering(**changes))


def test_optional_progressive_catalog_accepts_expired_prices_for_owner_review():
    assert CatalogContent().offerings == []
    item = Offering.model_validate(
        offering(aliases=["  Folhado  "], price_minor=0, price_valid_until="2020-01-01", state="active")
    )
    assert item.name == "Croissant" and item.aliases == ["Folhado"]
    assert item.price_minor == 0
    service = Offering.model_validate(
        offering(kind="service", duration_minutes=60, booking_instructions="Agende pelo WhatsApp")
    )
    assert service.duration_minutes == 60
    assert Offering.model_validate(offering(kind="service")).booking_instructions is None


@pytest.mark.parametrize(
    "changes",
    [
        {"ends_at": "2026-10-01T13:00:00-03:00"},
        {"ends_at": "2026-09-30T18:00:00-03:00"},
        {"starts_at": "2026-10-01T13:00:00"},
        {"price_minor": -1},
        {"price_minor": False},
    ],
)
def test_promotion_requires_a_real_interval_and_integer_price(changes):
    with pytest.raises(ValidationError):
        OfferingPromotion.model_validate(promotion(offering(), **changes))


def test_catalog_requires_unique_ids_and_local_active_promotion_targets():
    item = offering(state="active")
    offer = promotion(item, state="active")
    assert CatalogContent.model_validate({"offerings": [item], "promotions": [offer]}).promotions[0].state == "active"
    invalid = [
        {"offerings": [item, item]},
        {"offerings": [item], "promotions": [offer, offer]},
        {"offerings": [], "promotions": [offer]},
        {"offerings": [{**item, "state": "archived"}], "promotions": [offer]},
    ]
    for document in invalid:
        with pytest.raises(ValidationError):
            CatalogContent.model_validate(document)
    assert (
        CatalogContent.model_validate(
            {"offerings": [{**item, "state": "archived"}], "promotions": [{**offer, "state": "archived"}]}
        )
        .offerings[0]
        .state
        == "archived"
    )
