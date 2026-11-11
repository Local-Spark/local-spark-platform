"""One-shot effect identity, exact payload evidence and the existing shared cost ledger."""

import base64
import hashlib
import json
from dataclasses import asdict
from typing import Any
from uuid import UUID, uuid5

from sqlalchemy import text

from app.adapters.material_media import MaterialStore
from app.db.session import Database
from app.services.auth import AuthError
from app.services.motion_budget import cost_bound, validate_tariff
from app.services.motion_context import digest
from app.services.motion_payloads import MotionPayloads
from app.services.motion_protocols import MotionModelProvider, MotionModelRequest, MotionModelResult
from app.services.motion_requests import MotionRequestService
from app.services.visual_cost_ledger import VisualCostLedger, VisualReservation


class MotionEffects:
    def __init__(self, requests: MotionRequestService, cost_database: Database, store: MaterialStore | None = None):
        self.requests = requests
        self.ledger = VisualCostLedger(requests.settings, cost_database)
        self.payloads = MotionPayloads(
            requests.context, store if store is not None else MaterialStore(requests.settings)
        )

    async def persist_payload(self, row: dict[str, Any], token: UUID, operation: UUID, slot: str, value: object) -> str:
        upload_operation = uuid5(operation, "payload:" + slot)
        prepared = self.payloads.prepare(row, upload_operation, value)
        if prepared.manifest is not None:
            # The small durable upload claim commits BEFORE storage IO. A failed
            # or uncertain upload remains claimed and prevents automatic replay.
            await self.claim(row, token, upload_operation, "upload", prepared.manifest)
            await self.payloads.upload(prepared)
            await self.received(row, token, upload_operation, prepared.manifest)
        return prepared.ciphertext

    async def capacity_for_correction(self, row: dict[str, Any], token: UUID) -> bool:
        """Require room for both correction and its review, before paying for either."""
        return await self.capacity(row, token, 2 * self.requests.settings.motion_ai_reservation_usd_micros)

    async def capacity(self, row: dict[str, Any], token: UUID, amount: int) -> bool:
        async with self.requests.database.transaction(row["tenant_id"], row["actor_id"]) as session:
            current = await self.requests.locked_running(session, row, token)
            used = await session.scalar(
                text("""SELECT coalesce(sum(greatest(reserved_usd_micros,
              coalesce(estimated_usd_micros,0))),0) FROM motion_effects
              WHERE tenant_id=:tenant AND business_id=:business AND request_id=:id"""),
                {"tenant": row["tenant_id"], "business": row["business_id"], "id": row["id"]},
            )
            return bool(used + amount <= current["budget_usd_micros"])

    async def claim(
        self, row: dict[str, Any], token: UUID, operation: UUID, kind: str, payload: object, reserved: int = 0
    ) -> None:
        request_hash = digest(payload)
        ciphertext = await self.persist_payload(row, token, operation, "request", payload)
        async with self.requests.database.transaction(row["tenant_id"], row["actor_id"]) as session:
            current = await self.requests.locked_running(session, row, token)
            exists = await session.scalar(
                text("""SELECT 1 FROM motion_effects
              WHERE tenant_id=:tenant AND operation_id=:operation"""),
                {"tenant": row["tenant_id"], "operation": operation},
            )
            if exists:
                raise AuthError("MOTION_EFFECT_ALREADY_CLAIMED", 409)
            used = await session.scalar(
                text("""SELECT coalesce(sum(greatest(reserved_usd_micros,
              coalesce(estimated_usd_micros,0))),0) FROM motion_effects
              WHERE tenant_id=:tenant AND business_id=:business AND request_id=:id"""),
                {"tenant": row["tenant_id"], "business": row["business_id"], "id": row["id"]},
            )
            if used + reserved > current["budget_usd_micros"]:
                raise AuthError("MOTION_REQUEST_BUDGET_EXCEEDED", 409)
            await session.execute(
                text("""INSERT INTO motion_effects
              (tenant_id,business_id,request_id,operation_id,kind,state,request_hash,request_ciphertext,reserved_usd_micros)
              VALUES(:tenant,:business,:id,:operation,:kind,'claimed',:hash,:payload,:reserved)"""),
                {
                    "tenant": row["tenant_id"],
                    "business": row["business_id"],
                    "id": row["id"],
                    "operation": operation,
                    "kind": kind,
                    "hash": request_hash,
                    "payload": ciphertext,
                    "reserved": reserved,
                },
            )
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
              VALUES(:tenant,:actor,:operation,'motion.effect_claimed',:business)"""),
                {
                    "tenant": row["tenant_id"],
                    "actor": row["actor_id"],
                    "operation": operation,
                    "business": row["business_id"],
                },
            )

    async def received(
        self, row: dict[str, Any], token: UUID, operation: UUID, result: object, estimate: int | None = None
    ) -> None:
        # Provider responses are bounded by the adapter (4 MiB raw), unlike
        # multimodal requests/evidence. Keep this path usable after revocation.
        ciphertext = self.requests.context.seal(result)
        # Narrow worker capability retains evidence after owner revocation. It can
        # only finish a previously claimed operation with the original run token.
        async with self.ledger.database.transaction(row["tenant_id"], row["actor_id"]) as session:
            changed = await session.scalar(
                text("""SELECT motion_record_result(
              :tenant,:business,:id,:actor,:token,:operation,:response,:estimate)"""),
                {
                    "tenant": row["tenant_id"],
                    "business": row["business_id"],
                    "id": row["id"],
                    "actor": row["actor_id"],
                    "token": token,
                    "operation": operation,
                    "response": ciphertext,
                    "estimate": estimate,
                },
            )
            if not changed:
                raise AuthError("MOTION_EFFECT_FENCED", 409)

    async def quarantine(self, row: dict[str, Any], token: UUID, *, failure_event_id: UUID | None = None) -> None:
        async with self.ledger.database.transaction(row["tenant_id"], row["actor_id"]) as session:
            await session.scalar(
                text("""SELECT motion_quarantine_request(
              :tenant,:business,:id,:actor,:token,'MOTION_OUTCOME_UNCERTAIN',:event)"""),
                {
                    "tenant": row["tenant_id"],
                    "business": row["business_id"],
                    "id": row["id"],
                    "actor": row["actor_id"],
                    "token": token,
                    "event": failure_event_id
                    if failure_event_id is not None
                    else uuid5(row["operation_id"], "motion.failed"),
                },
            )

    async def reserve_submission(
        self,
        row: dict[str, Any],
        token: UUID,
        operation: UUID,
        kind: str,
        signed: object,
        reserve: int,
        provider: str,
        model: str,
    ) -> VisualReservation:
        """Commit effect and shared reservation before dispatch; never authorizes replay."""
        await self.claim(row, token, operation, kind, signed, reserve)
        reservation = await self.ledger.reserve(
            row["tenant_id"],
            row["business_id"],
            row["actor_id"],
            operation,
            provider,
            model,
            digest(signed),
            reserve,
        )
        if not reservation.created:
            raise AuthError("MOTION_COST_RESERVATION_REPLAY", 409)
        async with self.requests.database.transaction(row["tenant_id"], row["actor_id"]) as session:
            await self.requests.locked_running(session, row, token)
            changed = await session.scalar(
                text("""UPDATE motion_effects SET state='submitted',reservation_id=:reservation
              WHERE tenant_id=:tenant AND operation_id=:operation AND state='claimed' RETURNING 1"""),
                {"tenant": row["tenant_id"], "operation": operation, "reservation": reservation.id},
            )
            if not changed:
                raise AuthError("MOTION_EFFECT_FENCED", 409)
        return reservation

    async def model(
        self, row: dict[str, Any], token: UUID, provider: MotionModelProvider, request: MotionModelRequest
    ) -> MotionModelResult:
        payload = provider.build_request(request)
        settings = self.requests.settings
        reserve = settings.motion_ai_reservation_usd_micros
        bound = None
        if provider.provider == "openai":
            maximum = payload.get("max_output_tokens")
            rate = settings.motion_ai_output_usd_micros_per_million_tokens
            if type(maximum) is not int or maximum <= 0 or rate <= 0:
                raise AuthError("MOTION_OUTPUT_COST_BOUND_REQUIRED", 409)
            output_bound = (maximum * rate + 999999) // 1000000
            if output_bound > reserve:
                raise AuthError("MOTION_OUTPUT_COST_EXCEEDS_RESERVATION", 409)
            validate_tariff(provider.model, settings.motion_ai_input_usd_micros_per_million_tokens, rate)
            count = await provider.count_input_tokens(request, payload)
            bound = cost_bound(count, maximum, settings.motion_ai_input_usd_micros_per_million_tokens, rate)
            if bound["maximum_usd_micros"] > reserve:
                raise AuthError("MOTION_TOTAL_COST_EXCEEDS_RESERVATION", 409)
        signed = {
            "provider": provider.provider,
            "model": provider.model,
            "payload": payload,
            "input_rate": settings.motion_ai_input_usd_micros_per_million_tokens,
            "output_rate": settings.motion_ai_output_usd_micros_per_million_tokens,
            "reservation": reserve,
            "cost_bound": bound,
            # The canonical ledger digest sorts keys; bind semantic wire order separately.
            "wire_sha256": hashlib.sha256(
                json.dumps(payload, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
            ).hexdigest(),
        }
        reservation = await self.reserve_submission(
            row, token, request.operation_id, request.kind, signed, reserve, provider.provider, provider.model
        )
        try:
            try:
                result = await provider.submit(request, payload)
            except Exception as exc:
                raw = getattr(exc, "raw_response", b"")
                if raw:
                    await self.received(
                        row,
                        token,
                        request.operation_id,
                        {
                            "error_code": getattr(exc, "code", "MOTION_MODEL_INVALID_RESPONSE"),
                            "raw_response_base64": base64.b64encode(raw).decode(),
                            "provider_request_id": getattr(exc, "provider_request_id", None),
                            "usage": getattr(exc, "usage", {}),
                        },
                        getattr(exc, "estimated_usd_micros", None),
                    )
                raise
            serialized = asdict(result)
            serialized["raw_response"] = base64.b64encode(result.raw_response).decode()
            serialized["composition"] = result.composition.model_dump(mode="json") if result.composition else None
            serialized["review"] = result.review.model_dump(mode="json") if result.review else None
            if result.construction_plan is not None:
                serialized["construction_plan"] = result.construction_plan.model_dump(mode="json")
            await self.received(row, token, request.operation_id, serialized, result.estimated_usd_micros)
        finally:
            # Persist evidence FIRST; invoice uncertainty still retains the shared hold.
            await self.ledger.finish(
                row["tenant_id"],
                row["actor_id"],
                reservation.id,
                actual_usd_micros=0 if provider.provider == "fake" else None,
            )
        if result.estimated_usd_micros is None:
            raise AuthError("MOTION_COST_ESTIMATE_UNKNOWN", 409)
        if result.estimated_usd_micros > reserve:
            raise AuthError("MOTION_COST_ESTIMATE_EXCEEDED", 409)
        return result
