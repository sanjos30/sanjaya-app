#!/usr/bin/env bash
# Development startup script for Sanjaya Autopilot core service
# This is for local development only.

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Set Python path
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Activate virtual environment if it exists
if [ -d "$PROJECT_ROOT/venv" ]; then
    source "$PROJECT_ROOT/venv/bin/activate"
fi

# Set environment variables
export SANJAYA_ENV="development"
export SANJAYA_LOG_LEVEL="DEBUG"

# Run the FastAPI service
cd "$PROJECT_ROOT"
uvicorn autopilot_core.main_service.api:app --reload

