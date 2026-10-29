import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr

from app.entrypoints import relay, worker


async def test_temporal_connection_configuration(settings, monkeypatch):
    connect = AsyncMock()
    monkeypatch.setattr(worker.Client, "connect", connect)
    await worker.connect_temporal(settings)
    assert connect.call_args.kwargs["namespace"] == settings.temporal_namespace
    assert connect.call_args.kwargs["api_key"] is None
    from pydantic import SecretStr

    secured = settings.model_copy(update={"temporal_tls": True, "temporal_api_key": SecretStr("test-key")})
    await worker.connect_temporal(secured)
    assert connect.call_args.kwargs["api_key"] == "test-key"
    assert connect.call_args.kwargs["tls"] is True


@pytest.mark.parametrize("failure", [False, True])
async def test_worker_closes_database_on_exit(settings, fake_database, monkeypatch, failure):
    monkeypatch.setattr(worker, "get_settings", lambda: settings.model_copy(update={"correlator_database_url": None}))
    monkeypatch.setattr(worker, "Database", lambda _: fake_database)
    monkeypatch.setattr(worker, "connect_temporal", AsyncMock())
    execution = MagicMock()
    execution.run = AsyncMock(side_effect=RuntimeError("failure") if failure else None)
    monkeypatch.setattr(worker, "Worker", lambda *args, **kwargs: execution)
    if failure:
        with pytest.raises(RuntimeError):
            await worker.run_worker()
    else:
        await worker.run_worker()
    fake_database.close.assert_awaited_once()


async def test_material_worker_registers_activities_and_closes_both_pools(settings, monkeypatch):
    database = AsyncMock()
    configured = settings.model_copy(update={"meta_encryption_key": SecretStr(Fernet.generate_key().decode())})
    monkeypatch.setattr(worker, "get_settings", lambda: configured)
    monkeypatch.setattr(worker, "Database", lambda *args, **kwargs: database)
    monkeypatch.setattr(worker, "connect_temporal", AsyncMock())
    execution = MagicMock()
    execution.run = AsyncMock()
    constructor = MagicMock(return_value=execution)
    monkeypatch.setattr(worker, "Worker", constructor)
    await worker.run_worker()
    assert len(constructor.call_args.kwargs["workflows"]) == 7
    assert worker.BrandKitChangedWorkflow in constructor.call_args.kwargs["workflows"]
    assert len(constructor.call_args.kwargs["activities"]) == 15
    assert any(
        activity.__name__ == "deliver_briefing_clarification" for activity in constructor.call_args.kwargs["activities"]
    )
    assert any(
        activity.__name__ == "record_brand_kit_changed" for activity in constructor.call_args.kwargs["activities"]
    )
    assert database.close.await_count == 2


async def test_explicit_visual_worker_registers_new_workflow_alongside_legacy(settings, monkeypatch):
    from app.tests.unit.test_visual_generation_runner import _enabled

    database = AsyncMock()
    monkeypatch.setattr(worker, "get_settings", lambda: _enabled(settings))
    monkeypatch.setattr(worker, "Database", lambda *args, **kwargs: database)
    monkeypatch.setattr(worker, "connect_temporal", AsyncMock())
    runner = MagicMock()
    constructor = MagicMock(return_value=runner)
    monkeypatch.setattr(worker, "DatabaseVisualGenerationRunner", constructor)
    execution = MagicMock(run=AsyncMock())
    temporal_worker = MagicMock(return_value=execution)
    monkeypatch.setattr(worker, "Worker", temporal_worker)
    await worker.run_worker()
    constructor.assert_called_once()
    workflows = temporal_worker.call_args.kwargs["workflows"]
    assert worker.VisualGenerationWorkflow in workflows and worker.StaticPreviewWorkflow in workflows
    assert len(workflows) == 8
    assert any(
        activity.__name__ == "run_visual_generation" for activity in temporal_worker.call_args.kwargs["activities"]
    )
    assert database.close.await_count == 2


async def test_visual_worker_without_restricted_pool_fails_before_connecting(settings, monkeypatch):
    from app.tests.unit.test_visual_generation_runner import _enabled

    database = AsyncMock()
    configured = _enabled(settings).model_copy(update={"correlator_database_url": None})
    monkeypatch.setattr(worker, "get_settings", lambda: configured)
    monkeypatch.setattr(worker, "Database", lambda *args, **kwargs: database)
    connect = AsyncMock()
    monkeypatch.setattr(worker, "connect_temporal", connect)
    with pytest.raises(RuntimeError, match="VISUAL_WORKER_DATABASE_REQUIRED"):
        await worker.run_worker()
    database.close.assert_awaited_once()
    connect.assert_not_awaited()


