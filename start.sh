#!/bin/bash
# Start Resource Monitor (non-service mode)

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Starting Resource Monitor ==="
echo ""

# Run setup to ensure environment is ready
"${SCRIPT_DIR}/setup_env.sh"

echo ""
echo "Starting monitor..."
echo "Press Ctrl+C to stop"
echo ""

# Run the monitor
"${SCRIPT_DIR}/.venv/bin/python" "${SCRIPT_DIR}/main.py"
