"""One tiny synthetic render to verify the packaged executor, without DB or AI calls."""

import asyncio
import json
from pathlib import Path

from app.adapters.motion_html_renderer import IsolatedMotionRenderer, MotionRenderError, RenderBundle
from app.core.config import Settings, get_settings


async def check_executor(settings: Settings) -> dict[str, object]:
    from uuid import uuid4

    if not settings.motion_renderer_scratch_directory:
        raise MotionRenderError("MOTION_RENDER_SHARED_SCRATCH_REQUIRED")
    renderer = IsolatedMotionRenderer(
        image=settings.motion_renderer_image,
        docker_executable=Path(settings.motion_renderer_docker_executable),
        docker_socket=Path(settings.motion_renderer_docker_socket),
        scratch_directory=Path(settings.motion_renderer_scratch_directory),
        timeout_seconds=60,
    )
    result = await renderer.render(
        RenderBundle(
            html='<html><body style="margin:0;background:#127a63">Executor</body></html>',
            scene_init="window.seek=async()=>{};",
            assets=(),
            audio={"mode": "silent", "tracks": []},
            width=64,
            height=64,
            fps=30,
            duration_ms=34,
        ),
        operation_id=uuid4(),
    )
    report: dict[str, object] = {
        "event": "motion.executor.checked",
        "video_bytes": len(result.mp4),
        "evidence_frames": len(result.evidence),
        "sha256": result.sha256,
    }
    if settings.motion_storyboard_enabled:
        board = await renderer.render(
            RenderBundle(
                html='<html><body style="margin:0;background:#127a63">Storyboard</body></html>',
                scene_init="window.seek=async()=>{};",
                assets=(),
                audio={"mode": "silent", "tracks": []},
                width=64,
                height=64,
                fps=30,
                duration_ms=34,
                sample_times_ms=(0,),
                frames_only=True,
            ),
            operation_id=uuid4(),
        )
        if board.mp4 or len(board.evidence) != 1:
            raise MotionRenderError("MOTION_STORYBOARD_CHECK_FAILED")
        report["storyboard_frames"] = len(board.evidence)
    return report


def main() -> None:
    try:
        report = asyncio.run(check_executor(get_settings()))
    except MotionRenderError as exc:
        print(json.dumps({"event": "motion.executor.check_failed", "code": exc.code}))
        raise SystemExit(1) from None
    print(json.dumps(report))


if __name__ == "__main__":
    main()
