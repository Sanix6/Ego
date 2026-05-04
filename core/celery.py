import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


CELERY_BEAT_SCHEDULE = {
    "courier-slot-reminders-every-5-min": {
        "task": "apps.taxi.tasks.send_courier_slot_reminders",
        "schedule": crontab(minute="*/60"),
    },
}