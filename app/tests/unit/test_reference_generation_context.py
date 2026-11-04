"""Pinned creative data never substitutes for facts, current choices, or provenance."""

import json
import traceback
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import SecretStr
from temporalio.api.failure.v1 import Failure
from temporalio.converter import DefaultFailureConverter, DefaultPayloadConverter

from app.adapters.editorial_ai import OpenAIEditorialProvider
from app.services.auth import AuthError
from app.services.editorial_proposals import EditorialProposalService
from app.services.reference_generation_context import (
    REFERENCE_CREATIVE_RULE,
    capture_generation_context,
    generation_context_is_current,
    read_generation_snapshot,
)


def context(*, status="partial", version=1):
    reference = str(uuid4())
    return {
        "version": 1,
        "selected": [
            {
                "reference_id": reference,
                "association_version": version,
                "source": "suggested",
                "instagram_handle": "exemplo.ficticio",
                "note": None,
                "score": "8.1",
                "similarity": "high",
                "analysis_status": status,
            }
        ],
        "learnings": [
            {
                "reference_id": reference,
                "association_version": version,
                "analysis_id": str(uuid4()),
                "source": "instagram_feed",
                "status": status,
                "patterns": [
                    {"dimension": "visual", "observation": "Composições destacam o produto"},
                    {"dimension": "editorial", "observation": "Tom acolhedor"},
                ],
            }
        ]
        if status in {"completed", "partial"}
        else [],
    }


def test_projection_preserves_partial_status_and_hides_private_identity(settings):
    raw = context()
    snapshot = read_generation_snapshot(raw)
    model = snapshot.model_input()
    assert model[0]["estado_analise"] == "partial"
    assert model[0]["nota_interna"] == "8.1"
    assert model[0]["padroes"][1]["observacao"] == "Tom acolhedor"
    assert snapshot.selected_versions() == [
        {"reference_id": raw["selected"][0]["reference_id"], "association_version": 1}
    ]
    model_json = json.dumps(model)
    assert raw["selected"][0]["reference_id"] not in model_json
    assert raw["learnings"][0]["analysis_id"] not in model_json
    assert "exemplo.ficticio" not in repr(snapshot)
    raw["learnings"].clear()
    assert snapshot.model_input() == model
    configured = settings.model_copy(update={"editorial_ai_mode": "openai", "openai_api_key": SecretStr("fake")})
    messages = OpenAIEditorialProvider(configured).build_request({"reference_context": model})["input"]
    assert REFERENCE_CREATIVE_RULE in messages[0]["content"]
    assert "não foram acessados ou analisados" not in messages[0]["content"]
    assert "Tom acolhedor" not in messages[0]["content"]
    assert json.loads(messages[1]["content"])["reference_context"] == model


@pytest.mark.parametrize("status", ["not_requested", "pending", "unavailable", "completed"])
def test_analysis_state_is_explicit_and_never_invented(status):
    raw = context(status=status)
    item = read_generation_snapshot(raw).model_input()[0]
    assert item["estado_analise"] == status
    assert bool(item["padroes"]) == (status == "completed")


def test_empty_context_and_all_manual_choices_are_preserved_without_truncation():
    assert read_generation_snapshot({"version": 1, "selected": [], "learnings": []}).model_input() == []
    raw = context(status="not_requested")
    raw["selected"] = [
        {
            **raw["selected"][0],
            "reference_id": str(uuid4()),
            "source": "owner",
            "score": None,
            "similarity": None,
            "note": "Minha preferência, sem análise",
        }
        for _ in range(40)
    ]
    model = read_generation_snapshot(raw).model_input()
    assert len(model) == 40
    assert all(item["nota_interna"] is None and item["padroes"] == [] for item in model)


