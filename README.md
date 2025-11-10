# FAE Issue System — 開發/部署約定 (單步協作版)

## 目錄結構（目標狀態）
```
/app
├── app/                         # Django 專案 (settings, urls, wsgi, celery)
│   └── templates/               # 專案共用模板
│       ├── _base_admin_like.html
│       └── includes/ (navbar.html, messages.html)
├── issues/                      # Issues App
│   ├── models.py / views.py / urls.py / migrations/
│   └── templates/issues/        # App 專屬模板
│       ├── home.html
│       └── issue_detail.html
├── static/                      # 原始靜態（開發時）
└── staticfiles/                 # collectstatic 輸出（部署/WhiteNoise）
```

## 設定摘要
- `STATIC_URL = "/static/"`
- `STATIC_ROOT = "/app/staticfiles"`
- `STATICFILES_DIRS = ["/app/static"]`（若有原始靜態）
- `MIDDLEWARE`：`SecurityMiddleware` → `WhiteNoiseMiddleware` → 其他

## 單步協作規則（精簡版）
1) 每次只做一件事（單一指令或單一檔案修改）。
2) **容器優先**：用 `docker exec` 在容器內執行；
3) 修改模板/HTML 時，**使用容器內 Python + Base64** 寫檔，避免 `{% %}`、`{{ }}`、`<!DOCTYPE>` 被 shell 誤解析。
4) 指令前先聲明「預期輸出重點」，執行後只貼必要片段（狀態碼、前 N 行、或 Traceback）。
5) 重啟後以 **socket 就緒輪詢**（0.5s x 60s）再打 HTTP，避免 `Connection refused` / `reset by peer`。

## 常用檢查
- 檢查模板存在：`python3 -c "from pathlib import Path; print(Path('/app/issues/templates/issues/home.html').exists())"`
- 啟動後健康檢查：在容器內用 Python 連至 `127.0.0.1:8000` 做 socket 檢查 + `urllib.request.urlopen("/")`。
- 近 3~5 分鐘 logs：`docker logs fae_issue_web --since=5m | tail -n 300`。

## 靜態與 WhiteNoise
- 設定完成後執行：`python manage.py collectstatic --noinput`（容器內）。
- WhiteNoise 會讀取 `STATIC_ROOT`（`/app/staticfiles`），不要把 `staticfiles/` 放入版本控管。

## 備份與歸檔
- 所有 `.bak*`、`.tmp*`、與雜資料夾（如 `[web]`、`^C` 等）集中移到 `/_archive/<日期時間>/`，保留可回溯版本。

## 風險注意
- bash 可能對 `!` 進行 history expansion（例如 `<!DOCTYPE>`）；使用 **容器內 Python 組字串** 或 **Base64** 可避免。

## 團隊小提醒
- 模板位置以 **App 內模板** 為準（`issues/templates/issues/`），避免與專案層 `templates/issues/` 混用造成覆蓋。
- 路由以 `path("issues/<int:issue_id>/", ...)` 為主，模板使用 `{% url "issue_detail" issue.id %}` 維持穩定。
