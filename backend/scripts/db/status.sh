#!/usr/bin/env bash
# urusai db status: container status + Postgres + Milvus connectivity.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/../_lib/common.sh"

wait_docker_ready

PY="$(resolve_env_python)" || exit 1

COMPOSE="$URUSAI_BACKEND_ROOT/docker-compose.yml"
if [ ! -f "$COMPOSE" ]; then
    COMPOSE="$(cd "$URUSAI_BACKEND_ROOT/.." && pwd)/docker-compose.yml"
fi

cd "$URUSAI_BACKEND_ROOT"
echo "=== Container status ==="
docker compose -p urusai -f "$COMPOSE" ps
echo ""

"$PY" -m urusai.scripts.db status
