@echo off
:: ─────────────────────────────────────────────────────────────────────────────
:: Show the running/stopped status of all AI Code Builder services.
::
:: Usage:
::   scripts\status.bat
:: ─────────────────────────────────────────────────────────────────────────────
cd /d "%~dp0.."
python scripts\manage.py status %*
