import os
from decimal import Decimal

from django.conf import settings
from django.db import transaction

from apps.balance.models import (
    WorkerWallet,
    WalletTransaction,
)
from apps.balance.choices import (
    TransactionType,
    TransactionStatus,
)
from apps.delivery.models import Delivery
from apps.taxi.models import TaxiRide
from apps.notify.bonus import deposit_success


LOG_DIR = os.path.join(settings.BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

PAYMENT_LOG_FILE = os.path.join(LOG_DIR, "payments.log")


def write_payment_log(message):
    with open(PAYMENT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{message}\n")

def handle_order_payment(payment):
    write_payment_log(f"[ORDER_PAYMENT] START payment_id={payment.id}")

    if payment.order_id is None:
        write_payment_log("[ORDER_PAYMENT] order_id is None")
        return

    order = None
    worker = None
    delivery = None
    taxi = None

    if payment.type_payment == "delivery":

        delivery = Delivery.objects.filter(
            id=payment.order_id
        ).first()

        if delivery:
            order = delivery
            worker = delivery.courier

            write_payment_log(
                f"[ORDER_PAYMENT] DELIVERY FOUND id={delivery.id}"
            )

    elif payment.type_payment == "taxi":

        taxi = TaxiRide.objects.filter(
            id=payment.order_id
        ).first()

        if taxi:
            order = taxi
            worker = taxi.driver

            write_payment_log(
                f"[ORDER_PAYMENT] TAXI FOUND id={taxi.id}"
            )

    if not order:
        write_payment_log("[ORDER_PAYMENT] ORDER NOT FOUND")
        return

    if not worker:
        write_payment_log("[ORDER_PAYMENT] WORKER NOT FOUND")
        return

    wallet, _ = WorkerWallet.objects.get_or_create(
        worker=worker
    )

    earning_amount = (
        getattr(order, "courier_earnings", None)
        or getattr(order, "driver_payout", None)
        or getattr(order, "courier_fee", None)
        or getattr(order, "driver_fee", None)
        or getattr(order, "price", None)
        or Decimal("0.00")
    )

    write_payment_log(
        f"[ORDER_PAYMENT] earning_amount={earning_amount}"
    )

    already_exists = WalletTransaction.objects.filter(
        wallet=wallet,
        transaction_type=TransactionType.ORDER_EARNING_ONLINE,
        delivery=delivery,
        taxi_ride=taxi,
        comment=f"order:{payment.id}",
    ).exists()

    if already_exists:
        write_payment_log(
            "[ORDER_PAYMENT] TRANSACTION ALREADY EXISTS"
        )
        return

    transaction_obj = WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type=TransactionType.ORDER_EARNING_ONLINE,
        status=TransactionStatus.COMPLETED,
        amount=earning_amount,
        sign=1,
        channel="online",
        delivery=delivery,
        taxi_ride=taxi,
        comment=f"order:{payment.id}",
    )

    write_payment_log(
        f"[ORDER_PAYMENT] TRANSACTION CREATED id={transaction_obj.id}"
    )


def handle_cash_order_complete(order, worker):
    wallet, _ = WorkerWallet.objects.get_or_create(worker=worker)

    earning_amount = (
        getattr(order, "courier_earnings", None)
        or getattr(order, "driver_payout", None)
        or getattr(order, "price", None)
        or Decimal("0.00")
    )

    already_exists = WalletTransaction.objects.filter(
        wallet=wallet,
        transaction_type=TransactionType.ORDER_EARNING_CASH,
        delivery=order if isinstance(order, Delivery) else None,
        taxi_ride=order if isinstance(order, TaxiRide) else None,
        comment=f"cash:{order.id}",
    ).exists()

    if already_exists:
        return

    WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type=TransactionType.ORDER_EARNING_CASH,
        status=TransactionStatus.COMPLETED,
        amount=earning_amount,
        sign=1,
        channel="cash",
        delivery=order if isinstance(order, Delivery) else None,
        taxi_ride=order if isinstance(order, TaxiRide) else None,
        comment=f"cash:{order.id}",
    )


def handle_payment_success(payment):
    write_payment_log(
        f"[PAYMENT_SUCCESS] payment_id={payment.id} type={payment.type_payment}"
    )

    if payment.type_payment == "deposit":
        handle_deposit(payment)
    else:
        handle_order_payment(payment)


def handle_deposit(payment):
    user = payment.user

    write_payment_log(
        f"[DEPOSIT] START payment_id={payment.id} user_id={user.id} amount={payment.amount}"
    )

    wallet, created = WorkerWallet.objects.get_or_create(worker=user)

    write_payment_log(
        f"[DEPOSIT] Wallet {'created' if created else 'found'} wallet_id={wallet.id}"
    )

    with transaction.atomic():

        already_exists = WalletTransaction.objects.filter(
            wallet=wallet,
            transaction_type=TransactionType.DEPOSIT,
            comment=f"deposit:{payment.id}",
        ).exists()

        if already_exists:
            write_payment_log("[DEPOSIT] TRANSACTION ALREADY EXISTS")
            return

        transaction_obj = WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=TransactionType.DEPOSIT,
            status=TransactionStatus.COMPLETED,
            amount=payment.amount,
            sign=1,
            channel="online",
            comment=f"deposit:{payment.id}",
        )

        write_payment_log(f"[DEPOSIT] TRANSACTION CREATED id={transaction_obj.id}")

    deposit_success(user, payment.amount)

    write_payment_log(f"[DEPOSIT] NOTIFICATION SENT user_id={user.id}")