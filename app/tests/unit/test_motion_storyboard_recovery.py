"""Reconciliation preserves received pixels and cannot restart paid/uncertain work."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4, uuid5

import pytest

from app.services.auth import AuthError
from app.services.motion_context import digest
from app.services.motion_storyboard_frames import storyboard_moments
from app.services.motion_storyboard_recovery import MotionStoryboardRecovery
from app.tests.unit.test_motion_storyboards import board_case, board_output, boarded  # noqa: F401


@pytest.fixture
def recovery_case(board_case, monkeypatch):  # noqa: F811
    c = board_case
    c.row.update(state="failed", failure_code="MOTION_EXECUTION_FAILED", piece_id=None, budget_usd_micros=3700000)
    version = uuid5(c.row["operation_id"], "storyboard:0")
    composition = boarded().model_dump(mode="json")
    moments = storyboard_moments(boarded())
    output = board_output(boarded())
    frames = []
    receipts = {}
    effects = {}
    pngs = {}

    def effect(operation, kind, response, request=None):
        response_key, request_key = str(operation) + "-response", str(operation) + "-request"
        receipts[response_key], receipts[request_key] = response, request
        effects[operation] = dict(
            operation_id=operation,
            kind=kind,
            state="received",
            request_hash="hash",
            request_ciphertext=request_key,
            response_ciphertext=response_key,
            reserved_usd_micros=850000 if kind == "generate" else 0,
            estimated_usd_micros=175000 if kind == "generate" else None,
        )

    for moment, frame in zip(moments, output.evidence, strict=True):
        operation = uuid5(version, moment["scene_id"])
        key = f"motion/{c.row['tenant_id']}/{c.row['business_id']}/{c.row['id']}/storyboard/{operation}.png"
        manifest = {
            **moment,
            "at_ms": frame.ms,
            "sha256": frame.sha256,
            "size_bytes": len(frame.png),
            "object_key": key,
        }
        frames.append(manifest)
        pngs[key] = frame.png
        effect(operation, "upload", manifest)
    payload = dict(
        composition=composition,
        context={"request": {"storyboard": True}},
        frames=frames,
        illustrations=[],
        source_fingerprint=c.row["source_fingerprint"],
    )
    effect(uuid5(c.row["operation_id"], "generate:0"), "generate", {"composition": deepcopy(composition)})
    effect(
        version,
        "render",
        {"diagnostics": output.diagnostics, "frames": [{"ms": f.ms, "sha256": f.sha256} for f in output.evidence]},
        {"purpose": "storyboard", "composition": deepcopy(composition), "moments": moments},
    )
    effect(uuid5(version, "payload:board"), "upload", payload)
    stored = []
    writes = []

    async def execute(statement, params):
        sql = str(statement)
        if sql.startswith("SELECT * FROM motion_storyboards"):
            return SimpleNamespace(mappings=lambda: SimpleNamespace(one_or_none=lambda: stored[0] if stored else None))
        if "FROM motion_effects" in sql:
            return SimpleNamespace(mappings=lambda: SimpleNamespace(all=lambda: list(effects.values())))
        writes.append(sql)
        if "INSERT INTO motion_storyboards" in sql:
            stored.append({"state": "awaiting_approval", "content_sha256": params["sha"]})

    async def open_payload(row, ciphertext):
        assert not c.active
        return deepcopy(receipts[ciphertext])

    async def read(key):
        assert not c.active
        return pngs[key]

    c.session.execute.side_effect = execute
    c.session.scalar.return_value = False
    c.service.payloads.open = AsyncMock(side_effect=open_payload)
    c.store.get_image.side_effect = read
    events = AsyncMock()
    monkeypatch.setattr("app.services.motion_storyboard_recovery._event", events)
    service = MotionStoryboardRecovery(c.service)
    args = tuple(c.row[k] for k in ("tenant_id", "business_id", "actor_id", "id"))
    return SimpleNamespace(
        c=c,
        service=service,
        args=args,
        payload=payload,
        effects=effects,
        receipts=receipts,
        sha=digest(payload),
        writes=writes,
        events=events,
        version=version,
        stored=stored,
        pngs=pngs,
    )


async def test_recovery_checks_bytes_outside_locks_and_is_idempotent(recovery_case):
    r = recovery_case
    assert await r.service.reconcile(*r.args, r.sha) == {"state": "awaiting_approval", "reconciled": True}
    assert len(r.writes) == 2
    assert [call.args[-1] for call in r.events.await_args_list] == [
        "motion.storyboard_reconciled",
        "motion.storyboard_ready",
    ]
    assert await r.service.reconcile(*r.args, r.sha) == {"state": "awaiting_approval", "reconciled": False}
    assert len(r.writes) == 2 and r.events.await_count == 2
    r.c.store.put.assert_not_awaited()
    assert r.c.requests.current.await_count == 2


@pytest.mark.parametrize("changed", [False, True])
async def test_staged_capture_recovery_requires_matching_planning_receipt(recovery_case, changed):
    from app.services.motion_context import digest
    from app.tests.unit.test_motion_construction import staged_context

    r = recovery_case
    r.payload["context"].update(staged_context())
    r.payload["context"]["request"]["storyboard"] = True
    planning = uuid5(r.c.row["operation_id"], "generate:plan:0")
    data = deepcopy(r.payload["composition"])
    data.pop("html")
    data.pop("scene_init")
    data.setdefault("illustrations", [])
    r.receipts["planning-response"] = {"construction_plan": data}
    r.effects[planning] = dict(
        operation_id=planning,
        kind="generate",
        state="received",
        request_hash="hash",
        request_ciphertext="planning-request",
        response_ciphertext="planning-response",
        reserved_usd_micros=850000,
        estimated_usd_micros=175000,
    )
    if changed:
        data["concept"] = "wrong plan"
        with pytest.raises(AuthError, match="BYTES_CHANGED"):
            await r.service.reconcile(*r.args, digest(r.payload))
    else:
        assert (await r.service.reconcile(*r.args, digest(r.payload)))["reconciled"]


@pytest.mark.parametrize("change", ["not_storyboard", "object_key", "existing_hash"])
async def test_recovery_rejects_changed_destination_or_non_capture_payload(recovery_case, change):
    from app.services.motion_context import digest

    r = recovery_case
    if change == "not_storyboard":
        r.payload["context"]["request"]["storyboard"] = False
    elif change == "object_key":
        r.payload["frames"][0]["object_key"] = "another-operation/frame.png"
    else:
        r.stored.append({"state": "awaiting_approval", "content_sha256": "0" * 64})
    with pytest.raises(AuthError):
        await r.service.reconcile(*r.args, digest(r.payload))
    assert not r.writes


@pytest.mark.parametrize("same_hash", [False, True])
async def test_recovery_race_preserves_already_recorded_capture(recovery_case, same_hash):
    r = recovery_case
    existing = {"state": "awaiting_approval", "content_sha256": r.sha if same_hash else "0" * 64}
    r.service.snapshot = AsyncMock(side_effect=[(r.c.row, None, r.effects), (r.c.row, existing, r.effects)])
    if same_hash:
        assert await r.service.reconcile(*r.args, r.sha) == {"state": "awaiting_approval", "reconciled": False}
    else:
        with pytest.raises(AuthError, match="BYTES_CHANGED"):
            await r.service.reconcile(*r.args, r.sha)
    assert not r.writes


@pytest.mark.parametrize(
    "case",
    [
        "actor",
        "running",
        "other_failure",
        "piece",
        "video",
        "pending_effect",
        "unknown_cost",
        "budget",
        "review",
        "missing_payload",
        "extra_render",
        "extra_generation",
        "hash",
        "png",
        "generation",
        "render",
        "frame_upload",
        "revoked",
    ],
)
async def test_recovery_rejects_ineligible_or_unverifiable_results(recovery_case, case):
    r = recovery_case
    row = r.c.row
    gen = uuid5(row["operation_id"], "generate:0")
    sha = r.sha
    if case == "actor":
        row["actor_id"] = uuid4()
    elif case == "running":
        row["state"] = "running"
    elif case == "other_failure":
        row["failure_code"] = "MOTION_RENDER_EXECUTION_FAILED"
    elif case == "piece":
        row["piece_id"] = uuid4()
    elif case == "video":
        r.c.session.scalar.return_value = True
    elif case == "pending_effect":
        r.effects[gen]["state"] = "submitted"
    elif case == "unknown_cost":
        r.effects[gen]["estimated_usd_micros"] = None
    elif case == "budget":
        row["budget_usd_micros"] = 1
    elif case == "review":
        r.effects[gen]["kind"] = "review"
    elif case == "missing_payload":
        del r.effects[uuid5(r.version, "payload:board")]
    elif case in {"extra_render", "extra_generation"}:
        e = dict(r.effects[r.version if case == "extra_render" else gen])
        e["operation_id"] = uuid4()
        r.effects[e["operation_id"]] = e
    elif case == "hash":
        sha = "f" * 64
    elif case == "png":
        r.pngs[next(iter(r.pngs))] = b"bad bytes"
    elif case == "generation":
        r.receipts[str(gen) + "-response"]["composition"]["concept"] = "changed"
    elif case == "render":
        r.receipts[str(r.version) + "-response"]["frames"] = []
    elif case == "frame_upload":
        del r.effects[uuid5(r.version, r.payload["frames"][0]["scene_id"])]
    elif case == "revoked":
        r.c.requests.current.side_effect = [None, AuthError("MOTION_CONTEXT_CHANGED", 409)]
    with pytest.raises(AuthError):
        await r.service.reconcile(*r.args, sha)
    assert not r.writes
    r.events.assert_not_awaited()


async def test_changed_receipts_during_download_are_fenced(recovery_case):
    r = recovery_case
    original = r.service.evidence

    async def change(*args):
        result = await original(*args)
        r.effects[r.version]["request_hash"] = "changed"
        return result

    r.service.evidence = change
    with pytest.raises(AuthError, match="FENCED"):
        await r.service.reconcile(*r.args, r.sha)
    assert not r.writes
