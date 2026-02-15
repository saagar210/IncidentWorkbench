#!/usr/bin/env bash
set -euo pipefail

# Baseline-ignore currently unavoidable transitive advisories in the
# Tauri/GTK ecosystem so the audit fails only on newly introduced warnings.
BASELINE_IGNORES=(
  "RUSTSEC-2024-0411"
  "RUSTSEC-2024-0412"
  "RUSTSEC-2024-0413"
  "RUSTSEC-2024-0414"
  "RUSTSEC-2024-0415"
  "RUSTSEC-2024-0416"
  "RUSTSEC-2024-0417"
  "RUSTSEC-2024-0418"
  "RUSTSEC-2024-0419"
  "RUSTSEC-2024-0420"
  "RUSTSEC-2024-0429"
  "RUSTSEC-2024-0436"
  "RUSTSEC-2024-0370"
  "RUSTSEC-2025-0057"
  "RUSTSEC-2025-0075"
  "RUSTSEC-2025-0080"
  "RUSTSEC-2025-0081"
  "RUSTSEC-2025-0098"
  "RUSTSEC-2025-0100"
  "RUSTSEC-2025-0141"
)

IGNORE_FLAGS=()
for advisory in "${BASELINE_IGNORES[@]}"; do
  IGNORE_FLAGS+=(--ignore "$advisory")
done

cd "$(dirname "$0")/../src-tauri"

if ! cargo audit --version >/dev/null 2>&1; then
  cargo install cargo-audit --locked
fi

cargo audit --deny warnings "${IGNORE_FLAGS[@]}"
