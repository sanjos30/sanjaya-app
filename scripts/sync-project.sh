#!/bin/bash
# Script to sync or register a project with Sanjaya Autopilot

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check if project path is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <project_path>"
    echo "Example: $0 /path/to/my-project"
    exit 1
fi

PROJECT_PATH="$1"

# Validate project path
if [ ! -d "$PROJECT_PATH" ]; then
    echo "Error: Project path does not exist: $PROJECT_PATH"
    exit 1
fi

# Check for autopilot.yaml
AUTOPILOT_CONFIG="$PROJECT_PATH/.sanjaya/autopilot.yaml"
if [ ! -f "$AUTOPILOT_CONFIG" ]; then
    echo "Error: autopilot.yaml not found at $AUTOPILOT_CONFIG"
    echo "Please create .sanjaya/autopilot.yaml in your project first."
    exit 1
fi

# Validate configuration
echo "Validating autopilot.yaml..."
# TODO: Add validation logic

# Register/sync project
echo "Syncing project: $PROJECT_PATH"
# TODO: Add sync/registration logic

echo "Project synced successfully!"

