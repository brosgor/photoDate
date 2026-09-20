@echo off
REM Genera photoDate.exe portable (ejecutar en Windows)
cd /d "%~dp0.."
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -U pip
python -m pip install -r requirements-build.txt
pyinstaller --noconfirm --clean photoDate.spec
echo.
echo Listo: dist\photoDate.exe
echo Copia ese .exe donde quieras; las carpetas *_fechada salen al lado del .exe
pause
