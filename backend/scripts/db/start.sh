#!/usr/bin/env bash
# urusai db start: docker compose up the dev stack.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/../_lib/common.sh"

COMPOSE="$URUSAI_BACKEND_ROOT/docker-compose.yml"
if [ ! -f "$COMPOSE" ]; then
    COMPOSE="$(cd "$URUSAI_BACKEND_ROOT/.." && pwd)/docker-compose.yml"
fi
if [ ! -f "$COMPOSE" ]; then
    echo "docker-compose.yml not found in backend/ or repo root." >&2
    exit 1
fi

wait_docker_ready

cd "$URUSAI_BACKEND_ROOT"
docker compose -p urusai -f "$COMPOSE" --progress=quiet up -d

echo ""
echo "Endpoints (host):"
echo "  Postgres : localhost:5433"
echo "  Milvus   : localhost:19531 (gRPC) / localhost:9092 (health)"
echo "  MinIO    : localhost:9100 (API) / http://localhost:9101 (console)"
echo "  Attu     : http://localhost:3001"
echo ""
echo "Status:  ./scripts/urusai.sh db status"
echo "Stop:    ./scripts/urusai.sh db stop"
