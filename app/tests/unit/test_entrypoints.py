import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

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
    monkeypatch.setattr(worker, "get_settings", lambda: settings)
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
