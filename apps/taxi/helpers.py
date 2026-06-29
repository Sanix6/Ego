from decimal import Decimal

from apps.balance.models import WorkerWallet
from apps.main.models import TaxiCommission


def driver_has_min_balance(driver, car_class, payment_method):

    wallet = getattr(driver, "wallet", None)

    if not wallet:
        return False

    commission = (
        TaxiCommission.objects.filter(
            car_class=car_class,
            payment_method=payment_method,
            is_active=True
        ).first()
    )

    if not commission:

        commission = (
            TaxiCommission.objects.filter(
                car_class=car_class,
                payment_method__isnull=True,
                is_active=True
            ).first()
        )

    if not commission:
        return True

    return wallet.balance >= commission.minimum_balance