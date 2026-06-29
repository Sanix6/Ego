from django.utils import timezone
from .models import CourierSlot
from apps.main.models import DeliveryCommission


def courier_has_min_balance(
    courier,
    type_delivery,
    payment_method
):

    wallet = getattr(courier, "wallet", None)

    if not wallet:
        return False

    commission = (
        DeliveryCommission.objects.filter(
            type_delivery=type_delivery,
            payment_method=payment_method,
            is_active=True
        ).first()
    )

    if not commission:

        commission = (
            DeliveryCommission.objects.filter(
                type_delivery=type_delivery,
                payment_method__isnull=True,
                is_active=True
            ).first()
        )

    if not commission:
        return True

    return wallet.balance >= commission.minimum_balance

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