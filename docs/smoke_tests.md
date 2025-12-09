# Smoke Tests Overview

This repo includes stack-specific smoke scripts and runtime entries to let OrchestratorAgent install, start, health-check, and stop services in a non-interactive way.

## Scripts
- `scripts/smoke_fastapi.sh` — uses `BACKEND_DIR` (default: `backend`); supports `--install-only`; creates venv, installs, runs uvicorn, curls `/health`, stops.
- `scripts/smoke_next.sh` — uses `FRONTEND_DIR` (default: `frontend`); npm install/ci, runs dev on port 3000, curls `/api/health`, stops.
- `scripts/smoke_php.sh` — uses `PHP_DIR` (default: `backend-php`); composer install, runs PHP server on port 8000, curls `/health`, stops.

Env overrides:
- `BACKEND_DIR`, `FRONTEND_DIR`, `PHP_DIR` can override default directories.

## Orchestrator usage
OrchestratorAgent reads `runtime.*` from `autopilot.yaml`:
- `runtime.<stack>.install_command`
- `runtime.<stack>.smoke_command`
- Flags on `/workflows/run`: `run_smoke`, `smoke_timeout`, `smoke_health_path` (if configured; currently unused in scripts).

## Example (FastAPI-only reference)
`configs/examples/example-project/.sanjaya/autopilot.yaml`:
```
runtime:
  backend_fastapi:
    install_command: "BACKEND_DIR=${BACKEND_DIR:-backend} bash scripts/smoke_fastapi.sh --install-only"
    smoke_command: "BACKEND_DIR=${BACKEND_DIR:-backend} bash scripts/smoke_fastapi.sh"
    dev_command: "cd ${BACKEND_DIR:-backend} && . .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"
    test_command: "cd ${BACKEND_DIR:-backend} && . .venv/bin/activate && pytest -q"
```

## Health endpoints required
- FastAPI: `GET /health` → `{"status": "ok"}` in `backend/app/main.py`.
- Next.js:
  - App Router: `app/api/health/route.ts` returning `{"status": "ok"}`.
  - Pages Router: `pages/api/health.ts` returning `{"status": "ok"}`.
- PHP: `public/index.php` returns `{"status": "ok"}` on `GET /health`.

With these in place, smoke scripts should pass when invoked via Orchestrator (with `run_smoke=true`) or manually.

## Workflow Status

When `run_smoke=true`:
- If smoke test fails → workflow status is set to `FAILED_SMOKE`
- Smoke failures block workflow success (workflow_status = `failed_smoke`)
- The response includes `smoke_passed: false` and `workflow_status: "failed_smoke"`

