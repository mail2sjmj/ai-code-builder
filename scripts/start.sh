#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Start the AI Code Builder backend (and optionally the frontend).
#
# Usage:
#   ./scripts/start.sh [--env development|staging|production] [--port PORT]
#                      [--frontend] [--foreground]
#
# Examples:
#   ./scripts/start.sh
#   ./scripts/start.sh --env staging
#   ./scripts/start.sh --env production --port 8080
#   ./scripts/start.sh --frontend          # also start the Vite dev server
#   ./scripts/start.sh --foreground        # blocking, useful for debugging
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/.."
python scripts/manage.py start "$@"
