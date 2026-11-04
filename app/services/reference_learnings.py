"""Read only the chosen profiles' persisted learning; a GET never starts an effect."""

from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.db.session import Database
from app.schemas.reference_learnings import ReferenceLearningsRead
from app.services.auth import AuthError
from app.services.whatsapp_materials import WhatsAppMaterialsService


class ReferenceLearningsService:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def read(self, tenant: UUID, business: UUID, actor: UUID) -> ReferenceLearningsRead:
        try:
            async with self.database.transaction(tenant, actor) as session:
                await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
                value = await session.scalar(
                    text("SELECT public.reference_read_learning_status(:business)"), {"business": business}
                )
        except DBAPIError as exc:
            if "REFERENCE_OWNER_INACTIVE" in str(exc.orig):
                raise AuthError("BUSINESS_OWNER_REQUIRED", 403) from None
            if "REFERENCE_BUSINESS_NOT_FOUND" in str(exc.orig):
                raise AuthError("BUSINESS_NOT_FOUND", 404) from None
            raise
        try:
            return ReferenceLearningsRead.model_validate(value)
        except ValidationError:
            raise AuthError("REFERENCE_LEARNINGS_UNAVAILABLE", 503) from None
