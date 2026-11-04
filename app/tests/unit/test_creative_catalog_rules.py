from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.auth import AuthError
from app.services.creative_catalog import (
    _head,
    _mentions,
    _price,
    _tokens,
    catalog_candidates,
    selected_catalog_snapshot,
)


def _rows(*, all_rows=None, one=None):
    result = MagicMock()
    result.mappings.return_value.all.return_value = all_rows if all_rows is not None else []
    result.mappings.return_value.one_or_none.return_value = one
    return result


def test_matching_normalizes_accents_and_requires_complete_words():
    assert _tokens("Faça uma foto do PÃO de queijo!") == "faca uma foto do pao de queijo"
    assert _mentions(_tokens("Mostre o pão de queijo"), "Pão de queijo", [])
    assert _mentions(_tokens("Um folhado, por favor"), "Croissant", ["Folhado"])
    assert not _mentions(_tokens("Pãozinho"), "Pão", ["  "])
    # A mention remains only a candidate; negation is not treated as approval.
    assert _mentions(_tokens("Não quero croissant"), "Croissant", [])


def test_prices_are_evaluated_in_business_timezone_and_unknown_is_not_usable():
    base = {"price_minor": 2000, "price_valid_until": date(2026, 10, 27)}
    same_local_day = datetime(2026, 10, 28, 1, 0, tzinfo=UTC)
    assert _price(base, "America/Sao_Paulo", same_local_day)["status"] == "valid"
    expired = _price(base, "America/Sao_Paulo", datetime(2026, 10, 28, 4, 0, tzinfo=UTC))
    assert expired == {"status": "expired", "amount_minor": None, "valid_until": "2026-10-27"}
    unknown = _price(base, "Invalid/Timezone", same_local_day)
    assert unknown["status"] == "unknown_timezone" and unknown["amount_minor"] is None
    assert _price({"price_minor": None, "price_valid_until": None}, "UTC", same_local_day)["status"] == "not_set"
    assert _price({"price_minor": 500, "price_valid_until": None}, "UTC", same_local_day)["status"] == "not_set"


async def test_catalog_head_returns_zero_when_absent():
    session = AsyncMock()
    session.scalar.side_effect = [None, 3]
    assert await _head(session, uuid4(), uuid4()) == 0
    assert await _head(session, uuid4(), uuid4()) == 3


@pytest.mark.parametrize(
    ("message", "version", "rows", "status", "expected_count"),
    [
        ("  ", 0, [], "no_text", 0),
        ("croissant", 0, [], "not_found", 0),
        ("suco", 1, [{"id": uuid4(), "kind": "product", "name": "Croissant", "aliases": []}], "not_found", 0),
        (
            "não quero croissant",
            1,
            [{"id": uuid4(), "kind": "product", "name": "Croissant", "aliases": []}],
            "needs_selection",
            1,
        ),
        (
            "folhado",
            1,
            [{"id": uuid4(), "kind": "product", "name": "Croissant", "aliases": ["Folhado"]}],
            "needs_selection",
            1,
        ),
        (
            "croissant",
            1,
            [{"id": uuid4(), "kind": "product", "name": "Croissant", "aliases": []}] * 9,
            "too_many_matches",
            0,
        ),
        (
            "croissant",
            1,
            [{"id": uuid4(), "kind": "product", "name": "Croissant", "aliases": []}] * 501,
            "catalog_too_large",
            0,
        ),
    ],
)
async def test_candidate_lookup_never_claims_semantic_confirmation(
    monkeypatch, message, version, rows, status, expected_count
):
    owner = AsyncMock()
    monkeypatch.setattr("app.services.creative_catalog.require_catalog_owner", owner)
    monkeypatch.setattr("app.services.creative_catalog._head", AsyncMock(return_value=version))
    session = AsyncMock()
    session.execute.return_value = _rows(all_rows=rows)
    tenant, business, actor = uuid4(), uuid4(), uuid4()
    result = await catalog_candidates(session, tenant, business, actor, message)
    assert result["status"] == status and len(result["candidates"]) == expected_count
    owner.assert_awaited_once_with(session, tenant, business, actor)


def _item(item):
    return {
        "id": item,
        "version": 3,
        "kind": "product",
        "name": "Croissant",
        "description": "Folhado artesanal",
        "category": "Lanches",
        "price_minor": 2000,
        "price_valid_until": date(2026, 10, 27),
        "duration_minutes": None,
        "booking_instructions": None,
        "timezone": "America/Sao_Paulo",
    }


def _promo():
    return {
        "id": uuid4(),
        "version": 3,
        "title": "Promoção",
        "description": None,
        "price_minor": 1800,
        "starts_at": datetime(2026, 10, 27, 0, 0, tzinfo=UTC),
        "ends_at": datetime(2026, 10, 29, 0, 0, tzinfo=UTC),
    }


