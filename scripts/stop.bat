@echo off
:: ─────────────────────────────────────────────────────────────────────────────
:: Stop the AI Code Builder backend (and optionally the frontend).
::
:: Usage:
::   scripts\stop.bat [--frontend] [--force]
::
:: Examples:
::   scripts\stop.bat
::   scripts\stop.bat --frontend
::   scripts\stop.bat --force
:: ─────────────────────────────────────────────────────────────────────────────
cd /d "%~dp0.."
python scripts\manage.py stop %*
