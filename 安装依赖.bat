@echo off
cd /d "%~dp0"
echo === Sherlock GUI - Install Dependencies ===
echo.
set "PY=python"
if exist "%~dp0.venv\Scripts\python.exe" set "PY=%~dp0.venv\Scripts\python.exe"
"%PY%" --version
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ first.
    pause
    exit /b 1
)
echo [1/2] Upgrading pip ...
"%PY%" -m pip install --upgrade pip
echo [2/2] Installing packages ...
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)
echo.
echo Done. Double-click gui.pyw or 启动.bat to run.
pause
