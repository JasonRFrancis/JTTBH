#!/bin/bash
# switch_env.sh
# Switch the active .env file between dev and prod configurations.
#
# Usage:
#   ./config/switch_env.sh dev     # Use .env.dev
#   ./config/switch_env.sh prod    # Use .env.prod
#   ./config/switch_env.sh status  # Show current FLASK_ENV and DEBUG values
#
# Run: chmod +x config/switch_env.sh

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

case "$1" in
  dev)
    if [ -f "$SCRIPT_DIR/.env.dev" ]; then
      cp "$SCRIPT_DIR/.env.dev" "$SCRIPT_DIR/.env"
      echo "Switched to development environment (.env.dev -> .env)"
    else
      echo "ERROR: .env.dev not found in $SCRIPT_DIR"
      exit 1
    fi
    ;;
  prod)
    if [ -f "$SCRIPT_DIR/.env.prod" ]; then
      cp "$SCRIPT_DIR/.env.prod" "$SCRIPT_DIR/.env"
      echo "Switched to production environment (.env.prod -> .env)"
    else
      echo "ERROR: .env.prod not found in $SCRIPT_DIR"
      exit 1
    fi
    ;;
  status)
    if [ -f "$SCRIPT_DIR/.env" ]; then
      echo "Current .env settings:"
      grep -E "^(FLASK_ENV|DEBUG|MYSQL_HOST|MYSQL_DB)" "$SCRIPT_DIR/.env" || echo "(no matching keys found)"
    else
      echo "No .env file found in $SCRIPT_DIR"
      exit 1
    fi
    ;;
  *)
    echo "Usage: $0 [dev|prod|status]"
    echo ""
    echo "  dev     Copy .env.dev to .env (development mode)"
    echo "  prod    Copy .env.prod to .env (production mode)"
    echo "  status  Show current environment settings"
    exit 1
    ;;
esac
