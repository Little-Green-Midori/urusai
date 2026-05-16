#!/usr/bin/env bash
# Stop urusai DB stack.
#   ./scripts/db-stop.sh              # docker compose stop（containers preserved）
#   ./scripts/db-stop.sh --down       # docker compose down（containers removed, volumes kept）
#   ./scripts/db-stop.sh --down-v     # docker compose down -v（DATA LOST）
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
. "$SCRIPT_DIR/_db-common.sh"

wait_docker_ready
cd "$ROOT"

case "${1:-}" in
    --down-v)
        echo "Stopping + removing urusai DB stack AND VOLUMES (data lost)..."
        docker compose -p urusai -f docker-compose.yml --progress=quiet down -v
        ;;
    --down)
        echo "Stopping + removing urusai DB containers (volumes kept)..."
        docker compose -p urusai -f docker-compose.yml --progress=quiet down
        ;;
    *)
        echo "Stopping urusai DB stack (containers preserved)..."
        docker compose -p urusai -f docker-compose.yml --progress=quiet stop
        ;;
esac
