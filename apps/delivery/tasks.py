from celery import shared_task
from apps.delivery.models import Delivery
from .dispatch import *

from celery import shared_task
from apps.notify.services import send_delivery_offer_push

#tasks.py - содержит определения задач Celery для асинхронного выполнения, таких как проверка таймаута оффера и повторная отправка офферов при неудаче первой волны. Также может содержать задачи для отправки пуш-уведомлений курьерам.
@shared_task
def check_delivery_offer_timeout(offer_id):
    offer = DeliveryOffer.objects.select_related("delivery").filter(id=offer_id).first()
    if not offer:
        return

    if offer.status != "pending":
        return

    if offer.expires_at > timezone.now():
        return

    expire_delivery_offer(offer)


@shared_task
def dispatch_delivery(delivery_id, wave_index=0):
    from services.dispatch_config import DISPATCH_WAVES

    if wave_index >= len(DISPATCH_WAVES):
        return

    config = DISPATCH_WAVES[wave_index]

    with transaction.atomic():
        delivery = Delivery.objects.select_for_update().filter(id=delivery_id).first()

        if not delivery:
            return

        if delivery.delivery_status != "searching_courier":
            return

        offers = dispatch_wave(
            delivery=delivery,
            limit=config["limit"]
        )

        if not offers:
            dispatch_delivery.delay(delivery.id, wave_index + 1)
            return

        dispatch_delivery.apply_async(
            args=[delivery.id, wave_index + 1],
            countdown=config["timeout"]
        )


@shared_task
def send_delivery_offer_push_task(offer_id):
    send_delivery_offer_push(offer_id)


