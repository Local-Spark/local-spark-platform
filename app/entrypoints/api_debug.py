"""Local VS Code launcher: refresh .env before importing the application settings."""

import runpy
from pathlib import Path

from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def main() -> None:
    # Integrated terminals/debug adapters can retain exported values across restarts.
    # Override only in this explicit local launcher, never in production Settings.
    if not ENV_FILE.is_file():
        raise RuntimeError("LOCAL_DEBUG_ENV_FILE_REQUIRED")
    load_dotenv(ENV_FILE, override=True)
    runpy.run_module("uvicorn", run_name="__main__")


if __name__ == "__main__":
    main()
