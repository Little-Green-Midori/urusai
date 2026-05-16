#!/usr/bin/env bash
# urusai server start (POSIX): launch uvicorn for the FastAPI app.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
. "$SCRIPT_DIR/../_lib/common.sh"

PY="$(resolve_env_python)" || exit 1

cd "$URUSAI_BACKEND_ROOT"
"$PY" -m uvicorn urusai.api.main:app --reload --host 127.0.0.1 --port 8000 &
UVICORN_PID=$!

echo "Started:"
echo "  uvicorn   PID $UVICORN_PID  http://127.0.0.1:8000"
echo ""
echo "Stop:    ./scripts/urusai.sh server stop"
echo "Status:  ./scripts/urusai.sh db status"
echo ""
echo "Ctrl+C to stop."

cleanup() {
    kill "$UVICORN_PID" 2>/dev/null || true
    exit 0
}
trap cleanup INT TERM

wait
