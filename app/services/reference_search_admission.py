"""Admit private real-search identities without dispatching paid effects."""

import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4, uuid5

from pydantic import SecretStr
from sqlalchemy import text

from app.db.session import Database
from app.schemas.business_address import ShopAddress
from app.services.reference_business_identity_mac import business_identity_mac


class SearchAdmissionError(Exception):
    """Stable admission error without business data or key material."""


@dataclass(frozen=True)
class AdmittedSearch:
    search_id: UUID
    cycle_id: UUID
    event_id: UUID
    state: str
    created: bool


def search_identity_mac(
    key: SecretStr,
    key_version: str,
    tenant: UUID,
    business: UUID,
    actor: UUID,
    operation: UUID,
    context_version: int,
    radius: int,
) -> str:
    if not isinstance(key, SecretStr) or len(key.get_secret_value().encode()) < 32:
        raise SearchAdmissionError("REFERENCE_SEARCH_KEY_INVALID")
    if (
        not isinstance(key_version, str)
        or re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", key_version) is None
        or any(not isinstance(value, UUID) for value in (tenant, business, actor, operation))
        or type(context_version) is not int
        or not 0 < context_version <= 9_223_372_036_854_775_807
        or type(radius) is not int
        or radius not in (5, 20, 50)
    ):
        raise SearchAdmissionError("REFERENCE_SEARCH_IDENTITY_INVALID")
    payload = json.dumps(
        [
            "reference-search-admission-v1",
            key_version,
            str(tenant),
            str(business),
            str(actor),
            str(operation),
            context_version,
            radius,
        ],
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hmac.new(key.get_secret_value().encode(), payload, hashlib.sha256).hexdigest()


async def admit_provider_search(
    database: Database,
    key: SecretStr,
    key_version: str,
    tenant: UUID,
    business: UUID,
    actor: UUID,
    operation: UUID,
    context_version: int,
    radius: int,
) -> AdmittedSearch:
    """Bind the declared shop identity and the chosen device or saved-address origin."""
    mac = search_identity_mac(key, key_version, tenant, business, actor, operation, context_version, radius)
    search = uuid5(operation, f"reference-provider-search-v1:{tenant}:{business}")
    async with database.transaction(tenant, actor) as session:
        own = await session.scalar(
            text("SELECT public.reference_prepare_business_identity(:business)"), {"business": business}
        )
        identity = business_identity_mac(
            key,
            key_version=key_version,
            tenant=tenant,
            business=business,
            search=search,
            search_actor=actor,
            context_version=context_version,
            business_row_version=own["row_version"],
            address_version=own["address_version"],
            location_version=own["location_version"],
            name=own["name"],
            address=ShopAddress.model_validate(own["address"]),
        )
        result: dict[str, Any] = await session.scalar(
            text("""SELECT public.reference_admit_bound_search(
              :business,:search,:operation,:event,:mac,:key_version,:context,CAST(:radius AS smallint),
              :identity,:name,:row,:address,:location,:origin)"""),
            {
                "business": business,
                "search": search,
                "operation": operation,
                "event": uuid4(),
                "mac": mac,
                "key_version": key_version,
                "context": context_version,
                "radius": radius,
                "identity": identity,
                "name": own["name"],
                "row": own["row_version"],
                "address": own["address_version"],
                "location": own["location_version"],
                "origin": UUID(own["origin_id"]) if own["origin_id"] else None,
            },
        )
    return AdmittedSearch(
        search_id=UUID(result["search_id"]),
        cycle_id=UUID(result["cycle_id"]),
        event_id=UUID(result["event_id"]),
        state=result["state"],
        created=result["created"],
    )
