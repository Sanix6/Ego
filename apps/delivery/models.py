from django.db import models
from django.core.exceptions import ValidationError
from assets.helpers.choices import *

class CourierSlot(models.Model):
    start_at = models.DateTimeField("Начало слота")
    end_at = models.DateTimeField("Конец слота")

    type_slot = models.CharField(
        "Тип слота",
        max_length=20,
        choices=TRANSPORT_TYPES,
        default="standard",
    )

    status = models.CharField(
        "Статус слота",
        max_length=20,
        choices=SLOT_STATUSES,
        default="planned",
        db_index=True,
    )

    courier = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="slots",
        limit_choices_to={"user_type": "courier"},
        verbose_name="Курьер",
    )

    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        verbose_name = "Таблица слотов"
        verbose_name_plural = "Таблица слотов"
        ordering = ["-start_at"]
        indexes = [
            models.Index(fields=["start_at", "end_at"]),
            models.Index(fields=["courier", "start_at"]),
        ]

    def clean(self):
        super().clean()

        if self.start_at and self.end_at and self.end_at <= self.start_at:
            raise ValidationError({
                "end_at": "Время окончания должно быть позже времени начала."
            })

        if self.start_at and self.end_at:
            qs = CourierSlot.objects.filter(
                start_at__lt=self.end_at,
                end_at__gt=self.start_at,
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)

            if self.courier:
                qs = qs.filter(courier=self.courier)
                if qs.exists():
                    raise ValidationError("У курьера уже есть пересекающийся слот на это время.")

    @property
    def is_free(self):
        return self.courier_id is None

    @property
    def is_personal(self):
        return self.courier_id is not None

    def __str__(self):
        return f"Слот #{self.id} {self.start_at:%d.%m %H:%M}-{self.end_at:%H:%M}"


class Delivery(models.Model):
    courier = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="deliveries",
        limit_choices_to={"user_type": "courier"},
        verbose_name="Курьер",
        null=True,
        blank=True,
    )
    client = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        related_name="client_deliveries",
        limit_choices_to={"user_type": "client"},
        verbose_name="Клиент",
        null=True,
        blank=True,
    )

    point_a = models.CharField("Адрес откуда", max_length=255)
    point_b = models.CharField("Адрес куда", max_length=255)
    pickup_lat = models.FloatField("Широта точки забора", null=True, blank=True)
    pickup_lon = models.FloatField("Долгота точки забора", null=True, blank=True)

    dropoff_lat = models.FloatField("Широта точки доставки", null=True, blank=True)
    dropoff_lon = models.FloatField("Долгота точки доставки", null=True, blank=True)
    slot = models.ForeignKey(
        CourierSlot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deliveries",
        verbose_name="Слот",
    )

    delivery_status = models.CharField(
        "Статус доставки",
        max_length=50,
        choices=DELIVERY_STATUSES,
        default="pending"
    )
    type_delivery = models.CharField(
        "Тип доставки",
        max_length=50,
        choices=DELIVERY_TYPES,
        default="standard"
    )

    price = models.DecimalField("Цена", max_digits=10, decimal_places=2, null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    free_waiting_started_at = models.DateTimeField(null=True, blank=True)
    free_waiting_minutes = models.PositiveIntegerField(default=10)
    paid_waiting_started_at = models.DateTimeField(null=True, blank=True)
    pickup_at = models.DateTimeField("Время забора", null=True, blank=True)
    delivered_at = models.DateTimeField("Время доставки", null=True, blank=True)
    time_left = models.IntegerField("Осталось времени", default=0)
    deadline_at = models.DateTimeField("Доставить до", null=True, blank=True)
    door_to_door = models.BooleanField("Доставка от двери до двери", default=False)

    sender_name = models.CharField("Имя отправителя", max_length=100, blank=True)
    sender_phone = models.CharField("Телефон отправителя", max_length=20, blank=True)

    recipient_name = models.CharField("Имя получателя", max_length=100, blank=True)
    recipient_phone = models.CharField("Телефон получателя", max_length=20, blank=True)

    pickup_entrance = models.CharField("Подъезд откуда", max_length=20, blank=True)
    pickup_floor = models.CharField("Этаж откуда", max_length=20, blank=True)
    pickup_apartment = models.CharField("Квартира/офис откуда", max_length=50, blank=True)
    pickup_intercom = models.CharField("Домофон откуда", max_length=50, blank=True)
    pickup_comment = models.TextField("Комментарий откуда", blank=True, default="")

    dropoff_entrance = models.CharField("Подъезд куда", max_length=20, blank=True)
    dropoff_floor = models.CharField("Этаж куда", max_length=20, blank=True)
    dropoff_apartment = models.CharField("Квартира/офис куда", max_length=50, blank=True)
    dropoff_intercom = models.CharField("Домофон куда", max_length=50, blank=True)
    dropoff_comment = models.TextField("Комментарий куда", blank=True, default="")

    client_comment = models.TextField("Комментарий клиента", blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.courier and getattr(self.courier, "user_type", None) != "courier":
            raise ValidationError({"courier": "Назначить можно только пользователя с ролью courier."})

    def __str__(self):
        return f"Доставка #{self.id} Курьер={self.courier_id}"

    class Meta:
        verbose_name = "Доставка"
        verbose_name_plural = "Доставки"


class DeliveryOffer(models.Model):
    delivery = models.ForeignKey(
        "Delivery",
        on_delete=models.CASCADE,
        related_name="offers",
        verbose_name="Доставка",
    )

    courier = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="delivery_offers",
        limit_choices_to={"user_type": "courier"},
        verbose_name="Курьер",
    )

    status = models.CharField(
        "Статус оффера",
        max_length=20,
        choices=OFFER_STATUSES,
        default="pending",
        db_index=True,
    )

    sent_at = models.DateTimeField("Отправлен", auto_now_add=True)
    responded_at = models.DateTimeField("Ответил в", null=True, blank=True)
    expires_at = models.DateTimeField("Истекает в")

    class Meta:
        verbose_name = "Диспетчерская"
        verbose_name_plural = "Диспетчерская"
        indexes = [
            models.Index(fields=["delivery", "courier"]),
            models.Index(fields=["status", "expires_at"]),
        ]

    def __str__(self):
        return f"Offer #{self.id} delivery={self.delivery_id} courier={self.courier_id}"