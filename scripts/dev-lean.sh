#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_PID=""
TAURI_PID=""
LEAN_TMP_ROOT="${LEAN_TMP_ROOT:-$(mktemp -d "${TMPDIR:-/tmp}/incident-workbench-lean.XXXXXX")}"
CLEANED_UP=0

cleanup() {
  if [[ "$CLEANED_UP" -eq 1 ]]; then
    return
  fi
  CLEANED_UP=1
  set +e
  echo ""
  echo "Stopping lean dev processes and cleaning temporary artifacts..."

  if [[ -n "${TAURI_PID}" ]]; then
    pkill -TERM -P "${TAURI_PID}" 2>/dev/null || true
    kill "${TAURI_PID}" 2>/dev/null || true
    wait "${TAURI_PID}" 2>/dev/null || true
  fi

  if [[ -n "${BACKEND_PID}" ]]; then
    pkill -TERM -P "${BACKEND_PID}" 2>/dev/null || true
    kill "${BACKEND_PID}" 2>/dev/null || true
    wait "${BACKEND_PID}" 2>/dev/null || true
  fi

  bash "$ROOT_DIR/scripts/clean.sh" --apply >/dev/null 2>&1 || true
  rm -rf "$LEAN_TMP_ROOT" 2>/dev/null || true
  find "${TMPDIR:-/tmp}" -maxdepth 1 -type d -name "incident-workbench-lean.*" -exec rm -rf {} + 2>/dev/null || true
}

handle_signal() {
  trap - INT TERM
  cleanup
  exit 130
}

trap handle_signal INT TERM
trap cleanup EXIT

echo "Starting Incident Workbench in lean development mode..."
echo "Temporary cache root: $LEAN_TMP_ROOT"

export VITE_CACHE_DIR="$LEAN_TMP_ROOT/vite-cache"
export CARGO_TARGET_DIR="$LEAN_TMP_ROOT/cargo-target"
export PYTHONDONTWRITEBYTECODE=1

cd "$ROOT_DIR/backend"

if [[ ! -d ".venv" ]]; then
  echo "Creating Python virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing Python dependencies..."
pip install -q -e .

echo "Starting FastAPI backend on port 8765..."
export DEV_MODE=1
uvicorn main:app --host 127.0.0.1 --port 8765 --reload &
BACKEND_PID=$!

sleep 2

cd "$ROOT_DIR"
echo "Starting Tauri frontend (lean cache mode)..."
export VITE_BACKEND_URL="http://127.0.0.1:8765"
npm run tauri dev &
TAURI_PID=$!

wait "$TAURI_PID"
