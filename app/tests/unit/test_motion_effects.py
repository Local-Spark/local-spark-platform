"""Effect claims, evidence and financial holds fail closed without a second dispatch."""

import base64
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4, uuid5

import pytest

from app.adapters.motion_ai import MotionAIError
from app.schemas.motion_production import MotionReview
from app.services.auth import AuthError
from app.services.motion_effects import MotionEffects
from app.services.motion_protocols import MotionModelRequest, MotionModelResult
from app.tests.unit.test_motion_ai import composition, review_data


def setup():
    row = {key: uuid4() for key in ("tenant_id", "business_id", "actor_id", "id", "operation_id")}
    session = SimpleNamespace(scalar=AsyncMock(side_effect=[None, 0, 1]), execute=AsyncMock())
    worker = SimpleNamespace(scalar=AsyncMock(return_value=1))
    active = {"owner": False, "worker": False}
    order = []

    @asynccontextmanager
    async def owner_transaction(*_):
        assert not active["owner"]
        active["owner"] = True
        try:
            yield session
        finally:
            active["owner"] = False
            order.append("owner_commit")

    @asynccontextmanager
    async def worker_transaction(*_):
        active["worker"] = True
        try:
            yield worker
        finally:
            active["worker"] = False
            order.append("worker_commit")

    database = SimpleNamespace(transaction=owner_transaction)
    cost_database = SimpleNamespace(transaction=worker_transaction)
    sealed = []

    def seal(value):
        sealed.append(value)
        return "ciphertext"

    requests = SimpleNamespace(
        settings=SimpleNamespace(
            motion_ai_reservation_usd_micros=100,
            motion_ai_input_usd_micros_per_million_tokens=2500000,
            motion_ai_output_usd_micros_per_million_tokens=10000000,
        ),
        database=database,
        context=SimpleNamespace(seal=Mock(side_effect=seal)),
        locked_running=AsyncMock(return_value={"budget_usd_micros": 1000}),
    )
    effects = MotionEffects(requests, cost_database)
    result = MotionModelResult(composition=composition(), estimated_usd_micros=50, raw_response=b"private response")

    async def submit(*_):
        assert not any(active.values()), "No provider IO under row locks"
        assert "owner_commit" in order
        order.append("submit")
        return result

    async def reserve(*_):
        assert not any(active.values())
        order.append("reserve")
        return SimpleNamespace(id=uuid4(), created=True)

    async def finish(*_, **kwargs):
        assert not any(active.values())
        order.append("finish")

    effects.ledger = SimpleNamespace(
        database=cost_database, reserve=AsyncMock(side_effect=reserve), finish=AsyncMock(side_effect=finish)
    )
    provider = SimpleNamespace(
        provider="openai",
        model="gpt-6.1-sol",
        build_request=Mock(return_value={"private": "payload", "max_output_tokens": 5}),
        count_input_tokens=AsyncMock(return_value=10),
        submit=AsyncMock(side_effect=submit),
    )
    request = MotionModelRequest(uuid4(), "generate", {})
    return SimpleNamespace(
        effects=effects,
        requests=requests,
        row=row,
        token=uuid4(),
        session=session,
        worker=worker,
        active=active,
        order=order,
        provider=provider,
        request=request,
        result=result,
        sealed=sealed,
    )


async def test_response_is_private_durable_before_ledger_and_transport_is_outside_locks():
    case = setup()
    result = await case.effects.model(case.row, case.token, case.provider, case.request)
    assert result == case.result
    assert case.order.index("reserve") < case.order.index("submit")
    assert case.order.index("submit") < case.order.index("worker_commit") < case.order.index("finish")
    case.provider.submit.assert_awaited_once()
    assert case.effects.ledger.finish.await_args.kwargs["actual_usd_micros"] is None
    assert case.sealed[0]["provider"] == "openai"
    assert case.sealed[0]["payload"] == {"private": "payload", "max_output_tokens": 5}
    assert case.sealed[0]["cost_bound"]["maximum_usd_micros"] == 75
    response = case.sealed[-1]
    assert response["raw_response"] == base64.b64encode(b"private response").decode()
    assert response["composition"]["html"] == composition().html and response["review"] is None
    assert "motion_record_result" in str(case.worker.scalar.await_args.args[0])
    assert case.worker.scalar.await_args.args[1]["token"] == case.token
    assert "audit_events" in str(case.session.execute.await_args_list[-1].args[0])
    assert case.session.execute.await_args_list[0].args[1]["payload"] == "ciphertext"


@pytest.mark.parametrize("code", ["MOTION_AI_OUTPUT_LIMIT", "MOTION_AI_RESPONSE_INVALID"])
async def test_invalid_response_keeps_usage_private_and_hold_pending_without_another_submission(code):
    case = setup()
    case.provider.submit.side_effect = MotionAIError(
        code,
        raw_response=b"private rejected response",
        usage={"input_tokens": 10, "output_tokens": 5},
        estimated_usd_micros=75,
        provider_request_id="limited-response",
    )
    with pytest.raises(MotionAIError, match=code):
        await case.effects.model(case.row, case.token, case.provider, case.request)
    case.provider.submit.assert_awaited_once()
    assert case.sealed[-1]["usage"] == {"input_tokens": 10, "output_tokens": 5}
    assert case.worker.scalar.await_args.args[1]["estimate"] == 75
    assert case.effects.ledger.finish.await_args.kwargs["actual_usd_micros"] is None


