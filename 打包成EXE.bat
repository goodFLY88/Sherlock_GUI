@echo off
cd /d "%~dp0"
echo === Sherlock GUI - Build EXE ===
echo.
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo [1/2] Checking PyInstaller ...
"%PY%" -m pip install pyinstaller
if errorlevel 1 goto :fail

echo [2/2] Building single-file windowed exe ...
"%PY%" -m PyInstaller -F -w --clean --noconfirm ^
  --icon "app.ico" --name "Sherlock_GUI" ^
  --add-data "app.ico;." ^
  --add-data "pyproject.toml;." ^
  --add-data "pyproject.toml;sherlock_project" ^
  --add-data "sherlock_project\resources\data.json;sherlock_project\resources" ^
  --add-data "sherlock_project\resources\data.schema.json;sherlock_project\resources" ^
  --collect-data certifi ^
  --exclude-module tomli ^
  gui.py
if errorlevel 1 goto :fail

echo.
echo ========================================
echo   SUCCESS: dist\Sherlock_GUI.exe
echo ========================================
pause
exit /b 0

:fail
echo Build failed. See the error above.
pause
exit /b 1
