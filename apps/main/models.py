from django.db import models
from django.utils import timezone
from datetime import timedelta
from apps.users.models import *
from assets.helpers.choices import *
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class DarkStore(models.Model):
    name = models.CharField("Название", max_length=100)
    address = models.CharField("Адрес", max_length=255)
    lat = models.DecimalField("Широта", max_digits=9, decimal_places=6)
    lon = models.DecimalField("Долгота", max_digits=9, decimal_places=6)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    def __str__(self):
        return f"Даркстор: {self.name}"

    class Meta:
        verbose_name = "Даркстор"
        verbose_name_plural = "Дарксторы"


class Tariff(models.Model):
    CAR_CLASSES = (
        ("econom", "Эконом"),
        ("comfort", "Комфорт"),
        ("comfort_plus", "Комфорт+"),
        ("business", "Бизнес"),
    )

    city = models.CharField("Город", max_length=100)
    car_class = models.CharField("Класс автомобиля", max_length=20, choices=CAR_CLASSES)

    base_fare = models.DecimalField("Базовая плата", max_digits=10, decimal_places=2)
    included_km = models.DecimalField("Включенные километры", max_digits=5, decimal_places=2, default=0)
    included_min = models.PositiveIntegerField("Включенные минуты", default=0)

    per_km_rate = models.DecimalField("Тариф за километр", max_digits=10, decimal_places=2)
    per_min_rate = models.DecimalField("Тариф за минуту", max_digits=10, decimal_places=2)

    commission_percent = models.DecimalField("Процент комиссии", max_digits=5, decimal_places=2, default=5.00)

    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы"
        unique_together = ("city", "car_class")




class DeliveryTariff(models.Model):
    type_delivery = models.CharField("Тип доставки", max_length=20, choices=TRANSPORT_TYPES)

    base_fare = models.DecimalField("Базовая плата", max_digits=10, decimal_places=2)
    included_km = models.DecimalField("Включенные километры", max_digits=5, decimal_places=2, default=0)
    included_min = models.PositiveIntegerField("Включенные минуты", default=0)

    per_km_rate = models.DecimalField("Тариф за километр", max_digits=10, decimal_places=2)
    per_min_rate = models.DecimalField("Тариф за минуту", max_digits=10, decimal_places=2)

    commission_percent = models.DecimalField("Процент комиссии", max_digits=5, decimal_places=2, default=5.00)

    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "Тариф доставки"
        verbose_name_plural = "Тарифы доставки"


class Review(models.Model):
    REVIEW_TARGETS = (
        ("delivery", "Delivery"),
        ("taxi", "Taxi"),
    )

    from_user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="reviews_given"
    )
    to_user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="reviews_received"
    )

    delivery = models.ForeignKey(
        "delivery.Delivery",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reviews"
    )
    ride = models.ForeignKey(
        "taxi.TaxiRide",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reviews"
    )

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(delivery__isnull=False, ride__isnull=True) |
                    models.Q(delivery__isnull=True, ride__isnull=False)
                ),
                name="review_has_exactly_one_target"
            ),
            models.UniqueConstraint(
                fields=["from_user", "to_user", "delivery"],
                condition=models.Q(delivery__isnull=False),
                name="unique_delivery_review_pair"
            ),
            models.UniqueConstraint(
                fields=["from_user", "to_user", "ride"],
                condition=models.Q(ride__isnull=False),
                name="unique_ride_review_pair"
            ),
        ]

    def __str__(self):
        target = f"delivery={self.delivery_id}" if self.delivery_id else f"ride={self.ride_id}"
        return f"{self.from_user_id} -> {self.to_user_id} | {self.rating} | {target}"
