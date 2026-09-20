"""Núcleo: marca de agua de fecha/hora estilo cámara digital."""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ExifTags

ORANGE = (255, 140, 0, 255)
SHADOW = (0, 0, 0, 128)
OUT_DIR_NAME = "_fechada"  # sufijo; carpeta final = f"{origen.name}_fechada"
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}


def project_root() -> Path:
    # Portable: junto al .exe / .AppImage (APPIMAGE = ruta al archivo real)
    if appimage := os.environ.get("APPIMAGE"):
        return Path(appimage).resolve().parent
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def output_dir_for(folder: Path) -> Path:
    """Junto a la app / <nombre_carpeta>_fechada."""
    return project_root() / f"{folder.name}{OUT_DIR_NAME}"

_EXIF_TAGS = {v: k for k, v in ExifTags.TAGS.items()}
_DATETIME_TAGS = ("DateTimeOriginal", "DateTimeDigitized", "DateTime")


def resolve_font(size: int) -> ImageFont.ImageFont:
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


def resolve_when(src: Path, forced: datetime | None = None) -> datetime:
    if forced is not None:
        return forced
    with Image.open(src) as img:
        return exif_datetime(img) or datetime.fromtimestamp(src.stat().st_mtime)


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
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.suffix.lower() in {".jpg", ".jpeg"}:
        out.convert("RGB").save(dst, quality=95)
    else:
        out.save(dst)


def list_images(folder: Path) -> list[Path]:
    return sorted(
        p
        for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )


def process_images(
    images: list[Path],
    out_dir: Path,
    forced: datetime | None = None,
    on_progress=None,
) -> Path:
    """Impregna cada imagen con su propia fecha EXIF (o `forced` si se pasa)."""
    if not images:
        raise FileNotFoundError("No hay imágenes para procesar")

    out_dir.mkdir(parents=True, exist_ok=True)
    total = len(images)
    for i, src in enumerate(images, start=1):
        when = resolve_when(src, forced)  # por defecto: metadata individual
        stamp(src, out_dir / src.name, when)
        if on_progress:
            on_progress(i, total, src.name)
    return out_dir


def process_folder(
    folder: Path,
    forced: datetime | None = None,
    on_progress=None,
) -> Path:
    """Lote: todas las fotos de `folder` → `<proyecto>/<nombre>_fechada`."""
    folder = folder.expanduser().resolve()
    if not folder.is_dir():
        raise NotADirectoryError(folder)
    return process_images(list_images(folder), output_dir_for(folder), forced, on_progress)


def process_files(
    files: list[Path],
    forced: datetime | None = None,
    on_progress=None,
) -> Path:
    """Uno o varios archivos → carpeta *_fechada (nombre del padre o del archivo)."""
    resolved = [p.expanduser().resolve() for p in files]
    missing = [str(p) for p in resolved if not p.is_file()]
    if missing:
        raise FileNotFoundError("No existen:\n" + "\n".join(missing))

    parents = {p.parent for p in resolved}
    if len(resolved) == 1:
        out_dir = project_root() / f"{resolved[0].stem}{OUT_DIR_NAME}"
    elif len(parents) == 1:
        out_dir = output_dir_for(next(iter(parents)))
    else:
        out_dir = project_root() / f"seleccion{OUT_DIR_NAME}"

    return process_images(resolved, out_dir, forced, on_progress)
