#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Stop the AI Code Builder backend (and optionally the frontend).
#
# Usage:
#   ./scripts/stop.sh [--frontend] [--force]
#
# Examples:
#   ./scripts/stop.sh
#   ./scripts/stop.sh --frontend   # also stop the frontend dev server
#   ./scripts/stop.sh --force      # skip graceful shutdown, force-kill
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/.."
python scripts/manage.py stop "$@"
