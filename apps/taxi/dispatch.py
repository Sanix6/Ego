from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.utils import timezone

from apps.taxi.models import TaxiOffer, TaxiRide
from apps.taxi.services import find_nearest_drivers
from apps.users.models import WorkerStatus
from assets.helpers.loggers import write_log


OFFER_TIMEOUT_SECONDS = 15
TAXI_DISPATCH_WAVES = [
    {"limit": 1, "timeout": 12},
    {"limit": 2, "timeout": 12},
    {"limit": 3, "timeout": 15},
]


def create_taxi_offer(ride, driver):
    return TaxiOffer.objects.create(
        ride=ride,
        driver=driver,
        status="pending",
        expires_at=timezone.now() + timedelta(seconds=OFFER_TIMEOUT_SECONDS),
    )


def send_taxi_offer_event(driver, ride, offer):
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"user_{driver.id}",
        {
            "type": "new_offer",
            "offer_kind": "taxi",
            "offer_id": offer.id,
            "ride_id": ride.id,
            
        }
    )


def send_offer_to_driver(ride, driver):
    offer = create_taxi_offer(ride, driver)
    send_taxi_offer_event(driver, ride, offer)
    return offer


def has_offer_been_sent(ride, driver):
    return TaxiOffer.objects.filter(
        ride=ride,
        driver=driver,
    ).exists()


def dispatch_wave(ride, limit):
    write_log(f"TAXI DISPATCH START ride={ride.id} limit={limit}")

    nearest = find_nearest_drivers(
        lat=float(ride.pickup_lat),
        lon=float(ride.pickup_lon),
        limit=limit * 3,
    )

    sent_offers = []

    for distance, driver in nearest:
        if has_offer_been_sent(ride, driver):
            continue

        offer = send_offer_to_driver(ride, driver)
        sent_offers.append(offer)

        if len(sent_offers) >= limit:
            break

    write_log(f"TAXI TOTAL SENT: {len(sent_offers)}")
    return sent_offers


def get_active_offer_for_driver(ride, driver):
    return TaxiOffer.objects.filter(
        ride=ride,
        driver=driver,
        status="pending",
        expires_at__gt=timezone.now(),
    ).first()


def accept_taxi_offer(offer, driver):
    with transaction.atomic():
        offer = TaxiOffer.objects.select_for_update().select_related("ride").get(id=offer.id)
        ride = TaxiRide.objects.select_for_update().get(id=offer.ride_id)

        if offer.driver_id != driver.id:
            return False, "Заказ не принадлежит этому водителю."

        if offer.status != "pending":
            return False, "Оффер уже недоступен."

        if offer.expires_at <= timezone.now():
            offer.status = "expired"
            offer.responded_at = timezone.now()
            offer.save(update_fields=["status", "responded_at"])
            return False, "Время оффера истекло."

        if ride.driver_id or ride.status != "searching_driver":
            offer.status = "expired"
            offer.responded_at = timezone.now()
            offer.save(update_fields=["status", "responded_at"])
            return False, "Заказ уже занят."

        now = timezone.now()

        ride.driver = driver
        ride.status = "driver_assigned"
        ride.assigned_at = now
        ride.accepted_at = now
        ride.save(update_fields=["driver", "status", "assigned_at", "accepted_at"])

        offer.status = "accepted"
        offer.responded_at = now
        offer.save(update_fields=["status", "responded_at"])

        WorkerStatus.objects.filter(user=driver).update(is_busy=True)

        TaxiOffer.objects.filter(
            ride=ride,
            status="pending",
        ).exclude(id=offer.id).update(
            status="expired",
            responded_at=now,
        )

    return True, "Заказ принят."


def reject_taxi_offer(offer, driver):
    with transaction.atomic():
        offer = TaxiOffer.objects.select_for_update().select_related("ride").get(id=offer.id)

        if offer.driver_id != driver.id:
            return False, "Оффер не принадлежит этому водителю."

        if offer.status != "pending":
            return False, "Оффер уже недоступен."

        offer.status = "rejected"
        offer.responded_at = timezone.now()
        offer.save(update_fields=["status", "responded_at"])

        ride = offer.ride

    return True, ride.id


def expire_taxi_offer(offer):
    with transaction.atomic():
        offer = TaxiOffer.objects.select_for_update().get(id=offer.id)

        if offer.status != "pending":
            return False

        offer.status = "expired"
        offer.responded_at = timezone.now()
        offer.save(update_fields=["status", "responded_at"])

    return True