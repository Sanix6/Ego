from decimal import Decimal
from django.db import transaction

from apps.balance.models import (
    WorkerWallet,
    WalletTransaction,
)

from .models import *
from apps.balance.choices import (
    TransactionType,
    TransactionStatus
)

from apps.main.models import (
    TaxiCommission,
    DeliveryCommission
)

from apps.payments.services import NambaPayService


class CommissionService:

    @staticmethod
    @transaction.atomic
    def process_taxi_commission(taxi):

        driver = taxi.driver

        wallet = WorkerWallet.objects.select_for_update().get(
            worker=driver
        )

        commission_rule = (
            TaxiCommission.objects.filter(
                car_class=taxi.car_class,
                payment_method=taxi.payment_method,
                is_active=True
            ).first()
        )

        if not commission_rule:
            commission_rule = (
                TaxiCommission.objects.filter(
                    car_class=taxi.car_class,
                    payment_method__isnull=True,
                    is_active=True
                ).first()
            )

        if not commission_rule:
            return

        order_amount = Decimal(str(taxi.price))

        commission_amount = (
            order_amount *
            commission_rule.commission_percent
        ) / Decimal("100")

        if commission_amount < commission_rule.min_commission:
            commission_amount = commission_rule.min_commission

        if (
            commission_rule.max_commission and
            commission_amount > commission_rule.max_commission
        ):
            commission_amount = commission_rule.max_commission

        commission_amount = commission_amount.quantize(
            Decimal("0.01")
        )

        transaction_obj = WalletTransaction.objects.create(
            wallet=wallet,
            taxi_ride=taxi,
            transaction_type=TransactionType.COMMISSION,
            status=TransactionStatus.COMPLETED,
            amount=commission_amount,
            sign=-1,
            comment=f"Taxi commission #{taxi.id}"
        )

        transfer_response = None
        transfer_status = "failed"

        try:

            transfer_response = NambaPayService.transfer_money(
                amount=int(commission_amount * 100),
                account=wallet.worker.phone,
                comment=f"taxi:{taxi.id}"
            )

            if transfer_response.get("status") == "OK":
                transfer_status = "success"

            else:
                transfer_status = "failed"

        except Exception as e:

            transfer_response = {
                "error": str(e)
            }

            transfer_status = "failed"

        NambaTransfer.objects.create(
            wallet_transaction=transaction_obj,
            amount=commission_amount,
            status=transfer_status,
            raw_response=transfer_response
        )

    @staticmethod
    @transaction.atomic
    def process_delivery_commission(delivery):

        courier = delivery.courier

        wallet = WorkerWallet.objects.select_for_update().get(
            worker=courier
        )

        commission_rule = (
            DeliveryCommission.objects.filter(
                type_delivery=delivery.type_delivery,
                payment_method=delivery.payment_method,
                is_active=True
            ).first()
        )

        if not commission_rule:
            commission_rule = (
                DeliveryCommission.objects.filter(
                    type_delivery=delivery.type_delivery,
                    payment_method__isnull=True,
                    is_active=True
                ).first()
            )

        if not commission_rule:
            return

        order_amount = Decimal(str(delivery.price))

        commission_amount = (
            order_amount *
            commission_rule.commission_percent
        ) / Decimal("100")

        if commission_amount < commission_rule.min_commission:
            commission_amount = commission_rule.min_commission

        if (
            commission_rule.max_commission and
            commission_amount > commission_rule.max_commission
        ):
            commission_amount = commission_rule.max_commission

        commission_amount = commission_amount.quantize(
            Decimal("0.01")
        )

        transaction_obj = WalletTransaction.objects.create(
            wallet=wallet,
            delivery=delivery,
            transaction_type=TransactionType.COMMISSION,
            status=TransactionStatus.COMPLETED,
            amount=commission_amount,
            sign=-1,
            comment=f"Delivery commission #{delivery.id}"
        )

        transfer_response = None
        transfer_status = "failed"

        try:

            transfer_response = NambaPayService.transfer_money(
                amount=int(commission_amount * 100),
                account=wallet.worker.phone,
                comment=f"delivery:{delivery.id}"
            )

            if transfer_response.get("status") == "OK":
                transfer_status = "success"

            else:
                transfer_status = "failed"

        except Exception as e:

            transfer_response = {
                "error": str(e)
            }

            transfer_status = "failed"

        NambaTransfer.objects.create(
            wallet_transaction=transaction_obj,
            amount=commission_amount,
            status=transfer_status,
            raw_response=transfer_response
        )