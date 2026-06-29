from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from apps.users.models import User
from .choices import *
from django.db.models import Sum, F, DecimalField, ExpressionWrapper, Q
from decimal import Decimal
from django.db.models import Sum, Q
from django.utils import timezone

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
        if self.worker.user_type not in [
            WorkerType.DRIVER,
            WorkerType.COURIER
        ]:
            raise ValidationError(
                "Кошелек можно создать только для курьера или таксиста."
            )

    def __str__(self):
        return f"Кошелек: {self.worker.phone}"

    @property
    def balance(self):

        total = self.transactions.filter(
            status=TransactionStatus.COMPLETED
        ).exclude(
            transaction_type=TransactionType.ORDER_EARNING_CASH
        ).aggregate(
            total=Sum(F("amount") * F("sign"))
        )["total"]

        return total or Decimal("0.00")

    @property
    def total_earnings(self):
        """
        Общий заработок
        """

        total = self.transactions.filter(
            status=TransactionStatus.COMPLETED,
            transaction_type__in=[
                TransactionType.ORDER_EARNING_ONLINE,
                TransactionType.ORDER_EARNING_CASH,
            ]
        ).aggregate(
            total=Sum("amount")
        )["total"]

        return total or Decimal("0.00")

    @property
    def online_earnings(self):
        total = self.transactions.filter(
            status=TransactionStatus.COMPLETED,
            transaction_type=TransactionType.ORDER_EARNING_ONLINE,
        ).aggregate(
            total=Sum("amount")
        )["total"]

        return total or Decimal("0.00")

    @property
    def cash_earnings(self):
        total = self.transactions.filter(
            status=TransactionStatus.COMPLETED,
            transaction_type=TransactionType.ORDER_EARNING_CASH,
        ).aggregate(
            total=Sum("amount")
        )["total"]

        return total or Decimal("0.00")

    @property
    def total_bonuses(self):
        total = self.transactions.filter(
            status=TransactionStatus.COMPLETED,
            transaction_type=TransactionType.BONUS,
        ).aggregate(
            total=Sum("amount")
        )["total"]

        return total or Decimal("0.00")

    @property
    def total_withdrawals(self):
        total = self.transactions.filter(
            status=TransactionStatus.COMPLETED,
            sign=-1,
        ).aggregate(
            total=Sum("amount")
        )["total"]

        return total or Decimal("0.00")

    class Meta:
        verbose_name = "Кошелек работника"
        verbose_name_plural = "Кошельки работников"

        indexes = [
            models.Index(fields=["worker"]),
        ]

class WalletTransaction(models.Model):
    wallet = models.ForeignKey(WorkerWallet,on_delete=models.CASCADE,related_name="transactions")
    payment = models.ForeignKey(
        "payments.Payment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="wallet_transactions"
    )
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

    class Meta:
        verbose_name = "Транзакция кошелька"
        verbose_name_plural = "Транзакции кошельков"


class MerchantPaymentAccount(models.Model):
    title = models.CharField(max_length=255)
    provider = models.CharField(max_length=50, default="online")
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
        "WorkerWallet",
        on_delete=models.CASCADE,
        related_name="withdrawal_requests"
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    card_number = models.CharField(max_length=32)

    card_holder = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    commission_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00")
    )

    commission_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    final_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    status = models.CharField(
        max_length=16,
        choices=WithdrawalStatus.choices,
        default=WithdrawalStatus.PENDING
    )

    note = models.TextField(
        blank=True,
        null=True
    )

    processed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

        withdrawal_transaction = WalletTransaction.objects.filter(
            withdrawal_request=self,
            transaction_type=TransactionType.WITHDRAWAL
        ).first()

        if self.status == WithdrawalStatus.APPROVED:

            if not withdrawal_transaction:

                WalletTransaction.objects.create(
                    wallet=self.wallet,
                    withdrawal_request=self,
                    transaction_type=TransactionType.WITHDRAWAL,
                    status=TransactionStatus.COMPLETED,
                    amount=self.amount,
                    sign=-1,
                    comment=f"withdraw:{self.id}",
                )
        else:

            if withdrawal_transaction:
                withdrawal_transaction.delete()

    class Meta:
        verbose_name = "Заявка на вывод средств"
        verbose_name_plural = "Заявки на вывод средств"
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
        default=PaymentMethod.ONLINE
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


class BonusRule(models.Model):
    title = models.CharField(max_length=255)

    bonus_type = models.CharField(
        max_length=32,
        choices=BonusType.choices
    )

    is_active = models.BooleanField(default=True)

    required_orders = models.PositiveIntegerField(default=0)
    required_online_hours = models.PositiveIntegerField(default=0)
    required_reviews_count = models.PositiveIntegerField(
        default=0
    )

    required_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True
    )

    reward_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    reward_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Правило бонуса"
        verbose_name_plural = "Правила бонусов"

    def __str__(self):
        return self.title


class BonusMission(models.Model):
    title = models.CharField(max_length=255)

    description = models.TextField(blank=True)

    required_orders = models.PositiveIntegerField(default=0)

    reward_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Бонусная миссия"
        verbose_name_plural = "Бонусные миссии"


class WorkerMissionProgress(models.Model):
    worker = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="mission_progress"
    )

    mission = models.ForeignKey(
        BonusMission,
        on_delete=models.CASCADE,
        related_name="workers"
    )

    completed_orders = models.PositiveIntegerField(default=0)

    is_completed = models.BooleanField(default=False)

    rewarded = models.BooleanField(default=False)

    rewarded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Бонусные прогрессы"
        verbose_name_plural = "Бонусные прогрессы"
        unique_together = ("worker", "mission")

    


class BonusReward(models.Model):
    worker = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bonus_rewards"
    )

    bonus_type = models.CharField(
        max_length=32,
        choices=BonusType.choices
    )

    rule = models.ForeignKey(
        BonusRule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    mission = models.ForeignKey(
        BonusMission,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    description = models.CharField(max_length=255)

    expires_at = models.DateTimeField(null=True, blank=True)

    is_canceled = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Бонусные награды"
        verbose_name_plural = "Бонусные награды"
        ordering = ["-created_at"]

    