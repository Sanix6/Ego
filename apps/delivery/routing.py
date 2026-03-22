from django.urls import re_path
from .consumer import BaseConsumer

websocket_urlpatterns = [
    re_path(r"ws/courier/$", BaseConsumer.as_asgi()),
]