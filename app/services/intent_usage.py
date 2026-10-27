"""At-most-once reservation for a text interpretation; amounts are USD micros.

Callers authenticate and authorize the owner before calling. Network calls must
occur only after the transaction containing the reservation commits.
"""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth import AuthError


def estimate_micros(input_tokens: int, output_tokens: int, input_rate: int, output_rate: int) -> int:
    """Round up configured rates (USD micros per million tokens), never down."""
    if min(input_tokens, output_tokens, output_rate) < 0 or input_rate <= 0:
        raise ValueError("Invalid token counts or price")
    return (input_tokens * input_rate + output_tokens * output_rate + 999_999) // 1_000_000


async def reserve_intent(
    session: AsyncSession,
    *,
    tenant: UUID,
    business: UUID,
    actor: UUID,
    operation: UUID,
    request_hash: str,
    model: str,
    input_rate: int,
    output_rate: int,
    max_input_tokens: int,
    max_output_tokens: int,
    daily_limit: int,
) -> bool:
    """Serialize a tenant's daily reservation; only a new row permits a call."""
    if daily_limit <= 0 or len(request_hash) != 64 or not model or len(model) > 120:
        raise AuthError("INTENT_BUDGET_DISABLED", 409)
    reserved = estimate_micros(max_input_tokens, max_output_tokens, input_rate, output_rate)
    if reserved <= 0:
        raise AuthError("INTENT_BUDGET_DISABLED", 409)
    params = {
        "tenant": tenant,
        "business": business,
        "actor": actor,
        "operation": operation,
        "request_hash": request_hash,
        "model": model,
        "input_rate": input_rate,
        "output_rate": output_rate,
        "reserved": reserved,
    }
    await session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:tenant, 43))"), {"tenant": str(tenant)})
    existing = (
        (
            await session.execute(
                text("""SELECT business_id,actor_id,request_hash,model,rate_input_micros,rate_output_micros,
                  reserved_micros FROM editorial_intent_usage WHERE tenant_id=:tenant AND operation_id=:operation"""),
                params,
            )
        )
        .mappings()
        .one_or_none()
    )
    if existing is not None:
        if (
            existing["business_id"] != business
            or existing["actor_id"] != actor
            or existing["request_hash"] != request_hash
            or existing["model"] != model
            or existing["rate_input_micros"] != input_rate
            or existing["rate_output_micros"] != output_rate
            or existing["reserved_micros"] != reserved
        ):
            raise AuthError("INTENT_OPERATION_CONFLICT", 409)
        return False
    used = await session.scalar(
        text("""SELECT coalesce(sum(greatest(reserved_micros,coalesce(estimated_micros,0))),0)
          FROM editorial_intent_usage WHERE tenant_id=:tenant
          AND created_at>=date_trunc('day',now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'
          AND created_at<(date_trunc('day',now() AT TIME ZONE 'UTC') + interval '1 day') AT TIME ZONE 'UTC'"""),
        params,
    )
    if used + reserved > daily_limit:
        raise AuthError("INTENT_BUDGET_EXCEEDED", 409)
    await session.execute(
        text("""INSERT INTO editorial_intent_usage
          (tenant_id,business_id,actor_id,operation_id,request_hash,provider,model,rate_input_micros,
           rate_output_micros,reserved_micros,state)
          VALUES(:tenant,:business,:actor,:operation,:request_hash,'typesafe',:model,:input_rate,:output_rate,
                 :reserved,'submitted')"""),
        params,
    )
    await session.execute(
        text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(:tenant,:actor,:operation,'intent.jev_submitted',:business) ON CONFLICT DO NOTHING"""),
        params,
    )
    return True


async def finish_intent(
    session: AsyncSession,
    *,
    tenant: UUID,
    operation: UUID,
    input_tokens: int | None,
    output_tokens: int | None,
    input_rate: int,
    output_rate: int,
) -> None:
    """Unknown outcomes retain their full hold; estimates are not invoices."""
    complete = input_tokens is not None and output_tokens is not None
    estimated = None
    if input_tokens is not None and output_tokens is not None:
        estimated = estimate_micros(input_tokens, output_tokens, input_rate, output_rate)
    result = await session.execute(
        text("""UPDATE editorial_intent_usage SET state=:state,input_tokens=:input,output_tokens=:output,
          estimated_micros=:estimated,updated_at=now()
          WHERE tenant_id=:tenant AND operation_id=:operation AND state='submitted' RETURNING actor_id,business_id"""),
        {
            "tenant": tenant,
            "operation": operation,
            "state": "completed" if complete else "uncertain",
            "input": input_tokens,
            "output": output_tokens,
            "estimated": estimated,
        },
    )
    row = result.mappings().one_or_none()
    if row is not None:
        await session.execute(
            text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
              VALUES(:tenant,:actor,:operation,:action,:business) ON CONFLICT DO NOTHING"""),
            {
                "tenant": tenant,
                "actor": row["actor_id"],
                "operation": operation,
                "action": "intent.jev_completed" if complete else "intent.jev_uncertain",
                "business": row["business_id"],
            },
        )
