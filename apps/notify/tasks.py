from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from apps.delivery.models import CourierSlot
from apps.notify.push import send_courier_slot_reminder_push


@shared_task
def send_courier_slot_reminders():
    now = timezone.now()
    one_hour_later = now + timedelta(hours=1)

    slots = CourierSlot.objects.select_related("courier").filter(
        courier__isnull=False,
        start_at__gte=now,
        start_at__lte=one_hour_later,
        slot_reminder_sent_at__isnull=True,
    )

    for slot in slots:
        send_courier_slot_reminder_push(slot)

        slot.slot_reminder_sent_at = now
        slot.save(update_fields=["slot_reminder_sent_at"])