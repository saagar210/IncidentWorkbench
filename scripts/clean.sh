#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APPLY=false

if [[ "${1:-}" == "--apply" ]]; then
  APPLY=true
fi

cd "$ROOT_DIR"

TARGETS=(
  ".DS_Store"
  "backend/.DS_Store"
  "backend/build"
  "backend/dist"
  "backend/.venv"
  "backend/.pytest_cache"
  "backend/incident_workbench.egg-info"
  "backend/__pycache__"
  "backend/models/__pycache__"
  "backend/routers/__pycache__"
  "backend/services/__pycache__"
  "node_modules"
)

echo "Incident Workbench cleanup"
echo "Mode: $([[ "$APPLY" == true ]] && echo "apply" || echo "dry-run")"
echo ""

found_any=false

for target in "${TARGETS[@]}"; do
  if [[ -e "$target" ]]; then
    found_any=true
    if [[ "$APPLY" == true ]]; then
      rm -rf "$target"
      echo "Removed: $target"
    else
      echo "Would remove: $target"
    fi
  fi
done

if [[ "$found_any" == false ]]; then
  echo "Nothing to clean."
  exit 0
fi

if [[ "$APPLY" == false ]]; then
  echo ""
  echo "Dry run only. Re-run with --apply to remove listed items."
fi
