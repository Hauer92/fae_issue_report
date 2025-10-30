#!/usr/bin/env bash
set -euo pipefail
APP_DIR="/srv/issue_server"
MEDIA_DIR="/srv/issue_server/media"
BACKUP_DIR="/srv/issue_server/backups"
DB_CONTAINER="fae_db"
DB_USER="$(grep -E '^DB_USER=' "$APP_DIR/.env" | cut -d'=' -f2)"
DB_NAME="$(grep -E '^DB_NAME=' "$APP_DIR/.env" | cut -d'=' -f2)"
TS=$(date +"%Y%m%d-%H%M%S")

mkdir -p "$BACKUP_DIR"

# 1) PostgreSQL 邏輯備份
docker exec -i "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/db-$TS.sql.gz"

# 2) 附件備份
tar -czf "$BACKUP_DIR/media-$TS.tar.gz" -C "$MEDIA_DIR" .

# 3) 保留策略：刪除 30 天前的檔案
find "$BACKUP_DIR" -type f -mtime +30 -delete

echo "Backup done @ $TS → $BACKUP_DIR"