@pytest.mark.parametrize(
    "failure",
    [
        "duplicate_selection",
        "duplicate_learning",
        "obsolete",
        "outsider",
        "missing",
        "status",
        "premature",
        "raw_post",
        "bad_version",
        "bad_score",
        "infinite_score",
        "high_score",
        "negative_score",
        "handle_url",
        "unsupported",
        "not_json",
        "null",
    ],
)
def test_invalid_or_unproven_records_fail_closed_with_stable_error(failure):
    raw = context()
    if failure == "duplicate_selection":
        raw["selected"] *= 2
    elif failure == "duplicate_learning":
        raw["learnings"] *= 2
    elif failure == "obsolete":
        raw["learnings"][0]["association_version"] = 2
    elif failure == "outsider":
        raw["learnings"][0]["reference_id"] = str(uuid4())
    elif failure == "missing":
        raw["learnings"] = []
    elif failure == "status":
        raw["learnings"][0]["status"] = "completed"
    elif failure == "premature":
        raw["selected"][0]["analysis_status"] = "pending"
    elif failure == "raw_post":
        raw["learnings"][0]["caption"] = "Conteúdo original não permitido"
    elif failure == "bad_version":
        raw["selected"][0]["association_version"] = 0
    elif failure in {"bad_score", "infinite_score", "high_score", "negative_score"}:
        raw["selected"][0]["score"] = {
            "bad_score": "raw private value",
            "infinite_score": "NaN",
            "high_score": "10.1",
            "negative_score": "-1",
        }[failure]
    elif failure == "handle_url":
        raw["selected"][0]["instagram_handle"] = "https://instagram.com/x"
    elif failure == "unsupported":
        raw["version"] = 2
    elif failure == "not_json":
        raw = object()
    else:
        raw = None
    with pytest.raises(AuthError, match="REFERENCE_GENERATION_SNAPSHOT_INVALID") as error:
        read_generation_snapshot(raw)
    assert "private" not in str(error.value) and "Conteúdo" not in str(error.value)


async def test_database_capture_and_current_check_use_scoped_server_identity_only():
    business = uuid4()
    raw = context()
    session = SimpleNamespace(scalar=AsyncMock(side_effect=[raw, True, False, None]))
    snapshot = await capture_generation_context(session, business)
    assert await generation_context_is_current(session, business, snapshot)
    assert not await generation_context_is_current(session, business, snapshot)
    assert not await generation_context_is_current(session, business, snapshot)
    assert session.scalar.call_args_list[0].args[1] == {"business": business}
    sent = session.scalar.call_args_list[1].args[1]
    assert json.loads(sent["selected"]) == snapshot.selected_versions()
    assert "Tom acolhedor" not in sent["selected"] and "exemplo.ficticio" not in sent["selected"]


async def test_editorial_revalidation_keeps_selection_lock_in_execution_transaction(settings):
    raw = context()
    row = {"tenant_id": uuid4(), "business_id": uuid4(), "actor_id": uuid4(), "reference_generation_snapshot": raw}
    session = SimpleNamespace(scalar=AsyncMock(return_value=True), execute=AsyncMock())
    service = EditorialProposalService(settings, None)
    assert await service._references_current(session, row)
    assert session.execute.await_args.args[1] == {"tenant": str(row["tenant_id"]), "actor": str(row["actor_id"])}
    assert session.scalar.await_args.args[1]["business"] == row["business_id"]
    session.scalar.return_value = False
    assert not await service._references_current(session, row)
    assert await service._references_current(session, {})
    assert await service._references_current(session, {"reference_generation_snapshot": None})
    assert not await service._references_current(session, {**row, "reference_generation_snapshot": {}})


def test_invalid_snapshot_does_not_serialize_private_input_in_temporal_failure():
    raw = context()
    private = "PROFILE_PRIVATE_VALUE_WITH_BAD_FORMAT"
    raw["selected"][0]["instagram_handle"] = private
    with pytest.raises(AuthError) as caught:
        read_generation_snapshot(raw)
    error = caught.value
    assert error.__cause__ is None and error.__suppress_context__
    assert private not in "".join(traceback.format_exception(error))
    failure = Failure()
    DefaultFailureConverter().to_failure(error, DefaultPayloadConverter(), failure)
    assert not failure.HasField("cause")
    assert private not in str(failure)
    assert failure.message == "REFERENCE_GENERATION_SNAPSHOT_INVALID"
