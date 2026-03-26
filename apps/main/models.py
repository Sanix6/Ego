from django.db import models
from django.utils import timezone
from datetime import timedelta
from apps.users.models import *

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

