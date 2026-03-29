#!/bin/bash
# quick_commands.sh
# Quick server management commands for JTTBH production.
#
# Usage:
#   ./config/quick_commands.sh status   # Check service status
#   ./config/quick_commands.sh logs     # View recent logs
#   ./config/quick_commands.sh restart  # Restart app and nginx
#   ./config/quick_commands.sh backup   # Create a database backup
#   ./config/quick_commands.sh db       # Connect to the database
#
# Run: chmod +x config/quick_commands.sh

BACKUP_DIR="/home/jttbh/backups"
DB_USER="jttbh"
DB_NAME="jttbh"

case "$1" in
  status)
    echo "=== Service Status ==="
    sudo systemctl status jttbh nginx mysql --no-pager -l
    ;;

  logs)
    echo "=== JTTBH Application Logs (last 100 lines) ==="
    journalctl -u jttbh -n 100 --no-pager
    ;;

  logs-nginx)
    echo "=== Nginx Error Logs ==="
    sudo tail -n 100 /var/log/nginx/error.log
    ;;

  restart)
    echo "Restarting jttbh and nginx..."
    sudo systemctl restart jttbh
    sudo systemctl restart nginx
    sleep 2
    if sudo systemctl is-active --quiet jttbh; then
      echo "jttbh is running."
    else
      echo "ERROR: jttbh failed to start. Check: journalctl -u jttbh -n 50"
      exit 1
    fi
    ;;

  backup)
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql"
    echo "Creating backup: $BACKUP_FILE"
    mysqldump -u "$DB_USER" -p "$DB_NAME" > "$BACKUP_FILE"
    gzip "$BACKUP_FILE"
    echo "Backup created: ${BACKUP_FILE}.gz"
    # Keep only the 30 most recent backups
    ls -t "$BACKUP_DIR"/*.sql.gz 2>/dev/null | tail -n +31 | xargs -r rm --
    echo "Old backups pruned (keeping 30 most recent)."
    ;;

  db)
    echo "Connecting to $DB_NAME database..."
    mysql -u "$DB_USER" -p "$DB_NAME"
    ;;

  deploy)
    echo "Delegating to deploy.sh..."
    "$(dirname "$0")/deploy.sh"
    ;;

  *)
    echo "Usage: $0 [status|logs|logs-nginx|restart|backup|db|deploy]"
    echo ""
    echo "  status      Check jttbh, nginx, and mysql service status"
    echo "  logs        Show last 100 lines of jttbh application logs"
    echo "  logs-nginx  Show last 100 lines of nginx error log"
    echo "  restart     Restart jttbh and nginx services"
    echo "  backup      Create a timestamped MySQL database backup"
    echo "  db          Open a MySQL shell for the jttbh database"
    echo "  deploy      Pull latest code and restart (calls deploy.sh)"
    exit 1
    ;;
esac
