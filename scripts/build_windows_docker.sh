#!/usr/bin/env bash
# Genera photoDate.exe desde Linux vía Docker (Wine + PyInstaller).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

IMAGE="${PYINSTALLER_WIN_IMAGE:-batonogov/pyinstaller-windows:python-3.12}"

echo "Usando imagen: $IMAGE"
docker pull "$IMAGE"

# El contenedor espera el proyecto en /src y genera en dist/
docker run --rm \
  -v "$ROOT:/src" \
  -w /src \
  "$IMAGE" \
  "pyinstaller --noconfirm --clean --distpath dist --workpath build/win photoDate.spec"

# Algunas imágenes dejan el exe en dist/ o dist/windows/
if [[ -f dist/photoDate.exe ]]; then
  OUT=dist/photoDate.exe
elif [[ -f dist/windows/photoDate.exe ]]; then
  mv -f dist/windows/photoDate.exe dist/photoDate.exe
  OUT=dist/photoDate.exe
else
  echo "No se encontró photoDate.exe. Contenido de dist/:"
  find dist -type f | head -40
  exit 1
fi

ls -lh "$OUT"
echo "Listo: $OUT"
