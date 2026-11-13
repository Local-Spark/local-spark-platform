"""Provider-independent grounding of a critique in the actual compared artifacts."""

from copy import deepcopy
from typing import Any

from app.schemas.motion_production import MotionReview
from app.schemas.motion_review_wire import (
    CompactMotionReview,
    EvolutionMotionReview,
    LinkedMotionReview,
    LocalizedMotionReview,
    StagedMotionReview,
)
from app.services.auth import AuthError
from app.services.motion_corrections import correction_enabled, validate_location
from app.services.motion_creative import CREATIVE_CRITERIA, SUPPORTED_CREATIVE_CONTRACTS
from app.services.motion_protocols import MotionModelRequest
from app.services.motion_staging import staging_enabled
from app.services.motion_temporal import TEMPORAL_CRITERIA, temporal_payload


class MotionReviewError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


REVIEW_CONTRACT: dict[str, Any] = {
    "version": "motion-review-v2",
    "wire_format": "compact-evidence-ids-v1",
    "scope": (
        "Targets orientam geração, crítica e correção. Response_rules e wire_format aplicam-se somente à crítica; "
        "geração/correção continuam entregando a composição conforme seu schema."
    ),
    "targets": {
        "mandatory": "Fatos, kit, legibilidade e integridade técnica são obrigatórios; não provam acabamento.",
        "brief_alignment": (
            "Conferir pedido e direção, fornecida ou proposta; sem inventar aprovação nem substituir direção fornecida."
        ),
        "narrative_progression": "Observar mudança de função e passagem de atenção, não apenas troca de frase/cartela.",
        "motion_role": (
            "Relacionar transformação a revelação, conexão ou resultado; deslocamento/pixels não medem qualidade."
        ),
        "visual_development": (
            "Observar hierarquia tipográfica, escala/profundidade, relações entre camadas e gravação e "
            "ação com resultado. "
            "Referências orientam mecanismos; não exigem sua identidade, órbita, neon, ícones ou desenho. "
            "Acabamento infantil deve ser descrito por defeito observável, não pelo simples uso de ilustração."
        ),
        "temporal": (
            "Continuidade, oclusão, leitura e coordenação somente nos eventos amostrados; áudio permanece uncertain."
        ),
    },
    "response_rules": (
        "Somente na crítica, retorne JSON compacto: evidence e preference_evidence usam IDs do review_evidence_index. "
        "Cada issue usa evidence_id current; o serviço recupera version/at_ms/sha256, não os repita na saída. "
        "As regras de quadros e sequências continuam valendo para os IDs. Não cite finish_reference como "
        "prova da peça. "
        "Uma observação curta por check, brief_basis apenas aponta o requisito. Até seis problemas "
        "distintos priorizados, "
        "sem repetir o mesmo defeito; até quatro limitações agrupadas. Se houver mais problemas, declare "
        "o escopo limitado. "
        "Cite só os quadros necessários, sem duplicar IDs no mesmo campo. Não repita HTML, plano, direção ou código. "
        "Os limites de tamanho não autorizam omitir checks obrigatórios, encobrir defeitos ou declarar aprovação."
    ),
    "correction_rules": (
        "Problema acionável deve indicar cena/elemento, evidência atual e ajuste realizável com os "
        "recursos autorizados. "
        "Falta de evidência gera uncertain/insufficient_evidence, não refação. Separe ganho técnico de ganho criativo. "
        "Se a solução exigir nova direção, fatos, materiais ou recursos não autorizados, não a marque acionável; "
        "registre a dependência e use reject ou insufficient_evidence conforme defeito demonstrado ou "
        "falta de evidência. "
        "Adequate não é aceite humano. Correção deve preservar direção fornecida, gravação, voz e kit."
    ),
    "input_projection": "review-composition-without-code-v1",
}


LINKED_REVIEW_CONTRACT: dict[str, Any] = {
    **REVIEW_CONTRACT,
    "version": "motion-review-v3",
    "wire_format": "compact-linked-evidence-v2",
    "response_rules": REVIEW_CONTRACT["response_rules"]
    + (
        " Cada creative_check inclui issue_indices: índices base zero dos problemas em issues que "
        "fundamentam esse not_met. O serviço inclui a evidência current desses problemas no check. "
        "Use [] em met/uncertain. Links exigem mesmo critério: brief_alignment/visual_development "
        "ligam composition; narrative_progression/motion_role ligam motion. Para needs_revision, "
        "todo not_met deve ligar problema major/blocking acionável. Não invente evidência; "
        "checks temporais continuam exigindo sequências amostradas suficientes."
    ),
}


