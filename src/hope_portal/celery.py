import os

import celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hope_portal.config.settings")

app = celery.Celery(
    "hope_portal",
    loglevel="error",
    broker=settings.CELERY_BROKER_URL,
)
app.config_from_object("django.conf:settings", namespace="CELERY", force=True)
