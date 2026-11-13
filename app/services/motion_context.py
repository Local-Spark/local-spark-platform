"""Owner-scoped immutable context for HTML motion, independent of photo proposals."""

import hashlib
import hmac
import json
from typing import Any, cast
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.schemas.motion_production import MotionRequest
from app.services.auth import AuthError
from app.services.brand_kits import BrandKitService
from app.services.editorial_context import EditorialContextService
from app.services.motion_corrections import CORRECTION_POLICY, correction_enabled
from app.services.motion_creative import MEDIA_VISIBILITY_POLICY, alternating_creative_contract
from app.services.motion_evolution import capture_evolution
from app.services.motion_generation import (
    ASSET_INFORMED_GENERATION_CONTRACT,
    PRODUCTION_GENERATION_CONTRACT,
    PROPOSED_GENERATION_CONTRACT,
    provided_output_enabled,
)
from app.services.motion_illustration_policy import illustration_policy
from app.services.motion_preparation import PREPARATION_RULES, PRODUCTION_PREPARATION_RULES, PROPOSED_PREPARATION_RULES
from app.services.motion_quality import QUALITY_CONTRACT
from app.services.motion_repertoire import capture_repertoire
from app.services.motion_review import compact_review_enabled, review_contract
from app.services.motion_skills import load_motion_skill, resolve_html_motion_skill, resolve_motion_skill
from app.services.motion_sound_analysis import ANALYSIS_CONTRACT
from app.services.motion_sound_library import capture_sound_library
from app.services.motion_speech_policy import speech_policy
from app.services.motion_staging import STAGING_CONTRACT
from app.services.motion_styles import html_style_card, list_motion_styles
from app.services.motion_temporal import POLICY_V3, POLICY_V4
from app.services.motion_visual_direction import supplied_direction
from app.services.reference_generation_context import capture_generation_context

