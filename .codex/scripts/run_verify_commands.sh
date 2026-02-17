#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Schemathesis currently emits third-party jsonschema deprecation warnings
# during plugin import. Keep gate output signal-focused until upstream fixes.
PY_WARNINGS_FILTERS="ignore:jsonschema.exceptions.RefResolutionError is deprecated.*:DeprecationWarning,ignore:jsonschema.RefResolver is deprecated.*:DeprecationWarning"
if [[ -n "${PYTHONWARNINGS:-}" ]]; then
  export PYTHONWARNINGS="${PYTHONWARNINGS},${PY_WARNINGS_FILTERS}"
else
  export PYTHONWARNINGS="${PY_WARNINGS_FILTERS}"
fi

while IFS= read -r cmd; do
  [[ -z "$cmd" ]] && continue
  [[ "$cmd" =~ ^# ]] && continue
  echo "==> $cmd"
  (
    cd "$REPO_ROOT"
    # Trusted input: `.codex/verify.commands` is version-controlled alongside source.
    eval "$cmd"
  )
done < .codex/verify.commands
