import requests
from django.conf import settings


class YandexSuggestService:
    BASE_URL = "https://suggest-maps.yandex.ru/v1/suggest"

    BISHKEK_CHUY_BBOX = "73.3,42.3~75.5,43.3"

    @classmethod
    def suggest(
        cls,
        text: str,
        ll: str | None = None,
        ull: str | None = None,
        only_bishkek_chuy: bool = True,
    ) -> dict:
        if not text or not text.strip():
            return {
                "success": False,
                "message": "Параметр text обязателен"
            }

        params = {
            "apikey": settings.YANDEX_SUGGEST_API_KEY,
            "text": text.strip(),
            "lang": "ru",
            "results": 10,
            "print_address": 1,
            "attrs": "uri",
            "types": "house,street,locality",
        }

        if only_bishkek_chuy:
            params["bbox"] = cls.BISHKEK_CHUY_BBOX
            params["strict_bounds"] = 1

        if ll:
            params["ll"] = ll
            params["spn"] = "0.2,0.2"

        if ull:
            params["ull"] = ull

        try:
            response = requests.get(cls.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Ошибка запроса к Yandex Suggest: {str(e)}"
            }

        return {
            "success": True,
            "results": data.get("results", []),
        }