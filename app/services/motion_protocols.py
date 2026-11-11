"""IO boundaries shared by production motion services and replaceable adapters."""

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol
from uuid import UUID

from app.adapters.motion_html_renderer import RenderAsset, RenderBundle, RenderedFrame, RenderedMotion
from app.schemas.motion_production import HTMLMotionComposition, MotionConstructionPlan, MotionReview
from app.services.motion_repertoire import RepertoireImage


@dataclass(frozen=True)
class MotionModelRequest:
    operation_id: UUID
    kind: Literal["generate", "review", "correct"]
    context: dict[str, Any] = field(repr=False)
    assets: tuple[RenderAsset, ...] = field(default=(), repr=False)
    frames: tuple[RenderedFrame, ...] = field(default=(), repr=False)
    composition: HTMLMotionComposition | None = field(default=None, repr=False)
    review: MotionReview | None = None
    incumbent_composition: HTMLMotionComposition | None = field(default=None, repr=False)
    incumbent_frames: tuple[RenderedFrame, ...] = field(default=(), repr=False)
    source_frames: tuple[RenderedFrame, ...] = field(default=(), repr=False)
    asset_previews: tuple[tuple[str, RenderedFrame], ...] = field(default=(), repr=False)
    reference_images: tuple[RepertoireImage, ...] = field(default=(), repr=False)
    construction_plan: MotionConstructionPlan | None = field(default=None, repr=False)


@dataclass(frozen=True)
class MotionModelResult:
    composition: HTMLMotionComposition | None = None
    review: MotionReview | None = None
    provider_request_id: str | None = None
    usage: dict[str, int] = field(default_factory=dict)
    estimated_usd_micros: int | None = None
    raw_response: bytes = field(default=b"", repr=False)
    http_status: int | None = None
    construction_plan: MotionConstructionPlan | None = field(default=None, repr=False)


class MotionModelProvider(Protocol):
    provider: str
    model: str

    def build_request(self, request: MotionModelRequest) -> dict[str, Any]: ...

    async def count_input_tokens(self, request: MotionModelRequest, payload: dict[str, Any]) -> int: ...

    async def submit(self, request: MotionModelRequest, payload: dict[str, Any]) -> MotionModelResult: ...


class MotionRenderer(Protocol):
    async def render(self, bundle: RenderBundle, *, operation_id: UUID) -> RenderedMotion: ...
