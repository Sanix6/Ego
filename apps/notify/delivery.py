from .services import PushService


def delivery_offer_created(offer):
    return PushService.send(
        user=offer.courier,
        event_type="delivery_offer",
        event_key=f"delivery_offer_{offer.id}",
        title="Новый заказ",
        message=f"Заказ #{offer.delivery_id}",
        delivery=offer.delivery,
        offer=offer,
        payload={
            "type": "navigate",
            "screen": "DeliveryOffer",
            "offer_id": offer.id,
            "delivery_id": offer.delivery_id,
        }
    )


def delivery_offer_accepted(offer):
    return PushService.send(
        user=offer.delivery.client,
        event_type="delivery_offer_accepted",
        event_key=f"delivery_offer_accepted_{offer.id}",
        title="Курьер назначен",
        message="Ваш заказ принят курьером",
        delivery=offer.delivery,
        payload={
            "type": "navigate",
            "screen": "DeliveryDetail",
            "delivery_id": offer.delivery_id,
        }
    )


def delivery_arrived(delivery):
    return PushService.send(
        user=delivery.client,
        event_type="delivery_arrived",
        event_key=f"delivery_arrived_{delivery.id}",
        title="Курьер прибыл",
        message="Курьер на точке A",
        delivery=delivery,
        payload={
            "type": "navigate",
            "screen": "DeliveryTracking",
            "delivery_id": delivery.id,
        }
    )


def delivery_picked_up(delivery):
    return PushService.send(
        user=delivery.client,
        event_type="delivery_picked_up",
        event_key=f"delivery_picked_up_{delivery.id}",
        title="Заказ забран",
        message="Курьер забрал заказ",
        delivery=delivery,
        payload={
            "type": "navigate",
            "screen": "DeliveryTracking",
            "delivery_id": delivery.id,
        }
    )


def delivery_arrived_b(delivery):
    return PushService.send(
        user=delivery.client,
        event_type="delivery_arrived_b",
        event_key=f"delivery_arrived_b_{delivery.id}",
        title="Курьер рядом",
        message="Курьер прибыл к точке B",
        delivery=delivery,
        payload={
            "type": "navigate",
            "screen": "DeliveryTracking",
            "delivery_id": delivery.id,
        }
    )


def delivery_completed(delivery):
    return PushService.send(
        user=delivery.client,
        event_type="delivery_completed",
        event_key=f"delivery_completed_{delivery.id}",
        title="Доставка завершена",
        message="Спасибо за заказ",
        delivery=delivery,
        payload={
            "type": "navigate",
            "screen": "DeliverySummary",
            "delivery_id": delivery.id,
        }
    )


def delivery_cancelled(delivery):
    return PushService.send(
        user=delivery.client,
        event_type="delivery_cancelled",
        event_key=f"delivery_cancelled_{delivery.id}",
        title="Заказ отменён",
        message="Доставка отменена",
        delivery=delivery,
        payload={
            "type": "navigate",
            "screen": "DeliveryList",
        }
    )