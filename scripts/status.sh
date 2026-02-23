#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Show the running/stopped status of all AI Code Builder services.
#
# Usage:
#   ./scripts/status.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail
cd "$(dirname "$0")/.."
python scripts/manage.py status "$@"
