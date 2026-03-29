#!/bin/bash
# setup_production.sh
# Initial production server setup script.
#
# Run as the jttbh user on an Ubuntu server after cloning the repository:
#   git clone https://github.com/JasonRFrancis/JTTBH.git ~/JTTBH
#   cd ~/JTTBH
#   chmod +x config/setup_production.sh
#   ./config/setup_production.sh
#
# Assumptions:
#   - Ubuntu 22.04 LTS
#   - Python 3.10+ installed (system or pyenv)
#   - MySQL 8.0+ already installed and running
#   - Nginx installed
#   - User 'jttbh' with home /home/jttbh
#
# Run: chmod +x config/setup_production.sh

set -e

DEPLOY_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_NAME="jttbh"
NGINX_CONF="/etc/nginx/sites-available/jttbh"
SYSTEMD_UNIT="/etc/systemd/system/${SERVICE_NAME}.service"

echo "=== JTTBH Production Setup ==="
echo "Directory: $DEPLOY_DIR"
echo ""

# -------------------------------------------------------------------
# 1. Python virtual environment
# -------------------------------------------------------------------
echo "-- Creating Python virtual environment..."
python3 -m venv "$DEPLOY_DIR/venv"
source "$DEPLOY_DIR/venv/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "$DEPLOY_DIR/requirements.txt"
echo "   Dependencies installed."

# -------------------------------------------------------------------
# 2. Environment file
# -------------------------------------------------------------------
if [ ! -f "$DEPLOY_DIR/.env" ]; then
  if [ -f "$DEPLOY_DIR/.env.prod" ]; then
    cp "$DEPLOY_DIR/.env.prod" "$DEPLOY_DIR/.env"
    echo "-- Copied .env.prod to .env"
  else
    echo "-- WARNING: No .env.prod found. Copy .env.example to .env.prod and fill in values."
    cp "$DEPLOY_DIR/.env.example" "$DEPLOY_DIR/.env"
  fi
fi

# -------------------------------------------------------------------
# 3. MySQL database setup
# -------------------------------------------------------------------
echo ""
echo "-- Database setup"
echo "   Run the following as root to create the database and user:"
echo "   mysql -u root -p << 'EOF'"
echo "   CREATE DATABASE IF NOT EXISTS jttbh CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
echo "   CREATE USER IF NOT EXISTS 'jttbh'@'localhost' IDENTIFIED BY 'CHANGE_ME';"
echo "   GRANT ALL PRIVILEGES ON jttbh.* TO 'jttbh'@'localhost';"
echo "   FLUSH PRIVILEGES;"
echo "   EOF"
echo ""
echo "   Then import the schema:"
echo "   mysql -u jttbh -p jttbh < $DEPLOY_DIR/schema.sql"

# -------------------------------------------------------------------
# 4. Systemd service unit
# -------------------------------------------------------------------
echo ""
echo "-- Creating systemd service unit at $SYSTEMD_UNIT..."
sudo tee "$SYSTEMD_UNIT" > /dev/null << EOF
[Unit]
Description=JTTBH Flask Application
After=network.target mysql.service

[Service]
User=jttbh
Group=jttbh
WorkingDirectory=$DEPLOY_DIR
EnvironmentFile=$DEPLOY_DIR/.env
ExecStart=$DEPLOY_DIR/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 "app:create_app()"
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
echo "   Systemd unit created and enabled."

# -------------------------------------------------------------------
# 5. Nginx configuration
# -------------------------------------------------------------------
echo ""
echo "-- Creating Nginx configuration at $NGINX_CONF..."
sudo tee "$NGINX_CONF" > /dev/null << 'EOF'
server {
    listen 80;
    server_name jttbh.org www.jttbh.org;

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name jttbh.org www.jttbh.org;

    # SSL certificates (replace with your Let's Encrypt paths)
    ssl_certificate /etc/letsencrypt/live/jttbh.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/jttbh.org/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;

    location /static/ {
        alias /home/jttbh/JTTBH/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/jttbh
sudo nginx -t && echo "   Nginx config is valid."

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Configure .env with real credentials"
echo "  2. Import database schema"
echo "  3. Set up SSL: certbot --nginx -d jttbh.org -d www.jttbh.org"
echo "  4. Start services: sudo systemctl start $SERVICE_NAME && sudo systemctl reload nginx"
echo "  5. Verify: sudo systemctl status $SERVICE_NAME"
