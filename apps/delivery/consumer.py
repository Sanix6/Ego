import json
from channels.generic.websocket import AsyncWebsocketConsumer
from assets.helpers.loggers import write_log
from channels.db import database_sync_to_async
from django.utils import timezone



class BaseConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        user = self.scope["user"]

        if not user.is_authenticated:
            write_log("WS REJECTED: anonymous user")
            await self.close()
            return

        self.group_name = f"user_{user.id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.set_online(user.id)

        write_log(f"WS CONNECTED: user={user.id} group={self.group_name}")

        await self.accept()

    async def disconnect(self, close_code):
        write_log(f"WS DISCONNECTED: {self.group_name}, code={close_code}")

        user = self.scope["user"]

        if user.is_authenticated:
            await self.set_offline(user.id)

        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    @database_sync_to_async
    def set_online(self, user_id):
        from apps.users.models import WorkerStatus
        WorkerStatus.objects.update_or_create(
            user_id=user_id,
            defaults={
                "is_online": True,
                "online_started_at": timezone.now(),
            }
        )

    @database_sync_to_async
    def set_offline(self, user_id):
        from apps.users.models import WorkerStatus
        status = WorkerStatus.objects.filter(user_id=user_id).first()

        if not status:
            return

        now = timezone.now()

        if status.online_started_at:
            delta = now - status.online_started_at
            seconds = int(delta.total_seconds())
            status.today_online_seconds += max(seconds, 0)

        status.is_online = False
        status.online_started_at = None
        status.save(update_fields=[
            "is_online",
            "online_started_at",
            "today_online_seconds"
        ])

    async def new_offer(self, event):
        try:
            write_log(f"NEW OFFER: {event}")

            payload = dict(event)
            payload.pop("channel", None)

            text = json.dumps(payload, ensure_ascii=False)

            write_log(f"WS SEND PAYLOAD: {text}")

            await self.send(text_data=text)

            write_log("WS SEND SUCCESS")

        except Exception as e:
            write_log(f"WS ERROR in new_offer: {str(e)}")