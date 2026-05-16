#!/usr/bin/env bash
# Start urusai DB stack via docker compose.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
. "$SCRIPT_DIR/_db-common.sh"

COMPOSE="$ROOT/docker-compose.yml"
if [ ! -f "$COMPOSE" ]; then
    echo "docker-compose.yml not found at $COMPOSE" >&2
    exit 1
fi

wait_docker_ready

cd "$ROOT"
docker compose -p urusai -f docker-compose.yml --progress=quiet up -d

echo ""
echo "Endpoints (host):"
echo "  Postgres : localhost:5433"
echo "  Milvus   : localhost:19531 (gRPC) / localhost:9092 (health)"
echo "  MinIO    : localhost:9100 (API) / http://localhost:9101 (console)"
echo "  Attu     : http://localhost:3001"
echo ""
echo "Status: ./scripts/db-status.sh"
echo "Stop:   ./scripts/db-stop.sh"