async def test_worker_does_not_register_material_activity_without_cipher_key(settings, monkeypatch):
    database = AsyncMock()
    configured = settings.model_copy(
        update={"correlator_database_url": settings.database_url, "meta_encryption_key": None}
    )
    monkeypatch.setattr(worker, "get_settings", lambda: configured)
    monkeypatch.setattr(worker, "Database", lambda *args, **kwargs: database)
    monkeypatch.setattr(worker, "connect_temporal", AsyncMock())
    execution = MagicMock()
    execution.run = AsyncMock()
    constructor = MagicMock(return_value=execution)
    monkeypatch.setattr(worker, "Worker", constructor)
    await worker.run_worker()
    assert len(constructor.call_args.kwargs["workflows"]) == 4
    assert worker.BrandKitChangedWorkflow in constructor.call_args.kwargs["workflows"]
    assert len(constructor.call_args.kwargs["activities"]) == 4
    assert any(
        activity.__name__ == "record_brand_kit_changed" for activity in constructor.call_args.kwargs["activities"]
    )
    assert database.close.await_count == 2


async def test_whatsapp_dispatcher_disabled_and_loop_shutdown(settings, monkeypatch):
    from app.entrypoints import whatsapp_dispatcher as dispatcher

    disabled = settings.model_copy(update={"correlator_database_url": None})
    monkeypatch.setattr(dispatcher, "get_settings", lambda: disabled)
    database = AsyncMock()
    monkeypatch.setattr(dispatcher, "Database", lambda *args, **kwargs: database)
    await dispatcher.run_dispatcher()
    database.close.assert_not_awaited()

    from cryptography.fernet import Fernet
    from pydantic import SecretStr

    configured = settings.model_copy(update={"meta_encryption_key": SecretStr(Fernet.generate_key().decode())})
    monkeypatch.setattr(dispatcher, "get_settings", lambda: configured)
    monkeypatch.setattr(dispatcher, "connect_temporal", AsyncMock())
    dispatch = AsyncMock(side_effect=[1, 0, asyncio.CancelledError()])
    monkeypatch.setattr(dispatcher, "dispatch_materials", dispatch)
    monkeypatch.setattr(dispatcher, "dispatch_proposals", AsyncMock(return_value=1))
    monkeypatch.setattr(dispatcher, "dispatch_previews", AsyncMock(return_value=1))
    monkeypatch.setattr(dispatcher, "dispatch_publications", AsyncMock(return_value=1))
    purge = AsyncMock(return_value=1)
    monkeypatch.setattr(dispatcher, "purge_once", purge)
    monkeypatch.setattr(dispatcher, "reconcile_stale_audio", AsyncMock(return_value=0))
    monkeypatch.setattr(dispatcher, "reconcile_stale_proposals", AsyncMock(return_value=0))
    monkeypatch.setattr(dispatcher, "reconcile_stale_previews", AsyncMock(return_value=0))
    monkeypatch.setattr(dispatcher, "reconcile_publications", AsyncMock(return_value=0))
    monkeypatch.setattr(dispatcher, "purge_expired_previews", AsyncMock(return_value=0))
    monkeypatch.setattr(dispatcher.asyncio, "sleep", AsyncMock())
    with pytest.raises(asyncio.CancelledError):
        await dispatcher.run_dispatcher()
    assert dispatch.await_count == 3
    purge.assert_awaited_once()
    dispatcher.reconcile_stale_audio.assert_awaited_once()
    assert database.close.await_count == 1


