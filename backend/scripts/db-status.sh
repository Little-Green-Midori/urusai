#!/usr/bin/env bash
# Show urusai DB stack status (containers + Postgres + Milvus connectivity).
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
. "$SCRIPT_DIR/_db-common.sh"

wait_docker_ready

PY=$(resolve_env_python) || exit 1

cd "$ROOT"

echo "=== Container status ==="
docker compose -p urusai -f docker-compose.yml ps
echo ""

"$PY" -m urusai.scripts.db status
