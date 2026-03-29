#!/bin/bash
# deploy.sh
# Deploy updates to the production server.
#
# Run from the project root on the production server as the jttbh user:
#   ./config/deploy.sh
#
# Prerequisites:
#   - Git remote 'origin' pointing to the production branch
#   - venv/ virtual environment already created (see setup_production.sh)
#   - Systemd unit jttbh.service configured
#   - Nginx configured as reverse proxy
#
# Run: chmod +x config/deploy.sh

set -e

DEPLOY_DIR="/home/jttbh/JTTBH"
SERVICE_NAME="jttbh"

echo "=== Deploying JTTBH ==="
echo "Directory: $DEPLOY_DIR"
echo "Timestamp: $(date)"
echo ""

# 1. Pull latest code from main
echo "-- Pulling latest code..."
cd "$DEPLOY_DIR"
git pull origin main

# 2. Activate virtual environment and update dependencies
echo "-- Installing Python dependencies..."
source "$DEPLOY_DIR/venv/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "$DEPLOY_DIR/requirements.txt"

# 3. Switch to production environment file
echo "-- Activating production environment..."
if [ -f "$DEPLOY_DIR/.env.prod" ]; then
  cp "$DEPLOY_DIR/.env.prod" "$DEPLOY_DIR/.env"
  echo "   .env.prod -> .env"
else
  echo "   WARNING: .env.prod not found; using existing .env"
fi

# 4. Restart application and web server
echo "-- Restarting services..."
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl restart nginx

# 5. Wait a moment and check service status
sleep 2
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
  echo "-- $SERVICE_NAME is running"
else
  echo "ERROR: $SERVICE_NAME failed to start. Check logs:"
  echo "  journalctl -u $SERVICE_NAME -n 50 --no-pager"
  exit 1
fi

echo ""
echo "=== Deploy complete ==="
echo "App URL: https://jttbh.org"
