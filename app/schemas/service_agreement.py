"""An explicit decision about the exact service notice shown to the customer."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ServiceAgreementAcceptance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = Field(min_length=1, max_length=80)
    notice_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    accept: Literal[True]
