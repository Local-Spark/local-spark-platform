"""Render the editable story and silent motion reel for the fictional café kit.

Run inside the worker image with the repository mounted at /work:
docker run --rm -v "$PWD:/work" -w /work --entrypoint python \
  meu-braco-direito-platform-worker:latest scripts/build_cafe_kit_media.py
"""

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1] / "catalog/kits/cafe-pausas/v1"
ASSETS = ROOT / "assets"
FONTS = ROOT / "fonts"
WIDTH, HEIGHT = 1080, 1920


def frame(photo: str, headline: str, subline: str, destination: Path) -> None:
    image = ImageOps.fit(Image.open(ASSETS / photo).convert("RGB"), (WIDTH, HEIGHT), centering=(0.5, 0.4))
    shade = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    pixels = shade.load()
    assert pixels is not None
    for y in range(HEIGHT):
        opacity = round(170 * max(0.0, (y / HEIGHT - 0.52) / 0.48))
        ImageDraw.Draw(shade).line((0, y, WIDTH, y), fill=(9, 25, 20, opacity))
    image = Image.alpha_composite(image.convert("RGBA"), shade)
    draw = ImageDraw.Draw(image)
    serif = ImageFont.truetype(FONTS / "DejaVuSerif.ttf", 104)
    sans = ImageFont.truetype(FONTS / "DejaVuSans.ttf", 31)
    small = ImageFont.truetype(FONTS / "DejaVuSans.ttf", 25)
    draw.rounded_rectangle((72, 78, 421, 135), radius=27, fill=(245, 240, 231, 235))
    draw.text((95, 94), "PAUSAS COM SABOR", font=small, fill=(30, 67, 53))
    draw.line((76, 1480, 1004, 1480), fill=(245, 240, 231, 180), width=2)
    draw.multiline_text((74, 1518), headline, font=serif, spacing=3, fill=(255, 250, 240))
    draw.text((78, 1780), subline, font=sans, fill=(255, 250, 240))
    image.convert("RGB").save(destination, quality=88, optimize=True, subsampling=0)


def main() -> None:
    frame(
        "espresso-pour.jpg", "A pausa\ncomeça aqui.", "Café, conversa e um tempo para você.", ASSETS / "story-pausa.jpg"
    )
    frame("window-pause.jpg", "Seu tempo\ntambém importa.", "Um momento para desacelerar.", ASSETS / "story-janela.jpg")
    frames = [
        ("morning-pastries.jpg", "O dia pode\ncomeçar devagar.", "Uma história de cafeteria."),
        ("counter-service.jpg", "Um café.\nSeu tempo.", "Um convite para fazer uma pausa."),
        ("shared-table.jpg", "Pausas\ncom sabor.", "Meu Braço Direito · demonstração"),
    ]
    inputs: list[str] = []
    filters: list[str] = []
    for index, (photo, headline, subline) in enumerate(frames):
        path = ASSETS / f"reel-frame-{index + 1}.jpg"
        frame(photo, headline, subline, path)
        inputs += ["-loop", "1", "-framerate", "24", "-t", "3", "-i", str(path)]
        filters.append(
            f"[{index}:v]scale=600:1067,"
            "zoompan=z='min(zoom+0.0007,1.08)':d=1:"
            "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=540x960:fps=24,"
            f"trim=duration=3,setpts=PTS-STARTPTS[v{index}]"
        )
    graph = ";".join(filters) + ";[v0][v1][v2]concat=n=3:v=1:a=0[out]"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            *inputs,
            "-filter_complex",
            graph,
            "-map",
            "[out]",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(ASSETS / "reel-pausas.mp4"),
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
