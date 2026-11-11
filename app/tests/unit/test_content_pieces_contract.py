"""Review requests bind the complete ordered artifact set and explicit human checks."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.api.v1.content_pieces import service
from app.schemas.content_pieces import PieceArtifactRead, PieceDecision, PieceFromPreview


def artifact(position=0, **change):
    return {
        "id": uuid4(),
        "position": position,
        "sha256": "a" * 64,
        "mime_type": "video/mp4",
        "size_bytes": 100,
        **change,
    }


def confirmation(sha="a" * 64):
    return {
        "preview_sha256": sha,
        "price_and_terms": True,
        "spelling": True,
        "identity": True,
        "fidelity": True,
        "legibility": True,
    }


def decision(**change):
    return {
        "operation_id": uuid4(),
        "version_id": uuid4(),
        "decision": "approve",
        "artifacts": [artifact()],
        "confirmations": [confirmation()],
        **change,
    }


@pytest.mark.parametrize("mime", ["image/png", "image/jpeg", "video/mp4"])
def test_review_can_bind_each_supported_file_type(mime):
    assert PieceDecision.model_validate(decision(artifacts=[artifact(mime_type=mime)])).artifacts[0].mime_type == mime


@pytest.mark.parametrize(
    ("change", "error"),
    [
        ({"artifacts": [artifact(position=1)]}, "PIECE_ARTIFACT_ORDER_INVALID"),
        ({"artifacts": [artifact(1), artifact(0)]}, "PIECE_ARTIFACT_ORDER_INVALID"),
        ({"confirmations": []}, "PIECE_REVIEW_INCOMPLETE"),
        ({"confirmations": [confirmation("b" * 64)]}, "PIECE_REVIEW_INCOMPLETE"),
        ({"page_positions": [0]}, "PIECE_APPROVAL_MUST_COVER_ALL_PAGES"),
        ({"decision": "request_changes", "note": None}, "PIECE_CHANGE_NOTE_REQUIRED"),
        ({"decision": "request_changes", "note": "   "}, "PIECE_CHANGE_NOTE_REQUIRED"),
        (
            {"decision": "request_changes", "note": "Aumentar texto", "page_positions": [0, 0]},
            "PIECE_CHANGE_PAGES_INVALID",
        ),
        (
            {"decision": "request_changes", "note": "Aumentar texto", "page_positions": [-1]},
            "PIECE_CHANGE_PAGES_INVALID",
        ),
        (
            {"decision": "request_changes", "note": "Aumentar texto", "page_positions": [1]},
            "PIECE_CHANGE_PAGES_INVALID",
        ),
    ],
)
def test_invalid_review_is_rejected_before_any_effect(change, error):
    with pytest.raises(ValidationError, match=error):
        PieceDecision.model_validate(decision(**change))


def test_duplicate_files_and_wrong_confirmation_order_are_rejected():
    first = artifact()
    with pytest.raises(ValidationError, match="PIECE_ARTIFACT_DUPLICATE"):
        PieceDecision.model_validate(decision(artifacts=[first, {**first, "position": 1}]))
    files = [first, artifact(1, sha256="b" * 64)]
    with pytest.raises(ValidationError, match="PIECE_REVIEW_INCOMPLETE"):
        PieceDecision.model_validate(decision(artifacts=files, confirmations=[confirmation("b" * 64), confirmation()]))
    accepted = PieceDecision.model_validate(
        decision(artifacts=files, confirmations=[confirmation(), confirmation("b" * 64)])
    )
    assert [a.position for a in accepted.artifacts] == [0, 1]
    change = PieceDecision.model_validate(
        decision(
            decision="request_changes", artifacts=files, confirmations=[], note="Ajustar página 2", page_positions=[1]
        )
    )
    assert change.page_positions == [1]
    assert (
        PieceDecision.model_validate(
            decision(decision="request_changes", note="Ajustar tudo", confirmations=[])
        ).page_positions
        == []
    )


@pytest.mark.parametrize(
    "change", [{"object_key": "private/arbitrary"}, {"mime_type": "text/html"}, {"sha256": "A" * 64}, {"size_bytes": 0}]
)
def test_public_artifact_contract_rejects_storage_keys_and_invalid_metadata(change):
    with pytest.raises(ValidationError):
        PieceArtifactRead.model_validate(artifact(**change))


def test_public_import_cannot_supply_a_version_or_object_key():
    with pytest.raises(ValidationError):
        PieceFromPreview.model_validate({"operation_id": uuid4(), "preview_id": uuid4(), "object_key": "external"})


def test_route_factory_uses_only_the_application_database(settings):
    database, worker_database = object(), object()
    request = SimpleNamespace(
        app=SimpleNamespace(
            state=SimpleNamespace(settings=settings, database=database, correlator_database=worker_database)
        )
    )
    created = service(request)
    assert created.database is database
    assert created.settings is settings
