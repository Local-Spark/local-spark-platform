"""Private image entrypoint using productive catalog, editorial and image algorithms."""

import asyncio
import base64
import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from uuid import UUID, uuid5

from sqlalchemy import text

from app.adapters.editorial_ai import OpenAIEditorialProvider
from app.adapters.jev_intent_ai import JevIntentProvider
from app.adapters.material_media import FetchedMedia, MaterialStore
from app.adapters.visual_ai import OpenAIVisualProvider, VisualReference, VisualRequest, visual_request_http_parts
from app.schemas.brand_kits import BrandKitOverrides
from app.schemas.creation_lab import LabStart
from app.schemas.editorial_proposals import ProposalDraft
from app.services.auth import AuthError
from app.services.brand_kits import BrandKitService
from app.services.business_collection import normalize_photo
from app.services.creation_lab_checkpoints import LabCheckpoints
from app.services.creation_lab_drafts import ZERO
from app.services.creation_lab_motion_requests import LabMotionRequests
from app.services.creative_catalog import catalog_candidates, selected_catalog_snapshot
from app.services.editorial_context import EditorialContextService
from app.services.editorial_materials import editorial_material_reference
from app.services.editorial_proposals import (
    EditorialProposalService,
    _catalog_fact,
    _catalog_price_fact,
    editorial_business_facts,
    editorial_kit_input,
)
from app.services.service_agreement_scope import accepted_agreement_sql
from app.services.visual_brand_finish import _full_piece_prompt
from app.services.visual_kit_reference import load_kit_example
from app.services.visual_references import VisualReferenceSource
from app.services.visual_requests import _MODEL, _SIZES
from app.services.visual_skills import resolve_editorial_skill
from app.workflows.contracts import BusinessEvent