def review_contract() -> dict[str, Any]:
    return deepcopy(LINKED_REVIEW_CONTRACT)


def review_wire_model(context: dict[str, Any]) -> type[CompactMotionReview]:
    if staging_enabled(context):
        return StagedMotionReview
    if context.get("evolution") is not None:
        return EvolutionMotionReview
    if correction_enabled(context):
        return LocalizedMotionReview
    return LinkedMotionReview if context.get("review_contract") == LINKED_REVIEW_CONTRACT else CompactMotionReview


def compact_review_enabled(context: dict[str, Any]) -> bool:
    policy = context.get("review_contract")
    if policy is None:
        return False
    if policy not in (REVIEW_CONTRACT, LINKED_REVIEW_CONTRACT):
        raise MotionReviewError("MOTION_REVIEW_CONTRACT_UNKNOWN")
    return True


def review_evidence_index(request: MotionModelRequest) -> dict[str, Any]:
    """Only actual piece/source frames get aliases; finish references never do."""
    return {
        f"{version}-{index}": {"version": version, "at_ms": frame.ms, "sha256": frame.sha256}
        for version, frames in (
            ("current", request.frames),
            ("previous", request.incumbent_frames),
            ("source", request.source_frames),
            ("baseline", request.baseline_frames),
        )
        for index, frame in enumerate(frames)
    }


def decode_review(request: MotionModelRequest, raw: str) -> MotionReview:
    """Restore the durable shape, then apply the same grounding rules as every provider."""
    if not compact_review_enabled(request.context):
        return MotionReview.model_validate_json(raw)
    data = review_wire_model(request.context).model_validate_json(raw).model_dump(mode="json")
    index = review_evidence_index(request)

    def expand(ids: list[str]) -> list[dict[str, Any]]:
        if len(ids) != len(set(ids)) or any(id not in index for id in ids):
            raise MotionReviewError("MOTION_REVIEW_EVIDENCE_ID_INVALID")
        return [index[id] for id in ids]

    if request.context.get("review_contract") == LINKED_REVIEW_CONTRACT:
        for check in data["creative_checks"]:
            links = check.pop("issue_indices")
            if len(links) != len(set(links)) or any(i >= len(data["issues"]) for i in links):
                raise MotionReviewError("MOTION_CREATIVE_ISSUE_LINK_INVALID")
            if links and check["status"] != "not_met":
                raise MotionReviewError("MOTION_CREATIVE_ISSUE_LINK_INVALID")
            # Validate direct evidence first; explicit links may overlap but cannot hide duplicates.
            expand(check["evidence"])
            for i in links:
                issue = data["issues"][i]
                if issue["criterion"] != CREATIVE_CRITERIA[check["name"]]:
                    raise MotionReviewError("MOTION_CREATIVE_ISSUE_LINK_INVALID")
                ref = issue["evidence_id"]
                if ref not in check["evidence"]:
                    check["evidence"].append(ref)
            if (
                check["status"] == "not_met"
                and data["verdict"] == "needs_revision"
                and not any(
                    data["issues"][i]["actionable"] and data["issues"][i]["severity"] in {"major", "blocking"}
                    for i in links
                )
            ):
                raise MotionReviewError("MOTION_CREATIVE_CORRECTION_UNGROUNDED")

    for group in ("criteria", "creative_checks", "temporal_checks"):
        for check in data[group]:
            check["evidence"] = expand(check["evidence"])
    for check in data.get("baseline_checks", []):
        check["evidence"] = expand(check["evidence"])
    data["preference_evidence"] = expand(data["preference_evidence"])
    for issue in data["issues"]:
        ref = expand([issue.pop("evidence_id")])[0]
        if ref["version"] != "current":
            raise MotionReviewError("MOTION_REVIEW_ISSUE_VERSION_INVALID")
        issue.update(at_ms=ref["at_ms"], evidence_sha256=ref["sha256"])
    return MotionReview.model_validate(data)


