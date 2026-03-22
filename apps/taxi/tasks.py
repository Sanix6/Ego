from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.taxi.models import TaxiOffer, TaxiRide
from apps.taxi.dispatch import dispatch_wave, expire_taxi_offer, TAXI_DISPATCH_WAVES


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