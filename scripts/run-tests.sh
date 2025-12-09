#!/bin/bash
# Test runner script for Sanjaya Autopilot

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

# Run tests
cd "$PROJECT_ROOT"

# Run pytest if available, otherwise use unittest
if command -v pytest &> /dev/null; then
    pytest tests/ -v
else
    python -m unittest discover -s tests -p "test_*.py" -v
fi

