import json
from channels.generic.websocket import AsyncWebsocketConsumer
from assets.helpers.loggers import write_log


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

        write_log(f"WS CONNECTED: user={user.id} group={self.group_name}")

        await self.accept()

    async def disconnect(self, close_code):
        write_log(f"WS DISCONNECTED: {self.group_name}, code={close_code}")

        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

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