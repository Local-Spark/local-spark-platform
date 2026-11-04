"""Mock-only inspection of a prior contacts Actor's terminal failure.

This verifies metadata within one trusted in-memory execution, not provider
provenance or durable evidence. Runtime networking, writing the proof, and retry
authorization remain disabled until the complete fences are connected.
"""

import json
import re
from dataclasses import dataclass
from typing import Literal, Protocol, cast
from uuid import UUID

import httpx
from pydantic import SecretStr

from app.adapters.apify_place_contacts import ApifyPlaceContacts, SubmittedPlaceContacts
from app.schemas.reference_contacts_effect import ContactsChargeableRequest, valid_place_id


class ContactsTerminalError(Exception):
    """Stable code without provider payload, Place ID or credentials."""


@dataclass(frozen=True, repr=False)
class ContactsTerminalBinding:
    submission: SubmittedPlaceContacts
    request: ContactsChargeableRequest


@dataclass(frozen=True, repr=False)
class ContactsTerminalFailure:
    submission_id: UUID
    run_id: str
    build_id: str
    build_number: str
    status: Literal["FAILED", "TIMED-OUT", "ABORTED"]


class ContactsTerminalGuard(Protocol):
    async def claim(self, operation_id: UUID, binding: ContactsTerminalBinding) -> bool:
        """Commit a unique authenticated inspection before I/O."""
        ...

    async def uncertain(self, operation_id: UUID, binding: ContactsTerminalBinding) -> None:
        """Retain the prior inspection when its result cannot be established."""
        ...


def _identifier(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value) is not None


class ApifyContactsTerminalFailure:
    def __init__(
        self,
        token: SecretStr | None = None,
        guard: ContactsTerminalGuard | None = None,
        *,
        enabled: bool = False,
        transport: httpx.MockTransport | None = None,
    ) -> None:
        self._token, self._guard, self._enabled, self._transport = token, guard, enabled, transport

    async def inspect(self, submission: SubmittedPlaceContacts, operation_id: UUID) -> ContactsTerminalFailure | None:
        if (
            not isinstance(submission, SubmittedPlaceContacts)
            or not isinstance(submission.submission_id, UUID)
            or not isinstance(operation_id, UUID)
            or not valid_place_id(submission.place_id)
            or not all(
                _identifier(value)
                for value in (
                    submission.provider_actor_id,
                    submission.run_id,
                    submission.dataset_id,
                    submission.key_value_store_id,
                    submission.request_queue_id,
                    submission.build_id,
                )
            )
            or not isinstance(submission.build_number, str)
            or len(submission.build_number) > 64
            or re.fullmatch(r"[0-9]+[.][0-9]+[.][0-9]+", submission.build_number) is None
        ):
            raise ContactsTerminalError("CONTACTS_TERMINAL_INPUT_INVALID")
        if (
            not self._enabled
            or not isinstance(self._token, SecretStr)
            or not self._token.get_secret_value()
            or self._guard is None
            or not isinstance(self._transport, httpx.MockTransport)
        ):
            raise ContactsTerminalError("CONTACTS_TERMINAL_DISABLED")
        try:
            token_bytes = self._token.get_secret_value().encode("ascii")
            if any(byte < 33 or byte > 126 for byte in token_bytes):
                raise ValueError
        except (UnicodeEncodeError, ValueError):
            raise ContactsTerminalError("CONTACTS_TERMINAL_DISABLED") from None
        request = ApifyPlaceContacts._request(
            "GET", f"https://api.apify.com/v2/actor-runs/{submission.run_id}", self._token
        )
        binding = ContactsTerminalBinding(
            submission, ApifyPlaceContacts._bind(request, self._token, submission.provider_actor_id)
        )
        try:
            claimed = await self._guard.claim(operation_id, binding)
        except Exception:
            raise ContactsTerminalError("CONTACTS_TERMINAL_GUARD_UNAVAILABLE") from None
        if claimed is not True:
            raise ContactsTerminalError("CONTACTS_TERMINAL_GUARD_UNAVAILABLE")
        try:
            async with self._transport:
                response = await self._transport.handle_async_request(request)
                try:
                    response.request = request
                    response.raise_for_status()
                    if response.status_code != 200:
                        raise ValueError
                    content = bytearray()
                    async for chunk in response.aiter_bytes():
                        content.extend(chunk)
                        if len(content) > 1_000_000:
                            raise ValueError
                    body = json.loads(content)
                finally:
                    await response.aclose()
            if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
                raise ValueError
            data = body["data"]
            expected = {
                "actId": submission.provider_actor_id,
                "id": submission.run_id,
                "defaultDatasetId": submission.dataset_id,
                "defaultKeyValueStoreId": submission.key_value_store_id,
                "defaultRequestQueueId": submission.request_queue_id,
                "buildId": submission.build_id,
                "buildNumber": submission.build_number,
            }
            if any(data.get(key) != value for key, value in expected.items()):
                raise ValueError
            status = data.get("status")
            if status in {"READY", "RUNNING", "TIMING-OUT", "ABORTING", "SUCCEEDED"}:
                return None
            if status not in {"FAILED", "TIMED-OUT", "ABORTED"}:
                raise ValueError
            return ContactsTerminalFailure(
                submission.submission_id,
                submission.run_id,
                submission.build_id,
                submission.build_number,
                cast(Literal["FAILED", "TIMED-OUT", "ABORTED"], status),
            )
        except Exception:
            try:
                await self._guard.uncertain(operation_id, binding)
            except Exception:
                pass
            raise ContactsTerminalError("CONTACTS_TERMINAL_RESULT_UNCERTAIN") from None
