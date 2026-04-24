import json
import requests
from django.conf import settings
from .models import PushNotification, PushDevice
from apps.taxi.models import TaxiOffer


def log_push(message):
    with open("logs/push.log", "a", encoding="utf-8") as f:
        f.write(str(message) + "\n")


def send_taxi_offer_push(offer_id):
    log_push(f"START TAXI PUSH offer_id={offer_id}")

    offer = TaxiOffer.objects.select_related("driver", "ride").filter(id=offer_id).first()
    if not offer:
        log_push("TAXI OFFER NOT FOUND")
        return

    driver = offer.driver
    ride = offer.ride

    log_push(f"TAXI OFFER FOUND driver={driver.id} ride={ride.id}")

    event_key = f"taxi_offer_{offer.id}"

    notification, created = PushNotification.objects.get_or_create(
        event_key=event_key,
        defaults={
            "recipient": driver,
            "event_type": "taxi_offer",
            "title": "Новая поездка",
            "message": f"Вам поступил новый заказ #{ride.id}",
            "payload": {
                "offer_id": offer.id,
                "ride_id": ride.id,
                "type": "taxi_offer",
            },
            "ride": ride,
            "taxi_offer": offer,
            "status": "pending",
        }
    )

    log_push(f"TAXI NOTIFICATION CREATED={created}")

    if not created:
        log_push("TAXI NOTIFICATION ALREADY EXISTS")
        return

    devices = PushDevice.objects.filter(user=driver, is_active=True)

    log_push(f"TAXI DEVICES COUNT={devices.count()}")
    log_push(f"TAXI DEVICE IDS={list(devices.values_list('id', flat=True))}")
    log_push(f"TAXI DEVICE EXTERNAL IDS RAW={list(devices.values_list('external_user_id', flat=True))}")

    external_ids = list({
        str(d.external_user_id).strip()
        for d in devices
        if d.external_user_id
    })

    log_push(f"TAXI EXTERNAL IDS={external_ids}")

    if not external_ids:
        notification.status = "failed"
        notification.error_message = "Нет external_user_id для OneSignal"
        notification.save(update_fields=["status", "error_message", "updated_at"])

        log_push("TAXI NO EXTERNAL IDS")
        return

    payload = {
        "app_id": settings.ONESIGNAL_APP_ID,
        "include_aliases": {
            "external_id": external_ids
        },
        "target_channel": "push",
        "headings": {
            "en": "New ride",
            "ru": "Новая поездка",
        },
        "contents": {
            "en": f"You have a new order #{ride.id}",
            "ru": f"Вам поступил новый заказ #{ride.id}",
        },
        "data": {
            "offer_id": offer.id,
            "ride_id": ride.id,
            "type": "taxi_offer",
        },
    }

    headers = {
        "Authorization": f"Key {settings.ONESIGNAL_API_KEY}",
        "Content-Type": "application/json",
    }

    log_push("TAXI ONESIGNAL REQUEST PAYLOAD=" + json.dumps(payload, ensure_ascii=False))

    try:
        response = requests.post(
            "https://api.onesignal.com/notifications",
            json=payload,
            headers=headers,
            timeout=15,
        )

        log_push(f"TAXI ONESIGNAL RESPONSE STATUS={response.status_code}")
        log_push(f"TAXI ONESIGNAL RESPONSE BODY={response.text}")

        if response.ok:
            notification.status = "sent"

            try:
                notification.provider_message_id = response.json().get("id")
            except Exception:
                notification.provider_message_id = None

            notification.save(
                update_fields=[
                    "status",
                    "provider_message_id",
                    "updated_at"
                ]
            )

            log_push("TAXI PUSH SENT SUCCESS")

        else:
            notification.status = "failed"
            notification.error_message = response.text

            notification.save(
                update_fields=[
                    "status",
                    "error_message",
                    "updated_at"
                ]
            )

            log_push("TAXI PUSH FAILED")

    except Exception as e:
        notification.status = "failed"
        notification.error_message = str(e)

        notification.save(
            update_fields=[
                "status",
                "error_message",
                "updated_at"
            ]
        )

        log_push(f"TAXI PUSH EXCEPTION {str(e)}")