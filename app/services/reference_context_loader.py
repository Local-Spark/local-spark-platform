"""Load trusted, versioned search inputs directly into an activity's memory."""

import hmac
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal
from uuid import UUID, uuid5

from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError
from sqlalchemy import text

from app.db.session import Database
from app.schemas.editorial_context import EditorialPreferences, ReferenceCoordinates
from app.services.reference_search_admission import SearchAdmissionError, search_identity_mac


class ReferenceContextLoadError(Exception):
    """Stable error without location, context, MAC, or key material."""


class _StoredContext(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    operation_id: UUID
    context_version: int = Field(gt=0)
    radius_km: Literal[5, 20, 50]
    identity_key_version: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,64}$")
    request_mac: str = Field(pattern=r"^[0-9a-f]{64}$")
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    business_terms: list[str]
    business_description: str | None


@dataclass(frozen=True, repr=False)
class LoadedSearchContext:
    context_version: int
    radius_km: int
    latitude: float
    longitude: float
    business_terms: tuple[str, ...]
    business_description: str | None


async def load_search_context(
    database: Database,
    keys: Mapping[str, SecretStr],
    tenant: UUID,
    business: UUID,
    actor: UUID,
    search: UUID,
    event: UUID,
) -> LoadedSearchContext:
    """Use an authorized event, then check the private HMAC before returning inputs.

    Inputs never become a Temporal workflow result or log field. The caller
    must still bind the eventual provider request and reserve its cost.
    """
    async with database.transaction(tenant, actor) as session:
        value = await session.scalar(
            text("SELECT public.reference_load_search_context(:business,:search,:event)"),
            {"business": business, "search": search, "event": event},
        )
    try:
        parsed = _StoredContext.model_validate(value)
        key = keys[parsed.identity_key_version]
        expected = search_identity_mac(
            key,
            parsed.identity_key_version,
            tenant,
            business,
            actor,
            parsed.operation_id,
            parsed.context_version,
            parsed.radius_km,
        )
        expected_search = uuid5(parsed.operation_id, f"reference-provider-search-v1:{tenant}:{business}")
        if search != expected_search or not hmac.compare_digest(expected, parsed.request_mac):
            raise ReferenceContextLoadError("REFERENCE_CONTEXT_INTEGRITY_INVALID")
        coordinates = ReferenceCoordinates(latitude=parsed.latitude, longitude=parsed.longitude, confirmed=True)
        preferences = EditorialPreferences(
            business_terms=parsed.business_terms, business_characteristics=parsed.business_description
        )
        if not preferences.business_terms:
            raise ReferenceContextLoadError("REFERENCE_CONTEXT_INTEGRITY_INVALID")
    except (ValidationError, KeyError, SearchAdmissionError, TypeError):
        raise ReferenceContextLoadError("REFERENCE_CONTEXT_INTEGRITY_INVALID") from None
    return LoadedSearchContext(
        context_version=parsed.context_version,
        radius_km=parsed.radius_km,
        latitude=coordinates.latitude,
        longitude=coordinates.longitude,
        business_terms=tuple(preferences.business_terms),
        business_description=preferences.business_characteristics,
    )
