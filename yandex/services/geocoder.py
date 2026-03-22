import requests
from django.conf import settings


class YandexGeocoderService:
    BASE_URL = "https://geocode-maps.yandex.ru/v1/"

    @classmethod
    def _extract_geoobject(cls, data: dict):
        return (
            data.get("response", {})
            .get("GeoObjectCollection", {})
            .get("featureMember", [])
        )

    @staticmethod
    def parse_address_components(components):
        country = None
        city = None
        street = None
        house = None

        for comp in components:
            kind = comp.get("kind")
            name = comp.get("name")

            if kind == "country":
                country = name
            elif kind == "locality":
                city = name
            elif kind == "province" and not city:
                city = name
            elif kind == "street":
                street = name
            elif kind == "house":
                house = name

        address = " ".join(filter(None, [street, house]))

        return {
            "country": country,
            "city": city,
            "address": address,
        }

    @staticmethod
    def _extract_point(obj: dict):
        point = obj.get("Point", {}).get("pos", "")
        if not point:
            return None, None

        parts = point.split()
        if len(parts) != 2:
            return None, None

        lon_str, lat_str = parts
        return float(lat_str), float(lon_str)

    @classmethod
    def geocode_address(cls, address: str) -> dict:
        if not address:
            return {
                "success": False,
                "message": "Адрес не может быть пустым"
            }

        params = {
            "apikey": settings.YANDEX_GEOCODER_API_KEY,
            "geocode": address,
            "lang": "ru_RU",
            "format": "json",
            "results": 1,
        }

        try:
            response = requests.get(cls.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Ошибка запроса к Yandex Geocoder: {str(e)}"
            }

        if data.get("message"):
            return {
                "success": False,
                "message": data.get("message")
            }

        members = cls._extract_geoobject(data)
        if not members:
            return {
                "success": False,
                "message": "Адрес не найден"
            }

        obj = members[0].get("GeoObject", {})
        meta = obj.get("metaDataProperty", {}).get("GeocoderMetaData", {})
        address_data = meta.get("Address", {})
        components = address_data.get("Components", [])

        parsed = cls.parse_address_components(components)
        lat, lon = cls._extract_point(obj)

        full_address = (
            address_data.get("formatted")
            or meta.get("text")
            or address
        )

        return {
            "success": True,
            "country": parsed.get("country"),
            "city": parsed.get("city"),
            "address": parsed.get("address") or full_address,
            "full_address": full_address,
            "lat": lat,
            "lon": lon,
        }

    @classmethod
    def reverse_geocode(cls, lat: float, lon: float) -> dict:
        if lat is None or lon is None:
            return {
                "success": False,
                "message": "Координаты lat и lon обязательны"
            }

        params = {
            "apikey": settings.YANDEX_GEOCODER_API_KEY,
            "geocode": f"{lon},{lat}",
            "sco": "longlat",
            "kind": "house",
            "lang": "ru_RU",
            "format": "json",
            "results": 1,
        }

        try:
            response = requests.get(cls.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Ошибка запроса к Yandex Geocoder: {str(e)}"
            }

        if data.get("message"):
            return {
                "success": False,
                "message": data.get("message")
            }

        members = cls._extract_geoobject(data)
        if not members:
            return {
                "success": False,
                "message": "Адрес по координатам не найден"
            }

        obj = members[0].get("GeoObject", {})
        meta = obj.get("metaDataProperty", {}).get("GeocoderMetaData", {})
        address_data = meta.get("Address", {})
        components = address_data.get("Components", [])

        parsed = cls.parse_address_components(components)
        result_lat, result_lon = cls._extract_point(obj)

        full_address = (
            address_data.get("formatted")
            or meta.get("text")
            or ""
        )

        return {
            "success": True,
            "country": parsed.get("country"),
            "city": parsed.get("city"),
            "address": parsed.get("address") or full_address,
            "full_address": full_address,
            "lat": result_lat,
            "lon": result_lon,
        }