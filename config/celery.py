import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# 毎日 0:00 (Asia/Tokyo) に実行
app.conf.beat_schedule = {
    "nightly-slack-import-and-export": {
        "task": "jobs.tasks.nightly_import_and_export",
        "schedule": crontab(hour=0, minute=0),
    },
}
