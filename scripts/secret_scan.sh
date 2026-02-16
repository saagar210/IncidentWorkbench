#!/usr/bin/env bash
set -euo pipefail

if command -v gitleaks >/dev/null 2>&1; then
  gitleaks detect --source . --no-git
  exit 0
fi

echo "gitleaks not found; falling back to Semgrep secrets scan"
cd backend
./.venv/bin/semgrep --config p/secrets --error
