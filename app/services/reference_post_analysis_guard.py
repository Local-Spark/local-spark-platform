"""Durable, exact-request authorization for a selected profile's Jev analysis."""

import hashlib
import hmac
import json
import re
from dataclasses import dataclass
from typing import Literal, cast
from uuid import UUID

from pydantic import SecretStr
from sqlalchemy import text

from app.adapters.jev_reference_post_analysis import PostAnalysisResult
from app.adapters.jev_reference_similarity import JevChargeableRequest
from app.db.session import Database


class PostGuardError(Exception):
    """Stable code without source data or secrets."""


@dataclass(frozen=True, repr=False)
class PostGuardContext:
    tenant: UUID
    business: UUID
    actor: UUID
    window: UUID
    reference: UUID
    association_version: int
    parent_feed_effect: UUID
    parent_feed_token: UUID
    effect: UUID
    sample_mac: str
    pilot: UUID
    key: SecretStr
    key_version: str
    tariff_version: str
    credential_version: str
    reserved_usd_micros: int
    caption_mac: str | None = None


def post_sample_mac(key: SecretStr, window: UUID, post_id: str, image_index: int | None) -> str:
    """Stable opaque identity, never a stored post ID, caption, image or URL."""
    if (
        not isinstance(key, SecretStr)
        or len(key.get_secret_value().encode()) < 32
        or not isinstance(window, UUID)
        or not isinstance(post_id, str)
        or re.fullmatch(r"[A-Za-z0-9_-]{1,128}", post_id) is None
        or (image_index is not None and (type(image_index) is not int or image_index < 0))
    ):
        raise PostGuardError("REFERENCE_POST_IDENTITY_INVALID")
    body = json.dumps(["reference-post-sample-v1", str(window), post_id, image_index], separators=(",", ":")).encode()
    return hmac.new(key.get_secret_value().encode(), body, hashlib.sha256).hexdigest()


