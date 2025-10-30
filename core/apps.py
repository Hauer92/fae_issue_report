from django.apps import AppConfig
import logging

log = logging.getLogger(__name__)

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Issue Core'

    def ready(self):
        # 這裡只做輕量 import，避免副作用
        try:
            import core.signals  # noqa
            log.info("core.signals loaded")
        except Exception as e:
            log.exception("Failed to load core.signals: %s", e)
