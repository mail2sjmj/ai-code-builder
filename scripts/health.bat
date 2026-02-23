@echo off
:: ─────────────────────────────────────────────────────────────────────────────
:: Check the AI Code Builder backend health endpoint.
::
:: Usage:
::   scripts\health.bat [--port PORT] [--url URL]
::
:: Examples:
::   scripts\health.bat
::   scripts\health.bat --port 8080
::   scripts\health.bat --url http://myhost:8000/health
:: ─────────────────────────────────────────────────────────────────────────────
cd /d "%~dp0.."
python scripts\manage.py health %*
