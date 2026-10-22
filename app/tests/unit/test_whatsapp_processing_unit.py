"""Retry, replay and malformed-message behavior at the material workflow boundary."""

import json
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr
from temporalio.exceptions import ApplicationError, WorkflowAlreadyStartedError

from app.adapters.material_media import FetchedMedia, MaterialError
from app.services import whatsapp_processing as module
from app.services.whatsapp_processing import MaterialClaim, MaterialProcessor


def fake_database(rows, eligible=(True, True)):
    statements = []
    selected = iter(rows)
    session = Mock()
    session.scalar = AsyncMock(side_effect=list(eligible))

    async def execute(statement, _params=None):
        statements.append(str(statement))
        result = Mock()
        if "SELECT delete_owner FROM whatsapp_upload_intents" in str(statement):
            result.mappings.return_value.one_or_none.return_value = {"delete_owner": None}
        elif str(statement).lstrip().startswith("SELECT"):
            result.mappings.return_value.one_or_none.return_value = next(selected)
        return result

    session.execute = AsyncMock(side_effect=execute)

    @asynccontextmanager
    async def opened():
        yield session

    session.begin = opened
    database = Mock(sessions=opened)
    return database, statements, session


def processor_with_rows(settings, messages, rows, eligible=(True, True)):
    key = Fernet.generate_key()
    cipher = Fernet(key)
    first = rows[0]
    if first is not None:
        first["ciphertext"] = cipher.encrypt(json.dumps(messages).encode()).decode()
    config = settings.model_copy(update={"meta_encryption_key": SecretStr(key.decode())})
    database, statements, session = fake_database(rows, eligible)
    media = AsyncMock()
    media.fetch.return_value = FetchedMedia(b"checked", "image/png", "a" * 64)
    store = AsyncMock()
    return MaterialProcessor(config, database, media, store), statements, session


def event_row(kind="text", state="pending", expires=None):
    return {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "business_id": uuid4(),
        "kind": kind,
        "sender_hash": "a" * 64,
        "state": state,
        "created_at": datetime.now(UTC),
        "expires_at": expires or datetime.now(UTC) + timedelta(days=1),
    }


@pytest.mark.parametrize(
    "message,code",
    [
        (["not-a-message"], "MATERIAL_INVALID"),
        ({"type": "image", "text": {"body": "idea"}}, "MATERIAL_INVALID"),
        ({"type": "text", "text": "idea"}, "MATERIAL_INVALID"),
        ({"type": "text", "text": {"body": 42}}, "MATERIAL_INVALID"),
        ({"type": "text", "text": {"body": "x" * 4097}}, "MATERIAL_INVALID"),
    ],
)
async def test_rejects_malformed_messages(settings, message, code):
    row = event_row()
    processor, statements, _ = processor_with_rows(settings, message, [row, row])
    assert await processor.process(row["id"]) == "failed"
    assert any("state='failed'" in statement for statement in statements)
    assert code == "MATERIAL_INVALID"


async def test_invalid_ciphertext_is_nonretryable(settings):
    row = event_row()
    processor, _, _ = processor_with_rows(settings, {"type": "text", "text": {"body": "ok"}}, [row])
    row["ciphertext"] = "invalid"
    with pytest.raises(ApplicationError, match="MATERIAL_INVALID"):
        await processor.process(row["id"])


async def test_absent_finished_expired_and_failed_events(settings):
    pending = event_row(expires=datetime.now(UTC) - timedelta(seconds=1))
    processor, _, _ = processor_with_rows(settings, {}, [None])
    assert await processor.process(uuid4()) == "already_finished"
    processor, _, _ = processor_with_rows(settings, {}, [event_row(state="processed")])
    assert await processor.process(uuid4()) == "already_finished"
    processor, _, _ = processor_with_rows(settings, {}, [pending, pending])
    assert await processor.process(pending["id"]) == "failed"


@pytest.mark.parametrize("current", [None, "processed", "revoked"])
async def test_rechecks_access_and_state_after_media_fetch(settings, current):
    row = event_row(kind="image")
    second = None if current is None else dict(row, state=current if current == "processed" else "pending")
    processor, statements, session = processor_with_rows(
        settings,
        {"type": "image", "image": {"id": "123"}},
        [row, second],
        eligible=[True, current != "revoked"],
    )
    expected = "failed" if current == "revoked" else "already_finished"
    assert await processor.process(row["id"]) == expected
    processor.store.put.assert_awaited_once()
    if current == "revoked":
        assert any("state='failed'" in statement for statement in statements)
        assert session.scalar.await_count == 2


