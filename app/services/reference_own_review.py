"""Resolve own-business ambiguity without repeating a paid source request."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db.session import Database
from app.schemas.reference_own_review import OwnBusinessReviewConfirm, OwnBusinessReviewRead
from app.services.auth import AuthError

_CODES = {
    "REFERENCE_OWNER_REQUIRED": 403,
    "REFERENCE_OWNER_INACTIVE": 403,
    "REFERENCE_SEARCH_NOT_FOUND": 404,
    "REFERENCE_OWN_REVIEW_CONFLICT": 409,
    "REFERENCE_OWN_REVIEW_INVALID": 409,
    "REFERENCE_BUSINESS_IDENTITY_STALE": 409,
    "REFERENCE_BUSINESS_ADDRESS_REQUIRED": 409,
    "REFERENCE_BUSINESS_LOCATION_REQUIRED": 409,
    "REFERENCE_SEARCH_CONTEXT_INVALID": 409,
}


def _error(error: DBAPIError) -> AuthError:
    for code, status in _CODES.items():
        if code in str(error.orig):
            return AuthError(code, status)
    return AuthError("REFERENCE_OWN_REVIEW_UNAVAILABLE", 503)


class ReferenceOwnReviewService:
    def __init__(self, database: Database):
        self.database = database

    async def read(self, tenant: UUID, business: UUID, actor: UUID, search: UUID) -> OwnBusinessReviewRead:
        try:
            async with self.database.transaction(tenant, actor) as session:
                value = await session.scalar(
                    text("SELECT public.reference_read_own_business_review(:business,:search)"),
                    {"business": business, "search": search},
                )
        except DBAPIError as error:
            raise _error(error) from None
        return OwnBusinessReviewRead.model_validate(value)

    async def confirm(
        self, tenant: UUID, business: UUID, actor: UUID, search: UUID, payload: OwnBusinessReviewConfirm
    ) -> OwnBusinessReviewRead:
        try:
            async with self.database.transaction(tenant, actor) as session:
                value = await session.scalar(
                    text("SELECT public.reference_confirm_own_business_review(:business,:search,:operation,:place)"),
                    {
                        "business": business,
                        "search": search,
                        "operation": payload.operation_id,
                        "place": payload.place_id,
                    },
                )
        except DBAPIError as error:
            raise _error(error) from None
        return OwnBusinessReviewRead.model_validate(value)
