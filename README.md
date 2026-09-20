# photoDate

Impregna fecha y hora en una foto, estilo marca de agua LCD de cámara digital (naranja, esquina inferior derecha).

La fecha sale del EXIF (`DateTimeOriginal` → `DateTimeDigitized` → `DateTime`). Si no hay metadata, usa la fecha del archivo. También se puede forzar con `-t`.

## Requisitos

- Python 3.10+
- Pillow (`requirements.txt`)

## Windows

Abre **PowerShell** o **CMD** en la carpeta del proyecto:

```bat
cd ruta\a\photoDate
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py foto.jpg
```

Salida por defecto: `foto_dated.jpg` (junto al original).

### Opciones

```bat
python main.py foto.jpg -o salida.jpg
python main.py foto.jpg -t "2026-09-18 16:47"
```

### Sin activar el venv

```bat
.venv\Scripts\python.exe main.py foto.jpg
```

## Linux / macOS

```bash
cd ruta/a/photoDate
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py foto.jpg
```
