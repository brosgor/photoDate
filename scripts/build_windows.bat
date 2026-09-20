@echo off
REM Genera photoDate.exe portable (ejecutar en Windows)
cd /d "%~dp0.."
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -U pip
python -m pip install -r requirements-build.txt
REM Regenerar .ico desde brosgor.png por si falta
python -c "from PIL import Image; img=Image.open('brosgor.png').convert('RGBA'); sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)]; imgs=[img.resize(s, Image.Resampling.LANCZOS) for s in sizes]; imgs[-1].save('brosgor.ico', format='ICO', sizes=[(i.width,i.height) for i in imgs])"
pyinstaller --noconfirm --clean photoDate.spec
echo.
echo Listo: dist\photoDate.exe
echo Copia ese .exe donde quieras; las carpetas *_fechada salen al lado del .exe
pause
