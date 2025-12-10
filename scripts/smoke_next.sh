#!/usr/bin/env bash
set -euo pipefail

FRONTEND_DIR="${FRONTEND_DIR:-frontend}"
PORT="${PORT:-3000}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:3000/api/health}"
SLEEP_START="${SLEEP_START:-15}"

if [[ ! -d "$FRONTEND_DIR" ]]; then
  echo "Frontend dir not found: $FRONTEND_DIR" >&2
  exit 1
fi

pushd "$FRONTEND_DIR" >/dev/null

if [[ -f "package-lock.json" ]]; then
  npm ci >/dev/null
else
  npm install >/dev/null
fi

NEXT_TELEMETRY_DISABLED=1 PORT="$PORT" npm run dev >/dev/null 2>&1 &
SERVER_PID=$!

sleep "$SLEEP_START"

curl --fail --silent --show-error "$HEALTH_URL"

kill "$SERVER_PID" >/dev/null 2>&1 || true
wait "$SERVER_PID" 2>/dev/null || true

popd >/dev/null


