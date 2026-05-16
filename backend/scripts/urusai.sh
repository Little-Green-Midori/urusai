#!/usr/bin/env bash
# URUSAI unified launcher (POSIX / bash / git-bash).
#
# Usage:
#   ./scripts/urusai.sh <category> <action> [args...]
#
# Categories and actions:
#   env       install | uninstall | reinstall    (Windows-only — use urusai.ps1)
#   server    start | stop
#   db        start | stop | status              (init / clear / rebuild are Windows-only currently)
#   models    download
#   help

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CATEGORY="${1:-help}"
ACTION="${2:-}"
shift 2 >/dev/null 2>&1 || true

show_help() {
    cat <<EOF

URUSAI launcher

Usage:
  ./scripts/urusai.sh <category> <action> [args...]

Categories:
  env       install | uninstall | reinstall    (Windows-only — use urusai.ps1)
  server    start | stop
  db        start | stop | status              (init / clear / rebuild are Windows-only)
  models    download

Common flows:
  First time (Windows):  .\\scripts\\urusai.ps1 env install
  Start everything:      ./scripts/urusai.sh db start && ./scripts/urusai.sh server start
  Health check:          ./scripts/urusai.sh db status
  Stop everything:       ./scripts/urusai.sh server stop && ./scripts/urusai.sh db stop

EOF
}

case "$CATEGORY" in
    help|-h|--help|"")
        show_help
        exit 0
        ;;
esac

case "$CATEGORY" in
    env|server|db|models)
        ;;
    *)
        echo "Unknown category: $CATEGORY" >&2
        show_help
        exit 1
        ;;
esac

if [ -z "$ACTION" ]; then
    echo "Missing action for category '$CATEGORY'." >&2
    show_help
    exit 1
fi

TARGET="$SCRIPT_DIR/$CATEGORY/$ACTION.sh"
if [ ! -f "$TARGET" ]; then
    echo "Action script missing: $TARGET" >&2
    echo "(Some actions are Windows-only — see urusai.ps1.)" >&2
    exit 1
fi

exec "$TARGET" "$@"
