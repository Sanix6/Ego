# core/asgi.py
import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

def get_application():
    from .middleware import TokenAuthMiddleware
    from apps.delivery.routing import websocket_urlpatterns

    return ProtocolTypeRouter({
        "http": get_asgi_application(),
        "websocket": TokenAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        ),
    })

application = get_application()