HTML_EXECUTOR_CONTRACT = {
    "version": "html-motion-executor-v1",
    "capabilities": (
        "O executor isolado executa HTML com estilos inline e scene_init JavaScript determinístico no Chromium; "
        "aceita grafismos originais em HTML, SVG e Canvas, além dos recursos locais explicitamente fornecidos. "
        "O plano de áudio pode usar a faixa original e misturar faixas autorizadas; o resultado é codificado em AAC "
        "e não preserva identidade binária do áudio. Transições e movimento não se limitam a cut/fade."
    ),
    "integration_policy": (
        "Nesta integração, preserve a gravação inteira, sua ação e voz, e o kit confirmado. "
        "O modelo recebe apenas quadros amostrados, sem escuta; não invente transcrição ou sincronismo. "
        "O código usa assets autorizados e isolamento existente, sem rede, imports ou bibliotecas não fornecidas. "
        "Capacidade técnica não comprova acabamento nem aprovação humana."
    ),
}


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def capture_motion_guidance(
    request: MotionRequest,
    *,
    illustration_generation: dict[str, Any] | None = None,
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Shared product assembler; local file reads only, no credentials, database or model calls."""
    creative = (
        previous.get("creative_contract")
        if previous is not None
        else alternating_creative_contract(provided=request.scene_direction is not None)
    )
    generation = (
        previous.get("generation_contract")
        if previous is not None
        else dict(PRODUCTION_GENERATION_CONTRACT)
        if request.propose_direction and request.evolution is None
        else dict(PROPOSED_GENERATION_CONTRACT)
        if request.propose_direction
        else dict(ASSET_INFORMED_GENERATION_CONTRACT)
        if request.scene_direction is not None
        else None
    )
    if request.evolution is not None and previous is None:
        creative = {**cast(dict[str, Any], creative), "temporal_review": dict(POLICY_V3)}
    if generation is not None and previous is None and not request.propose_direction:
        creative = dict(cast(dict[str, Any], creative))
        creative["scene_direction_rules"] = creative["scene_direction_rules"].replace(
            "Devolva scene_direction com os mesmos campos, valores e IDs fornecidos. Isso registra fidelidade "
            "à entrada, não aprovação humana.",
            "O servidor preserva a direção fornecida integralmente; não a repita na saída. "
            "Isso não significa aprovação humana.",
        )
    if request.propose_direction and previous is None:
        creative = dict(cast(dict[str, Any], creative))
        creative["version"] = "reel-creative-v8"
        for field in ("scene_direction_rules", "motion_plan_rules", "direction"):
            creative[field] = (
                creative[field]
                .replace(
                    "na mesma resposta que motion_plan e HTML/scene_init, sem chamada extra",
                    "na etapa plan, junto ao motion_plan; código somente depois da aprovação exata",
                )
                .replace(
                    "Entregue motion_plan junto com HTML/scene_init na mesma geração.",
                    "Entregue motion_plan na etapa plan, sem código.",
                )
                .replace(
                    "Implemente esse plano no HTML/scene_init.",
                    "Somente após aprovação exata, implemente esse plano no HTML/scene_init.",
                )
            )
    quality = (
        {"quality_contract": QUALITY_CONTRACT if previous is None else previous.get("quality_contract")}
        if generation == PRODUCTION_GENERATION_CONTRACT
        else {}
    )
    if quality and previous is None:
        creative = dict(cast(dict[str, Any], creative))
        creative["version"] = "reel-creative-v9"
        for key in ("calibration", "counterexample", "reference_scope"):
            creative.pop(key, None)
    provided_output_enabled(
        {
            **quality,
            "generation_contract": generation,
            "creative_contract": creative,
            "request": request.model_dump(mode="json"),
            "illustration_generation": illustration_generation,
        }
    )
    review_policy = review_contract() if previous is None else previous.get("review_contract")
    compact_review_enabled({"review_contract": review_policy})
    correction_policy = dict(CORRECTION_POLICY) if previous is None else previous.get("correction_contract")
    correction_enabled({"correction_contract": correction_policy})
    supplied_direction(
        {
            "request": request.model_dump(mode="json"),
            "creative_contract": creative,
            "illustration_generation": illustration_generation,
        }
    )
    html_contract = previous is None or "executor_contract" in previous
    if html_contract and previous is not None:
        # Keep the captured HTML skill version, including pre-construction v2 requests.
        skill_id, skill_hash = previous["skill"]["id"], previous["skill"]["sha256"]
        skill_text = load_motion_skill(skill_id, skill_hash, request.format)
    else:
        skill_id, skill_hash, skill_text = (
            resolve_html_motion_skill(request.format) if html_contract else resolve_motion_skill(request.format)
        )
    styles = []
    for style in list_motion_styles():
        card = html_style_card(style.content) if html_contract else json.loads(style.content)
        for item in card["sources"]:
            item.pop("path", None)
            item.pop("ref", None)
        styles.append(
            {
                "id": style.id,
                "version": style.version,
                "sha256": style.sha256,
                **({"projection": "html-executor-style-v1"} if html_contract else {}),
                "card": card,
            }
        )
    staging = (
        {"staging_contract": STAGING_CONTRACT}
        if previous is None and quality and request.repertoire_id in (None, "business-reel-v5")
        else {"staging_contract": previous["staging_contract"]}
        if previous is not None and "staging_contract" in previous
        else {}
    )
    if staging and previous is None:
        creative = {**cast(dict[str, Any], creative), "temporal_review": dict(POLICY_V4)}
    if previous is None and request.structural_floor and isinstance(creative, dict):
        creative = dict(creative)
        creative["motion_plan_rules"] = (
            creative.get("motion_plan_rules", "")
            + " Piso estrutural v3: pelo menos três cenas com structural_scale distintas "
            "(macro, medium, card), papéis establish/extract/invite, texto ancorado por "
            "related_element_ids num asset da cena, hold >= 700 ms, hero_height_ratio >= 0.18, "
            "contrast_ratio >= 4.5, mechanism_ids dentre ellipse_to_glyph, axis_type_in, "
            'mask_open_from_point e plate_cta no CTA. HTML com um único data-stage="media"; '
            "cada mechanism_id vira data-mechanism, data-start e data-end. scene_init chama "
            "StructuralFloorV1.apply(ms) dentro de window.seek. Texto fora desse stage é recusado."
        )
    repertoire_id = request.repertoire_id or ("business-reel-v5" if staging else None)
    return {
        **staging,
        **quality,
        **(
            {"audio_analysis_contract": ANALYSIS_CONTRACT}
            if quality and previous is None
            else {"audio_analysis_contract": previous["audio_analysis_contract"]}
            if previous is not None and "audio_analysis_contract" in previous
            else {}
        ),
        **(
            {
                "preparation_contract": PRODUCTION_PREPARATION_RULES
                if quality
                else PROPOSED_PREPARATION_RULES
                if request.propose_direction
                else PREPARATION_RULES
            }
            if request.preparation is not None
            else {}
        ),
        **({"sound_library": capture_sound_library(request.sound_library_id)} if request.sound_library_id else {}),
        **({"structural_floor": request.structural_floor} if request.structural_floor else {}),
        **(
            {
                "executor_contract": previous["executor_contract"]
                if previous is not None
                else {
                    **HTML_EXECUTOR_CONTRACT,
                    "version": "html-motion-executor-v2",
                    "integration_policy": MEDIA_VISIBILITY_POLICY,
                }
            }
            if html_contract
            else {}
        ),
        "creative_contract": creative,
        **({"generation_contract": generation} if generation is not None else {}),
        **({"review_contract": review_policy} if review_policy is not None else {}),
        **({"correction_contract": correction_policy} if correction_policy is not None else {}),
        "request": request.model_dump(mode="json"),
        **({"illustration_generation": illustration_generation} if illustration_generation is not None else {}),
        "skill": {"id": skill_id, "sha256": skill_hash, "instructions": skill_text},
        "styles": styles,
        **({"repertoire": capture_repertoire(repertoire_id)} if repertoire_id else {}),
    }


class MotionContext:
    def __init__(self, settings: Settings):
        self.settings = settings

    def cipher(self) -> Fernet:
        if self.settings.meta_encryption_key is None:
            raise AuthError("MOTION_ENCRYPTION_REQUIRED", 409)
        return Fernet(self.settings.meta_encryption_key.get_secret_value().encode())

    def seal(self, value: object) -> str:
        return self.cipher().encrypt(canonical(value).encode()).decode()

    def open(self, value: str) -> dict[str, Any]:
        try:
            decoded = json.loads(self.cipher().decrypt(value.encode()))
            if not isinstance(decoded, dict):
                raise ValueError
            return decoded
        except (InvalidToken, ValueError, UnicodeDecodeError):
            raise AuthError("MOTION_SNAPSHOT_INVALID", 409) from None

    def fingerprint(self, value: object) -> str:
        self.cipher()
        assert self.settings.meta_encryption_key is not None
        return hmac.new(
            self.settings.meta_encryption_key.get_secret_value().encode(), canonical(value).encode(), hashlib.sha256
        ).hexdigest()

    def require_qualification(self, business: UUID, source: UUID) -> None:
        settings = self.settings
        if (
            settings.environment not in {"development", "testing"}
            or not settings.motion_execution_enabled
            or settings.motion_ai_mode == "disabled"
            or settings.motion_local_qualification_business_id != business
            or source not in settings.motion_local_qualification_asset_ids
        ):
            raise AuthError("MOTION_LOCAL_QUALIFICATION_REQUIRED", 409)
        if (
            settings.motion_ai_reservation_usd_micros <= 0
            or settings.motion_request_budget_usd_micros < 2 * settings.motion_ai_reservation_usd_micros
        ):
            raise AuthError("MOTION_BUDGET_REQUIRED", 409)
        self.cipher()

    async def capture(
        self,
        session: AsyncSession,
        tenant: UUID,
        business: UUID,
        request: MotionRequest,
        *,
        previous: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if request.storyboard and not self.settings.motion_storyboard_enabled:
            raise AuthError("MOTION_STORYBOARD_NOT_CONFIGURED", 409)
        params = {"tenant": tenant, "business": business, "source": request.source_asset_id}
        source = (
            (
                await session.execute(
                    text("""SELECT id,kind,object_key,mime_type,size_bytes,sha256
          FROM whatsapp_material_assets WHERE tenant_id=:tenant AND business_id=:business AND id=:source
            AND kind='video' AND mime_type='video/mp4' AND object_key IS NOT NULL AND sha256 IS NOT NULL
            AND delete_requested_at IS NULL AND delete_lease_until IS NULL
            AND (expires_at IS NULL OR expires_at>clock_timestamp()) FOR SHARE"""),
                    params,
                )
            )
            .mappings()
            .one_or_none()
        )
        if source is None:
            raise AuthError("MOTION_SOURCE_UNAVAILABLE", 409)
        if request.speech_timing is not None and request.speech_timing.source_sha256 != source["sha256"]:
            raise AuthError("MOTION_SPEECH_SOURCE_CHANGED", 409)
        art_policy = (
            illustration_policy(self.settings) if previous is None or "illustration_generation" in previous else None
        )
        guidance = capture_motion_guidance(request, illustration_generation=art_policy, previous=previous)
        if request.speech_timing is None and (previous is None or "speech_recognition" in previous):
            policy = speech_policy(self.settings)
            if policy is not None:
                guidance["speech_recognition"] = policy
        photos = []
        photo_ids = request.collection_photo_ids
        if request.propose_direction and not photo_ids:
            photo_ids = tuple(
                (
                    await session.scalars(
                        text("""SELECT id FROM business_collection_photos
                WHERE tenant_id=:tenant AND business_id=:business AND state='ready' AND status='active'
                AND rights_scope='business_collection_confirmed' AND delete_owner IS NULL
                AND delete_lease_until IS NULL ORDER BY id LIMIT 4 FOR SHARE"""),
                        params,
                    )
                ).all()
            )
        for photo_id in photo_ids:
            photo = (
                (
                    await session.execute(
                        text("""SELECT id,version,title,item_id,space_kind,object_key,mime_type,size_bytes,sha256
                    FROM business_collection_photos WHERE tenant_id=:tenant AND business_id=:business AND id=:photo
                    AND state='ready' AND status='active' AND rights_scope='business_collection_confirmed'
                    AND delete_owner IS NULL AND delete_lease_until IS NULL FOR SHARE"""),
                        {"tenant": tenant, "business": business, "photo": photo_id},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if photo is None:
                raise AuthError("MOTION_COLLECTION_PHOTO_UNAVAILABLE", 409)
            photos.append(dict(photo))
        audio_materials = []
        for audio_id in sorted({event.asset_id for event in request.sound_events}):
            material = (
                (
                    await session.execute(
                        text("""SELECT id,object_key,mime_type,size_bytes,sha256 FROM whatsapp_material_assets
                          WHERE tenant_id=:tenant AND business_id=:business AND id=:audio AND kind='audio'
                            AND mime_type IN ('audio/wav','audio/ogg','audio/mpeg')
                            AND object_key IS NOT NULL AND sha256 IS NOT NULL AND size_bytes>0
                            AND delete_requested_at IS NULL AND delete_lease_until IS NULL
                            AND (expires_at IS NULL OR expires_at>clock_timestamp()) FOR SHARE"""),
                        {"tenant": tenant, "business": business, "audio": audio_id},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if material is None:
                raise AuthError("MOTION_AUDIO_MATERIAL_UNAVAILABLE", 409)
            audio_materials.append(dict(material))
        kit = (await BrandKitService._state(session, tenant, business)).confirmed
        if kit is None:
            raise AuthError("MOTION_CONFIRMED_KIT_REQUIRED", 409)
        context = EditorialContextService._present(await EditorialContextService._version(session, tenant, business))
        current_date = await session.scalar(
            text("""SELECT (clock_timestamp() AT TIME ZONE timezone)::date
          FROM businesses WHERE tenant_id=:tenant AND id=:business"""),
            params,
        )
        references = await capture_generation_context(session, business)
        evolution = await capture_evolution(session, tenant, business, request, self.open)
        logo = None
        if kit.overrides.logo_asset_id is not None:
            logo_row = (
                (
                    await session.execute(
                        text("""SELECT id,object_key,mime_type,size_bytes,sha256
              FROM business_brand_kit_logos WHERE tenant_id=:tenant AND business_id=:business AND id=:logo
                AND state='ready' AND rights_scope='business_brand_confirmed'"""),
                        {**params, "logo": kit.overrides.logo_asset_id},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if logo_row is None:
                raise AuthError("MOTION_LOGO_UNAVAILABLE", 409)
            logo = dict(logo_row)
        return cast(
            dict[str, Any],
            json.loads(
                canonical(
                    {
                        "schema": "html-motion-context-v1",
                        **guidance,
                        "tenant_id": tenant,
                        "business_id": business,
                        "source": dict(source),
                        **({"evolution": evolution} if evolution is not None else {}),
                        **({"collection_photos": photos} if photos else {}),
                        **({"audio_materials": audio_materials} if audio_materials else {}),
                        "logo": logo,
                        "kit": kit.model_dump(mode="json"),
                        "context_version": context.version,
                        "preferences": context.preferences.model_dump(mode="json", exclude={"reference_search"}),
                        "confirmed_facts": [
                            {
                                **fact.model_dump(mode="json", exclude={"source_detail"}),
                                "provenance": {"kind": "owner_context", "version": context.version},
                            }
                            for fact in context.facts
                            if fact.valid_until is None or fact.valid_until >= current_date
                        ],
                        "references": references.model_dump(mode="json"),
                        "reference_context": references.model_input(),
                        "execution": {
                            "mode": self.settings.motion_ai_mode,
                            "model": self.settings.motion_ai_model,
                            "renderer_image": self.settings.motion_renderer_image,
                            "max_output_tokens": self.settings.motion_ai_max_output_tokens,
                            "input_rate": self.settings.motion_ai_input_usd_micros_per_million_tokens,
                            "output_rate": self.settings.motion_ai_output_usd_micros_per_million_tokens,
                            "reservation": self.settings.motion_ai_reservation_usd_micros,
                            "request_budget": self.settings.motion_request_budget_usd_micros,
                            "max_corrections": self.settings.motion_max_corrections,
                        },
                    }
                )
            ),
        )
