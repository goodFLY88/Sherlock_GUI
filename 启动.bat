@echo off
cd /d "%~dp0"
set "PYW=%~dp0.venv\Scripts\pythonw.exe"
if exist "%PYW%" (
    start "" "%PYW%" "gui.pyw"
) else (
    start "" pythonw "gui.pyw"
)
exit
