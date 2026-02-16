#!/usr/bin/env bash
set -euo pipefail

if command -v gitleaks >/dev/null 2>&1; then
  report_file="$(mktemp -t gitleaks-report.XXXXXX.json)"
  if gitleaks detect --source . --no-git --report-format json --report-path "${report_file}"; then
    rm -f "${report_file}"
    exit 0
  fi

  echo "gitleaks detected potential secrets. Rule + file locations:"
  if command -v jq >/dev/null 2>&1; then
    jq -r '.[] | "- \(.RuleID): \(.File):\(.StartLine)"' "${report_file}"
  else
    echo "(jq not found; raw report at ${report_file})"
  fi
  exit 1
fi

echo "gitleaks not found; falling back to Semgrep secrets scan"
cd backend
./.venv/bin/semgrep --config p/secrets --error
