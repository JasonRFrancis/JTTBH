#!/bin/bash
# update_server.sh
# Safely apply OS package updates on the production Ubuntu server, and
# let the admin schedule a restart if one is required afterward.
#
# Run as the jttbh user (with sudo) on the production server:
#   chmod +x config/update_server.sh
#   ./config/update_server.sh
#
# Run: chmod +x config/update_server.sh

set -euo pipefail

if [ "$EUID" -eq 0 ]; then
  echo "Run this as a normal user with sudo privileges, not as root directly."
  exit 1
fi

echo "=== JTTBH Server Update ==="
echo "Timestamp: $(date)"
echo ""

# -------------------------------------------------------------------
# 1. Update package lists and apply upgrades
# -------------------------------------------------------------------
echo "-- Updating package lists..."
sudo apt-get update -qq

echo "-- Applying upgrades..."
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y

echo "-- Removing unused packages..."
sudo apt-get autoremove -y --purge
sudo apt-get autoclean -y

echo ""
echo "=== Update complete ==="

# -------------------------------------------------------------------
# 2. Check whether a restart is required
# -------------------------------------------------------------------
if [ ! -f /var/run/reboot-required ]; then
  echo "No restart required."
  exit 0
fi

echo ""
echo "!! A restart is required to finish applying updates."
if [ -f /var/run/reboot-required.pkgs ]; then
  echo "   Packages requiring restart:"
  sed 's/^/     - /' /var/run/reboot-required.pkgs
fi

echo ""
echo "Schedule the restart:"
echo "  1) Now"
echo "  2) In N minutes"
echo "  3) At a specific time (HH:MM)"
echo "  4) Skip (restart manually later with: sudo shutdown -r now)"
read -rp "Choice [1-4]: " choice

case "$choice" in
  1)
    sudo shutdown -r now "Restarting now to finish applying updates."
    ;;
  2)
    read -rp "Minutes from now: " mins
    sudo shutdown -r "+${mins}" "Restarting in ${mins} minute(s) to finish applying updates."
    echo "Restart scheduled in ${mins} minute(s). Cancel with: sudo shutdown -c"
    ;;
  3)
    read -rp "Time (HH:MM, 24h): " at_time
    sudo shutdown -r "${at_time}" "Restarting at ${at_time} to finish applying updates."
    echo "Restart scheduled for ${at_time}. Cancel with: sudo shutdown -c"
    ;;
  *)
    echo "Skipped. Remember to restart manually: sudo shutdown -r now"
    ;;
esac
