from celery import shared_task
from django.db import transaction
from django.utils import timezone
from apps.taxi.models import TaxiOffer, TaxiRide
from apps.taxi.dispatch import dispatch_wave, expire_taxi_offer, TAXI_DISPATCH_WAVES
from apps.notify.taxi import *

@shared_task
def check_taxi_offer_timeout(offer_id):
    offer = TaxiOffer.objects.select_related("ride").filter(id=offer_id).first()
    if not offer:
        return

    if offer.status != "pending":
        return

    if offer.expires_at > timezone.now():
        return

    expired = expire_taxi_offer(offer)
    if not expired:
        return

    dispatch_taxi.delay(offer.ride_id)


@shared_task
def dispatch_taxi(ride_id, wave_index=0):
    if wave_index >= len(TAXI_DISPATCH_WAVES):
        return

    config = TAXI_DISPATCH_WAVES[wave_index]

    with transaction.atomic():
        ride = TaxiRide.objects.select_for_update().filter(id=ride_id).first()

        if not ride:
            return

        if ride.status != "searching_driver":
            return

        offers = dispatch_wave(
            ride=ride,
            limit=config["limit"]
        )

        if not offers:
            dispatch_taxi.delay(ride.id, wave_index + 1)
            return

        for offer in offers:
            check_taxi_offer_timeout.apply_async(
                args=[offer.id],
                countdown=config["timeout"]
            )

        dispatch_taxi.apply_async(
            args=[ride.id, wave_index + 1],
            countdown=config["timeout"]
        )

@shared_task
def send_taxi_offer_push_task(offer_id):
    with open("logs/taxi_push.log", "a", encoding="utf-8") as f:
        f.write(f"START task offer_id={offer_id}\n")

    offer = (
        TaxiOffer.objects
        .select_related("driver", "ride")
        .filter(id=offer_id)
        .first()
    )

    if not offer:
        with open("logs/taxi_push.log", "a", encoding="utf-8") as f:
            f.write(f"NOT FOUND offer_id={offer_id}\n")
        return

    with open("logs/taxi_push.log", "a", encoding="utf-8") as f:
        f.write(
            f"FOUND offer_id={offer.id} driver_id={offer.driver_id} ride_id={offer.ride_id}\n"
        )

    try:
        result = taxi_offer_created(offer)

        with open("logs/taxi_push.log", "a", encoding="utf-8") as f:
            f.write(
                f"SENT offer_id={offer.id} status={getattr(result, 'status', None)} "
                f"push_id={getattr(result, 'id', None)}\n"
            )

    except Exception as e:
        with open("logs/taxi_push.log", "a", encoding="utf-8") as f:
            f.write(f"ERROR offer_id={offer_id} error={str(e)}\n")