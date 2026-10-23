"""Deterministic, owner-only local conversation rehearsal; no outbound messages."""

import hashlib
import json
import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, cast
from uuid import UUID, uuid4, uuid5
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from cryptography.fernet import Fernet
from sqlalchemy import text
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.db.session import Database
from app.schemas.editorial_context import ConfirmedFact, ContextContent
from app.schemas.editorial_conversation import ConversationDecision, SimulateMessage
from app.services.auth import AuthError
from app.services.editorial_context import EditorialContextService, _digest
from app.services.whatsapp_materials import WhatsAppMaterialsService

PRICE = re.compile(
    r"(?:hoje\s+)?(?:o|a)\s+([\wÀ-ÿ][\wÀ-ÿ -]{1,55}?)\s+"
    r"(?:está|esta|sai|custa)\s+(?:r\$\s*)?(\d{1,5}(?:[,.]\d{1,2})?)\s*(?:reais)?(?:\s+hoje)?\b",
    re.I,
)
AVAILABILITY = re.compile(
    r"\bhoje\b.*\b(?:agenda|horário|horario)\s+livre\s+(?:às|as)\s+(\d{1,2})(?::(\d{2}))?\s*h?\b", re.I
)


def classify(message: str, now: datetime) -> tuple[str, dict[str, Any], str]:
    """Only exact, bounded patterns receive a confirmable proposal."""
    value = " ".join(message.strip().split())
    match = PRICE.fullmatch(value)
    if match and "hoje" in value.casefold().split():
        product = match.group(1).strip()
        raw = match.group(2).replace(",", ".")
        amount = int(Decimal(raw) * 100)
        if amount > 0:
            price = f"R$ {amount // 100},{amount % 100:02d}"
            summary = f"{product}: {price} hoje"
            return (
                "price",
                {"summary": summary, "valid_until": now.date().isoformat()},
                f"Quer divulgar {summary}? Responda Confirmar ou Descartar.",
            )
    match = AVAILABILITY.fullmatch(value)
    if match:
        hour, minute = int(match.group(1)), int(match.group(2) or 0)
        if hour < 24 and minute < 60:
            summary = f"Horário livre hoje às {hour:02d}:{minute:02d}"
            return (
                "availability",
                {"summary": summary, "valid_until": now.date().isoformat()},
                f"Quer divulgar {summary}? Responda Confirmar ou Descartar.",
            )
    return (
        "unknown",
        {},
        "Recebi sua mensagem. Para criar uma oferta, informe produto, valor e validade. "
        "Para divulgar uma disponibilidade, informe o horário livre de hoje.",
    )


