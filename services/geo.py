import redis
from django.conf import settings


redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


class RedisGeoService:
    DRIVER_KEY = "geo:drivers"
    COURIER_KEY = "geo:couriers"

    @classmethod
    def get_key(cls, user_type: str) -> str | None:
        if user_type == "driver":
            return cls.DRIVER_KEY
        if user_type == "courier":
            return cls.COURIER_KEY
        return None

    @classmethod
    def add_worker(cls, user_type: str, user_id: int, lat: float, lon: float):
        key = cls.get_key(user_type)
        if not key:
            return

        redis_client.geoadd(key, [lon, lat, str(user_id)])

    @classmethod
    def remove_worker(cls, user_type: str, user_id: int):
        key = cls.get_key(user_type)
        if not key:
            return

        redis_client.zrem(key, str(user_id))

    @classmethod
    def find_nearest(cls, user_type: str, lat: float, lon: float, radius_km=5, limit=10):
        key = cls.get_key(user_type)
        if not key:
            return []

        results = redis_client.georadius(
            key,
            lon,
            lat,
            radius_km,
            unit="km",
            withdist=True,
            sort="ASC",
            count=limit
        )

        return [(int(user_id), float(distance)) for user_id, distance in results]