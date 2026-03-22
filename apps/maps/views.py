import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import *
from yandex.services.geocoder import YandexGeocoderService
from yandex.services.suggest import YandexSuggestService



class GeocodeView(APIView):
    def post(self, request):
        serializer = GeocodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = YandexGeocoderService.geocode_address(
                serializer.validated_data["address"]
            )
        except requests.RequestException:
            return Response(
                {"success": False, "message": "Ошибка запроса к Yandex Geocoder"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception:
            return Response(
                {"success": False, "message": "Внутренняя ошибка сервера"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not result["success"]:
            return Response(result, status=status.HTTP_404_NOT_FOUND)

        return Response(result, status=status.HTTP_200_OK)


class ReverseGeocodeView(APIView):
    def post(self, request):
        serializer = ReverseGeocodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = YandexGeocoderService.reverse_geocode(
                lat=serializer.validated_data["lat"],
                lon=serializer.validated_data["lon"],
            )
        except requests.RequestException:
            return Response(
                {"success": False, "message": "Ошибка запроса к Yandex Geocoder"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except Exception:
            return Response(
                {"success": False, "message": "Внутренняя ошибка сервера"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not result["success"]:
            return Response(result, status=status.HTTP_404_NOT_FOUND)

        return Response(result, status=status.HTTP_200_OK)


class AddressSuggestView(APIView):
    def get(self, request):
        serializer = SuggestQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            data = YandexSuggestService.suggest(
                text=serializer.validated_data["text"],
                ll=serializer.validated_data.get("ll"),
                ull=serializer.validated_data.get("ull"),
            )
        except requests.RequestException:
            return Response(
                {"success": False, "message": "Ошибка запроса к Yandex Geosuggest"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title", {}).get("text", ""),
                "subtitle": item.get("subtitle", {}).get("text", ""),
                "address": item.get("address", {}).get("formatted_address", ""),
                "uri": item.get("uri", ""),
                "distance": item.get("distance", {}).get("value"),
            })

        return Response({
            "success": True,
            "results": results
        }, status=status.HTTP_200_OK)