import os, requests
from celery import shared_task

GRAPH_BASE = "https://graph.microsoft.com/v1.0"

def get_graph_token() -> str:
    # client credentials flow
    tenant = os.environ.get("GRAPH_TENANT_ID")
    client_id = os.environ.get("GRAPH_CLIENT_ID")
    client_secret = os.environ.get("GRAPH_CLIENT_SECRET")
    url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "https://graph.microsoft.com/.default",
    }
    r = requests.post(url, data=data, timeout=10)
    r.raise_for_status()
    return r.json()["access_token"]

def post_channel_message(html_content: str):
    team_id = os.environ.get("TEAMS_TEAM_ID")
    channel_id = os.environ.get("TEAMS_CHANNEL_ID")
    token = get_graph_token()
    url = f"{GRAPH_BASE}/teams/{team_id}/channels/{channel_id}/messages"
    payload = {"body": {"contentType": "html", "content": html_content}}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.post(url, json=payload, headers=headers, timeout=10)
    r.raise_for_status()

@shared_task
def send_issue_update_to_teams(issue_id: int, event: str):
    from .models import Issue
    issue = Issue.objects.get(id=issue_id)
    assignee = issue.assignee.get_full_name() if issue.assignee else "未指派"
    html = (
        f"<b>#{issue.id} {issue.title}</b><br/>"
        f"事件：{event}｜狀態：{issue.get_status_display()}｜優先度：{issue.get_priority_display()}<br/>"
        f"指派：{assignee}<br/>"
        f"<a href='{os.environ.get('APP_BASEpost_channel_message(html)