def post_request_mac(c: PostGuardContext, request: JevChargeableRequest) -> str:
    if not isinstance(c.key, SecretStr) or len(c.key.get_secret_value().encode()) < 32:
        raise PostGuardError("REFERENCE_POST_KEY_INVALID")
    identities = (
        c.tenant,
        c.business,
        c.actor,
        c.window,
        c.reference,
        c.parent_feed_effect,
        c.parent_feed_token,
        c.effect,
        c.pilot,
    )
    versions = (c.key_version, c.tariff_version, c.credential_version)
    if (
        any(not isinstance(value, UUID) for value in identities)
        or any(not isinstance(v, str) or re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", v) is None for v in versions)
        or type(c.association_version) is not int
        or c.association_version < 1
        or type(c.reserved_usd_micros) is not int
        or not 0 < c.reserved_usd_micros <= 5_000_000
        or not isinstance(c.sample_mac, str)
        or re.fullmatch("[0-9a-f]{64}", c.sample_mac) is None
        or (
            c.caption_mac is not None
            and (not isinstance(c.caption_mac, str) or re.fullmatch("[0-9a-f]{64}", c.caption_mac) is None)
        )
        or not isinstance(request, JevChargeableRequest)
        or request.method != "POST"
        or request.url != "https://api.typesafe.ai/v1/systemone"
        or not isinstance(request.model, str)
        or re.fullmatch(r"[A-Za-z0-9_.-]{1,120}", request.model) is None
        or not isinstance(request.body, bytes)
        or not 0 < len(request.body) <= 16 * 1024 * 1024
        or not isinstance(request.credential, SecretStr)
        or not request.credential.get_secret_value()
    ):
        raise PostGuardError("REFERENCE_POST_BINDING_INVALID")
    try:
        body = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        raise PostGuardError("REFERENCE_POST_BINDING_INVALID") from None
    if (
        not isinstance(body, dict)
        or body.get("model") != request.model
        or not isinstance(body.get("state"), dict)
        or (body["state"].get("caption") is not None) != (c.caption_mac is not None)
    ):
        raise PostGuardError("REFERENCE_POST_BINDING_INVALID")
    metadata = json.dumps(
        [
            "reference-post-request-v1",
            *map(str, identities),
            *versions,
            c.association_version,
            c.reserved_usd_micros,
            c.sample_mac,
            c.caption_mac,
            request.method,
            request.url,
            request.model,
        ],
        separators=(",", ":"),
    ).encode()
    digest = hmac.new(c.key.get_secret_value().encode(), metadata + b"\0", hashlib.sha256)
    digest.update(request.body)
    digest.update(b"\0" + request.credential.get_secret_value().encode())
    return digest.hexdigest()


class DatabasePostAnalysisGuard:
    def __init__(self, database: Database, context: PostGuardContext) -> None:
        self._database, self._context = database, context
        self._attempted = False
        self._token: UUID | None = None

    async def claim(self, operation_id: UUID, request: JevChargeableRequest) -> bool:
        c = self._context
        if self._attempted or operation_id != c.effect:
            return False
        self._attempted = True
        mac = post_request_mac(c, request)
        async with self._database.transaction(c.tenant, c.actor) as session:
            result = await session.scalar(
                text("""SELECT public.reference_post_claim(
              :business,:window,:reference,:version,:parent,:parent_token,:effect,:sample,:caption,:pilot,
              :mac,:key,:tariff,:credential,:model,:amount)"""),
                {
                    "business": c.business,
                    "window": c.window,
                    "reference": c.reference,
                    "version": c.association_version,
                    "parent": c.parent_feed_effect,
                    "parent_token": c.parent_feed_token,
                    "effect": c.effect,
                    "sample": c.sample_mac,
                    "caption": c.caption_mac,
                    "pilot": c.pilot,
                    "mac": mac,
                    "key": c.key_version,
                    "tariff": c.tariff_version,
                    "credential": c.credential_version,
                    "model": request.model,
                    "amount": c.reserved_usd_micros,
                },
            )
        if result["created"] is not True:
            return False
        self._token = UUID(result["executor_token"])
        return True

    def execution_token(self) -> UUID:
        if self._token is None:
            raise PostGuardError("REFERENCE_POST_EXECUTOR_REQUIRED")
        return self._token

    async def uncertain(self) -> None:
        token, c = self.execution_token(), self._context
        async with self._database.transaction(c.tenant, c.actor) as session:
            await session.execute(
                text("SELECT public.reference_post_uncertain(:business,:effect,:token)"),
                {"business": c.business, "effect": c.effect, "token": token},
            )

    async def record(self, result: PostAnalysisResult) -> None:
        token, c = self.execution_token(), self._context
        async with self._database.transaction(c.tenant, c.actor) as session:
            await session.execute(
                text("""SELECT public.reference_post_record(
              :business,:effect,:token,CAST(:choices AS jsonb),:vocabulary,:model,:incoming,:outgoing)"""),
                {
                    "business": c.business,
                    "effect": c.effect,
                    "token": token,
                    "choices": json.dumps(dict(result.choices)),
                    "vocabulary": result.vocabulary_version,
                    "model": result.provider_model,
                    "incoming": result.input_tokens,
                    "outgoing": result.output_tokens,
                },
            )


async def load_post_analysis(
    database: Database,
    tenant: UUID,
    actor: UUID,
    business: UUID,
    window: UUID,
    sample_mac: str,
) -> PostAnalysisResult | None:
    async with database.transaction(tenant, actor) as session:
        result = await session.scalar(
            text("SELECT public.reference_post_read(:business,:window,:sample)"),
            {"business": business, "window": window, "sample": sample_mac},
        )
    if result is None:
        return None
    return PostAnalysisResult(
        tuple(result["choices"].items()),
        result["vocabulary_version"],
        result["provider_model"],
        result["input_tokens"],
        result["output_tokens"],
    )


async def record_feed_terminal_cost(
    database: Database,
    tenant: UUID,
    actor: UUID,
    business: UUID,
    effect: UUID,
    token: UUID,
    actual: int | None,
) -> None:
    async with database.transaction(tenant, actor) as session:
        await session.execute(
            text("SELECT public.reference_feed_record_terminal_cost(:business,:effect,:token,:actual)"),
            {"business": business, "effect": effect, "token": token, "actual": actual},
        )


@dataclass(frozen=True, repr=False)
class PostSample:
    state: Literal["running", "uncertain", "completed"]
    includes_caption: bool
    result: PostAnalysisResult | None


async def load_post_sample(
    database: Database,
    tenant: UUID,
    actor: UUID,
    business: UUID,
    window: UUID,
    sample_mac: str,
) -> PostSample | None:
    async with database.transaction(tenant, actor) as session:
        sample = await session.scalar(
            text("SELECT public.reference_post_sample_read(:business,:window,:sample)"),
            {"business": business, "window": window, "sample": sample_mac},
        )
    if sample is None:
        return None
    result = sample["result"]
    return PostSample(
        cast(Literal["running", "uncertain", "completed"], sample["state"]),
        sample["includes_caption"],
        None
        if result is None
        else PostAnalysisResult(
            tuple(result["choices"].items()),
            result["vocabulary_version"],
            result["provider_model"],
            result["input_tokens"],
            result["output_tokens"],
        ),
    )


async def caption_claimed(
    database: Database,
    tenant: UUID,
    actor: UUID,
    business: UUID,
    window: UUID,
    caption_mac: str,
) -> bool:
    async with database.transaction(tenant, actor) as session:
        return bool(
            await session.scalar(
                text("SELECT public.reference_post_caption_claimed(:business,:window,:caption)"),
                {"business": business, "window": window, "caption": caption_mac},
            )
        )


async def load_caption_sample(
    database: Database,
    tenant: UUID,
    actor: UUID,
    business: UUID,
    window: UUID,
    caption_mac: str,
) -> PostSample | None:
    async with database.transaction(tenant, actor) as session:
        sample = await session.scalar(
            text("SELECT public.reference_post_caption_read(:business,:window,:caption)"),
            {"business": business, "window": window, "caption": caption_mac},
        )
    if sample is None:
        return None
    result = sample["result"]
    return PostSample(
        cast(Literal["running", "uncertain", "completed"], sample["state"]),
        sample["includes_caption"],
        None
        if result is None
        else PostAnalysisResult(
            tuple(result["choices"].items()),
            result["vocabulary_version"],
            result["provider_model"],
            result["input_tokens"],
            result["output_tokens"],
        ),
    )