async def test_fake_zero_cost_and_review_result_are_explicit_not_provider_invoice_estimates():
    case = setup()
    case.provider.provider = "fake"
    review = MotionReview.model_validate(review_data())
    case.provider.submit.side_effect = None
    case.provider.submit.return_value = MotionModelResult(review=review, estimated_usd_micros=0)
    await case.effects.model(case.row, case.token, case.provider, case.request)
    assert case.effects.ledger.finish.await_args.kwargs["actual_usd_micros"] == 0
    assert case.sealed[-1]["composition"] is None and case.sealed[-1]["review"]["verdict"] == "adequate"


@pytest.mark.parametrize(
    "maximum,rate,code",
    [
        (None, 10000000, "BOUND_REQUIRED"),
        (True, 10000000, "BOUND_REQUIRED"),
        (0, 10000000, "BOUND_REQUIRED"),
        (5, 0, "BOUND_REQUIRED"),
        (11, 10000000, "EXCEEDS_RESERVATION"),
        (10, 10000001, "EXCEEDS_RESERVATION"),
    ],
)
async def test_output_cost_ceiling_cannot_exceed_reserve_before_any_claim(maximum, rate, code):
    case = setup()
    case.provider.build_request.return_value = {"max_output_tokens": maximum}
    case.requests.settings.motion_ai_output_usd_micros_per_million_tokens = rate
    with pytest.raises(AuthError, match=code):
        await case.effects.model(case.row, case.token, case.provider, case.request)
    case.requests.locked_running.assert_not_awaited()
    case.session.execute.assert_not_awaited()
    case.effects.ledger.reserve.assert_not_awaited()
    case.provider.submit.assert_not_awaited()
    case.provider.count_input_tokens.assert_not_awaited()


@pytest.mark.parametrize(
    "count,code",
    [
        (21, "TOTAL_COST_EXCEEDS_RESERVATION"),
        (None, "INPUT_COUNT_REQUIRED"),
        (True, "INPUT_COUNT_REQUIRED"),
        (0, "INPUT_COUNT_REQUIRED"),
        (272001, "LONG_CONTEXT_NOT_QUALIFIED"),
    ],
)
async def test_full_input_cost_blocks_before_claim_reservation_or_generation(count, code):
    case = setup()
    case.provider.count_input_tokens.return_value = count
    with pytest.raises(AuthError, match=code):
        await case.effects.model(case.row, case.token, case.provider, case.request)
    case.requests.locked_running.assert_not_awaited()
    case.effects.ledger.reserve.assert_not_awaited()
    case.provider.submit.assert_not_awaited()


async def test_exact_reservation_boundary_is_accepted():
    case = setup()
    case.provider.count_input_tokens.return_value = 20
    await case.effects.model(case.row, case.token, case.provider, case.request)
    assert case.sealed[0]["cost_bound"]["maximum_usd_micros"] == 100


@pytest.mark.parametrize(
    "model,input_rate,output_rate",
    [
        ("unknown-model", 2500000, 10000000),
        ("gpt-6.1-sol", 2499999, 10000000),
        ("gpt-6.1-sol", True, 10000000),
        ("gpt-6.1-sol", 2500000, 9999999),
        ("gpt-6.1-sol", 2500000, 10000000.0),
    ],
)
async def test_unqualified_tariff_blocks_even_the_count_request(model, input_rate, output_rate):
    case = setup()
    case.provider.model = model
    case.requests.settings.motion_ai_input_usd_micros_per_million_tokens = input_rate
    case.requests.settings.motion_ai_output_usd_micros_per_million_tokens = output_rate
    with pytest.raises(AuthError, match="COST_"):
        await case.effects.model(case.row, case.token, case.provider, case.request)
    case.provider.count_input_tokens.assert_not_awaited()
    case.effects.ledger.reserve.assert_not_awaited()
    case.provider.submit.assert_not_awaited()


async def test_count_failure_never_authorizes_generation_or_reserves_funds():
    case = setup()
    case.provider.count_input_tokens.side_effect = MotionAIError("MOTION_AI_INPUT_COUNT_FAILED")
    with pytest.raises(MotionAIError, match="INPUT_COUNT_FAILED"):
        await case.effects.model(case.row, case.token, case.provider, case.request)
    case.provider.count_input_tokens.assert_awaited_once()
    case.effects.ledger.reserve.assert_not_awaited()
    case.provider.submit.assert_not_awaited()


@pytest.mark.parametrize("used,expected", [(800, True), (801, False)])
async def test_capacity_keeps_budget_for_correction_and_final_review(used, expected):
    case = setup()
    case.session.scalar.side_effect = [used]
    assert await case.effects.capacity_for_correction(case.row, case.token) is expected
    case.requests.locked_running.assert_awaited_once()


