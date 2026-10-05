@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run Setup-PRAXIS.cmd first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m praxis.cli --db "%~dp0praxis.db" %*
if errorlevel 1 pause
