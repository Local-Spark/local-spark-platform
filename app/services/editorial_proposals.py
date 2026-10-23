"""Durable, owner-requested editorial proposals with one-shot paid execution."""

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import text

from app.adapters.editorial_ai import EditorialProviderError, OpenAIEditorialProvider
from app.core.config import Settings
from app.db.session import Database
from app.schemas.editorial_context import ContextContent
from app.schemas.editorial_proposals import ProposalDraft, ProposalRead, ProposalRequest
from app.services.auth import AuthError
from app.services.whatsapp_materials import WhatsAppMaterialsService


def _present(row: Any) -> ProposalRead:
    return ProposalRead.model_validate(row)


def _replay(row: Any, digest: str) -> ProposalRead:
    if row["request_hash"] != digest:
        raise AuthError("PROPOSAL_OPERATION_CONFLICT", 409)
    return _present(row)


def _access_sql() -> str:
    return """SELECT EXISTS(
      SELECT 1 FROM billing_sponsorships s WHERE s.tenant_id=:tenant
        AND s.revoked_at IS NULL AND s.starts_at<=now() AND s.ends_at>now()
      UNION ALL
      SELECT 1 FROM billing_accounts b WHERE b.tenant_id=:tenant AND b.livemode=:live
        AND b.status='active' AND NOT b.blocked AND b.paid_until>now())"""


async def _audit(session: Any, row: Any, action: str) -> None:
    await session.execute(
        text("""INSERT INTO audit_events(tenant_id,actor_id,operation_id,action,resource_id)
          VALUES(:tenant,:actor,:operation,:action,:resource)"""),
        {
            "tenant": row["tenant_id"],
            "actor": row["actor_id"],
            "operation": uuid4(),
            "action": action,
            "resource": row["business_id"],
        },
    )


