"""Advance a confirmed empty response through approved radii, sharing one budget."""

import hmac
from dataclasses import dataclass
from typing import Literal, cast
from uuid import UUID, uuid5

from pydantic import SecretStr
from sqlalchemy import text

from app.db.session import Database
from app.schemas.business_address import ShopAddress
from app.services.reference_business_identity_mac import BusinessIdentityBindingError, business_identity_mac
from app.services.reference_search_admission import search_identity_mac


@dataclass(frozen=True)
class EmptySearchAdvance:
    state: Literal["scheduled", "cached", "exhausted"]
    next_search_id: UUID | None = None
    result_id: UUID | None = None


async def advance_empty_search(
    database: Database, key: SecretStr, key_version: str, tenant: UUID, business: UUID, actor: UUID, search: UUID
) -> EmptySearchAdvance:
    root: UUID | None = None
    parent = search
    # Each successful pass advances 5→20 or20→50. Cached empty results do not cause new HTTP.
    while True:
        async with database.transaction(tenant, actor) as session:
            replay = await session.scalar(
                text("SELECT public.reference_read_empty_advance(:business,:root,:parent)"),
                {"business": business, "root": root, "parent": parent},
            )
            if replay is not None:
                root = UUID(replay["root_id"])
                if replay["state"] == "cached" and replay["next_empty"] and replay["result_id"] is None:
                    parent = UUID(replay["next_search_id"])
                    continue
                return EmptySearchAdvance(
                    replay["state"],
                    UUID(replay["next_search_id"]) if replay["next_search_id"] else None,
                    UUID(replay["result_id"]) if replay["result_id"] else None,
                )
            value = await session.scalar(
                text("SELECT public.reference_empty_successor_context(:business,:root,:parent)"),
                {"business": business, "root": root, "parent": parent},
            )
            root = UUID(value["root_id"])
            address = ShopAddress.model_validate(value["address"])
            if key_version != value["key_version"]:
                raise BusinessIdentityBindingError("REFERENCE_BUSINESS_IDENTITY_INVALID")
            expected = business_identity_mac(
                key,
                key_version=key_version,
                tenant=tenant,
                business=business,
                search=root,
                search_actor=actor,
                context_version=value["context_version"],
                business_row_version=value["row_version"],
                address_version=value["address_version"],
                location_version=value["location_version"],
                name=value["name"],
                address=address,
            )
            if not hmac.compare_digest(expected, value["identity_mac"]):
                raise BusinessIdentityBindingError("REFERENCE_BUSINESS_IDENTITY_INVALID")
            radius = value["next_radius"]
            if radius is None:
                operation = uuid5(root, "reference-empty-family-publication-v1")
                result_id = uuid5(parent, "reference-empty-result-v1")
                result = await session.scalar(
                    text("SELECT public.reference_publish_empty_search(:business,:root,:parent,:operation,:result)"),
                    {"business": business, "root": root, "parent": parent, "operation": operation, "result": result_id},
                )
                return EmptySearchAdvance("exhausted", result_id=UUID(str(result)))
            operation = uuid5(UUID(value["root_operation"]), f"reference-empty-radius-v1:{radius}")
            next_search = uuid5(operation, f"reference-provider-search-v1:{tenant}:{business}")
            search_mac = search_identity_mac(
                key, key_version, tenant, business, actor, operation, value["context_version"], radius
            )
            own_mac = business_identity_mac(
                key,
                key_version=key_version,
                tenant=tenant,
                business=business,
                search=next_search,
                search_actor=actor,
                context_version=value["context_version"],
                business_row_version=value["row_version"],
                address_version=value["address_version"],
                location_version=value["location_version"],
                name=value["name"],
                address=address,
            )
            result = await session.scalar(
                text("""SELECT public.reference_admit_empty_radius_successor(
              :business,:root,:parent,:operation,:search,:event,:mac,:identity,:key)"""),
                {
                    "business": business,
                    "root": root,
                    "parent": parent,
                    "operation": operation,
                    "search": next_search,
                    "event": uuid5(operation, "request-event"),
                    "mac": search_mac,
                    "identity": own_mac,
                    "key": key_version,
                },
            )
        next_search = UUID(result["next_search_id"])
        if result["state"] == "cached" and result["next_empty"] and result["result_id"] is None:
            parent = next_search
            continue
        return EmptySearchAdvance(
            cast(Literal["scheduled", "cached"], result["state"]),
            next_search,
            UUID(result["result_id"]) if result["result_id"] is not None else None,
        )
