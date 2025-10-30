cd /srv/issue_server

# 1) 停掉會循環重啟的服務
docker compose stop web celery beat

# 2) 先暫時停用 signals（讓 web 能先起來）
sed -i 's/^\s*from\s\.\simport\ssignals/# from . import signals/' core/apps.py

# 3) 用 Python 乾淨覆蓋 core/tasks.py（純 Python，無 shell 內容）
python3 - <<'PY'
from pathlib import Path
p = Path('core/tasks.py')
p.write_text("""\
import os
import requests
from celery import shared_task

GRAPH_BASE = "https://graph.microsoft.com/v1.0"

def get_graph_token():
    tenant = os.environ.get("GRAPH_TENANT_ID", "")
    client_id = os.environ.get("GRAPH_CLIENT_ID", "")
    client_secret = os.environ.get("GRAPH_CLIENT_SECRET", "")
    if not (tenant and client_id and client_secret):
        return None
    url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "https://graph.microsoft.com/.default",
    }
    resp = requests.post(url, data=data, timeout=10)
    resp.raise_for_status()
    return resp.json().get("access_token")

def post_channel_message(html_content: str):
    token = get_graph_token()
    team_id = os.environ.get("TEAMS_TEAM_ID", "")
    channel_id = os.environ.get("TEAMS_CHANNEL_ID", "")
    # 未設定 Graph/Teams 參數時，安靜略過
    if not (token and team_id and channel_id):
        return
    url = f"{GRAPH_BASE}/teams/{team_id}/channels/{channel_id}/messages"
    payload = {"body": {"contentType": "html", "content": html_content}}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers, timeout=10)
    r.raise_for_status()

@shared_task
def send_issue_update_to_teams(issue_id: int, event: str):
    from .models import Issue
    issue = Issue.objects.get(id=issue_id)
    assignee_name = issue.assignee.get_full_name() if issue.assignee else "未指派"
    base_url = os.environ.get("APP_BASE_URL", "http://localhost:8080")
    html = (
        f"<b>#{issue.id} {issue.title}</b><br/>"
        f"事件：{event}｜狀態：{issue.get_status_display()}｜優先度：{issue.get_priority_display()}<br/>"
        f"指派：{assignee_name}<br/>"
        f"<a href='{base_url}/admin/core/sue.id}/change/查看</a>"
    )
    post_channel_message(html)
""", encoding="utf-8")
PY

# 4) （若之前用 Windows 編輯器貼過）移除 CRLF
sed -i 's/\r$//' core/tasks.py

# 5) 在主機上檢查 Python 語法（沒有輸出=OK）
python3 -m py_compile core/tasks.py

# 6) 清掉 compose 的舊警告（可選，但建議）
sed -i '/^version:/d' docker-compose.yml

# 7) 重建並啟動
docker compose up -d --build

# 8) 套用遷移（建立資料表）
docker compose exec web python manage.py makemigrations core
docker compose exec web python manage.py migrate

# 9) 重新啟用 signals，並重啟服務
sed -i 's/^# from \. import signals/from . import signals/' core/apps.py
docker compose restart web celery beat

# 10) 查看 log 確認沒有錯誤
docker compose logs web --tail=200
docker compose logs celery --tail=200