@pytest.mark.parametrize("problem,retryable", [("MEDIA_ID_INVALID", False), ("META_MEDIA_UNAVAILABLE", True)])
async def test_provider_error_is_terminal_or_retryable(settings, problem, retryable):
    row = event_row(kind="image")
    processor, _, _ = processor_with_rows(settings, {"type": "image", "image": {"id": "123"}}, [row, row])
    processor.media.fetch.side_effect = MaterialError(problem, retryable=retryable)
    if retryable:
        with pytest.raises(ApplicationError, match=problem):
            await processor.process(row["id"])
    else:
        assert await processor.process(row["id"]) == "failed"


async def test_failed_upload_keeps_a_reconcilable_intent(settings):
    row = event_row(kind="image")
    processor, statements, _ = processor_with_rows(settings, {"type": "image", "image": {"id": "123"}}, [row])
    processor.store.put.side_effect = MaterialError("MATERIAL_STORAGE_UNAVAILABLE", retryable=True)
    with pytest.raises(ApplicationError, match="MATERIAL_STORAGE_UNAVAILABLE"):
        await processor.process(row["id"])
    assert any("INSERT INTO whatsapp_upload_intents" in statement for statement in statements)
    assert not any("DELETE FROM whatsapp_upload_intents" in statement for statement in statements)


@pytest.mark.parametrize("stage", [None, {"delete_owner": uuid4()}])
async def test_finalizer_cannot_attach_an_upload_claimed_by_reconciler(settings, stage):
    row = event_row(kind="image")
    processor, statements, session = processor_with_rows(
        settings, {"type": "image", "image": {"id": "123"}}, [row, row]
    )
    original_execute = session.execute.side_effect

    async def execute(statement, params=None):
        if "SELECT delete_owner FROM whatsapp_upload_intents" in str(statement):
            result = Mock()
            result.mappings.return_value.one_or_none.return_value = stage
            return result
        return await original_execute(statement, params)

    session.execute.side_effect = execute
    assert await processor.process(row["id"]) == "failed"
    assert not any("INSERT INTO whatsapp_material_assets" in statement for statement in statements)
    assert any("UPLOAD_RECONCILING" in str(call) for call in session.execute.call_args_list)


async def test_invalid_media_identifier_and_failure_activity(settings):
    row = event_row(kind="image")
    processor, _, _ = processor_with_rows(settings, {"type": "image", "image": {}}, [row, row])
    assert await processor.process(row["id"]) == "failed"
    processor, _, _ = processor_with_rows(settings, {}, [row])
    assert await processor.fail(row["id"]) == "failed"
    processor, _, _ = processor_with_rows(settings, {}, [None])
    assert await processor.fail(row["id"]) == "already_finished"


@pytest.mark.parametrize("failure", [None, "already", "unavailable"])
async def test_dispatch_handles_replay_and_temporal_failure(settings, monkeypatch, failure):
    claim = MaterialClaim(uuid4(), uuid4(), uuid4(), uuid4(), 1)
    monkeypatch.setattr(module, "claim_materials", AsyncMock(return_value=[claim]))
    finished = AsyncMock()
    monkeypatch.setattr(module, "finish_dispatch", finished)
    client = Mock()
    client.start_workflow = AsyncMock()
    if failure == "already":
        client.start_workflow.side_effect = WorkflowAlreadyStartedError(str(claim.id), "WhatsAppMaterialWorkflow")
    if failure == "unavailable":
        client.start_workflow.side_effect = RuntimeError("Temporal unavailable")
    assert await module.dispatch_materials(Mock(), client, settings, claim.owner_id) == 1
    finished.assert_awaited_once()
    assert finished.call_args.kwargs["accepted"] is (failure != "unavailable")


@pytest.mark.parametrize(
    "accepted,attempts,found,audited",
    [
        (True, 5, True, False),
        (False, 4, True, False),
        (False, 5, True, True),
        (False, 5, False, False),
    ],
)
async def test_dispatch_transition_audits_terminal_provider_failure(accepted, attempts, found, audited):
    claim = MaterialClaim(uuid4(), uuid4(), uuid4(), uuid4(), 3)
    row = {"tenant_id": claim.tenant_id, "business_id": claim.business_id, "attempts": attempts} if found else None
    session = Mock()
    result = Mock()
    result.mappings.return_value.one_or_none.return_value = row
    session.execute = AsyncMock(return_value=result)

    @asynccontextmanager
    async def opened():
        yield session

    session.begin = opened
    await module.finish_dispatch(Mock(sessions=opened), claim, accepted=accepted)
    assert session.execute.await_count == (2 if audited else 1)
    if audited:
        assert "whatsapp.material_dispatch_failed" in str(session.execute.call_args_list[-1].args[0])
