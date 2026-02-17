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
  "dist"
  "src-tauri/target"
  "backend/build"
  "backend/dist"
  "backend/.pytest_cache"
  "node_modules/.vite"
)

echo "Incident Workbench cleanup"
echo "Profile: heavy artifacts only"
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

while IFS= read -r pycache_path; do
  found_any=true
  if [[ "$APPLY" == true ]]; then
    rm -rf "$pycache_path"
    echo "Removed: ${pycache_path#./}"
  else
    echo "Would remove: ${pycache_path#./}"
  fi
done < <(find backend -path "backend/.venv" -prune -o -type d -name "__pycache__" -print 2>/dev/null)

if [[ "$found_any" == false ]]; then
  echo "Nothing to clean."
  exit 0
fi

if [[ "$APPLY" == false ]]; then
  echo ""
  echo "Dry run only. Re-run with --apply to remove listed items."
fi
