#!/usr/bin/env bash
# Genera binario Linux + AppImage portable
# Usa el Python del sistema (tkinter enlazado a Tcl/Tk del SO).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="${PYTHON:-/usr/bin/python3}"
if [[ ! -x .venv/bin/python ]] || ! .venv/bin/python -c "import tkinter" 2>/dev/null; then
  rm -rf .venv
  "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements-build.txt

pyinstaller --noconfirm --clean photoDate.spec

DIST="$ROOT/dist"
BIN="$DIST/photoDate"
APPDIR="$DIST/photoDate.AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"

cp "$BIN" "$APPDIR/usr/bin/photoDate"
chmod +x "$APPDIR/usr/bin/photoDate"

cat > "$APPDIR/photoDate.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=photoDate
Comment=Marca de agua de fecha/hora en fotos
Exec=photoDate
Icon=photoDate
Categories=Graphics;Photography;
Terminal=false
EOF

python - <<'PY'
from pathlib import Path
from PIL import Image, ImageDraw
import shutil

root = Path("dist/photoDate.AppDir")
img = Image.new("RGBA", (256, 256), (30, 30, 30, 255))
d = ImageDraw.Draw(img)
d.rounded_rectangle((24, 24, 232, 232), radius=32, fill=(255, 140, 0, 255))
d.text((48, 100), "DATE", fill=(30, 30, 30, 255))
icon = root / "photoDate.png"
img.save(icon)
shutil.copy(icon, root / ".DirIcon")
PY

cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/photoDate" "$@"
EOF
chmod +x "$APPDIR/AppRun"

TOOL="$DIST/appimagetool"
if [[ ! -x "$TOOL" ]]; then
  echo "Descargando appimagetool…"
  curl -L --fail -o "$TOOL" \
    "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
  chmod +x "$TOOL"
fi

export ARCH=x86_64
set +e
"$TOOL" "$APPDIR" "$DIST/photoDate-x86_64.AppImage" 2>/tmp/ait.err
rc=$?
set -e
if [[ $rc -ne 0 ]]; then
  if grep -qi 'fuse\|AppImages require\|No such file\|cannot mount\|AppImageLauncher' /tmp/ait.err; then
    echo "Sin FUSE: extrayendo appimagetool…"
    cd "$DIST"
    rm -rf squashfs-root
    ./appimagetool --appimage-extract >/dev/null
    ARCH=x86_64 ./squashfs-root/AppRun "$APPDIR" "$DIST/photoDate-x86_64.AppImage"
    cd "$ROOT"
  else
    cat /tmp/ait.err
    exit 1
  fi
fi

echo
echo "Listo:"
ls -lh "$DIST/photoDate" "$DIST/photoDate-x86_64.AppImage"
echo "Las carpetas *_fechada salen al lado del ejecutable."
