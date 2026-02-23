@echo off
:: ─────────────────────────────────────────────────────────────────────────────
:: Start the AI Code Builder backend (and optionally the frontend).
::
:: Usage:
::   scripts\start.bat [--env development|staging|production] [--port PORT]
::                     [--frontend] [--foreground]
::
:: Examples:
::   scripts\start.bat
::   scripts\start.bat --env staging
::   scripts\start.bat --env production --port 8080
::   scripts\start.bat --frontend
::   scripts\start.bat --foreground
:: ─────────────────────────────────────────────────────────────────────────────
cd /d "%~dp0.."
python scripts\manage.py start %*
