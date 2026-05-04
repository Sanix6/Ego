import requests
from django.conf import settings
from django.utils import timezone

from .models import PushNotification, PushDevice
from apps.delivery.models import DeliveryOffer


ONESIGNAL_URL = "https://api.onesignal.com/notifications?c=push"


class PushService:

    @staticmethod
    def send(
        *,
        user,
        event_type: str,
        event_key: str,
        title: str,
        message: str,
        payload: dict = None,
        ride=None,
        delivery=None,
        offer=None,
        slot=None,
    ):
        payload = payload or {}

        with open("logs/push.log", "a", encoding="utf-8") as f:
            f.write(f"START event={event_type} user={user.id} event_key={event_key}\n")

        notification, created = PushNotification.objects.get_or_create(
            event_key=event_key,
            defaults={
                "recipient": user,
                "event_type": event_type,
                "title": title,
                "message": message,
                "payload": payload,
                "ride": ride,
                "delivery": delivery,
                "taxi_offer": offer if ride else None,
                "delivery_offer": offer if delivery else None,
                "slot": slot,
                "status": "pending",
            }
        )

        if not created:
            return notification

        devices = PushDevice.objects.filter(user=user, is_active=True)

        external_ids = list({
            str(d.external_user_id).strip()
            for d in devices
            if d.external_user_id
        })

        if not external_ids:
            notification.status = "failed"
            notification.error_message = "No external_user_id"
            notification.save()
            return notification

        os_payload = {
            "app_id": settings.ONESIGNAL_APP_ID,
            "target_channel": "push",
            "include_aliases": {
                "external_id": external_ids
            },
            "headings": {
                "en": title,
                "ru": title
            },
            "contents": {
                "en": message,
                "ru": message
            },
            "data": payload,
        }

        headers = {
            "Authorization": f"Key {settings.ONESIGNAL_API_KEY}",  # 🔥 ВАЖНО
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                ONESIGNAL_URL,
                json=os_payload,
                headers=headers,
                timeout=15,
            )

            if response.ok:
                notification.status = "sent"
                notification.sent_at = timezone.now()

                try:
                    notification.provider_message_id = response.json().get("id")
                except Exception:
                    pass

            else:
                notification.status = "failed"
                notification.error_message = response.text

                with open("logs/push.log", "a", encoding="utf-8") as f:
                    f.write(f"FAILED {response.text}\n")

        except Exception as e:
            notification.status = "failed"
            notification.error_message = str(e)

        notification.save()
        return notification

