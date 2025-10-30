#!/usr/bin/env bash
set -Eeuo pipefail

cd /srv/issue_server

COMPOSE_FILES=(-f docker-compose.yml)
# 如需疊加另一份：COMPOSE_FILES+=(-f fae_issue/docker-compose.yml)

echo "[1/5] YAML 驗證（不展開環境變數）"
docker compose "${COMPOSE_FILES[@]}" config --no-interpolate >/tmp/compose.yaml

echo "[2/5] 建置 web 映像（離線 wheelhouse）"
docker compose "${COMPOSE_FILES[@]}" build --no-cache web

echo "[3/5] 啟動服務（清理孤兒）"
docker compose "${COMPOSE_FILES[@]}" up -d --remove-orphans

echo "[4/5] 等待 web 就緒（健康檢查）"
# 觀察狀態；如無 healthcheck，可簡要 sleep 10
docker compose "${COMPOSE_FILES[@]}" ps web
sleep 10 || true

STATUS=$(docker inspect -f '{{.State.Status}}' fae_issue_web || echo "unknown")
if [[ "$STATUS" != "running" ]]; then
  echo "❌ web 未在運行（狀態：$STATUS）。顯示最近 200 行日誌："
  docker compose "${COMPOSE_FILES[@]}" logs --tail=200 web || true
  exit 1
fi

echo "[5/5] 執行 Django 管理命令"
docker compose "${COMPOSE_FILES[@]}" exec web python manage.py migrate
# 如不想互動卡住，可改用環境變數 + --noinput（示例）
# docker compose "${COMPOSE_FILES[@]}" exec -e DJANGO_SUPERUSER_USERNAME=admin -e DJANGO_SUPERUSER_PASSWORD='P@ssw0rd!' -e DJANGO_SUPERUSER_EMAIL=admin@example.com web python manage.py createsuperuser --noinput || true
docker compose "${COMPOSE_FILES[@]}" exec web python manage.py collectstatic --noinput
docker compose "${COMPOSE_FILES[@]}" exec web python manage.py check

echo "✅ 完成，請連線 http://<server>:8000/admin"
