"""The executor check uses only synthetic media and never starts product processing."""

import json
import runpy
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.entrypoints import motion_executor_check as check


def test_module_command_runs_without_loading_project_credentials(settings, monkeypatch, capsys):
    monkeypatch.setattr("app.core.config.get_settings", lambda: settings)

    def run(coroutine):
        coroutine.close()
        return {"event": "motion.executor.checked"}

    monkeypatch.setattr(check.asyncio, "run", run)
    runpy.run_path(check.__file__, run_name="__main__")
    assert json.loads(capsys.readouterr().out) == {"event": "motion.executor.checked"}


async def test_check_is_bounded_and_uses_the_real_adapter_contract(settings, monkeypatch):
    configured = settings.model_copy(
        update={
            "motion_renderer_image": "sha256:" + "a" * 64,
            "motion_renderer_docker_executable": "/usr/local/bin/docker",
            "motion_renderer_docker_socket": "/run/motion-docker.sock",
            "motion_renderer_scratch_directory": "/shared/motion",
        }
    )

    async def render(renderer, bundle, *, operation_id):
        assert renderer.timeout_seconds == 60
        assert str(renderer.scratch_directory) == "/shared/motion"
        assert bundle.width == bundle.height == 64 and bundle.duration_ms == 34
        assert bundle.assets == () and bundle.audio == {"mode": "silent", "tracks": []}
        assert operation_id.version == 4
        return SimpleNamespace(mp4=b"synthetic", evidence=(1, 2), sha256="a" * 64)

    monkeypatch.setattr(check.IsolatedMotionRenderer, "render", render)
    report = await check.check_executor(configured)
    assert report == {"event": "motion.executor.checked", "video_bytes": 9, "evidence_frames": 2, "sha256": "a" * 64}


async def test_check_requires_an_explicit_shared_directory(settings):
    with pytest.raises(check.MotionRenderError, match="SHARED_SCRATCH_REQUIRED"):
        await check.check_executor(settings)


@pytest.mark.parametrize("fails", [False, True])
def test_command_reports_only_allowlisted_fields(settings, monkeypatch, capsys, fails):
    monkeypatch.setattr(check, "get_settings", lambda: settings)
    operation = AsyncMock(return_value={"event": "motion.executor.checked"})
    if fails:
        operation.side_effect = check.MotionRenderError("MOTION_RENDER_TIMEOUT")
    monkeypatch.setattr(check, "check_executor", operation)
    if fails:
        with pytest.raises(SystemExit) as exc:
            check.main()
        assert exc.value.code == 1
        assert json.loads(capsys.readouterr().out) == {
            "event": "motion.executor.check_failed",
            "code": "MOTION_RENDER_TIMEOUT",
        }
    else:
        check.main()
        assert json.loads(capsys.readouterr().out) == {"event": "motion.executor.checked"}
    operation.assert_awaited_once_with(settings)


@pytest.mark.parametrize("invalid", [None, "video", "missing_frame"])
async def test_storyboard_enabled_checks_frames_only_protocol(settings, monkeypatch, invalid):
    configured = settings.model_copy(
        update={
            "motion_storyboard_enabled": True,
            "motion_renderer_docker_executable": "/usr/local/bin/docker",
            "motion_renderer_docker_socket": "/run/motion-docker.sock",
            "motion_renderer_scratch_directory": "/shared/motion",
            "motion_renderer_image": "sha256:" + "a" * 64,
        }
    )
    bundles = []

    async def render(renderer, bundle, *, operation_id):
        bundles.append(bundle)
        if bundle.frames_only:
            return SimpleNamespace(
                mp4=b"unexpected" if invalid == "video" else b"",
                evidence=() if invalid == "missing_frame" else (1,),
            )
        return SimpleNamespace(mp4=b"video", evidence=(1,), sha256="a" * 64)

    monkeypatch.setattr(check.IsolatedMotionRenderer, "render", render)
    if invalid:
        with pytest.raises(check.MotionRenderError, match="STORYBOARD_CHECK_FAILED"):
            await check.check_executor(configured)
    else:
        assert (await check.check_executor(configured))["storyboard_frames"] == 1
    assert len(bundles) == 2
    assert not bundles[0].frames_only
    assert bundles[1].frames_only and bundles[1].sample_times_ms == (0,)
