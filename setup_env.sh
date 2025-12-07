#!/bin/bash
# Setup script for Resource Monitor
# This script checks and sets up the virtual environment using uv

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"
REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements.txt"

echo "=== Resource Monitor Environment Setup ==="
echo "Project directory: ${SCRIPT_DIR}"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "ERROR: uv is not installed!"
    echo "Please install uv first:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "  OR"
    echo "  pip install uv"
    exit 1
fi

echo "✓ uv is installed"

# Check if .venv exists
if [ -d "${VENV_DIR}" ]; then
    echo "✓ Virtual environment exists at ${VENV_DIR}"
    
    # Verify Python executable
    if [ ! -f "${VENV_DIR}/bin/python" ]; then
        echo "ERROR: Python executable not found in ${VENV_DIR}/bin/"
        echo "Recreating virtual environment..."
        rm -rf "${VENV_DIR}"
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "${VENV_DIR}" ]; then
    echo "Creating virtual environment with uv..."
    cd "${SCRIPT_DIR}"
    uv venv .venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
source "${VENV_DIR}/bin/activate"

# Check if requirements.txt exists
if [ ! -f "${REQUIREMENTS_FILE}" ]; then
    echo "ERROR: requirements.txt not found at ${REQUIREMENTS_FILE}"
    exit 1
fi

echo "Checking installed packages..."

# Install/update packages using uv pip
echo "Installing/updating packages from requirements.txt..."
uv pip install -r "${REQUIREMENTS_FILE}"

echo ""
echo "Verifying installation..."

# Verify critical packages
REQUIRED_PACKAGES=("flask" "paramiko" "apscheduler" "psutil")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! python -c "import ${package}" 2>/dev/null; then
        MISSING_PACKAGES+=("${package}")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo "ERROR: Missing required packages: ${MISSING_PACKAGES[*]}"
    echo "Installation may have failed. Please check errors above."
    exit 1
fi

echo "✓ All required packages are installed"
echo ""
echo "=== Setup Complete ==="
echo "Virtual environment: ${VENV_DIR}"
echo "Python executable: ${VENV_DIR}/bin/python"
echo ""
echo "To activate the virtual environment manually:"
echo "  source ${VENV_DIR}/bin/activate"
echo ""
echo "To run the monitor:"
echo "  ${VENV_DIR}/bin/python ${SCRIPT_DIR}/main.py"
