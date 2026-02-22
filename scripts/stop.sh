#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

COMPOSE="docker compose"
if command -v podman &>/dev/null && ! command -v docker &>/dev/null; then
  COMPOSE="podman compose"
fi

$COMPOSE down
echo "Kanban Studio stopped."
