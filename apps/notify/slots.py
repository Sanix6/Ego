from django.utils.timezone import localtime
from .services import PushService


def slot_booked(slot):
    start = slot.start_at.strftime("%d.%m.%Y %H:%M")
    end = slot.end_at.strftime("%H:%M")

    return PushService.send(
        user=slot.courier,
        event_type="slot_booked",
        event_key=f"slot_booked_{slot.id}_{slot.courier_id}",
        title="Слот забронирован",
        message=f"Вы забронировали слот {start} - {end}",
        slot=slot,
        payload={
            "type": "navigate",
            "screen": "SlotDetail",
            "slot_id": slot.id,
        }
    )


def slot_cancelled(slot, user):
    start = slot.start_at.strftime("%d.%m.%Y %H:%M")
    end = slot.end_at.strftime("%H:%M")

    return PushService.send(
        user=user,
        event_type="slot_cancelled",
        event_key=f"slot_cancelled_{slot.id}_{user.id}",
        title="Слот отменён",
        message=f"Вы отменили слот {start} - {end}. Частые отмены могут повлиять на рейтинг.",
        slot=slot,
        payload={
            "type": "navigate",
            "screen": "Slots",
        }
    )
