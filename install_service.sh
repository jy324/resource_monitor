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

if [ ! -f "${SCRIPT_DIR}/setup_env.sh" ]; then
    echo "ERROR: setup_env.sh not found in ${SCRIPT_DIR}"
    exit 1
fi

# Make scripts executable
chmod +x "${SCRIPT_DIR}/setup_env.sh"
echo "✓ Made setup_env.sh executable"

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
