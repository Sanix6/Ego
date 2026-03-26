from django.utils import timezone
from .models import CourierSlot


def courier_has_active_in_work_slot(courier):
    if courier.user_type != "courier":
        return False

    now = timezone.now()

    return CourierSlot.objects.filter(
        courier=courier,
        status="in_work",
        start_at__lte=now,
        end_at__gte=now,
    ).exists()