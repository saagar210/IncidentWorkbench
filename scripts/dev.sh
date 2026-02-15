#!/bin/bash
set -euo pipefail

echo "Starting Incident Workbench in development mode..."

# Start backend in dev mode (no PyInstaller, direct uvicorn)
cd "$(dirname "$0")/../backend"

# Create venv if needed
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -q -e .

# Start backend
echo "Starting FastAPI backend on port 8765..."
export DEV_MODE=1
uvicorn main:app --host 127.0.0.1 --port 8765 --reload &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start Tauri dev (frontend + webview)
cd ..
echo "Starting Tauri frontend..."
export VITE_BACKEND_URL="http://127.0.0.1:8765"
npm run tauri dev &
TAURI_PID=$!

# Cleanup on exit
trap "kill $BACKEND_PID $TAURI_PID 2>/dev/null; exit" INT TERM

wait
