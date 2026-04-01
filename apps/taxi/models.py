from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from assets.helpers.choices import TAXI_STATUSES, CAR_CLASSES, PAYMENT_METHODS, PAYMENT_STATUSES

class TaxiRide(models.Model):
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="taxi_rides",
        limit_choices_to={"user_type": "client"},
        verbose_name="Клиент",
    )

    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="driver_rides",
        limit_choices_to={"user_type": "driver"},
        verbose_name="Водитель",
        null=True,
        blank=True,
    )

    point_a = models.CharField("Адрес откуда", max_length=255, null=True, blank=True)
    point_b = models.CharField("Адрес куда", max_length=255, null=True, blank=True)

    pickup_lat = models.FloatField("Широта точки А", null=True, blank=True)
    pickup_lon = models.FloatField("Долгота точки А", null=True, blank=True)
    dropoff_lat = models.FloatField("Широта точки Б", null=True, blank=True)
    dropoff_lon = models.FloatField("Долгота точки Б", null=True, blank=True)

    status = models.CharField("Статус", max_length=20, choices=TAXI_STATUSES, default="searching_driver")
    car_class = models.CharField("Класс", max_length=20, choices=CAR_CLASSES, default="econom")

    passengers = models.PositiveSmallIntegerField("Пассажиры", default=1)
    client_comment = models.TextField("Комментарий клиента", blank=True, default="")

    distance_km = models.DecimalField("Дистанция (км)", max_digits=6, decimal_places=2, null=True, blank=True)
    duration_min = models.PositiveIntegerField("Время (мин)", null=True, blank=True)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    surge_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)

    #тарификация
    base_fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    per_km_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    per_min_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    included_km = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    included_min = models.PositiveIntegerField(default=0)
    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    driver_payout = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    payment_method = models.CharField("Оплата", max_length=20, choices=PAYMENT_METHODS, default="cash")
    payment_status = models.CharField("Статус оплаты", max_length=20, choices=PAYMENT_STATUSES, default="unpaid")

    requested_at = models.DateTimeField("Создано", auto_now_add=True)
    assigned_at = models.DateTimeField("Назначен", null=True, blank=True)
    accepted_at = models.DateTimeField("Принят", null=True, blank=True)
    arrived_at = models.DateTimeField("Прибыл", null=True, blank=True)
    started_at = models.DateTimeField("Начал поездку", null=True, blank=True)
    completed_at = models.DateTimeField("Завершил", null=True, blank=True)
    canceled_at = models.DateTimeField("Отменено", null=True, blank=True)
    order_code = models.CharField(max_length=20, db_index=True)
    canceled_by = models.CharField(
        max_length=20,
        choices=(
            ("client", "Клиент"),
            ("driver", "Водитель"),
            ("system", "Система"),
            ("operator", "Оператор"),
        ),
        null=True,
        blank=True,
    )
    cancel_reason = models.TextField(blank=True, default="")

    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.driver and getattr(self.driver, "user_type", None) != "driver":
            raise ValidationError({"driver": "Назначить можно только пользователя с ролью driver."})
        if getattr(self.client, "user_type", None) != "client":
            raise ValidationError({"client": "Клиент должен иметь роль client."})

    def __str__(self):
        return f"TaxiRide #{self.id} client={self.client_id} driver={self.driver_id}"

    class Meta:
        verbose_name = "Поездка"
        verbose_name_plural = "Поездки"


class TaxiOffer(models.Model):
    OFFER_STATUSES = (
        ("pending", "Ожидает ответа"),
        ("accepted", "Принят"),
        ("rejected", "Отклонен"),
        ("expired", "Истек"),
    )

    ride = models.ForeignKey(
        "TaxiRide",
        on_delete=models.CASCADE,
        related_name="offers",
        verbose_name="Поездка",
    )

    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="taxi_offers",
        limit_choices_to={"user_type": "driver"},
        verbose_name="Водитель",
    )

    status = models.CharField("Статус оффера", max_length=20, choices=OFFER_STATUSES, default="pending")
    sent_at = models.DateTimeField("Отправлен", auto_now_add=True)
    responded_at = models.DateTimeField("Ответил в", null=True, blank=True)
    expires_at = models.DateTimeField("Истекает в")

    class Meta:
        verbose_name = "Оффер водителю"
        verbose_name_plural = "Офферы водителям"
        indexes = [
            models.Index(fields=["ride", "driver"]),
            models.Index(fields=["status", "expires_at"]),
        ]

    def __str__(self):
        return f"TaxiOffer #{self.id} ride={self.ride_id} driver={self.driver_id}"