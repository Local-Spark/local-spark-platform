from pydantic import BaseModel, ConfigDict, Field


class SponsorshipCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    reason: str = Field(min_length=3, max_length=500)
