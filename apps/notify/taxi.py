from .services import PushService


def taxi_offer_created(offer):
    return PushService.send(
        user=offer.driver,
        event_type="taxi_offer",
        event_key=f"taxi_offer_{offer.id}",
        title="Новая поездка",
        message=f"Вам поступил заказ #{offer.ride_id}",
        ride=offer.ride,
        payload={
            "type": "navigate",
            "screen": "TaxiOffer",
            "offer_id": offer.id,
            "ride_id": offer.ride_id,
        }
    )


def taxi_offer_accepted(offer):
    return PushService.send(
        user=offer.ride.client,
        event_type="taxi_offer_accepted",
        event_key=f"taxi_offer_accepted_{offer.id}",
        title="Водитель назначен",
        message="Водитель принял ваш заказ",
        ride=offer.ride,
        payload={
            "type": "navigate",
            "screen": "RideDetail",
            "ride_id": offer.ride_id,
        }
    )


def taxi_arrived(ride):
    return PushService.send(
        user=ride.client,
        event_type="taxi_arrived",
        event_key=f"taxi_arrived_{ride.id}",
        title="Водитель прибыл",
        message="Водитель ожидает вас",
        ride=ride,
        payload={
            "type": "navigate",
            "screen": "RideTracking",
            "ride_id": ride.id,
        }
    )


def taxi_started(ride):
    return PushService.send(
        user=ride.client,
        event_type="taxi_started",
        event_key=f"taxi_started_{ride.id}",
        title="Поездка началась",
        message="Хорошей поездки!",
        ride=ride,
        payload={
            "type": "navigate",
            "screen": "ActiveRide",
            "ride_id": ride.id,
        }
    )


def taxi_completed(ride):
    return PushService.send(
        user=ride.client,
        event_type="taxi_completed",
        event_key=f"taxi_completed_{ride.id}",
        title="Поездка завершена",
        message="Спасибо за поездку",
        ride=ride,
        payload={
            "type": "navigate",
            "screen": "RideSummary",
            "ride_id": ride.id,
        }
    )


def taxi_cancelled(ride):
    return PushService.send(
        user=ride.client,
        event_type="taxi_cancelled",
        event_key=f"taxi_cancelled_{ride.id}",
        title="Поездка отменена",
        message="Поездка была отменена",
        ride=ride,
        payload={
            "type": "navigate",
            "screen": "RideList",
        }
    )