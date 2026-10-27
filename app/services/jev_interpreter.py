"""Authorized, budget-reserved one-shot Jev interpretation for a single source."""

import hashlib
import hmac
import json
from typing import Any, cast
from uuid import UUID

from app.adapters.jev_intent_ai import JevIntentError, JevIntentProvider
from app.core.config import Settings
from app.db.session import Database
from app.services.auth import AuthError
from app.services.creative_catalog_resolution import (
    CatalogIntent,
    CatalogInterpreterBudgetBlocked,
    CatalogInterpreterUnavailable,
)
from app.services.intent_usage import finish_intent, reserve_intent
from app.services.plan_capabilities import INITIAL_PLAN_INTENT_FORMATS


class BudgetedJevInterpreter:
    """Each instance is bound to one already identified owner and inbound operation."""

    def __init__(
        self,
        settings: Settings,
        database: Database,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        source: UUID,
        operation: UUID,
        provider: JevIntentProvider | None = None,
    ) -> None:
        self.settings, self.database = settings, database
        self.tenant, self.business, self.actor, self.source, self.operation = tenant, business, actor, source, operation
        if settings.typesafe_api_key is None or settings.meta_encryption_key is None:
            raise ValueError("Jev requires configured credentials")
        self.provider = provider or JevIntentProvider(settings.typesafe_api_key, settings.intent_ai_model)

    async def interpret(self, message: str, candidates: list[dict[str, str]]) -> CatalogIntent:
        # HMAC avoids storing a dictionary-attackable hash of short private messages.
        key = self.settings.meta_encryption_key
        assert key is not None
        digest = hmac.new(
            key.get_secret_value().encode(),
            json.dumps([message, candidates], ensure_ascii=False, sort_keys=True).encode(),
            hashlib.sha256,
        ).hexdigest()
        from app.services.editorial_briefings import EditorialBriefingService

        try:
            async with self.database.transaction(self.tenant, self.actor) as session:
                current = await EditorialBriefingService(self.settings, self.database)._source(
                    session, self.tenant, self.business, self.actor, self.source
                )
                if current != message:
                    raise AuthError("INTENT_SOURCE_CHANGED", 409)
                created = await reserve_intent(
                    session,
                    tenant=self.tenant,
                    business=self.business,
                    actor=self.actor,
                    operation=self.operation,
                    request_hash=digest,
                    model=self.settings.intent_ai_model,
                    input_rate=self.settings.intent_ai_input_rate_usd_micros,
                    output_rate=0,
                    max_input_tokens=64_000,
                    max_output_tokens=0,
                    daily_limit=self.settings.intent_ai_daily_budget_usd_micros,
                )
                if not created:
                    raise AuthError("INTENT_ALREADY_SUBMITTED", 409)
        except AuthError as exc:
            if exc.code in {"INTENT_BUDGET_DISABLED", "INTENT_BUDGET_EXCEEDED"}:
                raise CatalogInterpreterBudgetBlocked() from None
            raise CatalogInterpreterUnavailable() from None
        # No lock or database transaction is held during the request; no retry.
        try:
            result = await self.provider.interpret(
                message, candidates, list(INITIAL_PLAN_INTENT_FORMATS), self.operation
            )
        except JevIntentError:
            async with self.database.transaction(self.tenant, self.actor) as session:
                await finish_intent(
                    session,
                    tenant=self.tenant,
                    operation=self.operation,
                    input_tokens=None,
                    output_tokens=None,
                    input_rate=self.settings.intent_ai_input_rate_usd_micros,
                    output_rate=0,
                )
            raise CatalogInterpreterUnavailable() from None
        async with self.database.transaction(self.tenant, self.actor) as session:
            await finish_intent(
                session,
                tenant=self.tenant,
                operation=self.operation,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                input_rate=self.settings.intent_ai_input_rate_usd_micros,
                output_rate=0,
            )
        return CatalogIntent(
            cast(Any, result.decision), result.offering_id, cast(Any, result.intent), cast(Any, result.format)
        )
