"""Recording to reviewed private Reel; all IO follows committed one-shot claims."""

import base64
import hashlib
from dataclasses import asdict, dataclass
from typing import Any, Protocol
from uuid import UUID, uuid5

from sqlalchemy import text

from app.adapters.material_media import FetchedMedia, MaterialStore
from app.adapters.motion_html_renderer import RenderBundle, RenderedMotion
from app.adapters.motion_inputs import PreparedMotionInput
from app.db.session import Database
from app.schemas.motion_production import HTMLMotionComposition, MotionReview
from app.services.auth import AuthError
from app.services.content_pieces import PieceArtifact, _event, write_version
from app.services.motion_audio import validate_original_branch
from app.services.motion_construction import construct_motion, construct_motion_with_assets, plan_motion
from app.services.motion_corrections import (
    compare_frames,
    correction_enabled,
    correction_scope,
    fingerprint,
    review_diagnostics,
    validate_candidate,
)
from app.services.motion_effects import MotionEffects
from app.services.motion_elements import elements_hash
from app.services.motion_evolution import evolution_verdict
from app.services.motion_generation import asset_informed_enabled
from app.services.motion_illustrations import IllustrationProvider, MotionIllustrations
from app.services.motion_movement import movement_hash
from app.services.motion_plan import validate_motion_plan
from app.services.motion_protocols import MotionModelProvider, MotionModelRequest, MotionRenderer
from app.services.motion_requests import MotionRequestService
from app.services.motion_review import validate_review
from app.services.motion_speech_recognition import MotionSpeechRecognition, SpeechRecognizer
from app.services.motion_storyboards import MotionStoryboards
from app.services.motion_temporal import evidence_manifest, sample_times, temporal_enabled
from app.services.visual_pending_changes import VisualPendingChanges
from app.services.visual_pending_scripts import apply_pending_script_changes
from app.workflows.contracts import BusinessEvent


class MotionInputs(Protocol):
    async def prepare(self, snapshot: dict[str, Any]) -> PreparedMotionInput: ...


@dataclass(frozen=True)
class Candidate:
    number: int
    composition: HTMLMotionComposition
    rendered: RenderedMotion
    artifact: PieceArtifact
    review: MotionReview | None = None


def needs_correction(review: MotionReview) -> bool:
    return review.verdict == "needs_revision" and any(
        issue.actionable and issue.severity in {"blocking", "major"} for issue in review.issues
    )


def choose_candidate(previous: Candidate | None, current: Candidate, *, evolution: bool = False) -> Candidate | None:
    review = current.review
    if review is None or review.verdict != "adequate" or not review.mandatory_pass:
        return previous
    if evolution and evolution_verdict(review) != "improved":
        return previous
    if current.number > 0 and review.preferred != "current":
        return previous
    if previous is None:
        return current
    # Requiring a comparative verdict preserves the incumbent on uncertainty/ties.
    return current if review.preferred == "current" else previous


