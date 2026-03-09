from django.db import models
from django.core.exceptions import ValidationError
from assets.helpers.choices import DELIVERY_STATUSES, DELIVERY_TYPES, SLOT_STATUSES
from apps.main.models import Address



class CourierSlot(models.Model):
    start_at = models.DateTimeField("Начало слота")
    end_at = models.DateTimeField("Конец слота")

    status = models.CharField(
        "Статус слота",
        max_length=20,
        choices=SLOT_STATUSES,
        default="planned",
        db_index=True,
    )

    reserved_for = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reserved_slots",
        limit_choices_to={"user_type": "courier"},
        verbose_name="Зарезервирован для курьера",
    )

    booked_by = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="booked_slots",
        limit_choices_to={"user_type": "courier"},
        verbose_name="Занят курьером",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Слот курьера"
        verbose_name_plural = "Слоты курьеров"
        ordering = ["-start_at"]
        indexes = [
            models.Index(fields=["start_at", "end_at"]),
            models.Index(fields=["reserved_for", "start_at"]),
            models.Index(fields=["booked_by", "start_at"]),
        ]

    def clean(self):
        super().clean()

        if self.start_at and self.end_at and self.end_at <= self.start_at:
            raise ValidationError({"end_at": "Время окончания должно быть позже времени начала."})

        if self.reserved_for and self.booked_by and self.booked_by_id != self.reserved_for_id:
            raise ValidationError({"booked_by": "Этот слот зарезервирован для другого курьера."})

        if self.reserved_for and self.status == "in_work" and not self.booked_by:
            raise ValidationError({"status": "Нельзя поставить 'в работе' если слот еще не занят курьером."})


        if self.start_at and self.end_at:
            qs = CourierSlot.objects.filter(
                start_at__lt=self.end_at,
                end_at__gt=self.start_at,
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)

            if qs.exists():
                raise ValidationError("Слот пересекается по времени с существующим слотом.")

        if self.status in ("no_show", "closed_early") and not self.booked_by:
            raise ValidationError({"status": "Этот статус возможен только для занятого слота."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def is_free(self) -> bool:
        return self.booked_by_id is None

    @property
    def is_personal(self) -> bool:
        return self.reserved_for_id is not None

    def can_be_booked_by(self, courier) -> bool:
        if not courier:
            return False
        if self.booked_by_id is not None:
            return False
        if self.reserved_for_id and self.reserved_for_id != courier.id:
            return False
        return True

    def __str__(self):
        return f"Slot #{self.id} {self.start_at:%d.%m %H:%M}-{self.end_at:%H:%M}"

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

    point_a = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        related_name="deliveries_from",
        null=True,
        blank=True,
    )
    point_b = models.ForeignKey(
        Address,
        on_delete=models.PROTECT,
        related_name="deliveries_to",
        null=True,
        blank=True,
    )
    slot = models.ForeignKey(
        CourierSlot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="deliveries",
        verbose_name="Слот",
    )


    delivery_status = models.CharField("Статус доставки", max_length=50, choices=DELIVERY_STATUSES, default="pending")
    type_delivery = models.CharField("Тип доставки", max_length=50, choices=DELIVERY_TYPES, null=True, blank=True)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2, null=True, blank=True)
    pickup_at = models.DateTimeField("Время забора", null=True, blank=True)
    delivered_at = models.DateTimeField("Время доставки", null=True, blank=True)
    time_left = models.IntegerField("Осталось времени", default=0)
    deadline_at = models.DateTimeField("Доставить до", null=True, blank=True)
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
