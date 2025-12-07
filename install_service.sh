#!/bin/bash
# Install systemd service for Resource Monitor

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_TEMPLATE="${SCRIPT_DIR}/resource-monitor.service"
SERVICE_FILE="resource-monitor.service"
SYSTEMD_DIR="/etc/systemd/system"

echo "=== Resource Monitor Service Installation ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

# Get the current user (the one who invoked sudo)
ACTUAL_USER="${SUDO_USER:-$USER}"

if [ "$ACTUAL_USER" = "root" ]; then
    echo "WARNING: Running as root user. Please specify the user to run the service:"
    read -p "Enter username: " ACTUAL_USER
fi

echo "Installing service to run as user: ${ACTUAL_USER}"
echo "Project directory: ${SCRIPT_DIR}"
echo ""

# Verify project structure
if [ ! -f "${SCRIPT_DIR}/main.py" ]; then
    echo "ERROR: main.py not found in ${SCRIPT_DIR}"
    echo "Please run this script from the project directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "${SCRIPT_DIR}/.venv" ] || [ ! -f "${SCRIPT_DIR}/.venv/bin/python" ]; then
    echo "ERROR: Virtual environment not found or incomplete!"
    echo ""
    echo "Please run setup_env.sh first to create the virtual environment:"
    echo "  cd ${SCRIPT_DIR}"
    echo "  ./setup_env.sh"
    echo ""
    echo "This will:"
    echo "  1. Create a .venv directory with Python virtual environment"
    echo "  2. Install all required dependencies"
    echo ""
    exit 1
fi

echo "✓ Virtual environment found at ${SCRIPT_DIR}/.venv"

# Make scripts executable
if [ -f "${SCRIPT_DIR}/setup_env.sh" ]; then
    chmod +x "${SCRIPT_DIR}/setup_env.sh"
fi

# Create service file from template
echo "Creating systemd service file..."
sed -e "s|%USER%|${ACTUAL_USER}|g" \
    -e "s|%PROJECT_DIR%|${SCRIPT_DIR}|g" \
    "${SERVICE_TEMPLATE}" > "/tmp/${SERVICE_FILE}"

# Install service file
cp "/tmp/${SERVICE_FILE}" "${SYSTEMD_DIR}/${SERVICE_FILE}"
rm "/tmp/${SERVICE_FILE}"
echo "✓ Service file installed to ${SYSTEMD_DIR}/${SERVICE_FILE}"

# Reload systemd
systemctl daemon-reload
echo "✓ Systemd configuration reloaded"

# Enable service
systemctl enable ${SERVICE_FILE}
echo "✓ Service enabled (will start on boot)"

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Service management commands:"
echo "  Start service:   sudo systemctl start resource-monitor"
echo "  Stop service:    sudo systemctl stop resource-monitor"
echo "  Restart service: sudo systemctl restart resource-monitor"
echo "  View status:     sudo systemctl status resource-monitor"
echo "  View logs:       sudo journalctl -u resource-monitor -f"
echo "  Disable autostart: sudo systemctl disable resource-monitor"
echo ""
read -p "Would you like to start the service now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl start resource-monitor
    echo ""
    echo "Service started! Checking status..."
    sleep 2
    systemctl status resource-monitor --no-pager
fi
