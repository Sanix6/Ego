from django.utils.timezone import localtime
from .services import PushService


def send_courier_slot_reminder_push(slot):
    start_time = localtime(slot.start_at).strftime("%d.%m %H:%M")

    return PushService.send(
        user=slot.courier,
        event_type="courier_slot_reminder",
        event_key=f"courier_slot_reminder_{slot.id}",
        title="Напоминание о смене",
        message=f"Через 1 час у вас слот {start_time}",
        slot=slot,
        payload={
            "type": "navigate",
            "screen": "SlotDetail",
            "slot_id": slot.id,
        }
    )