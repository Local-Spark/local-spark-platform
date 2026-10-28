"""Unwired orchestration for a private visual preview.

No application route constructs this service. The injected guard must implement
the source/consent/budget protocol before a real provider can be enabled. This
module does not turn a snapshot or a successful recheck into authorization.
"""

from __future__ import annotations

import hashlib
import io
import logging
from dataclasses import dataclass
from typing import Literal, Protocol, TypeVar
from uuid import NAMESPACE_URL, UUID, uuid5

from PIL import Image, UnidentifiedImageError

from app.adapters.brand_overlay import BrandOverlayError
from app.adapters.material_media import FetchedMedia, MaterialStore
from app.adapters.visual_ai import VisualAIError
from app.services.auth import AuthError
from app.services.visual_attempts import FencedVisualReservation
from app.services.visual_provider_execution import (
    VisualLedger,
    VisualProvider,
    VisualSubmissionClaims,
    VisualSubmissionError,
    VisualSubmissionIdentity,
    execute_visual_submission,
)
from app.services.visual_requests import PreparedVisualRequest

logger = logging.getLogger("meu_braco_direito.visual_orchestrator")


@dataclass(frozen=True)
class VisualRunScope:
    tenant: UUID
    business: UUID
    actor: UUID
    preview: UUID
    proposal: UUID
    operation: UUID
    fence: int
    candidate: bool
    fingerprint: str


class PreparedBrand(Protocol):
    @property
    def request(self) -> PreparedVisualRequest: ...


BrandT = TypeVar("BrandT", bound=PreparedBrand)


class VisualBrandPreparation(Protocol[BrandT]):
    async def prepare(
        self, tenant: UUID, business: UUID, actor: UUID, proposal: UUID, operation: UUID, *, candidate: bool
    ) -> BrandT: ...

    async def finish(self, actor: UUID, prepared: BrandT, scene: FetchedMedia, *, candidate: bool) -> FetchedMedia: ...


class VisualEffectGuard(Protocol):
    """Contract only: no implementation is currently approved for real effects.

    `authorize` must commit current source/consent checks, fence and budget
    intent under a reviewed concurrency protocol. `commit` must atomically
    enforce the fence and current permissions before making the private object
    available. No guard may keep a DB lock across a provider or storage call.
    """

    async def admit(self, scope: VisualRunScope) -> bool: ...

    async def authorize(
        self, scope: VisualRunScope, prepared: PreparedVisualRequest, identity: VisualSubmissionIdentity
    ) -> FencedVisualReservation: ...

    async def current(self, scope: VisualRunScope, prepared: PreparedVisualRequest) -> bool: ...

    async def commit(self, scope: VisualRunScope, key: str, media: FetchedMedia, width: int, height: int) -> bool: ...

    async def finish(self, scope: VisualRunScope, *, completed: bool) -> None: ...


class VisualRunError(Exception):
    """Stable error code; never includes prompt, image bytes or credentials."""


def _verify_finished(media: FetchedMedia, expected: tuple[int, int]) -> None:
    if (
        media.mime_type != "image/png"
        or not 0 < len(media.data) <= 15 * 1024 * 1024
        or hashlib.sha256(media.data).hexdigest() != media.sha256
    ):
        raise VisualRunError("VISUAL_OUTPUT_INVALID")
    try:
        with Image.open(io.BytesIO(media.data)) as image:
            if image.format != "PNG" or image.size != expected:
                raise VisualRunError("VISUAL_OUTPUT_INVALID")
            image.verify()
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise VisualRunError("VISUAL_OUTPUT_INVALID") from exc


def _encode_preview(media: FetchedMedia) -> FetchedMedia:
    """Convert an already-validated, RGB finished image to the preview contract."""
    try:
        with Image.open(io.BytesIO(media.data)) as image:
            output = io.BytesIO()
            image.convert("RGB").save(output, format="JPEG", quality=95, subsampling=0, optimize=True)
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise VisualRunError("VISUAL_OUTPUT_INVALID") from exc
    data = output.getvalue()
    if not 0 < len(data) <= 15 * 1024 * 1024:
        raise VisualRunError("VISUAL_OUTPUT_INVALID")
    return FetchedMedia(data, "image/jpeg", hashlib.sha256(data).hexdigest())


