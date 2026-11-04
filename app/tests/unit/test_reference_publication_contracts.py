"""The client can select occurrences; only a trusted activity supplies effects."""

import json
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import DBAPIError

from app.schemas.reference_results import ReferenceSelectionRequest
from app.services.auth import AuthError
from app.services.reference_filtered_commit import FilteredCommitContext
from app.services.reference_publication import (
    CompletedContacts,
    CompletedEffect,
    CompletedRecommendation,
    PublicationProjection,
    publish_reference_shortlist,
)
from app.services.reference_results import ReferenceResultsService


def _effect():
    return CompletedEffect(effect_id=uuid4(), event_id=uuid4(), executor_token=uuid4())


def _selection(**changes):
    return {
        "operation_id": uuid4(),
        "cycle_id": uuid4(),
        "selection": [{"result_id": uuid4(), "candidate_id": uuid4()}],
        **changes,
    }


def _database(value=None, error=None):
    session = SimpleNamespace(scalar=AsyncMock(return_value=value, side_effect=error))

    @asynccontextmanager
    async def transaction(tenant, actor):
        yield session

    return SimpleNamespace(transaction=transaction), session


def test_client_cannot_supply_scores_place_ids_provider_receipts_or_more_than_three():
    for change in ({"reputation_score": "9"}, {"place_id": "google-id"}, {"executor_token": uuid4()}):
        payload = _selection()
        payload["selection"][0].update(change)
        with pytest.raises(ValidationError):
            ReferenceSelectionRequest.model_validate(payload)
    payload = _selection()
    for items in ([], payload["selection"] * 2, payload["selection"] * 4):
        with pytest.raises(ValidationError):
            ReferenceSelectionRequest.model_validate({**payload, "selection": items})
    decision = {"place_identity": uuid4(), "action": "keep"}
    for changes in ({"decisions": [decision]}, {"first_result_id": uuid4(), "decisions": [decision, decision]}):
        with pytest.raises(ValidationError):
            ReferenceSelectionRequest.model_validate(_selection(**changes))
    valid = ReferenceSelectionRequest.model_validate(_selection(first_result_id=uuid4(), decisions=[decision]))
    assert valid.decisions[0].action == "keep"


def test_internal_projection_preserves_provider_order_and_rejects_duplicate_unbounded_outputs():
    effect = _effect()
    contacts = CompletedContacts(
        candidate_id=uuid4(), effect=effect, handles=("@First", "MAIN"), primary_handle="@Main"
    )
    assert contacts.handles == ("first", "main") and contacts.primary_handle == "main"
    assert CompletedContacts(candidate_id=uuid4(), effect=_effect(), primary_handle=None).handles == ()
    for changes in ({"handles": ("duplicate", "@duplicate")}, {"handles": ("first",), "primary_handle": "absent"}):
        with pytest.raises(ValidationError):
            CompletedContacts(candidate_id=uuid4(), effect=effect, **changes)
    for ids in ((uuid4(),) * 2, tuple(uuid4() for _ in range(4))):
        with pytest.raises(ValidationError):
            CompletedRecommendation(effect=effect, candidate_ids=ids)
    recommendation = CompletedRecommendation(effect=effect, candidate_ids=(uuid4(),))
    assert len(recommendation.candidate_ids) == 1
    for values in ((contacts, contacts), (contacts, contacts.model_copy(update={"candidate_id": uuid4()}))):
        with pytest.raises(ValidationError):
            PublicationProjection(operation_id=uuid4(), contacts=values)
    with pytest.raises(ValidationError):
        PublicationProjection(operation_id=uuid4(), place_id="raw-google-id")


async def test_private_publisher_sends_only_identifiers_and_typed_sanitized_projection():
    ids = [uuid4() for _ in range(11)]
    ctx = FilteredCommitContext(*ids[:5], ids[5], ids[6], ids[7], ids[8], ids[9], ids[10], "a" * 64, 1)
    result = uuid4()
    db, session = _database(result)
    projection = PublicationProjection(operation_id=uuid4())
    assert await publish_reference_shortlist(db, ctx, projection) == result
    params = session.scalar.await_args.args[1]
    assert json.loads(params["projection"]) == projection.model_dump(mode="json")
    assert "reputation_score" not in params and "place_id" not in params


@pytest.mark.parametrize(
    "code,status",
    [
        ("REFERENCE_OWNER_INACTIVE", 403),
        ("REFERENCE_SELECTION_OPERATION_CONFLICT", 409),
        ("REFERENCE_CYCLE_DECISION_NOT_REQUIRED", 409),
        ("REFERENCE_SELECTION_CYCLE_STALE", 409),
        ("REFERENCE_SELECTION_RESULT_PENDING", 409),
        ("REFERENCE_SELECTION_INVALID_CANDIDATE", 409),
        ("REFERENCE_SELECTION_DUPLICATE_ENTITY", 409),
        ("REFERENCE_CYCLE_DECISION_INCOMPLETE", 409),
        ("REFERENCE_CYCLE_DECISION_SELECTION_MISMATCH", 409),
    ],
)
async def test_selection_maps_only_known_database_conflicts(code, status):
    db, _ = _database(error=DBAPIError(None, None, Exception(code), False))
    with pytest.raises(AuthError) as caught:
        await ReferenceResultsService(db).confirm(
            uuid4(), uuid4(), uuid4(), ReferenceSelectionRequest.model_validate(_selection())
        )
    assert caught.value.status == status


async def test_unknown_database_failure_remains_an_internal_failure():
    error = DBAPIError(None, None, Exception("unexpected"), False)
    db, _ = _database(error=error)
    with pytest.raises(DBAPIError) as caught:
        await ReferenceResultsService(db).confirm(
            uuid4(), uuid4(), uuid4(), ReferenceSelectionRequest.model_validate(_selection())
        )
    assert caught.value is error