def validate_review(request: MotionModelRequest, review: MotionReview) -> None:
    compact = compact_review_enabled(request.context)
    if staging_enabled(request.context):
        for issue in review.issues:
            if issue.repair_kind is None or (issue.actionable and issue.repair_kind != "implementation"):
                raise MotionReviewError("MOTION_REPAIR_KIND_INVALID")
        if any(i.repair_kind in {"direction", "material"} and i.severity != "minor" for i in review.issues):
            if review.verdict != "reject":
                raise MotionReviewError("MOTION_PLAN_REVISION_REQUIRED")
    if correction_enabled(request.context):
        for issue in review.issues:
            if issue.actionable and issue.severity != "minor":
                if request.composition is None:
                    raise MotionReviewError("MOTION_CORRECTION_COMPOSITION_REQUIRED")
                try:
                    validate_location(request.composition, issue)
                except AuthError as exc:
                    raise MotionReviewError(exc.code) from None
    available = {
        (version, frame.ms, frame.sha256)
        for version, frames in (
            ("source", request.source_frames),
            ("current", request.frames),
            ("previous", request.incumbent_frames),
            ("baseline", request.baseline_frames),
        )
        for frame in frames
    }
    references = [ref for criterion in review.criteria for ref in criterion.evidence]
    references.extend(review.preference_evidence)
    references.extend(ref for check in review.creative_checks for ref in check.evidence)
    references.extend(ref for check in review.temporal_checks for ref in check.evidence)
    references.extend(ref for check in review.baseline_checks for ref in check.evidence)
    if any((ref.version, ref.at_ms, ref.sha256) not in available for ref in references):
        raise MotionReviewError("MOTION_REVIEW_UNSENT_EVIDENCE")
    if any(("current", issue.at_ms, issue.evidence_sha256) not in available for issue in review.issues):
        raise MotionReviewError("MOTION_REVIEW_UNSENT_EVIDENCE")
    versions = {ref.version for ref in review.preference_evidence if ref.version in {"current", "previous"}}
    if review.preferred == "previous" and not request.incumbent_frames:
        raise MotionReviewError("MOTION_REVIEW_INVALID_PREFERENCE")
    if review.preferred == "current":
        required = {"current", "previous"} if request.incumbent_frames else {"current"}
        if versions != required:
            raise MotionReviewError("MOTION_REVIEW_INVALID_PREFERENCE")

    contract = request.context.get("creative_contract")
    if contract is not None:
        if not isinstance(contract, dict) or contract.get("version") not in SUPPORTED_CREATIVE_CONTRACTS:
            raise MotionReviewError("MOTION_CREATIVE_CONTRACT_UNKNOWN")
        if len(review.creative_checks) != 4 or {check.name for check in review.creative_checks} != set(
            CREATIVE_CRITERIA
        ):
            raise MotionReviewError("MOTION_CREATIVE_CHECKS_REQUIRED")
    for check in review.creative_checks:
        if check.status == "uncertain":
            continue
        moments = {ref.at_ms for ref in check.evidence if ref.version == "current"}
        minimum = 1 if check.name == "brief_alignment" else 2
        if len(moments) < minimum:
            raise MotionReviewError("MOTION_CREATIVE_TEMPORAL_EVIDENCE_REQUIRED")
        if (
            check.status == "not_met"
            and review.verdict == "needs_revision"
            and not any(
                issue.actionable
                and issue.severity in {"major", "blocking"}
                and issue.criterion == CREATIVE_CRITERIA[check.name]
                and (
                    not compact
                    or any(
                        ref.version == "current" and ref.at_ms == issue.at_ms and ref.sha256 == issue.evidence_sha256
                        for ref in check.evidence
                    )
                )
                for issue in review.issues
            )
        ):
            raise MotionReviewError("MOTION_CREATIVE_CORRECTION_UNGROUNDED")
    validate_temporal_review(request, review)
    validate_baseline_review(request, review)


def validate_baseline_review(request: MotionModelRequest, review: MotionReview) -> None:
    baseline = request.context.get("evolution")
    if baseline is None:
        if review.baseline_checks or review.baseline_video_sha256 is not None:
            raise MotionReviewError("MOTION_EVOLUTION_REVIEW_UNEXPECTED")
        return
    if (
        review.baseline_video_sha256 != baseline["selection"]["baseline_video_sha256"]
        or len(review.baseline_checks) != 5
        or {c.dimension for c in review.baseline_checks} != {"meaning", "recording", "space", "rhythm", "identity"}
    ):
        raise MotionReviewError("MOTION_EVOLUTION_REVIEW_REQUIRED")
    for check in review.baseline_checks:
        if check.result == "uncertain":
            continue
        minimum = 1 if check.dimension == "identity" else 2
        if any(
            len({r.at_ms for r in check.evidence if r.version == version}) < minimum
            for version in ("current", "baseline")
        ):
            raise MotionReviewError("MOTION_EVOLUTION_COMPARATIVE_EVIDENCE_REQUIRED")


