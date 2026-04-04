from django.db import models
from django.conf import settings
from apps.users.models import User
from .choices import *

class PushDevice(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="push_devices",
        verbose_name="Пользователь",
    )
    onesignal_id = models.CharField("OneSignal ID", max_length=255, unique=True)
    external_user_id = models.CharField(
        "OneSignal External User ID",
        max_length=255,
        blank=True,
        null=True,
    )
    platform = models.CharField("Платформа", max_length=20, choices=PLATFORM_CHOICES)
    is_active = models.BooleanField("Активно", default=True)

    last_seen_at = models.DateTimeField("Последняя активность", auto_now=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Push устройство"
        verbose_name_plural = "Push устройства"
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["platform", "is_active"]),
        ]

    def __str__(self):
        return f"{self.user_id} | {self.platform} | {self.onesignal_id}"


class PushNotification(models.Model):
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="push_notifications",
        verbose_name="Получатель",
    )

    event_type = models.CharField("Тип события", max_length=50, choices=EVENT_TYPES)
    event_key = models.CharField("Уникальный ключ события", max_length=255, unique=True)

    title = models.CharField("Заголовок", max_length=255)
    message = models.TextField("Текст")

    payload = models.JSONField("Payload", default=dict, blank=True)

    slot = models.ForeignKey(
        "delivery.CourierSlot",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="push_notifications",
        verbose_name="Слот",
    )
    delivery = models.ForeignKey(
        "delivery.Delivery",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="push_notifications",
        verbose_name="Доставка",
    )
    delivery_offer = models.ForeignKey(
        "delivery.DeliveryOffer",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="push_notifications",
        verbose_name="Оффер доставки",
    )
    ride = models.ForeignKey(
        "taxi.TaxiRide",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="push_notifications",
        verbose_name="Поездка",
    )
    taxi_offer = models.ForeignKey(
        "taxi.TaxiOffer",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="push_notifications",
        verbose_name="Оффер такси",
    )

    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default="pending")

    scheduled_at = models.DateTimeField("Запланировано на", null=True, blank=True)
    sent_at = models.DateTimeField("Отправлено в", null=True, blank=True)
    failed_at = models.DateTimeField("Ошибка в", null=True, blank=True)

    provider_message_id = models.CharField("ID сообщения у провайдера", max_length=255, blank=True, null=True)
    error_message = models.TextField("Текст ошибки", blank=True, default="")

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    class Meta:
        verbose_name = "Push уведомление"
        verbose_name_plural = "Push уведомления"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "status"]),
            models.Index(fields=["event_type", "status"]),
            models.Index(fields=["scheduled_at", "status"]),
            models.Index(fields=["slot", "event_type"]),
            models.Index(fields=["delivery", "event_type"]),
            models.Index(fields=["ride", "event_type"]),
        ]

    def __str__(self):
        return f"{self.recipient_id} | {self.event_type} | {self.status}"