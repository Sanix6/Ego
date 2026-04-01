from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from apps.users.models import User
from .choices import *


class WorkerWallet(models.Model):
    worker = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="wallet"
    )
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.worker.user_type not in [WorkerType.DRIVER, WorkerType.COURIER]:
            raise ValidationError("Кошелек можно создать только для курьера или таксиста.")

    def __str__(self):
        return f"Кошелек: {self.worker.phone}"


class WalletTransaction(models.Model):
    wallet = models.ForeignKey(WorkerWallet,on_delete=models.CASCADE,related_name="transactions")
    transaction_type = models.CharField(max_length=32,choices=TransactionType.choices)
    status = models.CharField(max_length=16,choices=TransactionStatus.choices,default=TransactionStatus.COMPLETED)
    channel = models.CharField(max_length=16,choices=PaymentChannel.choices,blank=True,null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    sign = models.SmallIntegerField(default=1)
    taxi_ride = models.ForeignKey("taxi.TaxiRide",on_delete=models.SET_NULL,null=True,blank=True,related_name="wallet_transactions")
    delivery = models.ForeignKey("delivery.Delivery",on_delete=models.SET_NULL,null=True,blank=True,related_name="wallet_transactions")
    withdrawal_request = models.ForeignKey( "WithdrawalRequest",on_delete=models.SET_NULL,null=True,blank=True,related_name="transactions")
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["wallet", "status", "created_at"]),
            models.Index(fields=["wallet", "channel", "created_at"]),
            models.Index(fields=["transaction_type", "status"]),
        ]

    def clean(self):
        refs_count = sum([
            1 if self.taxi_ride_id else 0,
            1 if self.delivery_id else 0,
            1 if self.withdrawal_request_id else 0,
        ])

        if self.transaction_type == TransactionType.ORDER_EARNING:
            if refs_count != 1 or not (self.taxi_ride_id or self.delivery_id):
                raise ValidationError("Доход по заказу должен быть связан либо с TaxiRide, либо с Delivery.")

        if self.taxi_ride_id and self.delivery_id:
            raise ValidationError("Транзакция не может быть одновременно привязана и к TaxiRide, и к Delivery.")

    @property
    def signed_amount(self):
        return self.amount * self.sign

    def __str__(self):
        return f"{self.wallet.worker.phone} | {self.transaction_type} | {self.signed_amount}"


class MerchantPaymentAccount(models.Model):
    title = models.CharField(max_length=255)
    provider = models.CharField(max_length=50, default="mbank")
    phone = models.CharField(max_length=30, blank=True, null=True)
    qr_code_image = models.ImageField(upload_to="payments/qr/", blank=True, null=True)
    deeplink = models.URLField(blank=True, null=True)
    account_number = models.CharField(max_length=64, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class WithdrawalRequest(models.Model):
    wallet = models.ForeignKey(
        WorkerWallet,
        on_delete=models.CASCADE,
        related_name="withdrawal_requests"
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    commission_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    final_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    status = models.CharField(
        max_length=16,
        choices=WithdrawalStatus.choices,
        default=WithdrawalStatus.PENDING
    )

    note = models.TextField(blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Вывод #{self.id} - {self.wallet.worker.phone} - {self.amount}"


class OrderPayment(models.Model):
    taxi_ride = models.ForeignKey(
        "taxi.TaxiRide",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="payments"
    )
    delivery = models.ForeignKey(
        "delivery.Delivery",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="payments"
    )

    provider = models.CharField(
        max_length=20,
        choices=PaymentProvider.choices,
        default=PaymentProvider.MKASSA
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.MBANK
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    currency = models.CharField(max_length=10, default="KGS")

    external_payment_id = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    qr_url = models.URLField(blank=True, null=True)
    deeplink = models.TextField(blank=True, null=True)

    raw_init_response = models.JSONField(blank=True, null=True)
    raw_check_response = models.JSONField(blank=True, null=True)

    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]

    def clean(self):
        if bool(self.taxi_ride_id) == bool(self.delivery_id):
            raise ValidationError("Платеж должен относиться либо к TaxiRide, либо к Delivery.")