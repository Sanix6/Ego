from decimal import Decimal, ROUND_HALF_UP

import requests
from django.conf import settings


class RoutingServiceError(Exception):
    pass


class YandexRoutingService:
    BASE_URL = "https://api.routing.yandex.net/v2/distancematrix"

    @classmethod
    def get_route(cls, *, pickup_lat: float, pickup_lon: float, dropoff_lat: float, dropoff_lon: float) -> dict:
        api_key = getattr(settings, "YANDEX_DISTANCE_MATRIX_API_KEY", "")
        if not api_key:
            raise RoutingServiceError("Не настроен ключ Yandex Distance Matrix API.")

        params = {
            "apikey": api_key,
            "origins": f"{pickup_lat},{pickup_lon}",
            "destinations": f"{dropoff_lat},{dropoff_lon}",
            "mode": "driving",
        }

        try:
            response = requests.get(
                cls.BASE_URL,
                params=params,
                timeout=getattr(settings, "YANDEX_DISTANCE_MATRIX_TIMEOUT", 10),
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RoutingServiceError("Ошибка запроса к сервису маршрутизации.") from exc

        data = response.json()

        try:
            element = data["rows"][0]["elements"][0]
        except (KeyError, IndexError, TypeError) as exc:
            raise RoutingServiceError("Некорректный ответ от сервиса маршрутизации.") from exc

        if element.get("status") != "OK":
            raise RoutingServiceError("Маршрут между указанными точками не найден.")

        try:
            distance_m = element["distance"]["value"]
            duration_s = element["duration"]["value"]
        except (KeyError, TypeError) as exc:
            raise RoutingServiceError("В ответе нет distance/duration.") from exc

        distance_km = (Decimal(str(distance_m)) / Decimal("1000")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        duration_min = int((Decimal(str(duration_s)) / Decimal("60")).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        ))

        return {
            "distance_km": distance_km,
            "duration_min": duration_min,
        }