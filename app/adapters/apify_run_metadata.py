"""Shared checks for explicit Actor pricing and authenticated terminal run costs."""

from datetime import UTC, datetime, timedelta
from decimal import ROUND_CEILING, Decimal
from typing import Any


def validate_actor_price(payload: Any, *, actor_id: str, build: str, maximum_usd_micros: int) -> None:
    """Reject unknown/extra usage charges before starting a bounded PPE run."""
    try:
        data = payload["data"]
        if data["id"] != actor_id or data["taggedBuilds"]["latest"]["buildNumber"] != build:
            raise ValueError
        now = datetime.now(UTC)
        prices = [(datetime.fromisoformat(p["startedAt"]), p) for p in data["pricingInfos"]]
        if any(start.tzinfo is None or now < start <= now + timedelta(seconds=120) for start, _ in prices):
            raise ValueError
        price = max((p for p in prices if p[0] <= now), key=lambda p: p[0])[1]
        if price["pricingModel"] != "PAY_PER_EVENT" or price.get("isPPEPlatformUsagePaidByUser") not in (None, False):
            raise ValueError
        minimum = Decimal(str(price.get("minimalMaxTotalChargeUsd") or 0)) * 1_000_000
        if not minimum.is_finite() or not 0 <= minimum <= maximum_usd_micros:
            raise ValueError
    except (KeyError, TypeError, ValueError, ArithmeticError):
        raise ValueError("APIFY_PRICING_UNAVAILABLE") from None


def terminal_run_cost(data: dict[str, object]) -> int | None:
    """Provider-declared total rounded up; an absent receipt never means free."""
    value = data.get("usageTotalUsd")
    if value is None:
        return None
    if type(value) not in (int, float):
        raise ValueError("APIFY_COST_UNAVAILABLE")
    amount = Decimal(str(value)) * 1_000_000
    if not amount.is_finite() or not 0 <= amount <= 1_000_000_000_000:
        raise ValueError("APIFY_COST_UNAVAILABLE")
    return int(amount.to_integral_value(rounding=ROUND_CEILING))


def terminal_run_cost_ready(data: dict[str, object], *, now: datetime | None = None) -> bool:
    """Wait for post-run accounting; terminal status alone is not a final bill.

    Apify documents preliminary costs immediately after completion. A thirty
    second margin and any exposed accounting counters precede releasing a hold.
    This is metadata validation only; the caller keeps polling the same run.
    """
    finished = data.get("finishedAt")
    if not isinstance(finished, str):
        return False
    try:
        finished_at = datetime.fromisoformat(finished)
    except ValueError:
        return False
    moment = datetime.now(UTC) if now is None else now
    if finished_at.tzinfo is None or moment.tzinfo is None or moment - finished_at < timedelta(seconds=30):
        return False
    charged, accounted = data.get("chargedEventCounts"), data.get("accountedChargedEventCounts")
    if charged is None and accounted is None:
        return True
    if not isinstance(charged, dict) or not isinstance(accounted, dict):
        return False
    if any(type(count) is not int or count < 0 for counts in (charged, accounted) for count in counts.values()):
        return False
    return charged == accounted
