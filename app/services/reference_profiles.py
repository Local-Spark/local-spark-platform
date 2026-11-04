"""Version the owner's correction; no profile access or analysis is implied."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db.session import Database
from app.schemas.reference_profiles import ReferenceProfileRead, ReferenceProfileWrite
from app.services.auth import AuthError


class ReferenceProfilesService:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def save(
        self, tenant: UUID, business: UUID, actor: UUID, place_identity: UUID, payload: ReferenceProfileWrite
    ) -> ReferenceProfileRead:
        try:
            async with self.database.transaction(tenant, actor) as session:
                value = await session.scalar(
                    text("""SELECT public.reference_save_profile_override(
                      :business,:place,:operation,:version,:result,:candidate,:handle)"""),
                    {
                        "business": business,
                        "place": place_identity,
                        "operation": payload.operation_id,
                        "version": payload.expected_version,
                        "result": payload.result_id,
                        "candidate": payload.candidate_id,
                        "handle": payload.instagram_handle,
                    },
                )
        except DBAPIError as error:
            message = str(error.orig)
            if "REFERENCE_OWNER_INACTIVE" in message:
                raise AuthError("BUSINESS_OWNER_REQUIRED", 403) from None
            for code in (
                "REFERENCE_PROFILE_VERSION_CONFLICT",
                "REFERENCE_PROFILE_OPERATION_CONFLICT",
                "REFERENCE_PROFILE_OCCURRENCE_INVALID",
            ):
                if code in message:
                    raise AuthError(code, 409) from None
            raise
        return ReferenceProfileRead.model_validate(value)
