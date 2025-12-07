#!/bin/bash
# Uninstall systemd service for Resource Monitor

set -e

SERVICE_FILE="resource-monitor.service"
SYSTEMD_DIR="/etc/systemd/system"

echo "=== Resource Monitor Service Uninstallation ==="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

# Check if service exists
if [ ! -f "${SYSTEMD_DIR}/${SERVICE_FILE}" ]; then
    echo "Service is not installed"
    exit 0
fi

echo "Stopping service..."
systemctl stop ${SERVICE_FILE} 2>/dev/null || true
echo "✓ Service stopped"

echo "Disabling service..."
systemctl disable ${SERVICE_FILE} 2>/dev/null || true
echo "✓ Service disabled"

echo "Removing service file..."
rm -f "${SYSTEMD_DIR}/${SERVICE_FILE}"
echo "✓ Service file removed"

echo "Reloading systemd..."
systemctl daemon-reload
echo "✓ Systemd configuration reloaded"

echo ""
echo "=== Uninstallation Complete ==="
echo "The service has been removed and will not start on boot."
echo ""
echo "Note: Virtual environment and project files are NOT deleted."
echo "To remove everything, manually delete the project directory."