class VisualRealOrchestrator[BrandT: PreparedBrand]:
    """Coordinates an effect only with an explicit injected authorization guard."""

    def __init__(
        self,
        *,
        guard: VisualEffectGuard,
        brand: VisualBrandPreparation[BrandT],
        provider: VisualProvider,
        ledger: VisualLedger,
        claims: VisualSubmissionClaims,
        store: MaterialStore,
        signing_key: str,
    ) -> None:
        self.guard, self.brand, self.provider, self.ledger = guard, brand, provider, ledger
        self.claims, self.store, self.signing_key = claims, store, signing_key

    async def run(self, scope: VisualRunScope) -> Literal["completed", "stale", "not_started", "uncertain"]:
        if (
            scope.fence <= 0
            or len(scope.fingerprint) != 64
            or any(ch not in "0123456789abcdef" for ch in scope.fingerprint)
        ):
            raise VisualRunError("VISUAL_SCOPE_INVALID")
        if not await self.guard.admit(scope):
            return "not_started"

        known_terminal = False
        completed = False
        submission_possible = False
        response_received = False
        uploaded_key: str | None = None
        commit_started = False
        commit_resolved = False
        try:
            brand = await self.brand.prepare(
                scope.tenant, scope.business, scope.actor, scope.proposal, scope.operation, candidate=scope.candidate
            )
            prepared = brand.request
            if (
                prepared.context.tenant_id != scope.tenant
                or prepared.context.business_id != scope.business
                or prepared.context.proposal_id != scope.proposal
                or prepared.context.fingerprint != scope.fingerprint
                or prepared.request.request_id != scope.operation
            ):
                known_terminal = True
                return "stale"
            identity = VisualSubmissionIdentity(
                scope.tenant,
                scope.business,
                scope.actor,
                scope.preview,
                uuid5(NAMESPACE_URL, f"visual-preview:{scope.preview}"),
                scope.fence,
                prepared.request_hash,
                "openai",
            )
            attempt = await self.guard.authorize(scope, prepared, identity)
            try:
                submission_possible = True
                result = await execute_visual_submission(
                    identity=identity,
                    prepared=prepared,
                    signing_key=self.signing_key,
                    attempt=attempt,
                    provider=self.provider,
                    ledger=self.ledger,
                    claims=self.claims,
                )
                response_received = True
            except VisualSubmissionError:
                # Another claim or an invalid payload must never cause a retry.
                return "uncertain"
            except VisualAIError as exc:
                if exc.uncertain:
                    return "uncertain"
                known_terminal = True
                return "not_started"
            if not await self.guard.current(scope, prepared):
                known_terminal = True
                return "stale"
            scene = FetchedMedia(result.content, result.mime_type, result.sha256)
            media = await self.brand.finish(scope.actor, brand, scene, candidate=scope.candidate)
            _verify_finished(media, (result.width, result.height))
            media = _encode_preview(media)
            if not await self.guard.current(scope, prepared):
                known_terminal = True
                return "stale"
            uploaded_key = (
                f"previews/{scope.tenant}/{scope.business}/{scope.preview}/attempt-{scope.fence}/{media.sha256}.jpg"
            )
            await self.store.put(uploaded_key, media)
            if not await self.guard.current(scope, prepared):
                await self.store.delete(uploaded_key)
                uploaded_key = None
                known_terminal = True
                return "stale"
            # A lost commit acknowledgement must not delete an object that may
            # already be referenced by a committed preview. Reconciliation is
            # required when commit outcome is unknown.
            commit_started = True
            committed = await self.guard.commit(scope, uploaded_key, media, result.width, result.height)
            commit_resolved = True
            if not committed:
                known_terminal = True
                await self.store.delete(uploaded_key)
                uploaded_key = None
                return "stale"
            completed = known_terminal = True
            return "completed"
        except AuthError:
            # A source or permission changed while preparing/finishing. Once
            # the provider has returned, discarding is a known terminal result.
            if (submission_possible and not response_received) or (commit_started and not commit_resolved):
                raise
            known_terminal = True
            return "stale"
        except (BrandOverlayError, VisualRunError):
            # Local output validation/finishing cannot start a provider call.
            if (submission_possible and not response_received) or (commit_started and not commit_resolved):
                raise
            known_terminal = True
            raise
        finally:
            if response_received and not commit_started:
                # The paid request has definitely finished; local processing or
                # storage failure cannot keep withdrawal pending indefinitely.
                known_terminal = True
            if uploaded_key is not None and not completed and (not commit_started or commit_resolved):
                try:
                    await self.store.delete(uploaded_key)
                except Exception:
                    # An orphan is never made visible; cleanup may be retried separately.
                    logger.warning("visual.orphan_cleanup_failed")
            # An unknown provider/worker outcome must keep the admission pending.
            if known_terminal or not submission_possible:
                await self.guard.finish(scope, completed=completed)
