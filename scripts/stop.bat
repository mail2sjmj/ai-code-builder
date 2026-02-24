@echo off
:: ─────────────────────────────────────────────────────────────────────────────
:: Stop the AI Code Builder backend and frontend.
::
:: Usage:
::   scripts\stop.bat [--backend-only] [--force]
::
:: Examples:
::   scripts\stop.bat
::   scripts\stop.bat --backend-only
::   scripts\stop.bat --force
:: ─────────────────────────────────────────────────────────────────────────────
cd /d "%~dp0.."
python scripts\manage.py stop %*
