from decimal import Decimal, ROUND_HALF_UP
import requests
from django.conf import settings
from datetime import datetime


class RoutingServiceError(Exception):
    pass


def write_log(message: str):
    with open("logs/routing.log", "a") as log_file:
        log_file.write(f"[{datetime.now()}] {message}\n")


class RoutingService:
    BASE_URL = "https://api.mapbox.com/directions/v5/mapbox/driving"

    @classmethod
    def get_route(cls, *, pickup_lat: float, pickup_lon: float, dropoff_lat: float, dropoff_lon: float) -> dict:
        api_key = getattr(settings, "MAPBOX_ACCESS_TOKEN", "")
        if not api_key:
            write_log("Ошибка: не настроен MAPBOX_ACCESS_TOKEN")
            raise RoutingServiceError("Не настроен ключ Mapbox Directions API.")

        try:
            pickup_lat = float(pickup_lat)
            pickup_lon = float(pickup_lon)
            dropoff_lat = float(dropoff_lat)
            dropoff_lon = float(dropoff_lon)
        except (TypeError, ValueError) as exc:
            write_log(
                f"Некорректные координаты: "
                f"pickup=({pickup_lat}, {pickup_lon}), "
                f"dropoff=({dropoff_lat}, {dropoff_lon})"
            )
            raise RoutingServiceError("Некорректные координаты для построения маршрута.") from exc

        if not cls._is_valid_coordinate(pickup_lat, pickup_lon):
            write_log(f"Некорректная точка отправления: ({pickup_lat}, {pickup_lon})")
            raise RoutingServiceError("Некорректные координаты точки отправления.")

        if not cls._is_valid_coordinate(dropoff_lat, dropoff_lon):
            write_log(f"Некорректная точка назначения: ({dropoff_lat}, {dropoff_lon})")
            raise RoutingServiceError("Некорректные координаты точки назначения.")

        coordinates = f"{pickup_lon},{pickup_lat};{dropoff_lon},{dropoff_lat}"
        url = f"{cls.BASE_URL}/{coordinates}"

        params = {
            "access_token": api_key,
            "alternatives": "false",
            "geometries": "geojson",
            "overview": "false",
            "steps": "false",
        }

        try:
            response = requests.get(
                url,
                params=params,
                timeout=getattr(settings, "MAPBOX_DIRECTIONS_TIMEOUT", 10),
            )

            write_log(f"REQUEST url={url} params={params}")
            write_log(f"RESPONSE status={response.status_code} body={response.text}")

            response.raise_for_status()

        except requests.RequestException as exc:
            write_log(f"Ошибка запроса к Mapbox: {str(exc)}")
            raise RoutingServiceError("Ошибка запроса к сервису маршрутизации.") from exc

        try:
            data = response.json()
        except ValueError:
            write_log(f"Ответ не JSON: {response.text}")
            raise RoutingServiceError("Некорректный ответ от сервиса маршрутизации.")

        if data.get("code") != "Ok":
            write_log(f"Mapbox вернул ошибку: {data}")
            raise RoutingServiceError("Маршрут между указанными точками не найден.")

        try:
            route = data["routes"][0]
            distance_m = route["distance"]
            duration_s = route["duration"]
        except (KeyError, IndexError, TypeError) as exc:
            write_log(f"Некорректная структура ответа: {data}")
            raise RoutingServiceError("Некорректный ответ от сервиса маршрутизации.") from exc

        distance_km = (Decimal(str(distance_m)) / Decimal("1000")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        duration_min = int(
            (Decimal(str(duration_s)) / Decimal("60")).quantize(
                Decimal("1"),
                rounding=ROUND_HALF_UP,
            )
        )

        write_log(f"distance_km={distance_km} duration_min={duration_min}")

        return {
            "distance_km": distance_km,
            "duration_min": duration_min,
        }

    @staticmethod
    def _is_valid_coordinate(lat: float, lon: float) -> bool:
        return -90 <= lat <= 90 and -180 <= lon <= 180