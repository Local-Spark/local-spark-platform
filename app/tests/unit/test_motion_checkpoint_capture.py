"""Checkpoints cannot present an unreceived or substituted model result for approval."""

from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.auth import AuthError
from app.services.motion_checkpoints import MotionCheckpoints
from app.services.motion_context import digest
from app.tests.unit.test_motion_checkpoint_execution import prepared
from app.tests.unit.test_motion_construction import plan


@pytest.mark.parametrize("changed", ["not_requested", "missing_receipt", "signed_input", "model_output"])
async def test_capture_requires_exact_received_model_receipt(changed):
    @asynccontextmanager
    async def transaction(*_args):
        yield object()

    requests = SimpleNamespace(
        database=SimpleNamespace(transaction=transaction), context=SimpleNamespace(), locked_running=AsyncMock()
    )
    service = MotionCheckpoints(requests, object())
    signed = {"payload": "exact", "wire_sha256": "a" * 64}
    model = {
        "kind": "generate",
        "state": "received",
        "request_ciphertext": "encrypted",
        "response_ciphertext": "encrypted",
        "request_hash": digest(signed),
    }
    output = {"construction_plan": plan().model_dump(mode="json")}
    value = prepared()
    if changed == "not_requested":
        value.context["request"]["review_checkpoints"] = False
    elif changed == "missing_receipt":
        model = None
    elif changed == "signed_input":
        model["request_hash"] = "0" * 64
    else:
        output["construction_plan"] = {}
    service.effect = AsyncMock(return_value=model)
    service.payloads.open = AsyncMock(side_effect=[signed, output])
    effects = SimpleNamespace(claim=AsyncMock())
    row = {key: uuid4() for key in ("tenant_id", "business_id", "actor_id", "operation_id")}
    with pytest.raises(AuthError, match="MOTION_CHECKPOINT_"):
        await service.capture(row, uuid4(), "plan", value, plan(), effects)
    effects.claim.assert_not_awaited()
