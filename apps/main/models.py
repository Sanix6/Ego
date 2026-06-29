from django.db import models
from django.utils import timezone
from datetime import timedelta
from apps.users.models import *
from assets.helpers.choices import *
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from shapely.geometry import Point, Polygon
from decimal import Decimal




class DarkStore(models.Model):
    name = models.CharField("Название", max_length=100)
    address = models.CharField("Адрес", max_length=255)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    def __str__(self):
        return f"Даркстор: {self.name}"

    class Meta:
        verbose_name = "Даркстор"
        verbose_name_plural = "Дарксторы"


class Tariff(models.Model):
    car_class = models.CharField("Класс автомобиля", max_length=20, choices=CAR_CLASSES)

    base_fare = models.DecimalField("Базовая плата", max_digits=10, decimal_places=2)
    included_km = models.DecimalField("Включенные километры", max_digits=5, decimal_places=2, default=0)
    included_min = models.PositiveIntegerField("Включенные минуты", default=0)

    per_km_rate = models.DecimalField("Тариф за километр", max_digits=10, decimal_places=2)
    per_min_rate = models.DecimalField("Тариф за минуту", max_digits=10, decimal_places=2)
    waiting_free_min = models.PositiveIntegerField(
        default=5,
        verbose_name="Бесплатное ожидание (мин)"
    )
    waiting_per_minute = models.DecimalField(
        "Цена ожидания за минуту",
        max_digits=10,
        decimal_places=2,
        default=0
    )

    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы"



class DeliveryTariff(models.Model):
    type_delivery = models.CharField("Тип доставки", max_length=20, choices=TRANSPORT_TYPES)

    base_fare = models.DecimalField("Базовая плата", max_digits=10, decimal_places=2)
    included_km = models.DecimalField("Включенные километры", max_digits=5, decimal_places=2, default=0)
    included_min = models.PositiveIntegerField("Включенные минуты", default=0)

    per_km_rate = models.DecimalField("Тариф за километр", max_digits=10, decimal_places=2)
    per_min_rate = models.DecimalField("Тариф за минуту", max_digits=10, decimal_places=2)

    door_to_door_price = models.DecimalField("Цена до двери", max_digits=10, decimal_places=2)
    entrance_price = models.DecimalField("Цена до подьезда", max_digits=10, decimal_places=2)
    waiting_free_min = models.PositiveIntegerField(
        default=5,
        verbose_name="Бесплатное ожидание (мин)"
    )
    waiting_per_minute = models.DecimalField(
        "Цена ожидания за минуту",
        max_digits=10,
        decimal_places=2,
        default=0
    )

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


class DeliveryZone(models.Model):
    darkstore = models.ForeignKey(
        "main.DarkStore",
        on_delete=models.CASCADE,
        related_name="zones",
        verbose_name="Даркстор"
    )
    name = models.CharField("Название зоны", max_length=100)

    polygon = models.JSONField("Координаты полигона", default=list, blank=True)

    is_active = models.BooleanField("Активна", default=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "Зона доставки"
        verbose_name_plural = "Зоны доставки"

    def __str__(self):
        return f"{self.darkstore.name} - {self.name}"

    def contains_point(self, lat, lon):
        if not self.polygon:
            return False

        coords = self.polygon

        if (
            isinstance(coords, list)
            and len(coords) > 0
            and isinstance(coords[0], list)
            and len(coords[0]) > 0
            and isinstance(coords[0][0], list)
        ):
            ring = coords[0]
        else:
            ring = coords

        try:
            ring = [(float(x), float(y)) for x, y in ring]
            polygon = Polygon(ring)

            if not polygon.is_valid or polygon.is_empty:
                return False

            point = Point(float(lon), float(lat))

            return polygon.covers(point)

        except Exception:
            return False



class TaxiCommission(models.Model):
    title = models.CharField(
        "Название",
        max_length=255
    )

    car_class = models.CharField(
        "Класс автомобиля",
        max_length=20,
        choices=CAR_CLASSES,
        db_index=True
    )

    payment_method = models.CharField(
        "Тип оплаты",
        max_length=20,
        choices=PAYMENT_METHODS,
        null=True,
        blank=True,
        help_text="Если пусто — применяется ко всем типам оплат"
    )

    commission_percent = models.DecimalField(
        "Процент комиссии",
        max_digits=5,
        decimal_places=2,
        default=Decimal("10.00")
    )

    min_commission = models.DecimalField(
        "Минимальная комиссия",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    max_commission = models.DecimalField(
        "Максимальная комиссия",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    minimum_balance = models.DecimalField(
        "Минимальный баланс для работы",
        max_digits=10,
        decimal_places=2,
        default=Decimal("300.00"),
        help_text="Если баланс ниже — водитель не сможет принимать заказы"
    )

    is_active = models.BooleanField(
        "Активен",
        default=True
    )

    created_at = models.DateTimeField(
        "Дата создания",
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        "Дата обновления",
        auto_now=True
    )

    class Meta:
        verbose_name = "Комиссия такси"
        verbose_name_plural = "Комиссии такси"

        indexes = [
            models.Index(fields=["car_class", "payment_method"]),
            models.Index(fields=["is_active"]),
        ]

        ordering = ["-id"]

    def __str__(self):
        payment = self.get_payment_method_display() if self.payment_method else "Все оплаты"

        return (
            f"{self.title} | "
            f"{self.get_car_class_display()} | "
            f"{payment} | "
            f"{self.commission_percent}%"
        )


class DeliveryCommission(models.Model):

    title = models.CharField(
        "Название",
        max_length=255
    )

    type_delivery = models.CharField(
        "Тип доставки",
        max_length=20,
        choices=DELIVERY_TYPES,
        db_index=True
    )

    payment_method = models.CharField(
        "Тип оплаты",
        max_length=20,
        choices=PAYMENT_METHODS,
        null=True,
        blank=True,
        help_text="Если пусто — применяется ко всем типам оплат"
    )

    commission_percent = models.DecimalField(
        "Процент комиссии",
        max_digits=5,
        decimal_places=2,
        default=Decimal("12.00")
    )

    min_commission = models.DecimalField(
        "Минимальная комиссия",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )

    max_commission = models.DecimalField(
        "Максимальная комиссия",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    minimum_balance = models.DecimalField(
        "Минимальный баланс для работы",
        max_digits=10,
        decimal_places=2,
        default=Decimal("300.00")
    )

    is_active = models.BooleanField(
        "Активен",
        default=True
    )

    created_at = models.DateTimeField(
        "Дата создания",
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        "Дата обновления",
        auto_now=True
    )

    class Meta:
        verbose_name = "Комиссия доставки"
        verbose_name_plural = "Комиссии доставки"

        indexes = [
            models.Index(fields=["type_delivery", "payment_method"]),
            models.Index(fields=["is_active"]),
        ]

        ordering = ["-id"]

    def __str__(self):
        payment = self.get_payment_method_display() if self.payment_method else "Все оплаты"

        return (
            f"{self.title} | "
            f"{self.get_type_delivery_display()} | "
            f"{payment} | "
            f"{self.commission_percent}%"
        )