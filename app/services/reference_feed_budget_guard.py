"""Inactive feed-submission guard: exact request MAC and a durable cost fence.

The SQL entry points are not granted to runtime, no intent/window creator is
available, and inspection is disabled. This is not an Apify integration switch.
"""

from dataclasses import dataclass
from uuid import UUID

from pydantic import SecretStr
from sqlalchemy import text

from app.adapters.apify_instagram_feed import FeedChargeableRequest, FeedInspectionIntent
from app.db.session import Database
from app.services.reference_feed_request_mac import feed_request_mac


class FeedGuardError(Exception):
    """Stable internal error without profile, provider content or secrets."""


@dataclass(frozen=True, repr=False)
class FeedGuardContext:
    tenant: UUID
    business: UUID
    actor: UUID
    reference: UUID
    association_version: int
    analysis_window: UUID
    search: UUID | None
    selection: UUID | None
    effect: UUID
    event: UUID
    pilot: UUID
    key: SecretStr
    key_version: str
    tariff_version: str
    credential_version: str
    reserved_usd_micros: int
    profile: str
    build: str


class DatabaseFeedBudgetGuard:
    """One-shot, financially fenced submission; never enables inspection."""

    def __init__(self, database: Database, context: FeedGuardContext) -> None:
        self._database = database
        self._context = context
        self._attempted = False
        self._token: UUID | None = None
        self._mac: str | None = None

    def _request_mac(self, request: FeedChargeableRequest) -> str:
        c = self._context
        return feed_request_mac(
            c.key,
            key_version=c.key_version,
            tariff_version=c.tariff_version,
            credential_version=c.credential_version,
            tenant=c.tenant,
            business=c.business,
            actor=c.actor,
            reference=c.reference,
            association_version=c.association_version,
            analysis_window=c.analysis_window,
            search=c.search,
            selection=c.selection,
            effect=c.effect,
            pilot=c.pilot,
            reserved_usd_micros=c.reserved_usd_micros,
            profile=c.profile,
            build=c.build,
            request=request,
        )

    async def claim_submission(self, operation_id: UUID, request: FeedChargeableRequest) -> bool:
        if self._attempted or operation_id != self._context.effect:
            return False
        self._attempted = True
        c = self._context
        mac = self._request_mac(request)
        async with self._database.transaction(c.tenant, c.actor) as session:
            result = await session.scalar(
                text("""SELECT public.reference_feed_claim(
              :business,:effect,:event,:window,:pilot,:mac,:key,:tariff,:credential,:build,:amount)"""),
                {
                    "business": c.business,
                    "effect": c.effect,
                    "event": c.event,
                    "window": c.analysis_window,
                    "pilot": c.pilot,
                    "mac": mac,
                    "key": c.key_version,
                    "tariff": c.tariff_version,
                    "credential": c.credential_version,
                    "build": c.build,
                    "amount": c.reserved_usd_micros,
                },
            )
        if result["created"] is not True:
            return False
        self._token = UUID(result["executor_token"])
        self._mac = mac
        return True

    async def submission_uncertain(self, operation_id: UUID, request: FeedChargeableRequest) -> None:
        if self._token is None or operation_id != self._context.effect or self._request_mac(request) != self._mac:
            raise FeedGuardError("FEED_EXECUTOR_FENCE_INVALID")
        c = self._context
        async with self._database.transaction(c.tenant, c.actor) as session:
            await session.execute(
                text("SELECT public.reference_feed_uncertain(:effect,:token)"),
                {"effect": c.effect, "token": self._token},
            )

    async def claim_inspection(self, operation_id: UUID, intent: FeedInspectionIntent) -> bool:
        return False

    async def inspection_uncertain(self, operation_id: UUID, intent: FeedInspectionIntent) -> None:
        raise FeedGuardError("FEED_INSPECTION_DISABLED")
