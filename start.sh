#!/usr/bin/env bash
# Reality Checkpoint — one-command launcher.
#
#   ./start.sh              build the UI if needed, then run API + UI
#   ./start.sh --api-only   run the FastAPI backend only
#   ./start.sh --ui-only     run the Vite dev server only
#   ./start.sh --rebuild     force a fresh frontend build
#
# Environment knobs:
#   REALITY_HOST / REALITY_PORT   backend bind address (default 0.0.0.0:8000)
#   REALITY_API                   backend URL the Vite proxy targets
#   OLLAMA_MODEL / OLLAMA_BASE_URL
#   REALITY_DISABLE_OLLAMA=1      force deterministic heuristic mode

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
DIST_DIR="$FRONTEND_DIR/dist"

HOST="${REALITY_HOST:-0.0.0.0}"
PORT="${REALITY_PORT:-8000}"
export REALITY_API="${REALITY_API:-http://localhost:${PORT}}"

MODE="all"
REBUILD=0
for arg in "$@"; do
  case "$arg" in
    --api-only) MODE="api" ;;
    --ui-only) MODE="ui" ;;
    --rebuild) REBUILD=1 ;;
    -h|--help)
      sed -n '2,16p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      exit 2
      ;;
  esac
done

PYTHON_BIN="$(command -v python3 || command -v python || true)"
if [ -z "$PYTHON_BIN" ]; then
  echo "Python 3.11+ is required but was not found on PATH." >&2
  exit 1
fi

NPM_CMD=()
if [ -x /usr/share/nodejs/corepack/shims/npm ]; then
  export PATH="/usr/share/nodejs/corepack/shims:$PATH"
  NPM_CMD=(/usr/share/nodejs/corepack/shims/npm)
elif command -v npm >/dev/null 2>if command -v npm >/dev/null 2>&1; then1; then
  NPM_CMD=(npm)
elif command -v corepack >/dev/null 2>&1; then
  NPM_CMD=(corepack npm)
elif command -v bun >/dev/null 2>&1; then
  NPM_CMD=(bun)
fi

PIDS=()
cleanup() {
  for pid in "${PIDS[@]:-}"; do
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
    fi
  done
}
trap cleanup EXIT INT TERM

banner() {
  printf '\n\033[38;5;79m  ┌───────────────────────────────────────────────┐\n'
  printf '  │  R E A L I T Y   C H E C K P O I N T          │\n'
  printf '  │  the screen is a portal, not a destination    │\n'
  printf '  └───────────────────────────────────────────────┘\033[0m\n\n'
}

start_api() {
  echo "→ API   http://localhost:${PORT}   (docs: /docs)"
  (
    cd "$BACKEND_DIR"
    exec "$PYTHON_BIN" -m uvicorn main:app --host "$HOST" --port "$PORT"
  ) &
  PIDS+=("$!")
}

ensure_frontend_deps() {
  if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    if [ "${#NPM_CMD[@]}" -eq 0 ]; then
      echo "No npm/corepack/bun found — cannot install frontend dependencies." >&2
      exit 1
    fi
    echo "→ Installing frontend dependencies…"
    ( cd "$FRONTEND_DIR" && "${NPM_CMD[@]}" install --no-fund --no-audit )
  fi
}

build_frontend() {
  ensure_frontend_deps
  if [ "$REBUILD" -eq 1 ] || [ ! -f "$DIST_DIR/index.html" ]; then
    echo "→ Building the interface…"
    ( cd "$FRONTEND_DIR" && "${NPM_CMD[@]}" run build )
  fi
}

start_ui() {
  ensure_frontend_deps
  echo "→ UI    http://localhost:5173   (proxying /api → ${REALITY_API})"
  (
    cd "$FRONTEND_DIR"
    exec "${NPM_CMD[@]}" run dev
  ) &
  PIDS+=("$!")
}

banner

case "$MODE" in
  api) start_api ;;
  ui)  start_ui ;;
  all)
    if [ -f "$DIST_DIR/index.html" ] && [ "$REBUILD" -eq 0 ]; then
      echo "→ Serving the prebuilt interface from the API process itself."
      start_api
    else
      build_frontend
      start_api
      start_ui
    fi
    ;;
esac

echo
echo "Press Ctrl+C to stop."
wait
