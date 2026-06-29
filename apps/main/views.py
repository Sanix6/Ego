from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.utils import timezone
from datetime import timedelta

from django.core.cache import cache

from apps.delivery.models import Delivery
from apps.taxi.models import TaxiRide
from .models import Review
from .serializers import ReviewCreateSerializer, ReviewSerializer
from .services import update_user_rating
from rest_framework.views import APIView
from .models import DeliveryZone
from apps.users.models import CourierProfile
from .serializers import (
    DeliveryZoneListSerializer,
    CourierOwnZoneSerializer,
    AssignDeliveryZoneSerializer,
)
from .permissions import IsCourier


class AvailableDeliveryZonesView(generics.ListAPIView):
    serializer_class = DeliveryZoneListSerializer
    permission_classes = [IsAuthenticated, IsCourier]

    def get_queryset(self):
        user = self.request.user
        courier_profile = getattr(user, "courier_profile", None)

        queryset = DeliveryZone.objects.filter(is_active=True)

        if courier_profile and courier_profile.darkstore_id:
            queryset = queryset.filter(darkstore_id=courier_profile.darkstore_id)

        return queryset.order_by("name")


class AssignDeliveryZoneView(APIView):
    permission_classes = [IsAuthenticated, IsCourier]

    def post(self, request, *args, **kwargs):
        try:
            courier_profile = request.user.courier_profile
        except CourierProfile.DoesNotExist:
            return Response(
                {"detail": "Профиль курьера не найден."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AssignDeliveryZoneSerializer(
            data=request.data,
            context={"courier_profile": courier_profile}
        )
        serializer.is_valid(raise_exception=True)
        courier_profile = serializer.save()

        return Response(
            {
                "detail": "Зона успешно назначена.",
                "zone": DeliveryZoneListSerializer(courier_profile.delivery_zones).data
            },
            status=status.HTTP_200_OK
        )


class MyDeliveryZoneView(APIView):
    permission_classes = [IsAuthenticated, IsCourier]

    def get(self, request, *args, **kwargs):
        try:
            courier_profile = request.user.courier_profile
        except CourierProfile.DoesNotExist:
            return Response(
                {"detail": "Профиль курьера не найден."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not courier_profile.delivery_zones:
            return Response(
                {"detail": "У курьера пока нет выбранной зоны.", "zone": None},
                status=status.HTTP_200_OK
            )

        return Response(
            CourierOwnZoneSerializer(courier_profile).data,
            status=status.HTTP_200_OK
        )


class DeliveryReviewView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewCreateSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        delivery_id = kwargs.get("delivery_id")

        delivery = Delivery.objects.select_related("client", "courier").filter(id=delivery_id).first()
        if not delivery:
            return Response(
                {"success": False, "message": "Доставка не найдена"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if delivery.delivery_status != "delivered":
            return Response(
                {"success": False, "message": "Отзыв можно оставить только после завершения доставки"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.id == delivery.client_id:
            from_user = user
            to_user = delivery.courier
        elif user.id == delivery.courier_id:
            from_user = user
            to_user = delivery.client
        else:
            return Response(
                {"success": False, "message": "Вы не участник этой доставки"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not to_user:
            return Response(
                {"success": False, "message": "Некого оценивать"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Review.objects.filter(
            from_user=from_user,
            to_user=to_user,
            delivery=delivery,
        ).exists():
            return Response(
                {"success": False, "message": "Вы уже оставили отзыв по этой доставке"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review = Review.objects.create(
            from_user=from_user,
            to_user=to_user,
            delivery=delivery,
            rating=serializer.validated_data["rating"],
            comment=serializer.validated_data.get("comment", ""),
        )

        update_user_rating(to_user)

        return Response(
            {
                "success": True,
                "message": "Отзыв успешно оставлен",
                "data": ReviewSerializer(review).data,
            },
            status=status.HTTP_201_CREATED,
        )


class TaxiReviewView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReviewCreateSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        ride_id = kwargs.get("ride_id")

        ride = TaxiRide.objects.select_related("client", "driver").filter(id=ride_id).first()
        if not ride:
            return Response(
                {"success": False, "message": "Поездка не найдена"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if ride.status != "completed":
            return Response(
                {"success": False, "message": "Отзыв можно оставить только после завершения поездки"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.id == ride.client_id:
            from_user = user
            to_user = ride.driver
        elif user.id == ride.driver_id:
            from_user = user
            to_user = ride.client
        else:
            return Response(
                {"success": False, "message": "Вы не участник этой поездки"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not to_user:
            return Response(
                {"success": False, "message": "Некого оценивать"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Review.objects.filter(
            from_user=from_user,
            to_user=to_user,
            ride=ride,
        ).exists():
            return Response(
                {"success": False, "message": "Вы уже оставили отзыв по этой поездке"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review = Review.objects.create(
            from_user=from_user,
            to_user=to_user,
            ride=ride,
            rating=serializer.validated_data["rating"],
            comment=serializer.validated_data.get("comment", ""),
        )

        update_user_rating(to_user)

        return Response(
            {
                "success": True,
                "message": "Отзыв успешно оставлен",
                "data": ReviewSerializer(review).data,
            },
            status=status.HTTP_201_CREATED,
        )





CACHE_TTL = 60 * 5  


class RecentAddressesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        cache_key = f"recent_addresses:{user.id}"

        cached = cache.get(cache_key)
        if cached:
            return Response({
                "success": True,
                "source": "cache",
                "data": cached
            })

        limit_date = timezone.now() - timedelta(days=30)

        delivery_qs = Delivery.objects.filter(
            client_id=user.id,
            created_at__gte=limit_date
        ).values(
            "id",
            "point_a",
            "point_b",
            "pickup_lat",
            "pickup_lon",
            "dropoff_lat",
            "dropoff_lon",
            "created_at"
        )

        taxi_qs = TaxiRide.objects.filter(
            client_id=user.id,
            requested_at__gte=limit_date
        ).values(
            "id",
            "point_a",
            "point_b",
            "pickup_lat",
            "pickup_lon",
            "dropoff_lat",
            "dropoff_lon",
            "requested_at"
        )

        result = []

        for d in delivery_qs:
            if d["point_a"]:
                result.append({
                    "type": "delivery",
                    "role": "pickup",
                    "address": d["point_a"],
                    "lat": d["pickup_lat"],
                    "lon": d["pickup_lon"],
                    "created_at": d["created_at"]
                })

            if d["point_b"]:
                result.append({
                    "type": "delivery",
                    "role": "dropoff",
                    "address": d["point_b"],
                    "lat": d["dropoff_lat"],
                    "lon": d["dropoff_lon"],
                    "created_at": d["created_at"]
                })

        for t in taxi_qs:
            if t["point_a"]:
                result.append({
                    "type": "taxi",
                    "role": "pickup",
                    "address": t["point_a"],
                    "lat": t["pickup_lat"],
                    "lon": t["pickup_lon"],
                    "created_at": t["requested_at"]
                })

            if t["point_b"]:
                result.append({
                    "type": "taxi",
                    "role": "dropoff",
                    "address": t["point_b"],
                    "lat": t["dropoff_lat"],
                    "lon": t["dropoff_lon"],
                    "created_at": t["requested_at"]
                })

        result.sort(key=lambda x: x["created_at"], reverse=True)
        result = result[:30]

        cache.set(cache_key, result, CACHE_TTL)

        return Response({
            "success": True,
            "source": "db",
            "data": result
        })