@pytest.mark.parametrize("scalars,code", [([1], "ALREADY_CLAIMED"), ([None, 950], "BUDGET_EXCEEDED")])
async def test_claim_collision_or_budget_failure_never_reserves_or_dispatches(scalars, code):
    case = setup()
    case.session.scalar.side_effect = scalars
    with pytest.raises(AuthError, match=code):
        await case.effects.model(case.row, case.token, case.provider, case.request)
    case.effects.ledger.reserve.assert_not_awaited()
    case.provider.submit.assert_not_awaited()
    case.session.execute.assert_not_awaited()


async def test_existing_reservation_cannot_authorize_a_second_paid_attempt():
    case = setup()
    case.effects.ledger.reserve.side_effect = None
    case.effects.ledger.reserve.return_value = SimpleNamespace(id=uuid4(), created=False)
    with pytest.raises(AuthError, match="RESERVATION_REPLAY"):
        await case.effects.model(case.row, case.token, case.provider, case.request)
    case.provider.submit.assert_not_awaited()
    case.effects.ledger.finish.assert_not_awaited()


async def test_fence_lost_between_reservation_and_submission_keeps_transport_unstarted():
    case = setup()
    case.session.scalar.side_effect = [None, 0, None]
    with pytest.raises(AuthError, match="EFFECT_FENCED"):
        await case.effects.model(case.row, case.token, case.provider, case.request)
    case.provider.submit.assert_not_awaited()
    case.effects.ledger.finish.assert_not_awaited()


@pytest.mark.parametrize("raw", [None, b"private invalid response"])
async def test_provider_error_is_not_retried_and_available_response_survives(raw):
    case = setup()
    case.provider.submit.side_effect = MotionAIError("MOTION_AI_UNCERTAIN", raw_response=raw)
    with pytest.raises(MotionAIError, match="UNCERTAIN"):
        await case.effects.model(case.row, case.token, case.provider, case.request)
    case.provider.submit.assert_awaited_once()
    assert case.effects.ledger.finish.await_args.kwargs["actual_usd_micros"] is None
    if raw:
        assert case.sealed[-1]["raw_response_base64"] == base64.b64encode(raw).decode()
        assert case.sealed[-1]["error_code"] == "MOTION_AI_UNCERTAIN"
        assert case.order.index("worker_commit") < case.order.index("finish")
    else:
        case.worker.scalar.assert_not_awaited()


@pytest.mark.parametrize("estimate,code", [(None, "ESTIMATE_UNKNOWN"), (101, "ESTIMATE_EXCEEDED")])
async def test_unknown_or_excess_cost_is_saved_but_stops_progress(estimate, code):
    case = setup()
    case.provider.submit.side_effect = None
    case.provider.submit.return_value = MotionModelResult(composition=composition(), estimated_usd_micros=estimate)
    with pytest.raises(AuthError, match=code):
        await case.effects.model(case.row, case.token, case.provider, case.request)
    assert case.worker.scalar.await_args.args[1]["estimate"] == estimate
    case.effects.ledger.finish.assert_awaited_once()
    case.provider.submit.assert_awaited_once()


async def test_fenced_result_cannot_overwrite_another_run():
    case = setup()
    case.worker.scalar.return_value = False
    with pytest.raises(AuthError, match="EFFECT_FENCED"):
        await case.effects.received(case.row, case.token, case.request.operation_id, {"private": "result"})
    assert case.worker.scalar.await_args.args[1]["response"] == "ciphertext"
    assert case.worker.scalar.await_args.args[1]["operation"] == case.request.operation_id


async def test_quarantine_uses_admitted_identity_and_token_only():
    case = setup()
    await case.effects.quarantine(case.row, case.token)
    params = case.worker.scalar.await_args.args[1]
    assert params["token"] == case.token and params["id"] == case.row["id"]
    assert params["event"] == uuid5(case.row["operation_id"], "motion.failed")
    assert "motion_quarantine_request" in str(case.worker.scalar.await_args.args[0])
    case.provider.submit.assert_not_awaited()


async def test_ledger_failure_cannot_discard_received_response():
    case = setup()
    case.effects.ledger.finish.side_effect = RuntimeError("database unavailable")
    with pytest.raises(RuntimeError, match="database unavailable"):
        await case.effects.model(case.row, case.token, case.provider, case.request)
    assert case.sealed[-1]["raw_response"]
    case.worker.scalar.assert_awaited_once()
    case.provider.submit.assert_awaited_once()


async def test_quarantine_preserves_explicit_resumed_failure_identity():
    case = setup()
    phase = uuid5(case.row["operation_id"], "motion.storyboard_approved")
    event = uuid5(phase, "motion.failed")
    await case.effects.quarantine(case.row, case.token, failure_event_id=event)
    assert case.worker.scalar.await_args.args[1]["event"] == event
    case.provider.submit.assert_not_awaited()
