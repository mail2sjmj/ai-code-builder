#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Check the AI Code Builder backend health endpoint.
#
# Usage:
#   ./scripts/health.sh [--port PORT] [--url URL]
#
# Examples:
#   ./scripts/health.sh
#   ./scripts/health.sh --port 8080
#   ./scripts/health.sh --url http://myhost:8000/health
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/.."
python scripts/manage.py health "$@"