class EditorialProposalService:
    def __init__(self, settings: Settings, database: Database, provider: OpenAIEditorialProvider | None = None) -> None:
        self.settings, self.database = settings, database
        self.provider = provider or OpenAIEditorialProvider(settings)

    async def consent_status(self, tenant: UUID, business: UUID, actor: UUID) -> dict[str, bool]:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            accepted = await session.scalar(
                text("""SELECT revoked_at IS NULL FROM editorial_ai_consents
              WHERE tenant_id=:tenant AND business_id=:business"""),
                {"tenant": tenant, "business": business},
            )
            return {"accepted": bool(accepted), "provider_enabled": self.settings.editorial_ai_mode == "openai"}

    async def set_consent(self, tenant: UUID, business: UUID, actor: UUID, accepted: bool) -> dict[str, bool]:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            current = await session.scalar(
                text("""SELECT revoked_at IS NULL FROM editorial_ai_consents
              WHERE tenant_id=:tenant AND business_id=:business FOR UPDATE"""),
                {"tenant": tenant, "business": business},
            )
            if current is not None and bool(current) == accepted:
                return {"accepted": accepted, "provider_enabled": self.settings.editorial_ai_mode == "openai"}
            if current is None and not accepted:
                return {"accepted": False, "provider_enabled": self.settings.editorial_ai_mode == "openai"}
            await session.execute(
                text("""INSERT INTO editorial_ai_consents(tenant_id,business_id,actor_id)
              VALUES(:tenant,:business,:actor) ON CONFLICT(tenant_id,business_id) DO UPDATE SET
              actor_id=EXCLUDED.actor_id,accepted_at=now(),revoked_at=CASE WHEN :accepted THEN NULL ELSE now() END"""),
                {"tenant": tenant, "business": business, "actor": actor, "accepted": accepted},
            )
            await _audit(
                session,
                {"tenant_id": tenant, "business_id": business, "actor_id": actor},
                "editorial.ai_consent_accepted" if accepted else "editorial.ai_consent_revoked",
            )
            return {"accepted": accepted, "provider_enabled": self.settings.editorial_ai_mode == "openai"}

    async def request(self, tenant: UUID, business: UUID, actor: UUID, payload: ProposalRequest) -> ProposalRead:
        digest = hashlib.sha256(str(payload.source_asset_id).encode()).hexdigest()
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            existing = (
                (
                    await session.execute(
                        text("""SELECT * FROM editorial_proposals
              WHERE tenant_id=:tenant AND business_id=:business AND operation_id=:operation"""),
                        {"tenant": tenant, "business": business, "operation": payload.operation_id},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if existing is not None:
                return _replay(existing, digest)
            if not await session.scalar(
                text(_access_sql()), {"tenant": tenant, "live": self.settings.environment == "production"}
            ):
                raise AuthError("PLAN_REQUIRED", 403)
            if self.settings.editorial_ai_mode == "openai" and not await self._consented(session, tenant, business):
                raise AuthError("EDITORIAL_AI_CONSENT_REQUIRED", 409)
            if payload.source_asset_id is not None:
                source = await session.scalar(
                    text("""SELECT 1 FROM whatsapp_material_assets
                  WHERE id=:source AND tenant_id=:tenant AND business_id=:business
                    AND delete_requested_at IS NULL AND expires_at>now()"""),
                    {"source": payload.source_asset_id, "tenant": tenant, "business": business},
                )
                if source is None:
                    raise AuthError("MATERIAL_NOT_FOUND", 404)
            version = (
                await session.scalar(
                    text("""SELECT version FROM business_context_heads
              WHERE tenant_id=:tenant AND business_id=:business"""),
                    {"tenant": tenant, "business": business},
                )
                or 0
            )
            proposal = uuid4()
            row = (
                (
                    await session.execute(
                        text("""INSERT INTO editorial_proposals
              (id,tenant_id,business_id,actor_id,operation_id,request_hash,context_version,source_asset_id)
              VALUES(:id,:tenant,:business,:actor,:operation,:digest,:version,:source)
              ON CONFLICT(tenant_id,business_id,operation_id) DO NOTHING RETURNING *"""),
                        {
                            "id": proposal,
                            "tenant": tenant,
                            "business": business,
                            "actor": actor,
                            "operation": payload.operation_id,
                            "digest": digest,
                            "version": version,
                            "source": payload.source_asset_id,
                        },
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                row = (
                    (
                        await session.execute(
                            text("""SELECT * FROM editorial_proposals
                  WHERE tenant_id=:tenant AND business_id=:business AND operation_id=:operation"""),
                            {"tenant": tenant, "business": business, "operation": payload.operation_id},
                        )
                    )
                    .mappings()
                    .one()
                )
                return _replay(row, digest)
            await _audit(session, row, "editorial.proposal_requested")
            return _present(row)

    async def list(self, tenant: UUID, business: UUID, actor: UUID, limit: int = 30) -> list[ProposalRead]:
        async with self.database.transaction(tenant, actor) as session:
            await WhatsAppMaterialsService._require_owner(session, tenant, business, actor)
            rows = (
                (
                    await session.execute(
                        text("""SELECT * FROM editorial_proposals
              WHERE tenant_id=:tenant AND business_id=:business AND expires_at>now()
              ORDER BY created_at DESC,id DESC LIMIT :limit"""),
                        {"tenant": tenant, "business": business, "limit": limit},
                    )
                )
                .mappings()
                .all()
            )
            return [_present(row) for row in rows]

    @staticmethod
    async def _consented(session: Any, tenant: UUID, business: UUID) -> bool:
        return bool(
            await session.scalar(
                text("""SELECT 1 FROM editorial_ai_consents
          WHERE tenant_id=:tenant AND business_id=:business AND revoked_at IS NULL"""),
                {"tenant": tenant, "business": business},
            )
        )

    async def _reject(self, session: Any, row: Any, code: str, state: str = "rejected") -> str:
        await session.execute(
            text("""UPDATE editorial_proposals SET state=:state,error_code=:code,
          updated_at=now() WHERE id=:id"""),
            {"id": row["id"], "state": state, "code": code},
        )
        await _audit(session, row, f"editorial.proposal_{state}")
        return state

    def _source(self, row: Any) -> str | None:
        ciphertext = row["transcript_ciphertext"] or row["ciphertext"]
        if not ciphertext or not self.settings.meta_encryption_key:
            return None
        try:
            return (
                Fernet(self.settings.meta_encryption_key.get_secret_value().encode())
                .decrypt(ciphertext.encode())
                .decode()[:4000]
            )
        except (InvalidToken, UnicodeDecodeError):
            return None

    async def _inputs(self, session: Any, row: Any) -> tuple[dict[str, object], set[UUID]] | None:
        if row["source_asset_id"] is not None:
            asset = (
                (
                    await session.execute(
                        text("""SELECT a.ciphertext,a.transcript_ciphertext,a.kind
              FROM whatsapp_material_assets a WHERE a.id=:source AND a.tenant_id=:tenant
                AND a.business_id=:business AND a.delete_requested_at IS NULL AND a.expires_at>now()"""),
                        {"source": row["source_asset_id"], "tenant": row["tenant_id"], "business": row["business_id"]},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if asset is None:
                return None
            source = self._source(asset)
            kind = asset["kind"]
        else:
            source, kind = None, None
        if row["context_version"]:
            context_row = await session.scalar(
                text("""SELECT document FROM business_context_versions
              WHERE tenant_id=:tenant AND business_id=:business AND version=:version"""),
                {"tenant": row["tenant_id"], "business": row["business_id"], "version": row["context_version"]},
            )
            if context_row is None:
                return None
            context = ContextContent.model_validate(context_row)
        else:
            context = ContextContent()
        facts = [
            fact for fact in context.facts if fact.valid_until is None or fact.valid_until >= datetime.now(UTC).date()
        ]
        if not source and not facts:
            return None
        data: dict[str, object] = {
            "confirmed_facts": [{"id": str(fact.id), "kind": fact.kind, "statement": fact.statement} for fact in facts],
            "preferences": context.preferences.model_dump(mode="json"),
            "material": source,
            "material_kind": kind,
            "context_version": row["context_version"],
        }
        return data, {fact.id for fact in facts}

    @staticmethod
    def _baseline(data: dict[str, object]) -> ProposalDraft:
        facts = data["confirmed_facts"]
        assert isinstance(facts, list)
        fact = facts[0] if facts else None
        assert fact is None or isinstance(fact, dict)
        angle = (
            f"Apresente este ponto do negócio: {str(fact['statement']).rstrip('. ')}."
            if fact
            else "Mostre o material recebido e explique ao público o que ele representa para o negócio."
        )
        kind = data["material_kind"]
        fmt: Literal["short_video", "photo", "story"] = (
            "short_video" if kind in {"audio", "video"} else "photo" if kind == "image" else "story"
        )
        return ProposalDraft(
            title="Uma história do seu negócio",
            format=fmt,
            angle=angle,
            fact_ids=[UUID(str(fact["id"]))] if fact else [],
            hypotheses=[],
            questions=["Qual detalhe você gostaria de destacar?"],
        )

    @staticmethod
    def _safe(draft: ProposalDraft, data: dict[str, object], valid_ids: set[UUID]) -> bool:
        if not draft.fact_ids or not set(draft.fact_ids) <= valid_ids:
            return False
        facts = data["confirmed_facts"]
        assert isinstance(facts, list)
        evidence = " ".join(str(fact["statement"]) for fact in facts if isinstance(fact, dict))
        if any(number not in evidence for number in re.findall(r"\d+", draft.title + " " + draft.angle)):
            return False
        preferences = data["preferences"]
        assert isinstance(preferences, dict)
        grounded = EditorialProposalService._ground(draft, data)
        visible_text = " ".join((draft.title, draft.angle, grounded.title, grounded.angle)).casefold()
        return not any(str(topic).casefold() in visible_text for topic in preferences.get("avoided_topics", []))

    @staticmethod
    def _ground(draft: ProposalDraft, data: dict[str, object]) -> ProposalDraft:
        """Keep the factual surface deterministic; model text is review-only."""
        baseline = EditorialProposalService._baseline(data)
        return ProposalDraft(
            title=baseline.title,
            format=draft.format,
            angle=baseline.angle,
            fact_ids=baseline.fact_ids,
            hypotheses=draft.hypotheses,
            questions=draft.questions,
        )

    async def run(self, proposal_id: UUID) -> str:
        async with self.database.sessions() as session, session.begin():
            row = (
                (
                    await session.execute(
                        text("SELECT * FROM editorial_proposals WHERE id=:id FOR UPDATE"), {"id": proposal_id}
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None or row["state"] != "dispatching":
                return "skipped"
            if row["expires_at"] <= datetime.now(UTC):
                return await self._reject(session, row, "PROPOSAL_EXPIRED")
            if not await session.scalar(
                text(_access_sql()), {"tenant": row["tenant_id"], "live": self.settings.environment == "production"}
            ):
                return await self._reject(session, row, "PLAN_INACTIVE")
            if self.settings.editorial_ai_mode == "openai" and not await self._consented(
                session, row["tenant_id"], row["business_id"]
            ):
                return await self._reject(session, row, "EDITORIAL_AI_CONSENT_REQUIRED")
            inputs = await self._inputs(session, row)
            if inputs is None:
                return await self._reject(session, row, "EDITORIAL_SOURCE_UNAVAILABLE")
            data, _ = inputs
            if not data["confirmed_facts"]:
                return await self._reject(session, row, "EDITORIAL_FACTS_REQUIRED")
            if self.settings.editorial_ai_mode == "disabled":
                baseline_draft = self._baseline(data)
                await session.execute(
                    text("""UPDATE editorial_proposals SET state='completed',
                  document=CAST(:doc AS jsonb),
                  model='baseline-v1',updated_at=now() WHERE id=:id"""),
                    {"doc": baseline_draft.model_dump_json(), "id": proposal_id},
                )
                await _audit(session, row, "editorial.proposal_completed")
                return "completed"
            reserved = len(json.dumps(data, ensure_ascii=False).encode()) + 3800
            if reserved > 30000:
                return await self._reject(session, row, "EDITORIAL_INPUT_TOO_LARGE")
            await session.execute(
                text("SELECT pg_advisory_xact_lock(hashtextextended(:tenant,1))"), {"tenant": str(row["tenant_id"])}
            )
            used = await session.scalar(
                text("""SELECT coalesce(sum(reserved_tokens),0) FROM editorial_ai_usage
              WHERE tenant_id=:tenant AND created_at>=date_trunc('day',now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'"""),
                {"tenant": row["tenant_id"]},
            )
            if used + reserved > self.settings.editorial_daily_token_limit:
                return await self._reject(session, row, "EDITORIAL_BUDGET_EXCEEDED", "budget_exceeded")
            await session.execute(
                text("""INSERT INTO editorial_ai_usage
              (proposal_id,tenant_id,business_id,reserved_tokens,state)
              VALUES(:id,:tenant,:business,:reserved,'submitted')"""),
                {"id": proposal_id, "tenant": row["tenant_id"], "business": row["business_id"], "reserved": reserved},
            )
            await session.execute(
                text("""UPDATE editorial_proposals SET state='submitted',reserved_tokens=:reserved,
              model=:model,updated_at=now() WHERE id=:id"""),
                {"id": proposal_id, "reserved": reserved, "model": self.settings.editorial_ai_model},
            )
            await _audit(session, row, "editorial.proposal_submitted")
        draft: ProposalDraft | None
        try:
            draft, input_tokens, output_tokens = await self.provider.propose(data, proposal_id)
        except EditorialProviderError:
            draft, input_tokens, output_tokens = None, None, None
        async with self.database.sessions() as session, session.begin():
            row = (
                (
                    await session.execute(
                        text("SELECT * FROM editorial_proposals WHERE id=:id FOR UPDATE"), {"id": proposal_id}
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None or row["state"] != "submitted":
                return "uncertain"
            consent = await self._consented(session, row["tenant_id"], row["business_id"])
            access = await session.scalar(
                text(_access_sql()),
                {"tenant": row["tenant_id"], "live": self.settings.environment == "production"},
            )
            fresh_inputs = await self._inputs(session, row) if consent and access else None
            safe = bool(
                draft is not None and fresh_inputs is not None and self._safe(draft, fresh_inputs[0], fresh_inputs[1])
            )
            if safe and draft is not None and fresh_inputs is not None:
                draft = self._ground(draft, fresh_inputs[0])
            state = "completed" if safe else "uncertain"
            await session.execute(
                text("""UPDATE editorial_proposals SET state=:state,
              document=CAST(:doc AS jsonb),error_code=:error,input_tokens=:input,
              output_tokens=:output,updated_at=now() WHERE id=:id"""),
                {
                    "id": proposal_id,
                    "state": state,
                    "doc": draft.model_dump_json() if safe and draft else None,
                    "error": None if safe else "EDITORIAL_RESULT_UNCERTAIN",
                    "input": input_tokens,
                    "output": output_tokens,
                },
            )
            await session.execute(
                text("""UPDATE editorial_ai_usage SET state=:state,
              input_tokens=:input,output_tokens=:output WHERE proposal_id=:id"""),
                {"id": proposal_id, "state": state, "input": input_tokens, "output": output_tokens},
            )
            await _audit(session, row, f"editorial.proposal_{state}")
            return state


async def reconcile_stale_proposals(database: Database, limit: int = 100) -> int:
    async with database.sessions() as session, session.begin():
        rows = (
            (
                await session.execute(
                    text("""WITH due AS (
          SELECT id FROM editorial_proposals WHERE
            (state='submitted' AND updated_at<now()-interval '5 minutes') OR
            (state='dispatching' AND dispatch_lease_until IS NULL
              AND updated_at<now()-interval '10 minutes')
          ORDER BY updated_at,id LIMIT :limit FOR UPDATE SKIP LOCKED)
          UPDATE editorial_proposals p SET state='uncertain',error_code='EDITORIAL_RESULT_UNCERTAIN',
            updated_at=now() FROM due WHERE p.id=due.id
          RETURNING p.id,p.tenant_id,p.business_id,p.actor_id"""),
                    {"limit": limit},
                )
            )
            .mappings()
            .all()
        )
        for row in rows:
            await session.execute(
                text("""UPDATE editorial_ai_usage SET state='uncertain'
              WHERE proposal_id=:id AND state='submitted'"""),
                {"id": row["id"]},
            )
            await _audit(session, row, "editorial.proposal_uncertain")
        await session.execute(text("DELETE FROM editorial_proposals WHERE expires_at<=now()"))
        return len(rows)