class MotionOrchestrator:
    def __init__(
        self,
        requests: MotionRequestService,
        cost_database: Database,
        provider: MotionModelProvider,
        renderer: MotionRenderer,
        inputs: MotionInputs,
        store: MaterialStore,
        *,
        illustration_provider: IllustrationProvider | None = None,
        speech_recognizer: SpeechRecognizer | None = None,
    ):
        self.requests, self.provider, self.renderer, self.inputs, self.store = (
            requests,
            provider,
            renderer,
            inputs,
            store,
        )
        self.effects = MotionEffects(requests, cost_database, store)
        self.illustration_provider = illustration_provider
        self.speech_recognizer = speech_recognizer

    async def run(self, event: BusinessEvent) -> str:
        from app.services.motion_checkpoint_execution import resume_checkpoint
        from app.services.motion_checkpoints import APPROVED, MotionCheckpoints

        tenant, business, actor, operation = map(
            UUID, (event.tenant_id, event.business_id, event.actor_id, event.operation_id)
        )
        for stage, kind in APPROVED.items():
            if UUID(event.event_id) == uuid5(operation, kind):
                return await resume_checkpoint(self, event, stage)
        if UUID(event.event_id) == uuid5(operation, "motion.storyboard_recapture_requested"):
            from app.services.motion_storyboard_recapture import MotionStoryboardRecapture

            return await MotionStoryboardRecapture(self).run(event)
        if UUID(event.event_id) == uuid5(operation, "motion.storyboard_approved"):
            return await self.resume(event)
        if UUID(event.event_id) != uuid5(operation, "motion.requested") and await MotionCheckpoints(
            self.requests, self.store
        ).is_recovery(event):
            return await resume_checkpoint(self, event, "plan")
        started = await self.requests.begin(tenant, business, actor, operation, UUID(event.event_id))
        if started is None:
            return "already_claimed"
        row, token = started
        try:
            prepared = await self.inputs.prepare(self.requests.context.open(row["snapshot_ciphertext"]))
            prepared = await MotionSpeechRecognition(self.effects, self.speech_recognizer).prepare(row, token, prepared)
            movement_hash(prepared.context)
            elements_hash(prepared.context)
            temporal_enabled(prepared.context)
            if prepared.context.get("request", {}).get("review_checkpoints"):
                plan = await plan_motion(self.effects, self.provider, row, token, prepared)
                await MotionCheckpoints(self.requests, self.store).capture(
                    row, token, "plan", prepared, plan, self.effects
                )
                return "awaiting_plan"
            illustrations = MotionIllustrations(self.effects, self.store, self.illustration_provider)
            if asset_informed_enabled(prepared.context):
                prepared, composition = await construct_motion_with_assets(
                    self.effects, self.provider, row, token, prepared, illustrations
                )
            else:
                composition = await construct_motion(self.effects, self.provider, row, token, prepared)
                prepared = await illustrations.prepare(row, token, prepared, composition)
            if prepared.context.get("request", {}).get("storyboard"):
                await MotionStoryboards(self.requests, self.store).capture(
                    row, token, prepared, composition, self.renderer, self.effects
                )
                return "awaiting_storyboard"
            return await self.produce(row, token, prepared, composition)
        except BaseException as exc:
            try:
                await self.fail(row, token, getattr(exc, "code", "MOTION_EXECUTION_FAILED"))
            except Exception:
                await self.effects.quarantine(row, token)
            raise

    async def resume(self, event: BusinessEvent) -> str:
        boards = MotionStoryboards(self.requests, self.store)
        started = await boards.begin_resume(event)
        if started is None:
            return "already_claimed"
        row, token, board = started
        failure_event_id = uuid5(UUID(event.event_id), "motion.failed")
        try:
            async with self.requests.database.transaction(row["tenant_id"], row["actor_id"]) as session:
                await self.requests._admission(session, row["tenant_id"], row["business_id"])
                await self.requests.locked_running(session, row, token)
            prepared = await self.inputs.prepare(self.requests.context.open(row["snapshot_ciphertext"]))
            prepared, composition = await boards.restore(row, board, prepared)
            return await self.produce(row, token, prepared, composition)
        except BaseException as exc:
            try:
                await self.fail(
                    row, token, getattr(exc, "code", "MOTION_EXECUTION_FAILED"), failure_event_id=failure_event_id
                )
            except Exception:
                await self.effects.quarantine(row, token, failure_event_id=failure_event_id)
            raise

    async def produce(
        self, row: dict[str, Any], token: UUID, prepared: PreparedMotionInput, composition: HTMLMotionComposition
    ) -> str:
        operation = row["operation_id"]
        initial_illustrations = composition.illustrations
        candidates: list[Candidate] = []
        incumbent: Candidate | None = None
        comparison: Candidate | None = None
        bounded = correction_enabled(prepared.context)
        scope: dict[str, Any] | None = None
        correction_base: Candidate | None = None
        number = 0
        while True:
            candidate = await self.render(row, token, prepared, number, composition)
            if bounded and correction_base is not None and scope is not None:
                try:
                    check = compare_frames(correction_base.rendered, candidate.rendered, scope)
                except AuthError as exc:
                    check = {"accepted": False, "reason": exc.code, "quality_validated": False}
                await self.effects.received(row, token, uuid5(operation, f"correction-check:{number}"), check)
                if not check["accepted"]:
                    candidates.append(candidate)
                    break
            review_request = MotionModelRequest(
                operation_id=uuid5(operation, f"review:{number}"),
                kind="review",
                context={**prepared.context, "render_diagnostics": review_diagnostics(candidate.rendered.diagnostics)},
                assets=prepared.assets,
                frames=candidate.rendered.evidence,
                source_frames=prepared.source_frames,
                asset_previews=prepared.asset_previews,
                reference_images=prepared.reference_images,
                baseline_frames=prepared.baseline_frames,
                composition=composition,
                incumbent_composition=comparison.composition if comparison else None,
                incumbent_frames=comparison.rendered.evidence if comparison else (),
            )
            reviewed = await self.effects.model(row, token, self.provider, review_request)
            if reviewed.review is None:
                raise AuthError("MOTION_REVIEW_RESULT_INVALID", 409)
            validate_review(review_request, reviewed.review)
            candidate = Candidate(number, composition, candidate.rendered, candidate.artifact, reviewed.review)
            await self.record_review(row, token, candidate)
            candidates.append(candidate)
            incumbent = choose_candidate(incumbent, candidate, evolution=prepared.context.get("evolution") is not None)
            if not needs_correction(reviewed.review) or number == row["max_corrections"]:
                break
            if number > 0 and reviewed.review.preferred != "current":
                break
            if not await self.effects.capacity_for_correction(row, token):
                break
            # Compare every candidate with the same actual incumbent (or initial
            # failed version if no technically usable incumbent exists yet).
            comparison = incumbent or candidates[0]
            scope = correction_scope(composition, reviewed.review) if bounded else None
            if scope is not None:
                # Missing or incompatible local evidence cannot justify a paid correction.
                compare_frames(candidate.rendered, candidate.rendered, scope)
            corrected = await self.effects.model(
                row,
                token,
                self.provider,
                MotionModelRequest(
                    operation_id=uuid5(operation, f"correct:{number + 1}"),
                    kind="correct",
                    context={**prepared.context, "correction_scope": scope} if scope else prepared.context,
                    assets=prepared.assets,
                    frames=candidate.rendered.evidence,
                    source_frames=prepared.source_frames,
                    asset_previews=prepared.asset_previews,
                    reference_images=prepared.reference_images,
                    baseline_frames=prepared.baseline_frames,
                    composition=composition,
                    review=reviewed.review,
                    incumbent_composition=comparison.composition,
                    incumbent_frames=comparison.rendered.evidence,
                ),
            )
            if corrected.composition is None:
                raise AuthError("MOTION_CORRECTION_RESULT_INVALID", 409)
            if bounded:
                check_operation = uuid5(operation, f"correction-check:{number + 1}")
                await self.effects.claim(
                    row,
                    token,
                    check_operation,
                    "review",
                    {
                        "kind": "local_correction_guard",
                        "scope": scope,
                        "base_composition_sha256": fingerprint(composition.model_dump(mode="json")),
                        "candidate_composition_sha256": fingerprint(corrected.composition.model_dump(mode="json")),
                        "assets": [{"id": item.id, "sha256": item.sha256} for item in prepared.assets],
                        "audio": prepared.soundtrack if prepared.soundtrack is not None else prepared.audio,
                    },
                )
                try:
                    validate_candidate(composition, corrected.composition)
                except AuthError as exc:
                    await self.effects.received(
                        row,
                        token,
                        check_operation,
                        {
                            "accepted": False,
                            "reason": exc.code,
                            "quality_validated": False,
                        },
                    )
                    break
                correction_base = candidate
            if corrected.composition.illustrations != initial_illustrations:
                raise AuthError("MOTION_ILLUSTRATION_CORRECTION_CHANGED", 409)
            composition = corrected.composition
            number += 1
        if incumbent is None:
            raise AuthError("MOTION_MANDATORY_REVIEW_FAILED", 409)
        await self.complete(row, token, candidates, incumbent)
        return "completed"

    async def render(
        self,
        row: dict[str, Any],
        token: UUID,
        prepared: PreparedMotionInput,
        number: int,
        composition: HTMLMotionComposition,
    ) -> Candidate:
        validate_motion_plan(
            composition,
            prepared.context,
            duration_ms=prepared.duration_ms,
            asset_ids={asset.id for asset in prepared.assets},
        )
        if composition.audio.model_dump(mode="json") != prepared.audio:
            raise AuthError("MOTION_ORIGINAL_AUDIO_CHANGED", 409)
        runtime_hash = movement_hash(prepared.context)
        element_hash = elements_hash(prepared.context)
        output_audio = prepared.soundtrack if prepared.soundtrack is not None else prepared.audio
        if prepared.soundtrack is not None and prepared.context.get("authorized_soundtrack") != prepared.soundtrack:
            raise AuthError("MOTION_AUDIO_CONTEXT_CHANGED", 409)
        if prepared.soundtrack is not None:
            validate_original_branch(prepared.soundtrack, prepared.audio)
        samples = sample_times(composition, prepared.context)
        operation = row["operation_id"]
        render_operation = uuid5(operation, f"render:{number}")
        profile = {"width": 720, "height": 1280, "fps": 30, "duration_ms": prepared.duration_ms}
        await self.effects.claim(
            row,
            token,
            render_operation,
            "render",
            {
                "composition": composition.model_dump(mode="json"),
                "profile": profile,
                **({"movement_runtime_sha256": runtime_hash} if runtime_hash is not None else {}),
                **({"element_runtime_sha256": element_hash} if element_hash is not None else {}),
                **({"sample_times_ms": list(samples)} if samples else {}),
                "assets": [{"id": item.id, "sha256": item.sha256} for item in prepared.assets],
                **({"soundtrack": output_audio} if prepared.soundtrack is not None else {}),
                **({"fingerprint_frames": True} if correction_enabled(prepared.context) else {}),
            },
        )
        rendered = await self.renderer.render(
            RenderBundle(
                html=composition.html,
                scene_init=composition.scene_init,
                assets=prepared.assets,
                audio=output_audio,
                width=720,
                height=1280,
                fps=30,
                duration_ms=prepared.duration_ms,
                movement_runtime_sha256=runtime_hash,
                element_runtime_sha256=element_hash,
                sample_times_ms=samples,
                fingerprint_frames=correction_enabled(prepared.context),
            ),
            operation_id=render_operation,
        )
        if (
            hashlib.sha256(rendered.mp4).hexdigest() != rendered.sha256
            or not rendered.evidence
            or not 1 <= len(rendered.mp4) <= 50 * 1024 * 1024
        ):
            raise AuthError("MOTION_RENDER_BYTES_INVALID", 409)
        await self.effects.received(
            row, token, render_operation, {"sha256": rendered.sha256, "diagnostics": rendered.diagnostics}
        )
        upload_operation = uuid5(operation, f"upload:{number}")
        key = f"motion/{row['tenant_id']}/{row['business_id']}/{row['id']}/{number}/{rendered.sha256}.mp4"
        if getattr(self.store, "single_attempt_put", False) is not True:
            raise AuthError("MOTION_STORAGE_SINGLE_ATTEMPT_REQUIRED", 409)
        await self.effects.claim(row, token, upload_operation, "upload", {"object_key": key, "sha256": rendered.sha256})
        await self.store.put(key, FetchedMedia(rendered.mp4, "video/mp4", rendered.sha256))
        stored = await self.store.get_video(key)
        if hashlib.sha256(stored).hexdigest() != rendered.sha256:
            raise AuthError("MOTION_STORAGE_BYTES_CHANGED", 409)
        await self.effects.received(row, token, upload_operation, {"object_key": key, "sha256": rendered.sha256})
        artifact = PieceArtifact(
            uuid5(render_operation, "artifact"), key, rendered.sha256, "video/mp4", len(rendered.mp4)
        )
        composition_ciphertext = self.requests.context.seal(composition.model_dump(mode="json"))
        diagnostics_ciphertext = self.requests.context.seal(rendered.diagnostics)
        evidence_ciphertext = await self.effects.persist_payload(
            row,
            token,
            render_operation,
            "evidence",
            {
                "frames": [
                    {**asdict(frame), "png": base64.b64encode(frame.png).decode()} for frame in rendered.evidence
                ],
                **(
                    {
                        "temporal_sampling": evidence_manifest(
                            composition,
                            rendered.evidence,
                            "current",
                            prepared.context["creative_contract"]["temporal_review"],
                        )
                    }
                    if samples
                    else {}
                ),
            },
        )
        async with self.requests.database.transaction(row["tenant_id"], row["actor_id"]) as session:
            await self.requests.locked_running(session, row, token)
            await session.execute(
                text("""INSERT INTO motion_render_versions
              (tenant_id,business_id,request_id,number,operation_id,composition_ciphertext,object_key,sha256,
               size_bytes,evidence_ciphertext,diagnostics_ciphertext)
              VALUES(:tenant,:business,:id,:number,:operation,:composition,:key,:sha,:size,:evidence,:diagnostics)"""),
                {
                    "tenant": row["tenant_id"],
                    "business": row["business_id"],
                    "id": row["id"],
                    "number": number,
                    "operation": render_operation,
                    "composition": composition_ciphertext,
                    "key": key,
                    "sha": rendered.sha256,
                    "size": len(rendered.mp4),
                    "evidence": evidence_ciphertext,
                    "diagnostics": diagnostics_ciphertext,
                },
            )
        return Candidate(number, composition, rendered, artifact)

    async def record_review(self, row: dict[str, Any], token: UUID, candidate: Candidate) -> None:
        assert candidate.review is not None
        review_ciphertext = self.requests.context.seal(candidate.review.model_dump(mode="json"))
        async with self.requests.database.transaction(row["tenant_id"], row["actor_id"]) as session:
            await self.requests.locked_running(session, row, token)
            changed = await session.scalar(
                text("""UPDATE motion_render_versions SET review_ciphertext=:review
              WHERE tenant_id=:tenant AND business_id=:business AND request_id=:id AND number=:number
                AND review_ciphertext IS NULL RETURNING 1"""),
                {
                    "tenant": row["tenant_id"],
                    "business": row["business_id"],
                    "id": row["id"],
                    "number": candidate.number,
                    "review": review_ciphertext,
                },
            )
            if not changed:
                raise AuthError("MOTION_REVIEW_ALREADY_RECORDED", 409)

    async def complete(
        self, row: dict[str, Any], token: UUID, candidates: list[Candidate], selected: Candidate
    ) -> None:
        tenant, business, actor = row["tenant_id"], row["business_id"], row["actor_id"]
        piece = uuid5(row["operation_id"], "piece")
        async with self.requests.database.transaction(tenant, actor) as session:
            await self.requests.locked_running(session, row, token)
            # Create the first version, retain rejected alternatives, then select
            # the proven incumbent. Latest is deliberately not presumed best.
            parent = None
            selected_version = None
            for candidate in candidates:
                version = await write_version(
                    session,
                    tenant,
                    business,
                    actor,
                    piece,
                    uuid5(row["operation_id"], f"piece:{candidate.number}"),
                    row["format"],
                    (candidate.artifact,),
                    parent_id=parent,
                    select_current=candidate.number == 0 or candidate is selected,
                    simulated=self.provider.provider == "fake",
                )
                if candidate is selected:
                    selected_version = version
                parent = version
            assert selected_version is not None
            await session.execute(
                text("""UPDATE motion_requests SET state='completed',piece_id=:piece,
              finished_at=clock_timestamp() WHERE tenant_id=:tenant AND business_id=:business AND id=:id"""),
                {"tenant": tenant, "business": business, "id": row["id"], "piece": piece},
            )
            await _event(session, tenant, business, actor, row["operation_id"], "motion.completed")
            await self.release(session, row)
        await apply_pending_script_changes(self.requests.settings, self.requests.database, tenant, business, actor)

    async def release(self, session: Any, row: dict[str, Any]) -> None:
        tenant, business, actor = row["tenant_id"], row["business_id"], row["actor_id"]
        gate = self.requests.gate
        await gate.finish_withdrawal_if_idle(
            session, tenant, business, actor, await gate._state(session, tenant, business)
        )
        await VisualPendingChanges.apply_pending_in_session(session, tenant, business)

    async def fail(self, row: dict[str, Any], token: UUID, code: str, *, failure_event_id: UUID | None = None) -> None:
        tenant, business, actor = row["tenant_id"], row["business_id"], row["actor_id"]
        async with self.requests.database.transaction(tenant, actor) as session:
            await self.requests.gate._lock(session, tenant, business, actor)
            current = await self.requests.row(session, tenant, business, row["id"])
            if current["state"] != "running" or current["execution_token"] != token:
                return
            uncertain = await session.scalar(
                text("""SELECT 1 FROM motion_effects
              WHERE tenant_id=:tenant AND request_id=:id AND
                ((kind IN ('generate','review','correct') AND state='submitted')
                  OR (kind='upload' AND state='claimed')) LIMIT 1"""),
                {"tenant": tenant, "id": row["id"]},
            )
            state = "uncertain" if uncertain else "failed"
            await session.execute(
                text("""UPDATE motion_requests SET state=:state,failure_code=:code,
              finished_at=clock_timestamp() WHERE tenant_id=:tenant AND business_id=:business AND id=:id"""),
                {
                    "tenant": tenant,
                    "business": business,
                    "id": row["id"],
                    "state": state,
                    "code": code
                    if isinstance(code, str) and code.isupper() and len(code) <= 100
                    else "MOTION_EXECUTION_FAILED",
                },
            )
            if failure_event_id is None:
                await _event(session, tenant, business, actor, row["operation_id"], "motion.failed")
            else:
                await _event(
                    session, tenant, business, actor, row["operation_id"], "motion.failed", event_id=failure_event_id
                )
            if not uncertain:
                await self.release(session, row)
