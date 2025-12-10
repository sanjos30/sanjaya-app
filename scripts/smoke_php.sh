#!/usr/bin/env bash
set -euo pipefail

PHP_DIR="${PHP_DIR:-backend-php}"
PORT="${PORT:-8000}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"
SLEEP_START="${SLEEP_START:-3}"

if [[ ! -d "$PHP_DIR" ]]; then
  echo "PHP backend dir not found: $PHP_DIR" >&2
  exit 1
fi

pushd "$PHP_DIR" >/dev/null

if [[ -f ".env.example" && ! -f ".env" ]]; then
  cp .env.example .env
fi

if command -v composer >/dev/null 2>&1; then
  composer install --no-interaction --no-progress --prefer-dist >/dev/null
else
  echo "composer not found on PATH" >&2
  exit 1
fi

php -S 127.0.0.1:"$PORT" -t public >/dev/null 2>&1 &
SERVER_PID=$!

sleep "$SLEEP_START"

curl --fail --silent --show-error "$HEALTH_URL"

kill "$SERVER_PID" >/dev/null 2>&1 || true
wait "$SERVER_PID" 2>/dev/null || true

popd >/dev/null


