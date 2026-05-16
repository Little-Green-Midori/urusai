#!/usr/bin/env bash
# urusai db stop: docker compose stop / down / down -v.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/../_lib/common.sh"

COMPOSE="$URUSAI_BACKEND_ROOT/docker-compose.yml"
if [ ! -f "$COMPOSE" ]; then
    COMPOSE="$(cd "$URUSAI_BACKEND_ROOT/.." && pwd)/docker-compose.yml"
fi

wait_docker_ready
cd "$URUSAI_BACKEND_ROOT"

case "${1:-}" in
    --down-v)
        echo "Stopping + removing urusai DB stack AND VOLUMES (data lost)..."
        docker compose -p urusai -f "$COMPOSE" --progress=quiet down -v
        ;;
    --down)
        echo "Stopping + removing urusai DB containers (volumes kept)..."
        docker compose -p urusai -f "$COMPOSE" --progress=quiet down
        ;;
    *)
        echo "Stopping urusai DB stack (containers preserved)..."
        docker compose -p urusai -f "$COMPOSE" --progress=quiet stop
        ;;
esac
