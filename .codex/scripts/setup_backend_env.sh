#!/usr/bin/env bash
set -euo pipefail

python3 -m venv backend/.venv
backend/.venv/bin/pip install --upgrade pip
backend/.venv/bin/pip install -e "backend/.[dev]"
