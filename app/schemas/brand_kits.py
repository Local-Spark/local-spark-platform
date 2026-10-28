"""Owner-selected, versioned brand kit contract."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

HexColor = Annotated[str, Field(pattern=r"^#[0-9A-Fa-f]{6}$")]
FontName = Literal["DejaVu Serif", "DejaVu Sans"]
ImagePosition = Literal["center", "top", "bottom"]


def _luminance(color: str) -> float:
    channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


class BrandKitPalette(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary: HexColor
    background: HexColor
    accent: HexColor

    @model_validator(mode="after")
    def readable_primary(self) -> "BrandKitPalette":
        light, dark = sorted((_luminance(self.primary), _luminance(self.background)), reverse=True)
        if (light + 0.05) / (dark + 0.05) < 4.5:
            raise ValueError("Primary and background colors need 4.5:1 contrast")
        return self


class FeedLayout(BaseModel):
    model_config = ConfigDict(extra="forbid")

    layout: Literal["photo_focus", "offer_focus"]
    image_position: ImagePosition


class StoryLayout(BaseModel):
    model_config = ConfigDict(extra="forbid")

    layout: Literal["photo_focus", "text_focus"]
    image_position: ImagePosition


class ReelCoverLayout(BaseModel):
    model_config = ConfigDict(extra="forbid")

    layout: Literal["photo_focus", "text_focus"]
    image_position: ImagePosition


class BrandKitFormats(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feed: FeedLayout
    story: StoryLayout
    reel_cover: ReelCoverLayout


class BrandKitOverrides(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    palette: BrandKitPalette
    heading_font: FontName
    body_font: FontName
    brand_name: str = Field(min_length=1, max_length=120)
    tagline: str = Field(max_length=100)
    cta: str = Field(min_length=2, max_length=50)
    formats: BrandKitFormats
    logo_asset_id: UUID | None = None


class BrandKitDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_id: UUID
    expected_version: int = Field(ge=0)
    kit_id: Literal["cafe-pausas"]
    kit_version: Literal[1]
    overrides: BrandKitOverrides


class BrandKitConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_id: UUID
    expected_version: int = Field(gt=0)


class BrandKitVersion(BaseModel):
    version: int
    state: Literal["draft", "confirmed"]
    kit_id: str
    kit_version: int
    overrides: BrandKitOverrides
    created_at: datetime


class BrandKitState(BaseModel):
    head_version: int
    confirmed: BrandKitVersion | None = None
    draft: BrandKitVersion | None = None
    pending_change: bool = False
    pending_change_error: str | None = None


class BrandKitOptions(BaseModel):
    fonts: list[FontName]
    layouts: dict[str, list[str]]
    image_positions: list[ImagePosition]


class BrandKitCatalogItem(BaseModel):
    kit_id: str
    kit_version: int
    status: str
    selectable: bool
    segment: str
    preview_images: dict[str, str]
    default_overrides: BrandKitOverrides
    options: BrandKitOptions


class BrandKitCatalog(BaseModel):
    kits: list[BrandKitCatalogItem]


class BrandKitLogoUpload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation_id: UUID
    mime_type: Literal["image/png", "image/jpeg", "image/webp"]
    content_base64: str = Field(min_length=16, max_length=2_900_000)
    rights_confirmed: Literal[True]


class BrandKitLogoRead(BaseModel):
    id: UUID
    preview_url: str


class BrandKitLogoUrl(BaseModel):
    url: str