async def _snapshot(monkeypatch, *, candidates=None, row=None, promos=None, photos=None, now=None):
    item = row["id"] if row else uuid4()
    monkeypatch.setattr(
        "app.services.creative_catalog.catalog_candidates",
        AsyncMock(
            return_value=candidates
            or {"status": "needs_selection", "catalog_version": 3, "candidates": [{"id": str(item)}]}
        ),
    )
    session = AsyncMock()
    session.execute.side_effect = [_rows(one=row), _rows(all_rows=promos), _rows(all_rows=photos)]
    return await selected_catalog_snapshot(
        session, uuid4(), uuid4(), uuid4(), "crie um croissant", item, 3, now or datetime(2026, 10, 28, 1, tzinfo=UTC)
    )


async def test_snapshot_keeps_only_authorized_versions_and_no_urls(monkeypatch):
    item = uuid4()
    picture, room = uuid4(), uuid4()
    photos = [
        {"id": picture, "version": 1, "sha256": "a" * 64, "item_id": item, "space_kind": None},
        {"id": room, "version": 2, "sha256": "b" * 64, "item_id": None, "space_kind": "room"},
    ]
    result = await _snapshot(monkeypatch, row=_item(item), promos=[_promo(), _promo()], photos=photos)
    assert result["catalog_version"] == 3
    assert result["offering"]["price"] == {
        "status": "valid",
        "amount_minor": 2000,
        "valid_until": "2026-10-27",
        "currency": "BRL",
    }
    assert result["multiple_promotions"] is True and len(result["promotions"]) == 2
    assert result["item_photo"]["id"] == str(picture) and result["space_photo"]["id"] == str(room)
    assert "object_key" not in str(result) and "url" not in str(result)


async def test_snapshot_without_photos_and_promotions_is_still_valid(monkeypatch):
    result = await _snapshot(monkeypatch, row=_item(uuid4()))
    assert result["item_photo"] is None and result["space_photo"] is None
    assert result["promotions"] == [] and result["multiple_promotions"] is False


async def test_snapshot_refuses_naive_time_changed_version_and_unselected_candidate(monkeypatch):
    with pytest.raises(ValueError, match="timezone-aware"):
        await _snapshot(monkeypatch, now=datetime(2026, 10, 28))
    with pytest.raises(AuthError, match="COLLECTION_CONTEXT_CHANGED"):
        await _snapshot(monkeypatch, candidates={"status": "needs_selection", "catalog_version": 2, "candidates": []})
    for candidates in (
        {"status": "not_found", "catalog_version": 3, "candidates": []},
        {"status": "needs_selection", "catalog_version": 3, "candidates": [{"id": str(uuid4())}]},
    ):
        with pytest.raises(AuthError, match="COLLECTION_ITEM_NOT_CANDIDATE"):
            await _snapshot(monkeypatch, candidates=candidates)


async def test_snapshot_refuses_disappearing_item_and_many_active_promotions(monkeypatch):
    with pytest.raises(AuthError, match="COLLECTION_CONTEXT_CHANGED"):
        await _snapshot(monkeypatch)
    with pytest.raises(AuthError, match="COLLECTION_PROMOTIONS_AMBIGUOUS"):
        await _snapshot(monkeypatch, row=_item(uuid4()), promos=[_promo()] * 11)


def _saved_snapshot(*, item=None, photos=False):
    item = item or uuid4()
    snapshot = {
        "catalog_version": 3,
        "offering": {
            "id": str(item),
            "version": 3,
            "kind": "product",
            "name": "Croissant",
            "description": "Folhado artesanal",
            "category": "Lanches",
            "duration_minutes": None,
            "booking_instructions": None,
            "price": {"status": "valid", "amount_minor": 2000, "valid_until": "2026-10-27", "currency": "BRL"},
        },
        "promotions": [],
        "multiple_promotions": False,
        "item_photo": None,
        "space_photo": None,
    }
    if photos:
        snapshot["item_photo"] = {"id": str(uuid4()), "version": 1, "sha256": "a" * 64, "space_kind": None}
        snapshot["space_photo"] = {"id": str(uuid4()), "version": 2, "sha256": "b" * 64, "space_kind": "room"}
    return snapshot


async def _validate(monkeypatch, snapshot, *, version=3, row=None, promos=None, found=None, now=None):
    from app.services.creative_catalog import validate_catalog_snapshot

    monkeypatch.setattr("app.services.creative_catalog.require_catalog_owner", AsyncMock())
    monkeypatch.setattr("app.services.creative_catalog._head", AsyncMock(return_value=version))
    session = AsyncMock()
    session.execute.side_effect = [_rows(one=row), _rows(all_rows=promos)]
    session.scalar.side_effect = found if found is not None else []
    return await validate_catalog_snapshot(
        session, uuid4(), uuid4(), uuid4(), snapshot, now or datetime(2026, 10, 28, 1, tzinfo=UTC)
    )