async def test_whatsapp_dispatcher_empty_purge_is_quiet(settings, monkeypatch):
    from app.entrypoints import whatsapp_dispatcher as dispatcher

    configured = settings.model_copy(update={"meta_encryption_key": SecretStr(Fernet.generate_key().decode())})
    monkeypatch.setattr(dispatcher, "get_settings", lambda: configured)
    database = AsyncMock()
    monkeypatch.setattr(dispatcher, "Database", lambda *args, **kwargs: database)
    monkeypatch.setattr(dispatcher, "connect_temporal", AsyncMock())
    monkeypatch.setattr(dispatcher, "dispatch_materials", AsyncMock(side_effect=[0, asyncio.CancelledError()]))
    monkeypatch.setattr(dispatcher, "dispatch_proposals", AsyncMock(return_value=0))
    monkeypatch.setattr(dispatcher, "dispatch_previews", AsyncMock(return_value=0))
    monkeypatch.setattr(dispatcher, "dispatch_publications", AsyncMock(return_value=0))
    monkeypatch.setattr(dispatcher, "purge_once", AsyncMock(return_value=0))
    monkeypatch.setattr(dispatcher, "reconcile_stale_audio", AsyncMock(return_value=0))
    monkeypatch.setattr(dispatcher, "reconcile_stale_proposals", AsyncMock(return_value=0))
    monkeypatch.setattr(dispatcher, "reconcile_stale_previews", AsyncMock(return_value=0))
    monkeypatch.setattr(dispatcher, "reconcile_publications", AsyncMock(return_value=0))
    monkeypatch.setattr(dispatcher, "purge_expired_previews", AsyncMock(return_value=0))
    monkeypatch.setattr(dispatcher.asyncio, "sleep", AsyncMock())
    with pytest.raises(asyncio.CancelledError):
        await dispatcher.run_dispatcher()
    dispatcher.purge_once.assert_awaited_once()


async def test_editorial_dispatcher_runs_without_whatsapp_cipher(settings, monkeypatch):
    from app.entrypoints import whatsapp_dispatcher as dispatcher

    configured = settings.model_copy(update={"meta_encryption_key": None})
    monkeypatch.setattr(dispatcher, "get_settings", lambda: configured)
    database = AsyncMock()
    monkeypatch.setattr(dispatcher, "Database", lambda *args, **kwargs: database)
    monkeypatch.setattr(dispatcher, "connect_temporal", AsyncMock())
    material = AsyncMock()
    monkeypatch.setattr(dispatcher, "dispatch_materials", material)
    proposal = AsyncMock(return_value=1)
    monkeypatch.setattr(dispatcher, "dispatch_proposals", proposal)
    monkeypatch.setattr(dispatcher, "dispatch_previews", AsyncMock(return_value=0))
    reconcile = AsyncMock(return_value=0)
    monkeypatch.setattr(dispatcher, "reconcile_stale_proposals", reconcile)
    monkeypatch.setattr(dispatcher, "reconcile_stale_previews", AsyncMock(return_value=0))
    monkeypatch.setattr(dispatcher, "purge_expired_previews", AsyncMock(return_value=0))
    purge = AsyncMock()
    monkeypatch.setattr(dispatcher, "purge_once", purge)
    monkeypatch.setattr(dispatcher.asyncio, "sleep", AsyncMock(side_effect=asyncio.CancelledError()))
    with pytest.raises(asyncio.CancelledError):
        await dispatcher.run_dispatcher()
    material.assert_not_awaited()
    proposal.assert_awaited_once()
    reconcile.assert_awaited_once()
    purge.assert_not_awaited()
    database.close.assert_awaited_once()


async def test_relay_releases_database_on_shutdown(settings, fake_database, monkeypatch):
    monkeypatch.setattr(relay, "get_settings", lambda: settings)
    monkeypatch.setattr(relay, "Database", lambda *args, **kwargs: fake_database)
    monkeypatch.setattr(relay, "connect_temporal", AsyncMock())
    dispatch = AsyncMock()
    monkeypatch.setattr(relay, "dispatch_once", dispatch)
    monkeypatch.setattr(relay.asyncio, "sleep", AsyncMock(side_effect=asyncio.CancelledError()))
    with pytest.raises(asyncio.CancelledError):
        await relay.run_relay()
    dispatch.assert_awaited_once()
    fake_database.close.assert_awaited_once()


async def test_auth_mail_worker_closes_pool_and_waits_when_empty(settings, fake_database, monkeypatch):
    from app.entrypoints import auth_mail

    monkeypatch.setattr(auth_mail, "get_settings", lambda: settings)
    monkeypatch.setattr(auth_mail, "Database", lambda *args, **kwargs: fake_database)
    delivery = AsyncMock(side_effect=[False, True, asyncio.CancelledError()])
    sleep = AsyncMock()
    monkeypatch.setattr(auth_mail, "deliver_once", delivery)
    monkeypatch.setattr(auth_mail.asyncio, "sleep", sleep)
    with pytest.raises(asyncio.CancelledError):
        await auth_mail.main()
    sleep.assert_awaited_once_with(1)
    fake_database.close.assert_awaited_once()
