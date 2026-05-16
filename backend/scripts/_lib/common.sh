#!/usr/bin/env bash
# Shared helpers for urusai launcher scripts. Source via:
#   SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
#   . "$SCRIPT_DIR/../_lib/common.sh"

_THIS_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
URUSAI_SCRIPTS_ROOT="$(cd "$_THIS_LIB_DIR/.." && pwd)"
URUSAI_BACKEND_ROOT="$(cd "$URUSAI_SCRIPTS_ROOT/.." && pwd)"

check_docker() {
    docker info >/dev/null 2>&1
}

wait_docker_ready() {
    if check_docker; then return 0; fi

    echo ""
    echo "Docker daemon not reachable."
    echo "Start Docker Desktop / the docker daemon, then press Enter to retry (Ctrl+C to abort)..."

    while true; do
        read -r
        if check_docker; then
            echo "Docker ready."
            return 0
        fi
        echo "  still not reachable, retry?"
    done
}

resolve_env_python() {
    local config="$URUSAI_SCRIPTS_ROOT/.urusai-launcher.json"
    if [ ! -f "$config" ]; then
        echo "Launcher config missing: $config" >&2
        echo "Run scripts/urusai.ps1 env install (on Windows) first to do the one-time setup." >&2
        return 1
    fi

    local conda_root env_name
    conda_root=$(grep -oE '"conda_root":[[:space:]]*"[^"]*"' "$config" | sed -E 's/.*"conda_root":[[:space:]]*"([^"]*)".*/\1/')
    env_name=$(grep -oE '"env_name":[[:space:]]*"[^"]*"' "$config" | sed -E 's/.*"env_name":[[:space:]]*"([^"]*)".*/\1/')

    case "$conda_root" in
        [A-Za-z]:*)
            conda_root=$(echo "$conda_root" | sed -E 's|^([A-Za-z]):\\?|/\L\1/|; s|\\|/|g')
            ;;
    esac

    local py="$conda_root/envs/$env_name/python.exe"
    [ -x "$py" ] || py="$conda_root/envs/$env_name/bin/python"
    if [ ! -x "$py" ]; then
        echo "Python not found: $py" >&2
        return 1
    fi
    echo "$py"
}