async def test_revalidate_current_snapshot_and_every_photo(monkeypatch):
    item = uuid4()
    assert await _validate(monkeypatch, _saved_snapshot(item=item), row=_item(item)) == "valid"
    assert (
        await _validate(monkeypatch, _saved_snapshot(item=item, photos=True), row=_item(item), found=[1, 1]) == "valid"
    )
    assert (
        await _validate(monkeypatch, _saved_snapshot(item=item, photos=True), row=_item(item), found=[1, None])
        == "photo_changed_or_removed"
    )


@pytest.mark.parametrize(
    "field", ["kind", "name", "description", "category", "duration_minutes", "booking_instructions"]
)
async def test_revalidate_detects_tampered_offering_fields(monkeypatch, field):
    item = uuid4()
    snapshot = _saved_snapshot(item=item)
    snapshot["offering"][field] = "changed"
    assert await _validate(monkeypatch, snapshot, row=_item(item)) == "catalog_changed"


async def test_revalidate_rejects_inconsistent_promotion_flag_and_missing_field(monkeypatch):
    snapshot = _saved_snapshot()
    snapshot["multiple_promotions"] = True
    assert await _validate(monkeypatch, snapshot) == "invalid"
    snapshot = _saved_snapshot()
    del snapshot["offering"]["description"]
    assert await _validate(monkeypatch, snapshot) == "invalid"


async def test_request_only_snapshot_rejects_unknown_policy_and_embedded_legacy_promotion(monkeypatch):
    snapshot = _saved_snapshot()
    snapshot["promotion_policy"] = "unexpected"
    assert await _validate(monkeypatch, snapshot) == "invalid"
    snapshot["promotion_policy"] = "request_only"
    snapshot["promotions"] = [{"title": "Promoção antiga"}]
    assert await _validate(monkeypatch, snapshot) == "invalid"
    snapshot = _saved_snapshot()
    snapshot["promotion_policy"] = "request_only"
    snapshot["offering"]["version"] = 4
    assert await _validate(monkeypatch, snapshot) == "invalid"
    snapshot["offering"]["version"] = 3
    assert await _validate(monkeypatch, snapshot, version=2) == "catalog_changed"


async def test_revalidate_conflict_expiration_and_promotion_change(monkeypatch):
    item = uuid4()
    snapshot = _saved_snapshot(item=item)
    assert await _validate(monkeypatch, snapshot, version=4) == "catalog_changed"
    assert await _validate(monkeypatch, snapshot) == "catalog_changed"
    assert await _validate(monkeypatch, snapshot, row={**_item(item), "version": 4}) == "catalog_changed"
    assert (
        await _validate(monkeypatch, snapshot, row=_item(item), now=datetime(2026, 10, 28, 4, tzinfo=UTC))
        == "price_changed_or_expired"
    )
    assert await _validate(monkeypatch, snapshot, row=_item(item), promos=[_promo()]) == "promotions_changed_or_expired"
    assert (
        await _validate(monkeypatch, snapshot, row=_item(item), promos=[_promo()] * 11)
        == "promotions_changed_or_expired"
    )


@pytest.mark.parametrize(
    "snapshot",
    [
        {},
        {**_saved_snapshot(), "catalog_version": 0},
        {**_saved_snapshot(), "catalog_version": True},
        {**_saved_snapshot(), "catalog_version": "3"},
        {**_saved_snapshot(), "promotions": "not-a-list"},
        {**_saved_snapshot(), "offering": {"id": str(uuid4()), "version": 3, "price": "bad"}},
        {**_saved_snapshot(), "item_photo": {"id": "bad", "version": 1, "sha256": "a" * 64, "space_kind": None}},
        {**_saved_snapshot(), "item_photo": {"id": str(uuid4()), "version": 0, "sha256": "a" * 64, "space_kind": None}},
        {**_saved_snapshot(), "item_photo": {"id": str(uuid4()), "version": 1, "sha256": "bad", "space_kind": None}},
        {
            **_saved_snapshot(),
            "item_photo": {"id": str(uuid4()), "version": 1, "sha256": "a" * 64, "space_kind": "room"},
        },
        {
            **_saved_snapshot(),
            "space_photo": {"id": str(uuid4()), "version": 1, "sha256": "a" * 64, "space_kind": "facade"},
        },
    ],
)
async def test_revalidate_rejects_malformed_snapshots(monkeypatch, snapshot):
    assert await _validate(monkeypatch, snapshot) == "invalid"


async def test_revalidate_requires_aware_clock(monkeypatch):
    with pytest.raises(ValueError, match="timezone-aware"):
        await _validate(monkeypatch, _saved_snapshot(), now=datetime(2026, 10, 28))
