"""Native checkpoints, render critique and bounded replanning on restricted PostgreSQL."""

import hashlib
from dataclasses import replace
from uuid import uuid4, uuid5

import pytest
from sqlalchemy import text

from app.adapters.motion_html_renderer import RenderedMotion
from app.schemas.motion_production import MotionReview
from app.schemas.motion_storyboards import StoryboardDecision
from app.services.auth import AuthError
from app.services.motion_checkpoints import MotionCheckpoints
from app.services.motion_plan_revision import MotionPlanRevision
from app.services.motion_protocols import MotionModelResult
from app.services.motion_repertoire import load_repertoire_images
from app.services.motion_sound_library import load_sound_library
from app.services.motion_storyboards import MotionStoryboards
from app.services.motion_temporal import TEMPORAL_CRITERIA, temporal_payload
from app.tests.integration.test_motion_checkpoints import decide, decision, event
from app.tests.integration.test_motion_production import motion_case  # noqa: F401
from app.tests.unit.test_motion_ai import frame, provider, review_data
from app.tests.unit.test_motion_audiovisual import natural_body
from app.tests.unit.test_motion_staging import staged_composition
from app.workflows.contracts import BusinessEvent

pytestmark = pytest.mark.integration


@pytest.fixture
async def rejected_staging(motion_case, request):  # noqa: F811
    c = motion_case
    adequate = getattr(request, "param", None) == "adequate"
    c.cfg = c.cfg.model_copy(update={"motion_storyboard_enabled": True})
    c.requests.settings = c.requests.context.settings = c.cfg
    c.body = natural_body(operation_id=c.body.operation_id, source_asset_id=c.source, repertoire_id="business-reel-v5")
    composition = staged_composition()
    composition = composition.model_copy(
        update={"motion_plan": composition.motion_plan.model_copy(update={"style_id": None})}
    )
    from app.schemas.motion_production import MotionConstructionPlan

    plan = MotionConstructionPlan.model_validate(
        {**composition.model_dump(mode="json", exclude={"html", "scene_init"}), "illustrations": []}
    )
    prior = c.inputs.prepare.return_value

    async def prepare(snapshot):
        ctx = {
            k: v
            for k, v in snapshot.items()
            if k not in {"tenant_id", "business_id", "source", "logo", "execution", "references"}
        }
        ctx.update(
            source={"asset_id": "assets/source.mp4", "sha256": prior.assets[0].sha256, "duration_ms": 1000},
            output={"width": 720, "height": 1280, "fps": 30, "duration_ms": 1000},
            authorized_audio=prior.audio,
        )
        return replace(
            prior,
            context=ctx,
            assets=(*prior.assets, *load_sound_library(ctx)),
            source_frames=(frame(100), frame(300)),
            reference_images=load_repertoire_images(ctx),
        )

    async def render(bundle, *, operation_id):
        frames = tuple(
            replace(
                frame(round((ms * 30 // 1000) * 1000 / 30)),
                frame_index=ms * 30 // 1000,
                pts_seconds=f"{(ms * 30 // 1000) / 30:.6f}",
            )
            for ms in bundle.sample_times_ms
        )
        data = b"" if bundle.frames_only else c.rendered.mp4
        return RenderedMotion(
            data,
            hashlib.sha256(data).hexdigest(),
            frames,
            {"evidence_source": "browser_keyframes" if bundle.frames_only else "decoded_video"},
        )

    async def submit(job, payload):
        c.provider.calls.append(job.kind)
        if job.kind == "generate":
            if job.construction_plan is None:
                assert payload["text"]["format"]["name"] == "MotionStagedPlanningOutput"
                return MotionModelResult(construction_plan=plan, estimated_usd_micros=0)
            assert job.construction_plan == plan
            return MotionModelResult(composition=composition, estimated_usd_micros=0)
        assert job.kind == "review" and len(job.frames) > 3
        assert payload["text"]["format"]["name"] == "StagedMotionReview"
        refs = [{"version": "current", "at_ms": f.ms, "sha256": f.sha256} for f in job.frames[:2]]
        data = review_data(current=job.frames[0], revise=not adequate)
        data.update(verdict="adequate" if adequate else "reject", preferred="undetermined", preference_evidence=[])
        if not adequate:
            data["issues"][0].update(actionable=False, repair_kind="direction")
        data["creative_checks"] = [
            dict(
                name=name,
                status="met" if adequate else "uncertain",
                brief_basis="Synthetic request",
                observation="No artistic certification",
                evidence=refs,
            )
            for name in ("brief_alignment", "narrative_progression", "motion_role", "visual_development")
        ]
        manifest = temporal_payload(job.context, job.composition, job.frames, None, ())
        data["temporal_checks"] = [
            dict(
                name=name,
                status="pass" if adequate else "uncertain",
                observation="Synthetic evidence only",
                event_ids=[e["id"] for e in manifest["current"]["events"]] if adequate else [],
                evidence=[dict(version="current", at_ms=f.ms, sha256=f.sha256) for f in job.frames] if adequate else [],
                issue_indices=[],
            )
            for name in TEMPORAL_CRITERIA
        ]
        return MotionModelResult(review=MotionReview.model_validate(data), estimated_usd_micros=0)

    c.inputs.prepare.side_effect, c.renderer.render.side_effect, c.provider.submit = prepare, render, submit
    c.provider.build_request = provider().build_request
    c.store.get_image = c.store.get_video
    c.checkpoints = MotionCheckpoints(c.requests, c.store)
    c.requested = await c.requests.create(c.tenant, c.business, c.actor, c.body)
    assert await c.runner.run(c.event) == "awaiting_plan"
    await decide(c, "plan", await decision(c, "plan"))
    assert await c.runner.run(event(c, "plan")) == "awaiting_render"
    await decide(c, "render", await decision(c, "render"))
    assert await c.runner.run(event(c, "render")) == "awaiting_storyboard"
    boards = MotionStoryboards(c.requests, c.store)
    _, board, packet = await boards.load(c.tenant, c.business, c.actor, c.requested.id)
    view = boards.present(board, packet)
    await boards.decide(
        c.tenant,
        c.business,
        c.actor,
        c.requested.id,
        StoryboardDecision(
            operation_id=uuid4(), version_id=view.version_id, content_sha256=view.content_sha256, decision="approve"
        ),
    )
    resume = BusinessEvent(
        str(uuid5(c.body.operation_id, "motion.storyboard_approved")),
        str(c.tenant),
        str(c.business),
        str(c.actor),
        str(c.body.operation_id),
    )
    if adequate:
        assert await c.runner.run(resume) == "completed"
    else:
        with pytest.raises(AuthError, match="MOTION_PLAN_REVISION_REQUIRED"):
            await c.runner.run(resume)
    assert await c.runner.run(resume) == "already_claimed"
    assert c.provider.calls == ["generate", "generate", "review"]
    c.revisions = MotionPlanRevision(c.requests)
    return c


async def test_native_review_returns_to_planning_once_with_remaining_budget_and_preserved_history(rejected_staging):
    c = rejected_staging
    args = c.tenant, c.business, c.actor, c.requested.id
    body, remaining = await c.revisions.prepare(*args)
    assert remaining == 3000 and body.instruction == c.body.instruction
    revised = await c.revisions.create(*args)
    assert await c.revisions.create(*args) == revised
    async with c.database.transaction(c.tenant, c.actor) as session:
        parent = await c.requests.row(session, c.tenant, c.business, c.requested.id)
        child = await c.requests.row(session, c.tenant, c.business, revised.id)
        assert parent["state"] == "failed" and child["state"] == "queued" and child["budget_usd_micros"] == remaining
        assert (
            await session.scalar(
                text("SELECT count(*) FROM motion_render_versions WHERE request_id=:id"), {"id": c.requested.id}
            )
            == 1
        )
        assert (
            await session.scalar(
                text("SELECT count(*) FROM motion_effects WHERE request_id=:id AND operation_id IN (:plan,:render)"),
                {
                    "id": c.requested.id,
                    "plan": uuid5(c.body.operation_id, "checkpoint:plan"),
                    "render": uuid5(c.body.operation_id, "checkpoint:render"),
                },
            )
            == 2
        )
    assert c.provider.calls == ["generate", "generate", "review"]
    with pytest.raises(AuthError):
        await c.revisions.prepare(uuid4(), c.business, c.actor, c.requested.id)


@pytest.mark.parametrize(
    "change,code",
    [
        ("budget", "BUDGET_REQUIRED"),
        ("effect", "UNRESOLVED_EFFECT"),
        ("review", "EVIDENCE_REQUIRED"),
        ("state", "INELIGIBLE"),
    ],
)
async def test_replanning_refuses_unresolved_effects_missing_evidence_and_exhausted_cap(
    rejected_staging, admin, change, code
):
    c = rejected_staging
    statements = {
        "budget": "UPDATE motion_requests SET budget_usd_micros=1000 WHERE id=:id",
        "effect": "UPDATE motion_effects SET state='submitted' WHERE request_id=:id AND kind='review'",
        "review": "UPDATE motion_render_versions SET review_ciphertext=NULL WHERE request_id=:id",
        "state": "UPDATE motion_requests SET failure_code='MOTION_OTHER' WHERE id=:id",
    }
    async with admin.begin() as session:
        await session.execute(text(statements[change]), {"id": c.requested.id})
    with pytest.raises(AuthError, match=code):
        await c.revisions.prepare(c.tenant, c.business, c.actor, c.requested.id)


@pytest.mark.parametrize("rejected_staging", ["adequate"], indirect=True)
async def test_operator_can_request_one_grounded_revision_without_rewriting_native_acceptance(rejected_staging):
    from app.schemas.motion_plan_revision import MotionDirectionObservation

    c = rejected_staging
    args = c.tenant, c.business, c.actor, c.requested.id
    async with c.database.transaction(c.tenant, c.actor) as session:
        version = (
            (
                await session.execute(
                    text("SELECT * FROM motion_render_versions WHERE request_id=:r"), {"r": c.requested.id}
                )
            )
            .mappings()
            .one()
        )
        original_review = version["review_ciphertext"]
        review = MotionReview.model_validate(c.requests.context.open(original_review))
    observation = MotionDirectionObservation(
        mp4_sha256=version["sha256"],
        frames=[f.model_dump(exclude={"version"}) for f in review.creative_checks[0].evidence],
        observation="Operator sees insufficient development in these received frames; revisit direction.",
    )
    body, remaining = await c.revisions.prepare(*args, observation)
    assert remaining == 3000 and body.instruction == c.body.instruction
    revised = await c.revisions.create(*args, observation)
    assert await c.revisions.create(*args, observation) == revised
    with pytest.raises(AuthError, match="CONFLICT"):
        await c.revisions.create(*args, observation.model_copy(update={"observation": "Changed feedback"}))
    async with c.database.transaction(c.tenant, c.actor) as session:
        parent = await c.requests.row(session, c.tenant, c.business, c.requested.id)
        child = await c.requests.row(session, c.tenant, c.business, revised.id)
        assert parent["state"] == "completed" and parent["piece_id"] is not None
        assert child["budget_usd_micros"] == remaining and child["state"] == "queued"
        assert (
            await session.scalar(
                text("SELECT review_ciphertext FROM motion_render_versions WHERE request_id=:r"), {"r": c.requested.id}
            )
        ) == original_review
        assert (
            c.requests.context.open(child["snapshot_ciphertext"])["request"]["preparation"]["decisions"][-1]["origin"]
            == "operator"
        )
    assert c.provider.calls == ["generate", "generate", "review"]
    with pytest.raises(AuthError, match="INELIGIBLE"):
        await c.revisions.prepare(*args)
    with pytest.raises(AuthError, match="INELIGIBLE"):
        await c.revisions.prepare(c.tenant, c.business, c.actor, revised.id, observation)
    resumed = BusinessEvent(
        str(uuid5(revised.operation_id, "motion.requested")),
        str(c.tenant),
        str(c.business),
        str(c.actor),
        str(revised.operation_id),
    )
    assert await c.runner.run(resumed) == "awaiting_plan"
    assert c.provider.calls == ["generate", "generate", "review", "generate"]
