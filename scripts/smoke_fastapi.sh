#!/usr/bin/env bash
set -euo pipefail

BACKEND_DIR="${BACKEND_DIR:-backend}"
APP_MODULE="${APP_MODULE:-app.main:app}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"
SLEEP_START="${SLEEP_START:-5}"

install_only=false
if [[ "${1-}" == "--install-only" ]]; then
  install_only=true
fi

if [[ ! -d "$BACKEND_DIR" ]]; then
  echo "Backend dir not found: $BACKEND_DIR" >&2
  exit 1
fi

pushd "$BACKEND_DIR" >/dev/null

# Create env from example if present
if [[ -f ".env.example" && ! -f ".env" ]]; then
  cp .env.example .env
fi

# Create venv if missing
if [[ ! -d ".venv" ]]; then
  python -m venv .venv
fi

source .venv/bin/activate

if [[ -f "requirements.txt" ]]; then
  pip install --upgrade pip >/dev/null
  pip install -r requirements.txt >/dev/null
fi

if $install_only; then
  deactivate
  popd >/dev/null
  exit 0
fi

# Start server
uvicorn "$APP_MODULE" --host "$HOST" --port "$PORT" >/dev/null 2>&1 &
SERVER_PID=$!

sleep "$SLEEP_START"

curl --fail --silent --show-error "$HEALTH_URL"

kill "$SERVER_PID" >/dev/null 2>&1 || true
wait "$SERVER_PID" 2>/dev/null || true

deactivate
popd >/dev/null


