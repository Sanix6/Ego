# core/middleware.py
from urllib.parse import parse_qs
from channels.db import database_sync_to_async

class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        inner = TokenAuthMiddlewareInstance(scope, self.inner)
        return await inner(receive, send)


class TokenAuthMiddlewareInstance:
    def __init__(self, scope, inner):
        self.scope = dict(scope)
        self.inner = inner

    async def __call__(self, receive, send):
        query_string = self.scope.get("query_string", b"").decode()
        qs = parse_qs(query_string)
        token_key = qs.get("token")
        self.scope["user"] = await self.get_user(token_key[0] if token_key else None)

        inner = self.inner
        return await inner(self.scope, receive, send)

    @database_sync_to_async
    def get_user(self, token_key):
        from django.contrib.auth.models import AnonymousUser

        if not token_key:
            return AnonymousUser()

        from rest_framework.authtoken.models import Token
        try:
            token = Token.objects.select_related("user").get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return AnonymousUser()