def validate_temporal_review(request: MotionModelRequest, review: MotionReview) -> None:
    manifest = temporal_payload(
        request.context, request.composition, request.frames, request.incumbent_composition, request.incumbent_frames
    )
    if manifest is None:
        if review.temporal_checks:
            raise MotionReviewError("MOTION_TEMPORAL_CONTRACT_REQUIRED")
        return
    if len(review.temporal_checks) != 4 or {check.name for check in review.temporal_checks} != set(TEMPORAL_CRITERIA):
        raise MotionReviewError("MOTION_TEMPORAL_CHECKS_REQUIRED")
    windows = {event["id"]: event for event in manifest["current"]["events"]}

    def covered(event: dict[str, Any], refs: set[tuple[str, int, str]]) -> bool:
        sequence = [(ref["version"], ref["at_ms"], ref["sha256"]) for ref in event["evidence"]]
        return bool(
            event["complete"] and sequence[0] in refs and sequence[-1] in refs and len(refs.intersection(sequence)) >= 3
        )

    for check in review.temporal_checks:
        if (
            check.status == "pass"
            and manifest["current"]["policy"]["version"] == "motion-temporal-v4"
            and not manifest["current"]["coverage_complete"]
        ):
            raise MotionReviewError("MOTION_TEMPORAL_COVERAGE_REQUIRED")
        ids = set(check.event_ids)
        if len(ids) != len(check.event_ids) or not ids <= windows.keys():
            raise MotionReviewError("MOTION_TEMPORAL_EVENT_UNKNOWN")
        refs: set[tuple[str, int, str]] = {(ref.version, ref.at_ms, ref.sha256) for ref in check.evidence}
        if check.status != "uncertain":
            if not ids or any(not covered(windows[id], refs) for id in ids):
                raise MotionReviewError("MOTION_TEMPORAL_SEQUENCE_REQUIRED")
            if check.status == "pass" and ids != windows.keys():
                raise MotionReviewError("MOTION_TEMPORAL_COVERAGE_REQUIRED")
            if (
                check.status == "pass"
                and manifest["current"]["policy"]["version"]
                in {"motion-temporal-v2", "motion-temporal-v3", "motion-temporal-v4"}
                and (manifest["current"]["omitted_transitions"] or manifest["current"]["uncovered_scene_ids"])
            ):
                raise MotionReviewError("MOTION_TEMPORAL_COVERAGE_REQUIRED")
        if check.issue_indices and check.status != "fail":
            raise MotionReviewError("MOTION_TEMPORAL_CORRECTION_UNGROUNDED")
        if check.status == "fail" and review.verdict == "needs_revision" and not check.issue_indices:
            raise MotionReviewError("MOTION_TEMPORAL_CORRECTION_UNGROUNDED")
        for index in check.issue_indices:
            if index < 0 or index >= len(review.issues):
                raise MotionReviewError("MOTION_TEMPORAL_CORRECTION_UNGROUNDED")
            issue = review.issues[index]
            event_refs = {(r["version"], r["at_ms"], r["sha256"]) for id in ids for r in windows[id]["evidence"]}
            if (
                not issue.actionable
                or issue.severity == "minor"
                or issue.criterion != TEMPORAL_CRITERIA[check.name]
                or ("current", issue.at_ms, issue.evidence_sha256) not in refs.intersection(event_refs)
            ):
                raise MotionReviewError("MOTION_TEMPORAL_CORRECTION_UNGROUNDED")
    linked = {index for check in review.temporal_checks if check.status == "fail" for index in check.issue_indices}
    creative_motion_failure = any(
        check.status == "not_met" and CREATIVE_CRITERIA[check.name] == "motion" for check in review.creative_checks
    )
    for index, issue in enumerate(review.issues):
        if (
            issue.actionable
            and issue.severity != "minor"
            and issue.criterion == "motion"
            and index not in linked
            and not creative_motion_failure
        ):
            raise MotionReviewError("MOTION_TEMPORAL_CORRECTION_UNGROUNDED")
    if review.preferred == "current" and request.incumbent_frames:
        refs = {(r.version, r.at_ms, r.sha256) for r in review.preference_evidence}
        for version in ("current", "previous"):
            group = manifest[version]
            if not group or not any(covered(event, refs) for event in group["events"]):
                raise MotionReviewError("MOTION_TEMPORAL_COMPARISON_REQUIRED")
