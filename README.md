# photoDate

Impregna fecha y hora en fotos, estilo marca de agua LCD de cámara digital (naranja).

- Elige **carpeta** (lote) o **archivo(s)** (uno o varios).
- Por defecto cada foto usa **su propia** fecha/hora del EXIF; opcional forzar una para todas.
- Salida en `<nombre>_fechada/` junto a la app / raíz del proyecto.

Dependencia: Pillow (`requirements.txt`).

## Windows

PowerShell o CMD en la carpeta del proyecto:

```bat
cd ruta\a\photoDate
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

Se abre la ventana: **Examinar…** → elige la carpeta → **Procesar → _fechada**.

### Sin activar el venv

```bat
.venv\Scripts\python.exe main.py
```

### Por línea de comandos (sin ventana)

```bat
python main.py C:\Fotos\viaje
python main.py C:\Fotos\viaje -t "2026-09-18 16:47"
python main.py C:\Fotos\una.jpg
```

## Linux / macOS

```bash
cd ruta/a/photoDate
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

CLI:

```bash
python main.py ~/Fotos/viaje
python main.py ~/Fotos/viaje -t "2026-09-18 16:47"
```

## Builds portables (.exe / AppImage)

No se puede generar un `.exe` de Windows desde Linux (hay que compilarlo en Windows).
El AppImage se genera en Linux.

### Windows → `photoDate.exe`

Doble clic o en CMD:

```bat
scripts\build_windows.bat
```

Sale en `dist\photoDate.exe`. Cópialo donde quieras; las carpetas `*_fechada` aparecen **al lado del .exe**.

### Linux → AppImage

```bash
chmod +x scripts/build_linux.sh
./scripts/build_linux.sh
```

Sale en `dist/photoDate-x86_64.AppImage`. Hazlo ejecutable y listo:

```bash
chmod +x dist/photoDate-x86_64.AppImage
./dist/photoDate-x86_64.AppImage
```

### GitHub Actions

En el repo: Actions → **Build portable** → Run workflow. Baja los artefactos `photoDate-windows` y `photoDate-linux`.
