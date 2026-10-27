"""Prepare a text-free image request and apply a verified owner brand kit.

This service does not call a provider, reserve budget or expose files. The
caller must prove admission, fence and consent at the external-effect boundary
and revalidate the returned candidate before allowing access.
"""

import asyncio
import hashlib
import hmac
import json
from dataclasses import dataclass, field, replace
from uuid import UUID

from sqlalchemy import text

from app.adapters.brand_overlay import render_brand_overlay
from app.adapters.material_media import FetchedMedia, MaterialStore
from app.core.config import Settings
from app.db.session import Database
from app.schemas.brand_kits import BrandKitOverrides
from app.schemas.editorial_proposals import ProposalDraft
from app.services.auth import AuthError
from app.services.editorial_briefings import EditorialBriefingService
from app.services.visual_context import VisualContextService
from app.services.visual_requests import PreparedVisualRequest, VisualRequestService, visual_request_digest

RECIPE = "verified-brand-overlay-v1"


@dataclass(frozen=True)
class PreparedBrandScene:
    """Server-built request and private finishing material; never log its content."""

    request: PreparedVisualRequest = field(repr=False)
    kit: BrandKitOverrides = field(repr=False)
    statement: str = field(repr=False)
    cta: str = field(repr=False)
    logo: FetchedMedia | None = field(default=None, repr=False)
    recipe: str = RECIPE


class VisualBrandFinishService:
    def __init__(self, settings: Settings, database: Database, store: MaterialStore | None = None) -> None:
        self.settings, self.database = settings, database
        self.store = store or MaterialStore(settings)

    async def prepare(
        self, tenant: UUID, business: UUID, actor: UUID, proposal: UUID, operation: UUID, *, candidate: bool = False
    ) -> PreparedBrandScene:
        # The editorial service validates the selected fact, CTA, source rights,
        # business access and the snapshot. The resulting request is rebuilt to
        # ask for a text-free scene; copy is applied locally, not invented.
        original = await VisualRequestService(self.settings, self.database, self.store).prepare(
            tenant, business, actor, proposal, operation, candidate=candidate
        )
        context = original.context
        if (
            context.tenant_id != tenant
            or context.business_id != business
            or context.proposal_id != proposal
            or original.request.request_id != operation
        ):
            raise AuthError("VISUAL_CONTEXT_CHANGED", 409)
        async with self.database.transaction(tenant, actor) as session:
            status, catalog = await EditorialBriefingService(self.settings, self.database).read_valid(
                session, tenant, business, actor, context.briefing_id
            )
            row = (
                (
                    await session.execute(
                        text("""SELECT document,brand_kit_document FROM editorial_proposals
                          WHERE tenant_id=:tenant AND business_id=:business AND id=:proposal"""),
                        {"tenant": tenant, "business": business, "proposal": proposal},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if status != "prepared" or catalog is None or row is None or row["brand_kit_document"] is None:
                raise AuthError("VISUAL_CONTEXT_CHANGED", 409)
            draft = ProposalDraft.model_validate(row["document"])
            kit = BrandKitOverrides.model_validate(row["brand_kit_document"]["overrides"])
            fact = [item.on_screen_text for item in draft.script if item.role == "fact"]
            cta = [item.on_screen_text for item in draft.script if item.role == "cta"]
            if len(fact) != 1 or len(cta) != 1:
                raise AuthError("VISUAL_COPY_UNVERIFIED", 409)
            product_name = str(catalog["offering"]["name"])  # type: ignore[index]
            logo_row = None
            if kit.logo_asset_id is not None:
                logo_row = (
                    (
                        await session.execute(
                            text("""SELECT object_key,sha256,mime_type FROM business_brand_kit_logos
                              WHERE tenant_id=:tenant AND business_id=:business AND id=:logo
                                AND state='ready' AND rights_scope='business_brand_confirmed'
                                AND mime_type='image/png'"""),
                            {"tenant": tenant, "business": business, "logo": kit.logo_asset_id},
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if logo_row is None:
                    raise AuthError("VISUAL_LOGO_CHANGED", 409)
        logo = None
        if logo_row is not None:
            data = await self.store.get_image(logo_row["object_key"])
            digest = hashlib.sha256(data).hexdigest()
            if not hmac.compare_digest(digest, logo_row["sha256"]):
                raise AuthError("VISUAL_LOGO_CHANGED", 409)
            logo = FetchedMedia(data, logo_row["mime_type"], digest)
        current = await VisualContextService(self.settings, self.database).capture(
            tenant, business, actor, proposal, candidate=candidate
        )
        if current != context:
            raise AuthError("VISUAL_CONTEXT_CHANGED", 409)
        instructions = {
            "source_photo": "imagem enviada pelo cliente; preserve seus elementos reconhecíveis",
            "item_photo": "produto ou serviço do acervo; preserve seus detalhes visíveis",
            "space_photo": "espaço real do negócio; preserve seus elementos visíveis",
        }
        reference_text = " ".join(
            f"Referência {index}: {instructions[source.kind]}." for index, source in enumerate(original.sources, 1)
        )
        if not any(source.kind == "space_photo" for source in original.sources):
            reference_text += " Sem referência do espaço, não apresente um local inventado como real."
        layout = kit.formats.feed if context.format == "photo" else kit.formats.story
        prompt = (
            "Crie uma fotografia publicitária natural para uma prévia de rede social. "
            f"O tema autorizado é {json.dumps(product_name, ensure_ascii=False)}. "
            f"Direção visual: cores {kit.palette.primary}, {kit.palette.background}, {kit.palette.accent}; "
            f"composição {layout.layout}, enquadramento {layout.image_position}. {reference_text} "
            "Deixe áreas de respiro para textos e identidade visual aplicados depois. "
            "Não acrescente palavras, letras, números, logotipos, preços, marcas d'água ou alegações. "
            "Não invente ingredientes, promoções, resultados ou características não fornecidas. "
            "O resultado será uma prévia sujeita à revisão humana."
        )
        request = replace(original.request, prompt=prompt)
        key = self.settings.meta_encryption_key
        if key is None or not key.get_secret_value().strip():
            raise AuthError("VISUAL_CONTEXT_KEY_REQUIRED", 409)
        prepared = PreparedVisualRequest(
            context,
            original.sources,
            visual_request_digest(key.get_secret_value(), context, original.sources, request),
            request,
        )
        return PreparedBrandScene(prepared, kit, fact[0], cta[0], logo)

    async def finish(
        self, actor: UUID, prepared: PreparedBrandScene, scene: FetchedMedia, *, candidate: bool = False
    ) -> FetchedMedia:
        """Render private output only while its prepared sources still match."""
        context = prepared.request.context
        params = (
            context.tenant_id,
            context.business_id,
            actor,
            context.proposal_id,
            prepared.request.request.request_id,
        )
        before = await self.prepare(*params, candidate=candidate)
        if not hmac.compare_digest(before.request.request_hash, prepared.request.request_hash) or before != prepared:
            raise AuthError("VISUAL_CONTEXT_CHANGED", 409)
        result = await asyncio.to_thread(
            render_brand_overlay,
            scene,
            kit=before.kit,
            format=context.format,  # type: ignore[arg-type]
            statement=before.statement,
            cta=before.cta,
            logo=before.logo,
        )
        after = await self.prepare(*params, candidate=candidate)
        if not hmac.compare_digest(after.request.request_hash, prepared.request.request_hash) or after != before:
            raise AuthError("VISUAL_CONTEXT_CHANGED", 409)
        return result