async def record_inbound_text(session: AsyncSession, row: Any, body: str, recipient: str, cipher: Fernet) -> None:
    """Persist one proposal with the processed material, without sending a reply."""
    source = (
        (
            await session.execute(
                text("""SELECT l.actor_id,b.timezone FROM whatsapp_channel_links l
                  JOIN businesses b ON b.tenant_id=l.tenant_id AND b.id=l.business_id
                  WHERE l.tenant_id=:tenant AND l.business_id=:business
                    AND l.sender_hash=:sender AND l.active AND l.linked_at<=:created"""),
                {
                    "tenant": row["tenant_id"],
                    "business": row["business_id"],
                    "sender": row["sender_hash"],
                    "created": row["created_at"],
                },
            )
        )
        .mappings()
        .one()
    )
    local_time = row["created_at"].astimezone(ZoneInfo(source["timezone"]))
    intent, proposal, reply = classify(body, local_time)
    decision_id = uuid5(row["id"], "editorial-decision")
    result = await session.execute(
        text("""INSERT INTO editorial_conversation_decisions
          (id,tenant_id,business_id,actor_id,operation_id,request_hash,intent,state,proposal,reply)
          VALUES(:id,:tenant,:business,:actor,:operation,:digest,:intent,:state,CAST(:proposal AS jsonb),:reply)
          ON CONFLICT(tenant_id,business_id,operation_id) DO NOTHING"""),
        {
            "id": decision_id,
            "tenant": row["tenant_id"],
            "business": row["business_id"],
            "actor": source["actor_id"],
            "operation": row["id"],
            "digest": hashlib.sha256(body.encode()).hexdigest(),
            "intent": intent,
            "state": "needs_review" if intent == "unknown" else "awaiting_confirmation",
            "proposal": json.dumps(proposal),
            "reply": reply,
        },
    )
    if cast(CursorResult[Any], result).rowcount:
        if intent != "unknown":
            await session.execute(
                text("""INSERT INTO editorial_whatsapp_replies
                  (id,tenant_id,business_id,source_event_id,sender_hash,recipient_ciphertext,state,expires_at)
                  VALUES(:id,:tenant,:business,:event,:sender,:recipient,'pending',:expires)"""),
                {
                    "id": decision_id,
                    "tenant": row["tenant_id"],
                    "business": row["business_id"],
                    "event": row["id"],
                    "sender": row["sender_hash"],
                    "recipient": cipher.encrypt(recipient.encode()).decode(),
                    "expires": min(
                        row["created_at"] + timedelta(hours=23),
                        local_time.replace(hour=23, minute=59, second=0, microsecond=0).astimezone(UTC),
                    ),
                },
            )
        await session.execute(
            text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
              VALUES(:tenant,:actor,:operation,'editorial.conversation_received',:business)"""),
            {
                "tenant": row["tenant_id"],
                "actor": source["actor_id"],
                "operation": row["id"],
                "business": row["business_id"],
            },
        )


class EditorialConversationService:
    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings, self.database = settings, database

    @staticmethod
    def _present(row: Any) -> ConversationDecision:
        return ConversationDecision(
            id=row["id"],
            state=row["state"],
            intent=row["intent"],
            summary=row["proposal"].get("summary"),
            reply=row["reply"],
        )

    async def list(self, tenant: UUID, business: UUID, actor: UUID, limit: int) -> list[ConversationDecision]:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            rows = (
                (
                    await session.execute(
                        text("""SELECT id,state,intent,proposal,reply FROM editorial_conversation_decisions
                          WHERE tenant_id=:tenant AND business_id=:business
                          ORDER BY created_at DESC,id DESC LIMIT :limit"""),
                        {"tenant": tenant, "business": business, "limit": limit},
                    )
                )
                .mappings()
                .all()
            )
            return [self._present(row) for row in rows]

    async def simulate(
        self, tenant: UUID, business: UUID, actor: UUID, payload: SimulateMessage
    ) -> ConversationDecision:
        if self.settings.environment not in {"development", "testing"}:
            raise AuthError("CONVERSATION_SIMULATOR_DISABLED", 404)
        digest = hashlib.sha256(payload.text.encode()).hexdigest()
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            timezone = await session.scalar(
                text("SELECT timezone FROM businesses WHERE tenant_id=:tenant AND id=:business"),
                {"tenant": tenant, "business": business},
            )
            try:
                now = datetime.now(ZoneInfo(timezone))
            except ZoneInfoNotFoundError as exc:
                raise AuthError("BUSINESS_TIMEZONE_INVALID", 409) from exc
            intent, proposal, reply = classify(payload.text, now)
            state = "needs_review" if intent == "unknown" else "awaiting_confirmation"
            created = (
                (
                    await session.execute(
                        text("""INSERT INTO editorial_conversation_decisions
              (id,tenant_id,business_id,actor_id,operation_id,request_hash,intent,state,proposal,reply)
              VALUES(:id,:tenant,:business,:actor,:operation,:digest,:intent,:state,CAST(:proposal AS jsonb),:reply)
              ON CONFLICT(tenant_id,business_id,operation_id) DO NOTHING
              RETURNING id,intent,state,proposal,reply"""),
                        {
                            "id": uuid4(),
                            "tenant": tenant,
                            "business": business,
                            "actor": actor,
                            "operation": payload.operation_id,
                            "digest": digest,
                            "intent": intent,
                            "state": state,
                            "proposal": json.dumps(proposal),
                            "reply": reply,
                        },
                    )
                )
                .mappings()
                .one_or_none()
            )
            if created is None:
                replay = (
                    (
                        await session.execute(
                            text("""SELECT * FROM editorial_conversation_decisions
                          WHERE tenant_id=:tenant AND business_id=:business AND operation_id=:operation"""),
                            {"tenant": tenant, "business": business, "operation": payload.operation_id},
                        )
                    )
                    .mappings()
                    .one()
                )
                if replay["request_hash"] != digest:
                    raise AuthError("CONVERSATION_OPERATION_CONFLICT", 409)
                return self._present(replay)
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
              VALUES(:tenant,:actor,:operation,'editorial.conversation_simulated',:business)"""),
                {"tenant": tenant, "actor": actor, "operation": payload.operation_id, "business": business},
            )
            return self._present(created)

    async def decide(
        self, tenant: UUID, business: UUID, actor: UUID, decision: UUID, confirmed: bool
    ) -> ConversationDecision:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            row = (
                (
                    await session.execute(
                        text("""SELECT * FROM editorial_conversation_decisions
              WHERE id=:id AND tenant_id=:tenant AND business_id=:business FOR UPDATE"""),
                        {"id": decision, "tenant": tenant, "business": business},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise AuthError("CONVERSATION_NOT_FOUND", 404)
            if row["state"] in {"confirmed", "discarded"}:
                if (row["state"] == "confirmed") != confirmed:
                    raise AuthError("CONVERSATION_DECISION_CONFLICT", 409)
                return self._present(row)
            if row["state"] != "awaiting_confirmation":
                raise AuthError("CONVERSATION_NOT_CONFIRMABLE", 409)
            if confirmed:
                context = EditorialContextService(self.database)
                current = await context._version(session, tenant, business)
                content = ContextContent.model_validate(current["document"] if current else {})
                if len(content.facts) >= 20:
                    raise AuthError("CONTEXT_FACT_LIMIT", 409)
                fact = ConfirmedFact(
                    id=uuid5(decision, "confirmed-fact"),
                    kind="price" if row["intent"] == "price" else "hours",
                    statement=row["proposal"]["summary"],
                    source_detail="Confirmado pelo proprietário",
                    valid_until=row["proposal"]["valid_until"],
                )
                content.facts.append(fact)
                await context._save(
                    session,
                    tenant,
                    business,
                    actor,
                    current["version"] if current else 0,
                    decision,
                    _digest(content),
                    content,
                )
            state = "confirmed" if confirmed else "discarded"
            reply = (
                "Informação confirmada e salva para suas próximas ideias."
                if confirmed
                else "Tudo bem, não vou usar essa informação."
            )
            updated = (
                (
                    await session.execute(
                        text("""UPDATE editorial_conversation_decisions
              SET state=:state,reply=:reply,decided_at=now() WHERE id=:id
              RETURNING id,intent,state,proposal,reply"""),
                        {"id": decision, "state": state, "reply": reply},
                    )
                )
                .mappings()
                .one()
            )
            await session.execute(
                text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
              VALUES(:tenant,:actor,:decision,:action,:business)"""),
                {
                    "tenant": tenant,
                    "actor": actor,
                    "decision": decision,
                    "business": business,
                    "action": "editorial.conversation_confirmed" if confirmed else "editorial.conversation_discarded",
                },
            )
            return self._present(updated)
