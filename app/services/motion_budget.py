"""Admission ceiling for the qualified Sol request, not a provider invoice.

Policy checked 2026-11-09 against the official gpt-6.1-sol model page.
Input rate includes the higher cache-write rate. Long-context requests and
unreviewed models fail closed instead of silently applying the wrong tariff.
"""

from typing import Any

from app.services.auth import AuthError

POLICY = "sol-standard-2026-11-09"
MAX_INPUT_TOKENS = 272_000


def validate_tariff(model: str, input_rate: int, output_rate: int) -> None:
    if model != "gpt-6.1-sol":
        raise AuthError("MOTION_COST_MODEL_NOT_QUALIFIED", 409)
    if (
        type(input_rate) is not int
        or type(output_rate) is not int
        or input_rate < 2_500_000
        or output_rate < 10_000_000
    ):
        raise AuthError("MOTION_COST_TARIFF_UNDERESTIMATED", 409)


def cost_bound(input_tokens: int, output_tokens: int, input_rate: int, output_rate: int) -> dict[str, Any]:
    if type(input_tokens) is not int or input_tokens <= 0:
        raise AuthError("MOTION_INPUT_COUNT_REQUIRED", 409)
    if input_tokens > MAX_INPUT_TOKENS:
        raise AuthError("MOTION_LONG_CONTEXT_NOT_QUALIFIED", 409)
    return {
        "policy": POLICY,
        "input_tokens": input_tokens,
        "max_output_tokens": output_tokens,
        "maximum_usd_micros": (input_tokens * input_rate + output_tokens * output_rate + 999_999) // 1_000_000,
    }
