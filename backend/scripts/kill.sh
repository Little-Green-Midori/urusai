#!/usr/bin/env bash
# Force-kill urusai uvicorn processes and free port 8000.
# Usage:
#   ./scripts/kill.sh

set +e

# 1. Kill by command-line pattern.
if command -v pkill >/dev/null 2>&1; then
    pkill -f "uvicorn urusai.api.main:app" && echo "killed uvicorn process(es)"
fi

# 2. Free port 8000 if anything still holds it.
free_port() {
    local port=$1
    local pid=""
    if command -v lsof >/dev/null 2>&1; then
        pid=$(lsof -ti ":$port" 2>/dev/null)
    elif command -v ss >/dev/null 2>&1; then
        pid=$(ss -lntp 2>/dev/null | awk -v p=":$port" '$4 ~ p {print $7}' | grep -oE 'pid=[0-9]+' | head -1 | cut -d= -f2)
    elif command -v netstat >/dev/null 2>&1; then
        pid=$(netstat -ano 2>/dev/null | awk -v p=":$port" '$2 ~ p && $4 == "LISTENING" {print $5}' | head -1)
    fi
    if [ -n "$pid" ]; then
        kill -9 "$pid" 2>/dev/null && echo "freed port $port (killed PID $pid)"
    fi
}

free_port 8000

echo "Done."
