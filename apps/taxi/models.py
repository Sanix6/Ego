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

    point_a = models.ForeignKey("main.Address", on_delete=models.PROTECT, null=True, blank=True, related_name="taxi_from")
    point_b = models.ForeignKey("main.Address", on_delete=models.PROTECT, null=True, blank=True, related_name="taxi_to")

    status = models.CharField("Статус", max_length=20, choices=TAXI_STATUSES, default="pending")
    car_class = models.CharField("Класс", max_length=20, choices=CAR_CLASSES, default="econom")

    passengers = models.PositiveSmallIntegerField("Пассажиры", default=1)

    client_comment = models.TextField("Комментарий клиента", blank=True, default="")

    distance_km = models.DecimalField("Дистанция (км)", max_digits=6, decimal_places=2, null=True, blank=True)
    duration_min = models.PositiveIntegerField("Время (мин)", null=True, blank=True)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2, null=True, blank=True)

    payment_method = models.CharField("Оплата", max_length=20, choices=PAYMENT_METHODS, default="cash")
    payment_status = models.CharField("Статус оплаты", max_length=20, choices=PAYMENT_STATUSES, default="unpaid")

    # тайминги поездки
    requested_at = models.DateTimeField("Создано", auto_now_add=True)
    assigned_at = models.DateTimeField("Назначен", null=True, blank=True)
    accepted_at = models.DateTimeField("Принят", null=True, blank=True)
    arrived_at = models.DateTimeField("Прибыл", null=True, blank=True)
    started_at = models.DateTimeField("Начал поездку", null=True, blank=True)
    completed_at = models.DateTimeField("Завершил", null=True, blank=True)
    canceled_at = models.DateTimeField("Отменено", null=True, blank=True)

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
