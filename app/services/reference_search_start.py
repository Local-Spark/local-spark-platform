"""Admit the saved radius and shop identity, without making a provider request."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.config import Settings
from app.db.session import Database
from app.schemas.editorial_context import EditorialPreferences
from app.schemas.reference_execution import ReferenceSearchRetried, ReferenceSearchStart, ReferenceSearchStarted
from app.services.auth import AuthError
from app.services.reference_search_admission import admit_provider_search
from app.services.whatsapp_materials import WhatsAppMaterialsService


class ReferenceSearchStartService:
    def __init__(self, database: Database, settings: Settings) -> None:
        self.database, self.settings = database, settings

    async def start(
        self, tenant: UUID, business: UUID, actor: UUID, payload: ReferenceSearchStart
    ) -> ReferenceSearchStarted:
        if not self.settings.reference_discovery_ready():
            raise AuthError("REFERENCE_DISCOVERY_DISABLED", 503)
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            row = (
                (
                    await session.execute(
                        text("""SELECT h.version,v.document
              FROM business_context_heads h JOIN business_context_versions v USING(tenant_id,business_id,version)
              WHERE h.tenant_id=:tenant AND h.business_id=:business"""),
                        {"tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise AuthError("REFERENCE_SEARCH_CONTEXT_REQUIRED", 409)
            preferences = EditorialPreferences.model_validate(row["document"].get("preferences", {}))
            scope = preferences.reference_search
            if scope is None or scope.scope != "local" or scope.radius_km not in (5, 20, 50):
                raise AuthError("REFERENCE_SEARCH_CONTEXT_REQUIRED", 409)
            version, radius = row["version"], int(scope.radius_km)
        key = self.settings.reference_provider_hmac_key
        assert key is not None
        try:
            admitted = await admit_provider_search(
                self.database,
                key,
                self.settings.reference_provider_key_version,
                tenant,
                business,
                actor,
                payload.operation_id,
                version,
                radius,
            )
        except DBAPIError as error:
            for code in (
                "REFERENCE_RADIUS_ALREADY_SEARCHED",
                "REFERENCE_SEARCH_ADMISSION_CONFLICT",
                "REFERENCE_SEARCH_CONTEXT_INVALID",
                "REFERENCE_BUSINESS_IDENTITY_STALE",
                "REFERENCE_BUSINESS_ADDRESS_REQUIRED",
                "REFERENCE_BUSINESS_LOCATION_REQUIRED",
            ):
                if code in str(error.orig):
                    raise AuthError(code, 409) from None
            raise
        return ReferenceSearchStarted(search_id=admitted.search_id, cycle_id=admitted.cycle_id, state=admitted.state)

    async def retry(
        self, tenant: UUID, business: UUID, actor: UUID, search: UUID, payload: ReferenceSearchStart
    ) -> ReferenceSearchRetried:
        if not self.settings.reference_discovery_ready():
            raise AuthError("REFERENCE_DISCOVERY_DISABLED", 503)
        try:
            async with self.database.transaction(tenant, actor) as session:
                value = await session.scalar(
                    text("SELECT public.reference_request_execution_retry(:business,:search,:operation)"),
                    {"business": business, "search": search, "operation": payload.operation_id},
                )
        except DBAPIError as error:
            if "REFERENCE_OWNER_INACTIVE" in str(error.orig):
                raise AuthError("BUSINESS_OWNER_REQUIRED", 403) from None
            for code in (
                "REFERENCE_RETRY_REQUEST_INVALID",
                "REFERENCE_RETRY_REQUEST_CONFLICT",
                "REFERENCE_RETRY_NOT_AVAILABLE",
            ):
                if code in str(error.orig):
                    raise AuthError(code, 409) from None
            raise
        return ReferenceSearchRetried.model_validate(value)
