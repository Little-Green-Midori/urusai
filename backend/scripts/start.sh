#!/usr/bin/env bash
# urusai launcher (bash version, e.g. git-bash on Windows or POSIX shells).
# Reads config saved by scripts/start.ps1 first-time setup.
# Run scripts/start.ps1 once on Windows to configure.

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="$(dirname "$0")/.urusai-launcher.json"

if [ ! -f "$CONFIG" ]; then
    echo "No launcher config: $CONFIG" >&2
    echo "Run scripts/start.ps1 first to do interactive setup." >&2
    exit 1
fi

# Naive JSON extract (avoid jq dependency).
CONDA_ROOT=$(grep -oE '"conda_root"[[:space:]]*:[[:space:]]*"[^"]+"' "$CONFIG" \
    | sed -E 's/.*"conda_root"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')
ENV_NAME=$(grep -oE '"env_name"[[:space:]]*:[[:space:]]*"[^"]+"' "$CONFIG" \
    | sed -E 's/.*"env_name"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/')

if [ -z "$CONDA_ROOT" ] || [ -z "$ENV_NAME" ]; then
    echo "Config missing conda_root or env_name." >&2
    exit 1
fi

# Translate Windows path (D:\foo\bar) to git-bash path (/d/foo/bar) if needed.
case "$CONDA_ROOT" in
    [A-Za-z]:*)
        CONDA_ROOT_BASH=$(echo "$CONDA_ROOT" | sed -E 's|^([A-Za-z]):\\?|/\L\1/|; s|\\|/|g')
        ;;
    *)
        CONDA_ROOT_BASH="$CONDA_ROOT"
        ;;
esac

PY="$CONDA_ROOT_BASH/envs/$ENV_NAME/python.exe"
if [ ! -x "$PY" ]; then
    PY="$CONDA_ROOT_BASH/envs/$ENV_NAME/bin/python"
fi
if [ ! -x "$PY" ]; then
    echo "Python not found in env '$ENV_NAME' under '$CONDA_ROOT_BASH'." >&2
    echo "Try: scripts/start.ps1 -Recreate" >&2
    exit 1
fi

cd "$ROOT"

"$PY" -m uvicorn urusai.api.main:app --reload --host 127.0.0.1 --port 8000 &
UVICORN_PID=$!

echo "Started:"
echo "  uvicorn   PID $UVICORN_PID  http://127.0.0.1:8000"
echo ""
echo "Ctrl+C to stop."

cleanup() {
    kill "$UVICORN_PID" 2>/dev/null || true
    exit 0
}
trap cleanup INT TERM

wait
