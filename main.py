#!/usr/bin/env python3
"""Impregna fecha/hora estilo marca de agua de cámara digital (LCD naranja)."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ExifTags

ORANGE = (255, 140, 0, 255)
SHADOW = (0, 0, 0, 128)

_EXIF_TAGS = {v: k for k, v in ExifTags.TAGS.items()}
_DATETIME_TAGS = ("DateTimeOriginal", "DateTimeDigitized", "DateTime")


def resolve_font(size: int) -> ImageFont.ImageFont:
    """Fuente del sistema según SO; si no hay, la default de Pillow."""
    if sys.platform == "win32":
        windir = Path(os.environ.get("WINDIR", r"C:\Windows"))
        candidates = [
            windir / "Fonts" / "consolab.ttf",
            windir / "Fonts" / "consola.ttf",
            windir / "Fonts" / "arialbd.ttf",
            windir / "Fonts" / "arial.ttf",
        ]
    elif sys.platform == "darwin":
        candidates = [
            Path("/System/Library/Fonts/Supplemental/Courier New Bold.ttf"),
            Path("/Library/Fonts/Arial Bold.ttf"),
            Path("/System/Library/Fonts/Menlo.ttc"),
            Path("/System/Library/Fonts/Helvetica.ttc"),
        ]
    else:
        candidates = [
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"),
            Path("/usr/share/fonts/TTF/DejaVuSansMono-Bold.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"),
            Path("/usr/share/fonts/gnu-free/FreeMonoBold.otf"),
        ]

    for path in candidates:
        if path.is_file():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    # ponytail: sin fuente del sistema → bitmap default (portable)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def exif_datetime(img: Image.Image) -> datetime | None:
    exif = img.getexif()
    if not exif:
        return None
    for name in _DATETIME_TAGS:
        tag = _EXIF_TAGS.get(name)
        if tag is None:
            continue
        raw = exif.get(tag)
        if not raw:
            continue
        text = str(raw).strip()[:19]
        for fmt in ("%Y:%m:%d %H:%M:%S", "%Y:%m:%d %H:%M"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
    return None


def stamp_text(dt: datetime) -> str:
    return dt.strftime("%y/%m/%d %H:%M")


def stamp(src: Path, dst: Path, when: datetime) -> None:
    img = Image.open(src).convert("RGBA")
    text = stamp_text(when)
    size = max(28, img.width // 28)
    font = resolve_font(size)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    margin = size // 2
    x = img.width - tw - margin
    y = img.height - th - margin

    draw.text((x + 2, y + 2), text, font=font, fill=SHADOW)
    draw.text((x, y), text, font=font, fill=ORANGE)

    out = Image.alpha_composite(img, overlay)
    if dst.suffix.lower() in {".jpg", ".jpeg"}:
        out = out.convert("RGB")
        out.save(dst, quality=95)
    else:
        out.save(dst)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Marca de agua de fecha/hora estilo cámara digital"
    )
    p.add_argument("foto", type=Path, help="ruta de la foto")
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        help="salida (default: <nombre>_dated.<ext>)",
    )
    p.add_argument(
        "-t",
        "--time",
        help="fecha/hora forzada: 'YYYY-MM-DD HH:MM' (default: EXIF o mtime)",
    )
    args = p.parse_args()

    src = args.foto.expanduser().resolve()
    if not src.is_file():
        print(f"No existe: {src}", file=sys.stderr)
        return 1

    with Image.open(src) as probe:
        if args.time:
            when = datetime.strptime(args.time, "%Y-%m-%d %H:%M")
        else:
            when = exif_datetime(probe) or datetime.fromtimestamp(src.stat().st_mtime)

    dst = args.output or src.with_name(f"{src.stem}_dated{src.suffix}")
    dst = dst.expanduser().resolve()
    stamp(src, dst, when)
    print(dst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
