import requests
from django.conf import settings
from .models import PushNotification, PushDevice
from apps.delivery.models import DeliveryOffer


def log_push(message):
    with open("logs/delivery_push.log", "a", encoding="utf-8") as f:
        f.write(message + "\n")


def send_delivery_offer_push(offer_id):
    log_push(f"START DELIVERY PUSH offer_id={offer_id}")

    offer = DeliveryOffer.objects.select_related("courier", "delivery").filter(id=offer_id).first()
    if not offer:
        log_push("DELIVERY OFFER NOT FOUND")
        return

    courier = offer.courier
    delivery = offer.delivery

    log_push(f"DELIVERY OFFER FOUND courier={courier.id} delivery={delivery.id}")

    event_key = f"delivery_offer_{offer.id}"

    notification, created = PushNotification.objects.get_or_create(
        event_key=event_key,
        defaults={
            "recipient": courier,
            "event_type": "delivery_offer",
            "title": "Новый заказ",
            "message": f"Вам поступил новый заказ #{delivery.id}",
            "payload": {
                "offer_id": offer.id,
                "delivery_id": delivery.id,
                "type": "delivery_offer",
            },
            "delivery": delivery,
            "delivery_offer": offer,
            "status": "pending",
        }
    )

    log_push(f"DELIVERY NOTIFICATION CREATED={created}")
    if not created:
        log_push("DELIVERY NOTIFICATION ALREADY EXISTS")
        return

    devices = PushDevice.objects.filter(user=courier, is_active=True)
    log_push(f"DELIVERY DEVICES COUNT={devices.count()}")

    external_ids = list({
        str(d.external_user_id).strip()
        for d in devices
        if d.external_user_id
    })
    log_push(f"DELIVERY EXTERNAL IDS={external_ids}")

    if not external_ids:
        notification.status = "failed"
        notification.error_message = "Нет external_user_id для OneSignal"
        notification.save(update_fields=["status", "error_message", "updated_at"])
        log_push("DELIVERY NO EXTERNAL IDS")
        return

    payload = {
        "app_id": settings.ONESIGNAL_APP_ID,
        "include_aliases": {
            "external_id": external_ids
        },
        "target_channel": "push",
        "headings": {
            "en": "New order",
            "ru": "Новый заказ",
        },
        "contents": {
            "en": f"You have a new order #{delivery.id}",
            "ru": f"Вам поступил новый заказ #{delivery.id}",
        },
        "data": {
            "offer_id": offer.id,
            "delivery_id": delivery.id,
            "type": "delivery_offer",
        },
    }

    headers = {
        "Authorization": f"Key {settings.ONESIGNAL_API_KEY}",
        "Content-Type": "application/json",
    }

    log_push(f"DELIVERY ONESIGNAL REQUEST PAYLOAD={payload}")

    try:
        response = requests.post(
            "https://api.onesignal.com/notifications",
            json=payload,
            headers=headers,
            timeout=15,
        )

        log_push(f"DELIVERY ONESIGNAL RESPONSE STATUS={response.status_code}")
        log_push(f"DELIVERY ONESIGNAL RESPONSE BODY={response.text}")

        if response.ok:
            notification.status = "sent"
            try:
                response_json = response.json()
                notification.provider_message_id = response_json.get("id")
            except Exception:
                notification.provider_message_id = None

            notification.save(
                update_fields=["status", "provider_message_id", "updated_at"]
            )
            log_push("DELIVERY PUSH SENT SUCCESS")
        else:
            notification.status = "failed"
            notification.error_message = response.text
            notification.save(update_fields=["status", "error_message", "updated_at"])
            log_push("DELIVERY PUSH FAILED")

    except Exception as e:
        notification.status = "failed"
        notification.error_message = str(e)
        notification.save(update_fields=["status", "error_message", "updated_at"])
        log_push(f"DELIVERY PUSH EXCEPTION {str(e)}")