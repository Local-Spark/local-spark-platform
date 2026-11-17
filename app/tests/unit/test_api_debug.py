"""The local debugger must not retain execution settings from a stale parent shell."""

import os
import runpy
from unittest.mock import Mock

import pytest

from app.entrypoints import api_debug


def test_debug_launch_refreshes_environment_before_starting_uvicorn(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("MEU_BRACO_DIREITO_MOTION_RENDERER_IMAGE=sha256:new\n")
    monkeypatch.setenv("MEU_BRACO_DIREITO_MOTION_RENDERER_IMAGE", "sha256:old")
    monkeypatch.setenv("UNRELATED_DEBUG_VALUE", "preserved")
    monkeypatch.setattr(api_debug, "ENV_FILE", env)

    def launch(name, *, run_name):
        assert (name, run_name) == ("uvicorn", "__main__")
        assert os.environ["MEU_BRACO_DIREITO_MOTION_RENDERER_IMAGE"] == "sha256:new"
        assert os.environ["UNRELATED_DEBUG_VALUE"] == "preserved"

    start = Mock(side_effect=launch)
    monkeypatch.setattr(api_debug.runpy, "run_module", start)
    api_debug.main()
    start.assert_called_once()


def test_missing_debug_env_does_not_start_with_inherited_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(api_debug, "ENV_FILE", tmp_path / "absent")
    start = Mock()
    monkeypatch.setattr(api_debug.runpy, "run_module", start)
    with pytest.raises(RuntimeError, match="LOCAL_DEBUG_ENV_FILE_REQUIRED"):
        api_debug.main()
    start.assert_not_called()


def test_module_entrypoint_invokes_uvicorn_after_refresh(monkeypatch):
    load = Mock()
    start = Mock()
    monkeypatch.setattr("dotenv.load_dotenv", load)
    monkeypatch.setattr("pathlib.Path.is_file", lambda _: True)
    monkeypatch.setattr(runpy, "run_module", start)
    runpy.run_path(str(api_debug.ENV_FILE.parent / "app/entrypoints/api_debug.py"), run_name="__main__")
    load.assert_called_once_with(api_debug.ENV_FILE, override=True)
    start.assert_called_once_with("uvicorn", run_name="__main__")
