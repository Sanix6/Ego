from datetime import timedelta
from django.utils import timezone
from channels.layers import get_channel_layer
from apps.delivery.models import DeliveryOffer
from asgiref.sync import async_to_sync
from assets.helpers.loggers import write_log
from django.db import transaction
from apps.users.models import WorkerStatus
from apps.delivery.services import find_nearest_couriers
from apps.delivery.models import Delivery
from .helpers import courier_has_active_in_work_slot

OFFER_TIMEOUT_SECONDS = 20

def dispatch_wave(delivery, limit):
    write_log(f"DISPATCH START delivery={delivery.id} limit={limit}")

    nearest = find_nearest_couriers(
        lat=float(delivery.pickup_lat),
        lon=float(delivery.pickup_lon),
        limit=limit * 3,
    )

    write_log(f"NEAREST FOUND: {[(c.id, d) for d, c in nearest]}")

    sent_offers = []

    for distance, courier in nearest:
        write_log(f"CHECK COURIER id={courier.id} distance={distance}")

        if courier_has_active_in_work_slot(courier):
            write_log(f"SKIP courier={courier.id} (active in_work slot)")
            continue

        if has_offer_been_sent(delivery, courier):
            write_log(f"SKIP courier={courier.id} (already has offer)")
            continue

        offer = send_offer_to_courier(delivery, courier)
        write_log(f"OFFER SENT id={offer.id} courier={courier.id}")

        sent_offers.append(offer)

        if len(sent_offers) >= limit:
            break

    write_log(f"TOTAL SENT: {len(sent_offers)}")
    return sent_offers


def create_delivery_offer(delivery, courier):
    return DeliveryOffer.objects.create(
        delivery=delivery,
        courier=courier,
        status="pending",
        expires_at=timezone.now() + timedelta(seconds=OFFER_TIMEOUT_SECONDS),
    )


def send_delivery_offer_event(courier, delivery, offer):

    channel_layer = get_channel_layer()

    write_log(
        f"SEND OFFER -> courier={courier.id}, delivery={delivery.id}, offer={offer.id}"
    )

    async_to_sync(channel_layer.group_send)(
        f"user_{courier.id}",
        {
            "type": "new_offer",
            "offer_kind": "courier",
            "offer_id": offer.id,
            "delivery_id": delivery.id,
            "expires_at": offer.expires_at.isoformat(),
        }
    )

def send_offer_to_courier(delivery, courier):
    from .tasks import check_delivery_offer_timeout
    offer = create_delivery_offer(delivery, courier)

    transaction.on_commit(
        lambda: send_delivery_offer_event(courier, delivery, offer)
    )

    transaction.on_commit(
        lambda: check_delivery_offer_timeout.apply_async(
            args=[offer.id],
            countdown=OFFER_TIMEOUT_SECONDS
        )
    )

    return offer

def has_offer_been_sent(delivery, courier):
    return DeliveryOffer.objects.filter(
        delivery=delivery,
        courier=courier,
    ).exists()

def dispatch_next_courier(delivery):
    if delivery.courier_id:
        return None

    if not delivery.pickup_lat or not delivery.pickup_lon:
        return None

    nearest = find_nearest_couriers(
        lat=float(delivery.pickup_lat),
        lon=float(delivery.pickup_lon),
        limit=10,
    )

    for _, courier in nearest:
        if courier_has_active_in_work_slot(courier):
            continue

        if has_offer_been_sent(delivery, courier):
            continue

        offer = send_offer_to_courier(delivery, courier)
        return offer

    return None


def get_active_offer_for_courier(delivery, courier):
    return DeliveryOffer.objects.filter(
        delivery=delivery,
        courier=courier,
        status="pending",
        expires_at__gt=timezone.now(),
    ).first()


def accept_delivery_offer(offer, courier):
    with transaction.atomic():
        offer = (
            DeliveryOffer.objects
            .select_for_update()
            .select_related("delivery", "courier")
            .get(id=offer.id)
        )
        delivery = (
            Delivery.objects
            .select_for_update()
            .get(id=offer.delivery_id)
        )

        if offer.courier_id != courier.id:
            return False, "Заказ не принадлежит этому курьеру."

        if offer.status != "pending":
            return False, "Заказ уже недоступен."

        now = timezone.now()

        if offer.expires_at and offer.expires_at <= now:
            offer.status = "expired"
            offer.responded_at = now
            offer.save(update_fields=["status", "responded_at"])
            return False, "Время оффера истекло."

        if delivery.courier_id or delivery.delivery_status != "searching_courier":
            offer.status = "expired"
            offer.responded_at = now
            offer.save(update_fields=["status", "responded_at"])
            return False, "Заказ уже занят."

        delivery.courier = courier
        delivery.delivery_status = "courier_assigned"
        delivery.save(update_fields=["courier", "delivery_status"])

        offer.status = "accepted"
        offer.responded_at = now
        offer.save(update_fields=["status", "responded_at"])

        worker_status, _ = WorkerStatus.objects.get_or_create(user=courier)
        worker_status.is_busy = True
        worker_status.is_online = True
        worker_status.save(update_fields=["is_busy", "is_online", "last_seen"])

        DeliveryOffer.objects.filter(
            delivery=delivery,
            status="pending",
        ).exclude(id=offer.id).update(
            status="expired",
            responded_at=now,
        )

    return True, "Заказ принят."


def reject_delivery_offer(offer, courier):
    with transaction.atomic():
        offer = DeliveryOffer.objects.select_for_update().select_related("delivery").get(id=offer.id)

        if offer.courier_id != courier.id:
            return False, "Оффер не принадлежит этому курьеру."

        if offer.status != "pending":
            return False, "Оффер уже недоступен."

        offer.status = "rejected"
        offer.is_busy = False
        offer.responded_at = timezone.now()
        offer.save(update_fields=["status", "responded_at"])

        delivery = offer.delivery

    return True, delivery.id


def expire_delivery_offer(offer):
    with transaction.atomic():
        offer = DeliveryOffer.objects.select_for_update().get(id=offer.id)

        if offer.status != "pending":
            return False

        offer.status = "expired"
        offer.responded_at = timezone.now()
        offer.save(update_fields=["status", "responded_at"])

    return True



def is_delivery_searching(delivery_id):
    delivery = Delivery.objects.filter(id=delivery_id).first()
    if not delivery:
        return False
    return delivery.delivery_status == "searching_courier" and delivery.courier_id is None