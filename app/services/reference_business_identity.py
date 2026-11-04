"""Load the bound, current owner identity into a provider activity's memory."""

import hmac
from collections.abc import Mapping
from dataclasses import dataclass
from uuid import UUID

from pydantic import SecretStr
from sqlalchemy import text

from app.db.session import Database
from app.schemas.business_address import ShopAddress
from app.services.reference_business_identity_mac import BusinessIdentityBindingError, business_identity_mac


@dataclass(frozen=True, repr=False)
class BusinessIdentity:
    name: str
    address: ShopAddress


async def load_business_identity(
    database: Database, keys: Mapping[str, SecretStr], tenant: UUID, business: UUID, actor: UUID, search: UUID
) -> BusinessIdentity:
    async with database.transaction(tenant, actor) as session:
        row = await session.scalar(
            text("SELECT public.reference_load_business_identity(:business,:search)"),
            {"business": business, "search": search},
        )
        try:
            address = ShopAddress.model_validate(row["address"])
            mac = business_identity_mac(
                keys[row["key_version"]],
                key_version=row["key_version"],
                tenant=tenant,
                business=business,
                search=search,
                search_actor=actor,
                context_version=row["context_version"],
                business_row_version=row["row_version"],
                address_version=row["address_version"],
                location_version=row["location_version"],
                name=row["name"],
                address=address,
            )
        except (KeyError, TypeError, ValueError):
            raise BusinessIdentityBindingError("REFERENCE_BUSINESS_IDENTITY_INVALID") from None
        if not hmac.compare_digest(mac, row["mac"]):
            raise BusinessIdentityBindingError("REFERENCE_BUSINESS_IDENTITY_INVALID")
        return BusinessIdentity(name=row["name"], address=address)
