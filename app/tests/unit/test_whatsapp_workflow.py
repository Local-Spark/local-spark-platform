"""Material workflow delegates side effects to retryable activities."""

from unittest.mock import AsyncMock
from uuid import uuid4

from app.workflows import whatsapp_material as module
from app.workflows.whatsapp_activities import WhatsAppMaterialActivities


async def test_material_workflow_success_and_terminal_failure(monkeypatch):
    execute = AsyncMock(side_effect=["processed", "completed", RuntimeError("failed"), "failed"])
    monkeypatch.setattr(module.workflow, "execute_activity", execute)
    workflow = module.WhatsAppMaterialWorkflow()
    assert await workflow.run("event-1") == "processed"
    assert await workflow.run("event-2") == "failed"
    assert execute.await_count == 4
    assert execute.await_args.args == ("fail_whatsapp_material", "event-2")


async def test_transcription_failure_does_not_fail_stored_material(monkeypatch):
    execute = AsyncMock(side_effect=["processed", RuntimeError("provider uncertain")])
    monkeypatch.setattr(module.workflow, "execute_activity", execute)
    assert await module.WhatsAppMaterialWorkflow().run("event") == "processed"


async def test_failed_material_does_not_submit_audio(monkeypatch):
    execute = AsyncMock(return_value="already_finished")
    monkeypatch.setattr(module.workflow, "execute_activity", execute)
    assert await module.WhatsAppMaterialWorkflow().run("event") == "already_finished"
    execute.assert_awaited_once()


async def test_activity_converts_event_identity_and_invokes_processor():
    processor = AsyncMock()
    processor.process.return_value = "processed"
    processor.fail.return_value = "failed"
    event = uuid4()
    activity = WhatsAppMaterialActivities(processor)
    assert await activity.process_whatsapp_material(str(event)) == "processed"
    assert await activity.fail_whatsapp_material(str(event)) == "failed"
    assert await activity.transcribe_whatsapp_audio(str(event)) == "disabled"
    transcription = AsyncMock()
    transcription.run.return_value = "completed"
    activity = WhatsAppMaterialActivities(processor, transcription)
    assert await activity.transcribe_whatsapp_audio(str(event)) == "completed"
    processor.process.assert_awaited_once_with(event)
    processor.fail.assert_awaited_once_with(event)
