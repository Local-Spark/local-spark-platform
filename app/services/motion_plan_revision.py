"""One explicit replanning continuation from a grounded native critique, within the original cap."""

from typing import Any
from uuid import UUID, uuid5

from sqlalchemy import text

from app.schemas.motion_plan_revision import MotionDirectionObservation
from app.schemas.motion_production import MotionRequest, MotionRequestRead, MotionReview
from app.services.auth import AuthError
from app.services.motion_context import digest
from app.services.motion_requests import MotionRequestService


def requires_replanning(review: MotionReview) -> bool:
    return any(i.repair_kind in {"direction", "material"} and i.severity != "minor" for i in review.issues)


def revision_request(
    original: MotionRequest,
    review: MotionReview,
    evidence_hash: str,
    observation: MotionDirectionObservation | None = None,
) -> MotionRequest:
    if original.preparation is None or not original.propose_direction:
        raise AuthError("MOTION_PLAN_REVISION_INELIGIBLE", 409)
    if observation is None and not requires_replanning(review):
        raise AuthError("MOTION_PLAN_REVISION_INELIGIBLE", 409)
    data = original.model_dump(mode="json")
    decisions = data["preparation"]["decisions"]
    if any(d["id"] == "plan-revision" for d in decisions):
        raise AuthError("MOTION_PLAN_REVISION_LIMIT", 409)
    # This is observed feedback about this attempt, never a new client requirement or baseline.
    issues = [i for i in review.issues if i.repair_kind in {"direction", "material"} and i.severity != "minor"]
    summary = " | ".join(f"{i.at_ms}ms: {i.problem} → {i.correction}" for i in issues)
    source = f"Native review {digest(review.model_dump(mode='json'))}; rendered MP4 {evidence_hash}"
    if observation is not None:
        available = {
            (f.at_ms, f.sha256)
            for evidence in (
                *(check.evidence for check in review.criteria),
                *(check.evidence for check in review.creative_checks),
                *(check.evidence for check in review.temporal_checks),
            )
            for f in evidence
            if f.version == "current"
        }
        selected = {(f.at_ms, f.sha256) for f in observation.frames}
        if (
            review.verdict != "adequate"
            or observation.mp4_sha256 != evidence_hash
            or len(selected) != len(observation.frames)
            or not selected <= available
        ):
            raise AuthError("MOTION_PLAN_REVISION_OBSERVATION_UNGROUNDED", 409)
        summary = observation.observation
        source = (
            f"Operator observation {digest(observation.model_dump(mode='json'))}; rendered MP4 {evidence_hash}; "
            "native adequate retained, not owner acceptance; frames "
            + ", ".join(f"{f.at_ms}ms/{f.sha256}" for f in observation.frames)
        )
    decisions.append(
        {
            "id": "plan-revision",
            "kind": "observation",
            "origin": "operator",
            "scope": "request",
            "source_excerpt": source,
            "interpretation": summary[:1000],
            "scene_ids": [],
        }
    )
    data["operation_id"] = str(uuid5(original.operation_id, "plan-revision:1"))
    return MotionRequest.model_validate(data)


class MotionPlanRevision:
    def __init__(self, requests: MotionRequestService):
        self.requests = requests

    async def prepare(
        self,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        request: UUID,
        observation: MotionDirectionObservation | None = None,
    ) -> tuple[MotionRequest, int]:
        """No IO beyond SQL, no mutation. A terminal parent cannot consume additional budget."""
        async with self.requests.database.transaction(tenant, actor) as session:
            await self.requests.gate._lock(session, tenant, business, actor)
            row = await self.requests.row(session, tenant, business, request)
            eligible = (
                row["state"] == "failed" and row["failure_code"] == "MOTION_PLAN_REVISION_REQUIRED"
                if observation is None
                else row["state"] == "completed"
            )
            if row["actor_id"] != actor or not eligible:
                raise AuthError("MOTION_PLAN_REVISION_INELIGIBLE", 409)
            version = (
                (
                    await session.execute(
                        text("""SELECT review_ciphertext,sha256 FROM motion_render_versions
                WHERE tenant_id=:tenant AND business_id=:business AND request_id=:request
                AND review_ciphertext IS NOT NULL ORDER BY number DESC LIMIT 1"""),
                        {"tenant": tenant, "business": business, "request": request},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if version is None:
                raise AuthError("MOTION_PLAN_REVISION_EVIDENCE_REQUIRED", 409)
            effects: list[Any] = list(
                (
                    await session.execute(
                        text("""SELECT state,reserved_usd_micros,
                estimated_usd_micros FROM motion_effects
                WHERE tenant_id=:tenant AND business_id=:business AND request_id=:request"""),
                        {"tenant": tenant, "business": business, "request": request},
                    )
                ).mappings()
            )
            if any(e["state"] != "received" for e in effects):
                raise AuthError("MOTION_PLAN_REVISION_UNRESOLVED_EFFECT", 409)
            remaining = row["budget_usd_micros"] - sum(
                max(e["reserved_usd_micros"], e["estimated_usd_micros"] or 0) for e in effects
            )
            # Never release prior reservations, even when estimated usage is smaller.
            if remaining < 3 * self.requests.settings.motion_ai_reservation_usd_micros:
                raise AuthError("MOTION_PLAN_REVISION_BUDGET_REQUIRED", 409)
            original = MotionRequest.model_validate(self.requests.context.open(row["snapshot_ciphertext"])["request"])
            review = MotionReview.model_validate(self.requests.context.open(version["review_ciphertext"]))
            return revision_request(original, review, version["sha256"], observation), remaining

    async def create(
        self,
        tenant: UUID,
        business: UUID,
        actor: UUID,
        request: UUID,
        observation: MotionDirectionObservation | None = None,
    ) -> MotionRequestRead:
        body, remaining = await self.prepare(tenant, business, actor, request, observation)
        # Existing admission owns RLS, owner, source recapture, audit/outbox and operation idempotency.
        settings = self.requests.settings.model_copy(update={"motion_request_budget_usd_micros": remaining})
        return await MotionRequestService(settings, self.requests.database).create(tenant, business, actor, body)
