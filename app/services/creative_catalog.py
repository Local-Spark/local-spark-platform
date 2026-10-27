"""Owner-scoped candidate lookup and factual snapshots for creative planning.

Text matching returns candidates, not a decision: wording, negation and intent
must be resolved separately. Call within the owner's tenant transaction.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import text

from app.services.auth import AuthError
from app.services.business_catalog import require_catalog_owner

MAX_SCANNED = 500
MAX_CANDIDATES = 8
MAX_PROMOTIONS = 10
OFFERING_FIELDS = ("kind", "name", "description", "category", "duration_minutes", "booking_instructions")


def _tokens(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).casefold()
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", without_accents))


def _mentions(request: str, name: str, aliases: list[str]) -> bool:
    source = f" {request} "
    for phrase in (name, *aliases):
        phrase = _tokens(phrase)
        if phrase and f" {phrase} " in source:
            return True
    return False


def _price(row: Any, timezone: str, now: datetime) -> dict[str, object]:
    amount = row["price_minor"]
    valid_until = row["price_valid_until"]
    if amount is None or valid_until is None:
        return {"status": "not_set", "amount_minor": None, "valid_until": None}
    try:
        current_date = now.astimezone(ZoneInfo(timezone)).date()
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        return {"status": "unknown_timezone", "amount_minor": None, "valid_until": valid_until.isoformat()}
    if valid_until < current_date:
        return {"status": "expired", "amount_minor": None, "valid_until": valid_until.isoformat()}
    return {"status": "valid", "amount_minor": int(amount), "valid_until": valid_until.isoformat()}


async def _head(session: Any, tenant: UUID, business: UUID) -> int:
    # Serialize against catalog edits during the caller's short transaction.
    return int(
        await session.scalar(
            text("""SELECT version FROM business_catalog_heads
              WHERE tenant_id=:tenant AND business_id=:business FOR SHARE"""),
            {"tenant": tenant, "business": business},
        )
        or 0
    )


async def catalog_candidates(
    session: Any, tenant: UUID, business: UUID, actor: UUID, message: str
) -> dict[str, object]:
    """Find bounded, owner-confirmed lexical candidates; never infer intent."""
    await require_catalog_owner(session, tenant, business, actor)
    version = await _head(session, tenant, business)
    query = _tokens(message[:4000])
    if not query:
        return {"status": "no_text", "catalog_version": version, "candidates": []}
    if not version:
        return {"status": "not_found", "catalog_version": version, "candidates": []}
    rows = (
        (
            await session.execute(
                text("""SELECT id,kind,name,aliases FROM business_offerings
                  WHERE tenant_id=:tenant AND business_id=:business AND state='active'
                  ORDER BY position,id LIMIT :limit"""),
                {"tenant": tenant, "business": business, "limit": MAX_SCANNED + 1},
            )
        )
        .mappings()
        .all()
    )
    # Do not claim uniqueness after inspecting only part of a large catalog.
    if len(rows) > MAX_SCANNED:
        return {"status": "catalog_too_large", "catalog_version": version, "candidates": []}
    matches = [
        {"id": str(row["id"]), "kind": row["kind"], "name": row["name"]}
        for row in rows
        if _mentions(query, row["name"], row["aliases"])
    ]
    if len(matches) > MAX_CANDIDATES:
        return {"status": "too_many_matches", "catalog_version": version, "candidates": []}
    return {
        "status": "needs_selection" if matches else "not_found",
        "catalog_version": version,
        "candidates": matches,
    }


async def selected_catalog_snapshot(
    session: Any,
    tenant: UUID,
    business: UUID,
    actor: UUID,
    message: str,
    offering_id: UUID,
    expected_catalog_version: int,
    now: datetime,
) -> dict[str, object]:
    """Capture only an explicitly resolved candidate; caller still checks intent.

    There is no network access here. A later effect must revalidate tenant,
    access, source versions, deletion, rights and time-sensitive prices.
    """
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("A timezone-aware instant is required")
    now = now.astimezone(UTC)
    candidates = await catalog_candidates(session, tenant, business, actor, message)
    if candidates["catalog_version"] != expected_catalog_version:
        raise AuthError("COLLECTION_CONTEXT_CHANGED", 409)
    choices = cast(list[dict[str, str]], candidates["candidates"])
    if candidates["status"] != "needs_selection" or not any(
        candidate["id"] == str(offering_id) for candidate in choices
    ):
        raise AuthError("COLLECTION_ITEM_NOT_CANDIDATE", 409)
    params = {"tenant": tenant, "business": business, "item": offering_id}
    row = (
        (
            await session.execute(
                text("""SELECT o.id,o.version,o.kind,o.name,o.description,o.category,o.price_minor,
                     o.price_valid_until,o.duration_minutes,o.booking_instructions,b.timezone
                  FROM business_offerings o JOIN businesses b ON b.tenant_id=o.tenant_id AND b.id=o.business_id
                  WHERE o.tenant_id=:tenant AND o.business_id=:business AND o.id=:item AND o.state='active'"""),
                params,
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None:
        raise AuthError("COLLECTION_CONTEXT_CHANGED", 409)
    promotions = (
        (
            await session.execute(
                text("""SELECT id,version,title,description,price_minor,starts_at,ends_at
                  FROM business_offering_promotions WHERE tenant_id=:tenant AND business_id=:business
                    AND offering_id=:item AND state='active' AND starts_at<=:now AND ends_at>:now
                  ORDER BY starts_at DESC,id LIMIT :limit"""),
                {**params, "now": now, "limit": MAX_PROMOTIONS + 1},
            )
        )
        .mappings()
        .all()
    )
    # An incomplete list of competing offers must not be passed off as complete.
    if len(promotions) > MAX_PROMOTIONS:
        raise AuthError("COLLECTION_PROMOTIONS_AMBIGUOUS", 409)
    photos = (
        (
            await session.execute(
                text("""(SELECT id,version,sha256,item_id,space_kind FROM business_collection_photos
                  WHERE tenant_id=:tenant AND business_id=:business AND state='ready' AND status='active'
                    AND rights_scope='business_collection_confirmed' AND item_id=:item
                  ORDER BY sort_order,id LIMIT 1)
                  UNION ALL
                  (SELECT id,version,sha256,item_id,space_kind FROM business_collection_photos
                  WHERE tenant_id=:tenant AND business_id=:business AND state='ready' AND status='active'
                    AND rights_scope='business_collection_confirmed' AND item_id IS NULL
                    AND space_kind IN ('environment','room','counter')
                  ORDER BY sort_order,id LIMIT 1)"""),
                params,
            )
        )
        .mappings()
        .all()
    )
    item_photo = next((photo for photo in photos if photo["item_id"] == offering_id), None)
    space_photo = next((photo for photo in photos if photo["item_id"] is None), None)

    def reference(photo: Any) -> dict[str, object] | None:
        if photo is None:
            return None
        return {
            "id": str(photo["id"]),
            "version": int(photo["version"]),
            "sha256": photo["sha256"],
            "space_kind": photo["space_kind"],
        }

    return {
        "catalog_version": expected_catalog_version,
        "offering": {
            "id": str(row["id"]),
            "version": int(row["version"]),
            "kind": row["kind"],
            "name": row["name"],
            "description": row["description"],
            "category": row["category"],
            "duration_minutes": row["duration_minutes"],
            "booking_instructions": row["booking_instructions"],
            "price": {**_price(row, row["timezone"], now), "currency": "BRL"},
        },
        "promotions": [
            {
                "id": str(promo["id"]),
                "version": int(promo["version"]),
                "title": promo["title"],
                "description": promo["description"],
                "price_minor": promo["price_minor"],
                "currency": "BRL",
                "starts_at": promo["starts_at"].isoformat(),
                "ends_at": promo["ends_at"].isoformat(),
            }
            for promo in promotions
        ],
        "multiple_promotions": len(promotions) > 1,
        "item_photo": reference(item_photo),
        "space_photo": reference(space_photo),
        "resolved_at": now.isoformat(),
    }


async def validate_catalog_snapshot(
    session: Any,
    tenant: UUID,
    business: UUID,
    actor: UUID,
    snapshot: dict[str, object],
    now: datetime,
) -> str:
    """Recheck captured sources just before a later effect under current owner/RLS.

    Catalog updates currently revise the whole projection. Rejecting an
    unrelated catalog edit is conservative and requires a new resolution.
    The snapshot must be generated and stored by a trusted server; this check
    does not authenticate arbitrary client JSON or atomically commit an external
    publication. Free-text descriptions are not proof of a current price.
    """
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("A timezone-aware instant is required")
    now = now.astimezone(UTC)
    await require_catalog_owner(session, tenant, business, actor)
    try:
        version = snapshot["catalog_version"]
        offering = cast(dict[str, Any], snapshot["offering"])
        offering_id = UUID(offering["id"])
        offering_version = int(offering["version"])
        captured_price = cast(dict[str, object], offering["price"])
        promotions = cast(list[dict[str, Any]], snapshot["promotions"])
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            return "invalid"
        if not isinstance(promotions, list) or not isinstance(captured_price, dict):
            return "invalid"
        if not all(field in offering for field in OFFERING_FIELDS):
            return "invalid"
        multiple = snapshot["multiple_promotions"]
        if not isinstance(multiple, bool) or multiple != (len(promotions) > 1):
            return "invalid"
        references = []
        for kind in ("item_photo", "space_photo"):
            reference = snapshot[kind]
            if reference is not None:
                reference = cast(dict[str, Any], reference)
                identifier = UUID(reference["id"])
                number = int(reference["version"])
                digest = reference["sha256"]
                space_kind = reference["space_kind"]
                if number < 1 or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                    return "invalid"
                if (kind == "item_photo" and space_kind is not None) or (
                    kind == "space_photo" and space_kind not in {"environment", "room", "counter"}
                ):
                    return "invalid"
                references.append((kind, identifier, number, digest, space_kind))
    except (KeyError, TypeError, ValueError, AttributeError):
        return "invalid"
    if await _head(session, tenant, business) != version:
        return "catalog_changed"
    params = {"tenant": tenant, "business": business, "item": offering_id}
    row = (
        (
            await session.execute(
                text("""SELECT o.version,o.kind,o.name,o.description,o.category,o.duration_minutes,
                  o.booking_instructions,o.price_minor,o.price_valid_until,b.timezone FROM business_offerings o
                  JOIN businesses b ON b.tenant_id=o.tenant_id AND b.id=o.business_id
                  WHERE o.tenant_id=:tenant AND o.business_id=:business AND o.id=:item AND o.state='active'"""),
                params,
            )
        )
        .mappings()
        .one_or_none()
    )
    if row is None or row["version"] != offering_version:
        return "catalog_changed"
    if any(offering[field] != row[field] for field in OFFERING_FIELDS):
        return "catalog_changed"
    current_price = {**_price(row, row["timezone"], now), "currency": "BRL"}
    if current_price != captured_price:
        return "price_changed_or_expired"
    current_promotions = (
        (
            await session.execute(
                text("""SELECT id,version,title,description,price_minor,starts_at,ends_at
                  FROM business_offering_promotions WHERE tenant_id=:tenant AND business_id=:business
                    AND offering_id=:item AND state='active' AND starts_at<=:now AND ends_at>:now
                  ORDER BY starts_at DESC,id LIMIT :limit"""),
                {**params, "now": now, "limit": MAX_PROMOTIONS + 1},
            )
        )
        .mappings()
        .all()
    )
    present = [
        {
            "id": str(promo["id"]),
            "version": int(promo["version"]),
            "title": promo["title"],
            "description": promo["description"],
            "price_minor": promo["price_minor"],
            "currency": "BRL",
            "starts_at": promo["starts_at"].isoformat(),
            "ends_at": promo["ends_at"].isoformat(),
        }
        for promo in current_promotions
    ]
    if len(current_promotions) > MAX_PROMOTIONS or present != promotions:
        return "promotions_changed_or_expired"
    for kind, identifier, number, digest, space_kind in references:
        exists = await session.scalar(
            text("""SELECT 1 FROM business_collection_photos
              WHERE tenant_id=:tenant AND business_id=:business AND id=:id AND version=:version AND sha256=:sha
                AND state='ready' AND status='active' AND rights_scope='business_collection_confirmed'
                AND ((:kind='item_photo' AND item_id=:item AND space_kind IS NULL)
                  OR (:kind='space_photo' AND item_id IS NULL AND space_kind=:space))"""),
            {**params, "id": identifier, "version": number, "sha": digest, "kind": kind, "space": space_kind},
        )
        if not exists:
            return "photo_changed_or_removed"
    return "valid"
