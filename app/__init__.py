try:
    from .celery import app as celery_app
except Exception:
    celery_app = None  # 暫時避免在管理指令階段爆掉，之後再恢復
