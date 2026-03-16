#!/usr/bin/env bash
#
# Run Pax Nebulus locally for development (backend + frontend).
# From repo root:  ./scripts/dev.sh
# Then open http://localhost:5173
#
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Ensure venv exists
if [[ ! -d .venv ]]; then
  echo "Creating venv..."
  python3 -m venv .venv
fi
# Ensure backend deps
.venv/bin/pip install -q -r requirements.txt
# Ensure frontend deps
if [[ -f frontend/package.json ]]; then
  (cd frontend && npm install --silent)
fi

echo "Starting backend (http://127.0.0.1:8000) and frontend (http://localhost:5173)..."
echo "Open http://localhost:5173 in your browser. Stop with Ctrl+C."
echo ""

# Kill backend on exit
cleanup() {
  echo ""
  echo "Stopping backend..."
  kill "$UVICORN_PID" 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM

# Backend in background
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &
UVICORN_PID=$!

# Frontend in foreground (proxies /api to backend)
cd frontend && npm run dev