class LabImageRequests(LabMotionRequests):
    formats = {"photo", "story"}

    def minimum_budget(self) -> int:
        return (
            self.settings.visual_ai_reservation_usd_micros
            + self.settings.creation_lab_editorial_reservation_usd_micros
            + (64000 * self.settings.intent_ai_input_rate_usd_micros + 999999) // 1000000
        )

    async def _admission(self, session, tenant, business):
        await self.admission_scope(session, tenant, business)
        s = self.settings
        if not (
            s.visual_ai_execution_enabled
            and s.visual_ai_mode == "openai"
            and s.editorial_ai_mode == "openai"
            and s.openai_api_key
            and s.intent_ai_mode == "jev"
            and s.typesafe_api_key
            and s.visual_ai_reservation_usd_micros > 0
            and s.creation_lab_editorial_reservation_usd_micros > 0
            and s.creation_lab_editorial_input_usd_micros_per_million_tokens > 0
            and s.creation_lab_editorial_output_usd_micros_per_million_tokens > 0
            and s.material_storage_bucket
        ):
            raise AuthError("CREATION_LAB_IMAGE_EXECUTION_NOT_CONFIGURED", 409)
        if await self.gate._state(session, tenant, business) != "active":
            raise AuthError("VISUAL_AI_CONSENT_REQUIRED", 409)
        if not await session.scalar(
            text(
                f"SELECT {accepted_agreement_sql()} OR EXISTS(SELECT 1 FROM intent_jev_consents WHERE tenant_id=:tenant AND business_id=:business AND revoked_at IS NULL)"
            ),
            {"tenant": tenant, "business": business},
        ):
            raise AuthError("JEV_CONSENT_REQUIRED", 409)

    async def build_snapshot(self, session, row, body):
        tenant, business, actor = row["tenant_id"], row["business_id"], row["actor_id"]
        from app.services.message_creation import message_text

        message = message_text(self.context, row)
        candidates = await catalog_candidates(session, tenant, business, actor, message, lab_run=self.run_id)
        if candidates["status"] not in {"needs_selection", "not_found"}:
            raise AuthError("CREATION_LAB_CATALOG_" + str(candidates["status"]).upper(), 409)
        kit = (await BrandKitService._state(session, tenant, business)).confirmed
        if kit is None:
            raise AuthError("MOTION_CONFIRMED_KIT_REQUIRED", 409)
        context = EditorialContextService._present(await EditorialContextService._version(session, tenant, business))
        today = await session.scalar(
            text(
                "SELECT (clock_timestamp() AT TIME ZONE timezone)::date FROM businesses WHERE tenant_id=:tenant AND id=:business"
            ),
            {"tenant": tenant, "business": business},
        )
        references = await self.context.references(session, business)
        sources = []
        attachments = (
            (
                await session.execute(
                    text(
                        "SELECT id,object_key,mime_type,sha256,kind,byte_size FROM creation_lab_attachments WHERE run_id=:run AND active AND state='ready' ORDER BY id"
                    ),
                    {"run": self.run_id},
                )
            )
            .mappings()
            .all()
        )
        for item in attachments:
            if row.get("flow_version") == 2 and item["kind"] == "audio" and row.get("normalized_message_ciphertext"):
                continue
            if item["kind"] != "image":
                raise AuthError("CREATION_LAB_STATIC_IMAGE_MATERIAL_REQUIRED", 409)
            sources.append(dict(item) | {"role": "source_photo", "version": 1})
        if kit.overrides.logo_asset_id:
            logo = (
                (
                    await session.execute(
                        text(
                            "SELECT id,object_key,mime_type,sha256 FROM business_brand_kit_logos WHERE tenant_id=:tenant AND business_id=:business AND id=:id AND state='ready' AND rights_scope='business_brand_confirmed'"
                        ),
                        {"tenant": tenant, "business": business, "id": kit.overrides.logo_asset_id},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if logo is None:
                raise AuthError("VISUAL_LOGO_CHANGED", 409)
            sources.append(dict(logo) | {"role": "brand_logo", "version": 1})
        # Institutional requests have no offering, but still have the business acervo.
        # Capture a deterministic authorized environment reference in the fingerprint.
        if len(sources) < 4 and not any(item["role"] == "source_photo" for item in sources):
            identifier = await session.scalar(
                text("""SELECT id FROM business_collection_photos
                  WHERE tenant_id=:tenant AND business_id=:business
                    AND state='ready' AND status='active'
                    AND rights_scope='business_collection_confirmed'
                    AND item_id IS NULL AND space_kind IN ('environment','room','counter')
                    AND delete_owner IS NULL AND delete_lease_until IS NULL
                  ORDER BY CASE space_kind WHEN 'environment' THEN 0 WHEN 'room' THEN 1 ELSE 2 END,id
                  LIMIT 1"""),
                {"tenant": tenant, "business": business},
            )
            if identifier:
                photo = await self.context.photo(session, tenant, business, identifier)
                if photo is None:
                    raise AuthError("COLLECTION_CONTEXT_CHANGED", 409)
                sources.append(dict(photo) | {"role": "space_photo"})
        if len(sources) > 4:
            raise AuthError("CREATION_LAB_IMAGE_REFERENCE_LIMIT", 409)
        skill_id, skill_hash, instructions = resolve_editorial_skill(row["format"])
        snapshot = {
            "request": body.model_dump(mode="json"),
            "format": row["format"],
            "message": message,
            "catalog_candidates": candidates,
            "kit": kit.model_dump(mode="json"),
            "context_version": context.version,
            "preferences": context.preferences.model_dump(mode="json", exclude={"reference_search"}),
            "additional_facts": [
                fact.model_dump(mode="json", exclude={"source_detail"})
                for fact in context.facts
                if fact.valid_until is None or fact.valid_until >= today
            ],
            "reference_context": references.model_input(),
            "sources": sources,
            "editorial_skill": {"id": skill_id, "sha256": skill_hash, "instructions": instructions},
            "execution": {
                "request_budget": row["budget_usd_micros"],
                "editorial_model": self.settings.editorial_ai_model,
                "editorial_reservation": self.settings.creation_lab_editorial_reservation_usd_micros,
                "input_rate": self.settings.creation_lab_editorial_input_usd_micros_per_million_tokens,
                "output_rate": self.settings.creation_lab_editorial_output_usd_micros_per_million_tokens,
                "intent_model": self.settings.intent_ai_model,
                "intent_rate": self.settings.intent_ai_input_rate_usd_micros,
                "image_model": _MODEL,
                "image_reservation": self.settings.visual_ai_reservation_usd_micros,
            },
        }
        return json.loads(json.dumps(snapshot, default=str))

    async def normalized(self, session, row):
        ciphertext = await session.scalar(
            text("SELECT payload_ciphertext FROM creation_lab_trace WHERE id=:id AND run_id=:run"),
            {"id": row["snapshot_trace_id"], "run": self.run_id},
        )
        if not ciphertext:
            raise AuthError("CREATION_LAB_TRACE_EXPIRED", 410)
        return dict(row) | {
            "operation_id": self.run_id,
            "snapshot_ciphertext": self.context.seal(self.context.open(ciphertext)["value"]),
        }

    async def catalog(self, session, row, offering):
        snapshot = self.context.open(row["snapshot_ciphertext"])
        return await selected_catalog_snapshot(
            session,
            row["tenant_id"],
            row["business_id"],
            row["actor_id"],
            snapshot["message"],
            offering,
            snapshot["catalog_candidates"]["catalog_version"],
            datetime.now(UTC),
            promotion_policy="request_only",
            lab_run=self.run_id,
        )

    async def resolve_sources(self, session, row, snapshot, catalog):
        """Use photos picked by the productive catalog snapshot, never UI choices."""
        if catalog is None:
            return snapshot["sources"]
        sources = [item for item in snapshot["sources"] if item["role"] not in {"item_photo", "space_photo"}]
        for role in ("item_photo", "space_photo"):
            reference = catalog.get(role)
            if reference is None or len(sources) >= 4:
                continue
            photo = await self.context.photo(session, row["tenant_id"], row["business_id"], UUID(reference["id"]))
            if photo["version"] != reference["version"] or photo["sha256"] != reference["sha256"]:
                raise AuthError("COLLECTION_CONTEXT_CHANGED", 409)
            if not any(str(item["id"]) == str(photo["id"]) for item in sources):
                sources.append(dict(photo) | {"role": role})
        return json.loads(json.dumps(sources, default=str))

    async def current(self, session, row):
        await self.scope(session, row)
        await self._admission(session, row["tenant_id"], row["business_id"])
        snapshot = self.context.open(row["snapshot_ciphertext"])
        fresh = await self.build_snapshot(session, row, LabStart.model_validate(snapshot["request"]))
        if self.context.fingerprint(fresh) != row["source_fingerprint"]:
            raise AuthError("CREATION_LAB_CONTEXT_CHANGED", 409)
        # Revalidate price/versions at every approval and external effect.
        value = await session.scalar(
            text("""SELECT t.payload_ciphertext FROM creation_lab_checkpoints c
          JOIN creation_lab_trace t ON t.id=c.trace_id WHERE c.run_id=:run AND c.stage='catalog'"""),
            {"run": self.run_id},
        )
        if row.get("flow_version") == 2:
            value = await session.scalar(
                text("SELECT payload_ciphertext FROM creation_lab_trace WHERE id=:id AND run_id=:run"),
                {"id": uuid5(self.run_id, "intent-resolution"), "run": self.run_id},
            )
            if not value:
                raise AuthError("CREATION_LAB_TRACE_EXPIRED", 410)
        if value:
            selected = self.context.open(value)["value"].get("snapshot" if row.get("flow_version") == 2 else "catalog")
            if selected is None:
                return
            current = await self.catalog(session, row, UUID(selected["offering"]["id"]))
            if {k: v for k, v in current.items() if k != "resolved_at"} != {
                k: v for k, v in selected.items() if k != "resolved_at"
            }:
                raise AuthError("COLLECTION_CONTEXT_CHANGED", 409)


class LabImageRunner:
    def __init__(self, requests: LabImageRequests):
        self.requests, self.execution = requests, requests.execution
        self.store = MaterialStore(requests.settings)
        self.checkpoints = LabCheckpoints(requests)

    async def pause(self, row, token, stage, payload):
        trace = uuid5(row["id"], f"checkpoint:{stage}")
        await self.execution.evidence(row["actor_id"], row["id"], token, trace, stage, payload)
        async with self.requests.database.transaction(ZERO, row["actor_id"]) as session:
            if row.get("flow_version") == 2 and not row.get("snapshot_trace_id"):
                fresh = await self.execution.guard(session, row["actor_id"], row["id"], "creation.question")
                self.execution.fence(fresh, token)
            else:
                await self.requests.locked_running(session, row, token)
            await self.checkpoints.pause(session, row, token, stage, trace, payload)

    async def submit(self, row, token, operation, kind, payload, reserve, provider, model):
        await self.execution.claim(
            row["actor_id"],
            row["id"],
            token,
            operation,
            kind,
            payload,
            reserve=reserve,
            provider=provider,
            model=model,
            authorize=lambda session: self.requests.locked_running(session, row, token),
        )
        await self.execution.submitted(row["actor_id"], row["id"], token, operation)

    def observer(self, row, token, operation):
        async def observe(body):
            await self.execution.evidence(
                row["actor_id"], row["id"], token, uuid5(operation, "raw-response"), "provider_response", body
            )
            # A terminal, truncated reply is a known failure, not a lost call.
            # Preserve its usage and full reservation without accepting its draft.
            if operation == uuid5(row["id"], "editorial") and body.get("status") == "incomplete":
                usage = body.get("usage")
                if isinstance(usage, dict) and all(
                    type(usage.get(k)) is int and usage[k] >= 0 for k in ("input_tokens", "output_tokens")
                ):
                    s = self.requests.settings
                    estimate = (
                        usage["input_tokens"] * s.creation_lab_editorial_input_usd_micros_per_million_tokens
                        + usage["output_tokens"] * s.creation_lab_editorial_output_usd_micros_per_million_tokens
                        + 999999
                    ) // 1000000
                    await self.execution.received(
                        row["actor_id"],
                        row["id"],
                        token,
                        operation,
                        {
                            "accepted": False,
                            "provider_status": "incomplete",
                            "incomplete_details": body.get("incomplete_details"),
                            "usage": usage,
                        },
                        estimate,
                    )

        return observe

    def delta_observer(self, row, token):
        counts = {}

        async def observe(operation, delta):
            counts[operation] = counts.get(operation, 0) + 1
            await self.execution.evidence(
                row["actor_id"],
                row["id"],
                token,
                uuid5(operation, f"partial:{counts[operation]}"),
                "editorial",
                {"text": delta, "partial": True, "operation_id": str(operation)},
                slot="partial",
                effect=operation,
            )

        return observe

    async def run(self, event: BusinessEvent, stage: str, *, prepared=None):
        if prepared is not None:
            row, token, packet = prepared
            stage = "catalog_approved"
        elif stage == "requested":
            started = await self.requests.begin(
                UUID(event.tenant_id),
                UUID(event.business_id),
                UUID(event.actor_id),
                UUID(event.operation_id),
                UUID(event.event_id),
            )
            if started is None:
                return "already_claimed"
            row, token = started
            packet = None
        else:
            started = await self.checkpoints.begin(event, stage.removesuffix("_approved"))
            if started is None:
                return "already_claimed"
            row, token, packet = started
        snapshot = self.requests.context.open(row["snapshot_ciphertext"])
        s = self.requests.settings
        try:
            if packet is not None:
                async with self.requests.database.transaction(ZERO, row["actor_id"]) as session:
                    await self.requests.locked_running(session, row, token)
                    snapshot["sources"] = await self.requests.resolve_sources(
                        session, row, snapshot, packet.get("catalog")
                    )
            if stage == "requested":
                assert s.typesafe_api_key is not None
                provider = JevIntentProvider(s.typesafe_api_key, s.intent_ai_model)
                candidates = snapshot["catalog_candidates"]["candidates"]
                payload = provider.prepare(snapshot["message"], candidates, [row["format"]])[0]
                operation = uuid5(row["id"], "catalog-suggestion")
                reserve = (64000 * s.intent_ai_input_rate_usd_micros + 999999) // 1000000
                await self.submit(row, token, operation, "catalog", payload, reserve, "jev", s.intent_ai_model)
                suggestion = await provider.interpret(
                    snapshot["message"],
                    candidates,
                    [row["format"]],
                    operation,
                    response_observer=self.observer(row, token, operation),
                )
                await self.execution.received(
                    row["actor_id"],
                    row["id"],
                    token,
                    operation,
                    asdict(suggestion),
                    (suggestion.input_tokens * s.intent_ai_input_rate_usd_micros + 999999) // 1000000,
                )
                if suggestion.intent != "content_request" or suggestion.decision == "clarify":
                    await self.pause(
                        row,
                        token,
                        "catalog",
                        {
                            "questions": [
                                "O que você quer divulgar nesta peça? Se houver um produto ou serviço específico, descreva-o."
                            ],
                            "suggestion": asdict(suggestion),
                        },
                    )
                    return "awaiting_reply"
                if suggestion.decision == "none" and suggestion.offering_id is None:
                    catalog = None
                elif suggestion.decision == "selected" and suggestion.offering_id is not None:
                    async with self.requests.database.transaction(ZERO, row["actor_id"]) as session:
                        await self.requests.locked_running(session, row, token)
                        catalog = await self.requests.catalog(session, row, suggestion.offering_id)
                else:
                    raise AuthError("CREATION_LAB_CATALOG_INVALID_DECISION", 409)
                await self.pause(
                    row,
                    token,
                    "catalog",
                    {
                        "catalog": catalog,
                        "suggestion": asdict(suggestion),
                        "basis": "catalog" if catalog else "business",
                        "description": "Usar o pedido e o contexto confirmado do negócio, sem vincular um item do catálogo."
                        if catalog is None
                        else None,
                    },
                )
                return "awaiting_catalog"
            if stage == "catalog_approved":
                catalog = packet["catalog"]
                facts = (
                    [fact for fact in (_catalog_fact(catalog), _catalog_price_fact(catalog)) if fact]
                    if catalog
                    else editorial_business_facts(
                        snapshot["additional_facts"],
                        snapshot["kit"]["overrides"]["brand_name"],
                        row["business_id"],
                        snapshot["kit"]["version"],
                    )
                )
                if not facts:
                    await self.pause(
                        row,
                        token,
                        "editorial",
                        {
                            "questions": ["Qual informação confirmada sobre o negócio deve fundamentar esta peça?"],
                            "catalog": catalog,
                        },
                    )
                    return "awaiting_reply"
                data = {
                    "confirmed_facts": facts,
                    "preferences": snapshot["preferences"],
                    "material": snapshot["message"],
                    "material_kind": "text",
                    "source_asset_id": None,
                    "context_version": snapshot["context_version"],
                    "requested_format": row["format"],
                    "eligible_formats": [row["format"]],
                    "brand_kit": editorial_kit_input(snapshot["kit"], snapshot["kit"]["version"]),
                    "reference_context": snapshot["reference_context"],
                    "editorial_skill": snapshot["editorial_skill"],
                    "available_materials": [editorial_material_reference(item) for item in snapshot["sources"]],
                    "catalog_context": {
                        "name": catalog["offering"]["name"],
                        "kind": catalog["offering"]["kind"],
                        "price": catalog["offering"]["price"]
                        if catalog["offering"]["price"]["status"] == "valid"
                        else None,
                        "has_item_photo": any(item["role"] == "item_photo" for item in snapshot["sources"]),
                        "has_space_photo": any(item["role"] == "space_photo" for item in snapshot["sources"]),
                    }
                    if catalog
                    else None,
                }
                provider = OpenAIEditorialProvider(s, delta_observer=self.delta_observer(row, token))
                payload = provider.build_request(data)
                # Conservative UTF-8 upper bound plus bounded output; no guessed invoice.
                maximum = (
                    len(json.dumps(payload, ensure_ascii=False).encode())
                    * s.creation_lab_editorial_input_usd_micros_per_million_tokens
                    + payload["max_output_tokens"] * s.creation_lab_editorial_output_usd_micros_per_million_tokens
                    + 999999
                ) // 1000000
                if maximum > s.creation_lab_editorial_reservation_usd_micros:
                    raise AuthError("CREATION_LAB_EDITORIAL_RESERVATION_TOO_SMALL", 409)
                operation = uuid5(row["id"], "editorial")
                await self.submit(
                    row,
                    token,
                    operation,
                    "editorial",
                    payload,
                    s.creation_lab_editorial_reservation_usd_micros,
                    "openai",
                    s.editorial_ai_model,
                )
                draft, incoming, outgoing = await provider.propose(
                    data, operation, prepared_request=payload, response_observer=self.observer(row, token, operation)
                )
                await self.execution.received(
                    row["actor_id"],
                    row["id"],
                    token,
                    operation,
                    {"draft": draft.model_dump(mode="json"), "input_tokens": incoming, "output_tokens": outgoing},
                    (
                        incoming * s.creation_lab_editorial_input_usd_micros_per_million_tokens
                        + outgoing * s.creation_lab_editorial_output_usd_micros_per_million_tokens
                        + 999999
                    )
                    // 1000000,
                )
                if draft.questions:
                    await self.pause(
                        row,
                        token,
                        "editorial",
                        {
                            "catalog": catalog,
                            "draft": draft.model_dump(mode="json"),
                            "questions": draft.questions,
                            "data": data,
                        },
                    )
                    return "awaiting_reply"
                diagnostics: dict[str, object] = {}
                rejection = EditorialProposalService._generated_rejection(
                    draft, data, {UUID(f["id"]) for f in facts}, full_piece=True, diagnostics=diagnostics
                )
                if rejection:
                    await self.execution.evidence(
                        row["actor_id"],
                        row["id"],
                        token,
                        uuid5(row["id"], "editorial-validation"),
                        "editorial_validation",
                        {"code": rejection, **diagnostics},
                    )
                    raise AuthError(rejection, 409)
                draft = EditorialProposalService._ground_generated(draft, data).model_copy(
                    update={
                        "editorial_skill_id": snapshot["editorial_skill"]["id"],
                        "editorial_skill_sha256": snapshot["editorial_skill"]["sha256"],
                    }
                )
                packet = {"catalog": catalog, "draft": draft.model_dump(mode="json"), "data": data}
                if row["flow_version"] == 1 and row["mode"] == "accompanied":
                    await self.pause(row, token, "editorial", packet)
                    return "awaiting_editorial"
            await self.generate(row, token, snapshot, packet)
            return "completed"
        except BaseException as exc:
            code = getattr(exc, "code", "CREATION_LAB_IMAGE_EXECUTION_FAILED")
            await self.execution.finish(row["actor_id"], row["id"], token, "failed", code)
            raise

    async def generate(self, row, token, snapshot, packet):
        s = self.requests.settings
        draft = ProposalDraft.model_validate(packet["draft"])
        data = packet["data"]
        if not EditorialProposalService._safe_generated(
            draft, data, {UUID(f["id"]) for f in data["confirmed_facts"]}, full_piece=True
        ):
            raise AuthError("VISUAL_COPY_UNVERIFIED", 409)
        references, sources = [], []
        for item in snapshot["sources"]:
            raw = await self.store.get_image(item["object_key"])
            if hashlib.sha256(raw).hexdigest() != item["sha256"]:
                raise AuthError("VISUAL_REFERENCE_HASH_MISMATCH", 409)
            normalized = await asyncio.to_thread(normalize_photo, raw, item["mime_type"], 5 * 1024 * 1024)
            sources.append(
                VisualReferenceSource(
                    item["role"], UUID(item["id"]), item["version"], item["sha256"], normalized.sha256
                )
            )
            references.append(VisualReference(normalized.data, normalized.mime_type))
        kit_source, kit_reference = await asyncio.to_thread(load_kit_example, s, snapshot["kit"], row["format"])
        sources.append(kit_source)
        references.append(kit_reference)
        fact = next(f for f in data["confirmed_facts"] if f["id"] == str(draft.fact_ids[0]))
        prompt = _full_piece_prompt(
            product_name=(
                packet["catalog"]["offering"]["name"]
                if packet["catalog"]
                else snapshot["kit"]["overrides"]["brand_name"]
            ),
            kit=BrandKitOverrides.model_validate(snapshot["kit"]["overrides"]),
            draft=draft,
            confirmed_statement=fact["statement"],
            original_request=snapshot["message"],
            business_context={**snapshot["preferences"], "referencias_escolhidas": snapshot["reference_context"]},
            additional_facts=snapshot["additional_facts"],
            references=tuple(sources),
            skill=snapshot["editorial_skill"]["instructions"],
        )
        operation = uuid5(row["id"], "image:0")
        request = VisualRequest(prompt, _MODEL, "medium", _SIZES[row["format"]], "png", operation, tuple(references))
        endpoint, payload = visual_request_http_parts(request)
        if references:
            payload["images"] = [
                {"image_url": f"data:{r.mime_type};base64,{base64.b64encode(r.content).decode()}"} for r in references
            ]
        await self.submit(
            row,
            token,
            operation,
            "image",
            {"endpoint": endpoint, "payload": payload},
            s.visual_ai_reservation_usd_micros,
            "openai",
            _MODEL,
        )
        assert s.openai_api_key is not None
        result = await OpenAIVisualProvider(s.openai_api_key.get_secret_value()).generate(
            request, response_observer=self.observer(row, token, operation)
        )
        await self.execution.received(
            row["actor_id"],
            row["id"],
            token,
            operation,
            {
                "sha256": result.sha256,
                "mime_type": result.mime_type,
                "width": result.width,
                "height": result.height,
                "usage": result.usage,
                "provider_request_id": result.provider_request_id,
            },
        )
        upload = uuid5(operation, "upload")
        key = f"creation-lab/{row['actor_id']}/{row['id']}/versions/{operation}.png"
        await self.execution.claim(
            row["actor_id"],
            row["id"],
            token,
            upload,
            "upload",
            {"sha256": result.sha256, "size_bytes": len(result.content)},
            authorize=lambda session: self.requests.locked_running(session, row, token),
        )
        if self.store.single_attempt_put is not True:
            raise AuthError("MOTION_STORAGE_SINGLE_ATTEMPT_REQUIRED", 409)
        await self.store.put(key, FetchedMedia(result.content, result.mime_type, result.sha256))
        stored = await self.store.get_motion_payload(key)
        if hashlib.sha256(stored).hexdigest() != result.sha256:
            raise AuthError("VISUAL_OUTPUT_CHANGED", 409)
        await self.execution.received(row["actor_id"], row["id"], token, upload, {"sha256": result.sha256})
        async with self.requests.database.transaction(ZERO, row["actor_id"]) as session:
            current = await self.requests.locked_running(session, row, token)
            await session.execute(
                text("""INSERT INTO creation_lab_versions(id,run_id,number,object_key,sha256,mime_type,size_bytes,selected,review_verdict,copy_ciphertext)
              VALUES(:id,:run,0,:key,:sha,:mime,:size,true,'human_review_required',:copy)"""),
                {
                    "id": operation,
                    "run": row["id"],
                    "key": key,
                    "sha": result.sha256,
                    "mime": result.mime_type,
                    "size": len(result.content),
                    "copy": self.requests.context.seal(
                        {"art_text": draft.art_text, "caption": draft.caption, "cta": draft.cta}
                    ),
                },
            )
            await self.execution.event(session, row["id"], uuid5(operation, "recorded"), "artifact.recorded")
            await self.execution.finish_locked(session, current, "completed")
