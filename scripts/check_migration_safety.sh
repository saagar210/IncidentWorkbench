#!/usr/bin/env bash
set -euo pipefail

BAD_PATTERNS='DROP TABLE|DROP COLUMN|ALTER TABLE .* RENAME COLUMN'
EXIT_CODE=0

for file in backend/migrations/*.sql; do
  base="$(basename "$file")"

  # Legacy migrations predate expand/contract policy.
  if [[ "$base" < "006_" ]]; then
    continue
  fi

  if rg -n -i "$BAD_PATTERNS" "$file" >/dev/null 2>&1; then
    echo "Unsafe migration statement detected in $file"
    echo "Use expand/contract workflow or approved waiver comment."
    rg -n -i "$BAD_PATTERNS" "$file" || true
    EXIT_CODE=1
  fi
done

if [[ $EXIT_CODE -ne 0 ]]; then
  exit $EXIT_CODE
fi

echo "Migration safety check passed."
