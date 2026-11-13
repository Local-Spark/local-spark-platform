"""Local synthetic capability probe; no customer media, model, admission or publication."""

import argparse
import asyncio
import json
from pathlib import Path
from uuid import uuid4

from app.adapters.motion_html_renderer import IsolatedMotionRenderer, RenderBundle
from app.core.config import get_settings
from app.services.motion_movement import movement_contract


def bundle() -> RenderBundle:
    root = Path("app/assets/motion_repertoire/business-reel-v5/examples")
    examples = "\n".join(p.read_text() for p in sorted(root.glob("*.js")))
    html = """<!doctype html><style>
    *{box-sizing:border-box}body{margin:0;background:#f3eddf}
    #portal,#next{position:absolute;width:720px;height:1280px;inset:0}
    #next{background:#173c32;padding:120px 55px;color:#f3eddf}
    #title{font-size:125px;line-height:.95;position:absolute;top:100px;left:50px;z-index:3}
    .orb{width:570px;height:570px;border-radius:50%;margin:220px 0 0 20px;
    background:radial-gradient(circle at 30% 25%,#edcf90,#b75e22 40%,#32190d 80%);
    box-shadow:30px 50px 60px #0008}
    </style><div id="next"><div class="orb"></div></div><div id="portal"></div>
    <div id="title">FORMA<br>EM AÇÃO</div>"""
    scene = (
        examples
        + """
    const kit={background:'#f3eddf',foreground:'#f3eddf',font:'sans-serif'};
    const host=document.querySelector('#portal');
    const media=document.createElement('div');
    media.style.background='repeating-linear-gradient(25deg,#183d32 0 70px,#d59848 70px 140px,#923e2b 140px 210px)';
    const portal=makeTypePortal({host,media,label:'VER',kit,width:720,height:1280,start:700,end:1800});
    const handoff=makeDepthHandoff({outgoing:host,incoming:document.querySelector('#next'),
      title:document.querySelector('#title'),width:720,start:2300,end:3300,kit});
    window.seek=ms=>{portal(ms);handoff(ms);};
    """
    )
    return RenderBundle(
        html,
        scene,
        (),
        {"mode": "silent", "tracks": []},
        720,
        1280,
        30,
        4000,
        (0, 700, 1000, 1250, 1500, 1800, 2300, 2500, 2800, 3100, 3300, 3967),
        movement_runtime_sha256=movement_contract()["sha256"],
    )


async def qualify(output: Path) -> None:
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    (output / "scratch").mkdir(mode=0o700)
    cfg = get_settings()
    renderer = IsolatedMotionRenderer(
        image=cfg.motion_renderer_image,
        docker_executable=Path(cfg.motion_renderer_docker_executable),
        docker_socket=Path(cfg.motion_renderer_docker_socket),
        scratch_directory=output / "scratch",
    )
    operation = uuid4()
    (output / "claim.json").write_text(json.dumps({"operation_id": str(operation), "purpose": "synthetic_probe"}))
    source = bundle()
    (output / "index.html").write_text(source.html)
    (output / "scene.js").write_text(source.scene_init)
    result = await renderer.render(source, operation_id=operation)
    (output / "mechanisms.mp4").write_bytes(result.mp4)
    frames = []
    for frame in result.evidence:
        name = f"frame-{frame.ms:05}.png"
        (output / name).write_bytes(frame.png)
        frames.append({"file": name, "ms": frame.ms, "sha256": frame.sha256})
    (output / "receipt.json").write_text(
        json.dumps(
            {
                "operation_id": str(operation),
                "sha256": result.sha256,
                "frames": frames,
                "diagnostics": result.diagnostics,
                "generated_by_product_model": False,
                "quality_approved": False,
                "paid_calls": 0,
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps({"status": "rendered", "evidence_frames": len(frames), "paid_calls": 0}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    asyncio.run(qualify(parser.parse_args().output))
