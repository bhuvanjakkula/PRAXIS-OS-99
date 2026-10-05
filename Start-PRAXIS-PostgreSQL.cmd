@echo off
setlocal
cd /d "%~dp0"
".venv\Scripts\python.exe" -m praxis.product.local_postgres serve
if errorlevel 1 pause
