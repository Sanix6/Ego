from rest_framework import generics, status, views
from .models import TaxiRide
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .tasks import *
from django.db.transaction import on_commit
from .dispatch import *
from .services import *
from django.conf import settings
from services.matrix import RoutingService, RoutingServiceError
from apps.taxi.pricing import PricingService, PricingError


class TaxiRideCreateView(generics.CreateAPIView):
    queryset = TaxiRide.objects.all()
    serializer_class = TaxiRideCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        ride = serializer.save(
            client=self.request.user,
            status="searching_driver",
        )
        on_commit(lambda: dispatch_taxi.delay(ride.id))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        ride = serializer.instance  

        return Response(
            {
                "success": True,
                "message": "Поездка создана, ищем водителя.",
                "data": TaxiRideDetailSerializer(ride).data,
            },
            status=status.HTTP_201_CREATED,
        )


class AcceptTaxiOfferView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        offer_id = kwargs.get("offer_id")

        if user.user_type != "driver":
            return Response(
                {"success": False, "message": "Только водитель может принять заказ."},
                status=status.HTTP_403_FORBIDDEN,
            )

        offer = TaxiOffer.objects.filter(id=offer_id).first()
        if not offer:
            return Response(
                {"success": False, "message": "Оффер не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        success, message = accept_taxi_offer(offer, user)

        if success:
            ride = offer.ride  
            serializer = TaxiRideDetailSerializer(ride)

            return Response(
                {
                    "success": True,
                    "message": message,
                    "data": serializer.data
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"success": False, "message": message},
            status=status.HTTP_400_BAD_REQUEST,
        )


class RejectTaxiOfferView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        offer_id = kwargs.get("offer_id")

        if user.user_type != "driver":
            return Response(
                {"success": False, "message": "Только водитель может отклонить заказ."},
                status=status.HTTP_403_FORBIDDEN,
            )

        offer = TaxiOffer.objects.filter(id=offer_id).first()
        if not offer:
            return Response(
                {"success": False, "message": "Оффер не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        success, ride_id = reject_taxi_offer(offer, user)

        if success:
            dispatch_taxi.delay(ride_id)

        return Response(
            {"success": success},
            status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST,
        )


class TaxiPricesPreviewView(views.APIView):
    def post(self, request):
        serializer = TaxiPricesPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        city = data.get("city") or getattr(settings, "DEFAULT_TAXI_CITY", "Бишкек")

        try:
            route = RoutingService.get_route(
                pickup_lat=data["pickup_lat"],
                pickup_lon=data["pickup_lon"],
                dropoff_lat=data["dropoff_lat"],
                dropoff_lon=data["dropoff_lon"],
            )

            tariffs = PricingService.get_prices_for_city(
                city=city,
                distance_km=route["distance_km"],
                duration_min=route["duration_min"],
            )
        except RoutingServiceError as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except PricingError as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "route": {
                    "distance_km": str(route["distance_km"]),
                    "duration_min": route["duration_min"],
                },
                "tariffs": tariffs,
            },
            status=status.HTTP_200_OK,
        )

class TaxiTrackingView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TaxiTrackingSerializer

    def get(self, request, *args, **kwargs):
        ride_id = kwargs.get("ride_id")

        ride = (
            TaxiRide.objects
            .select_related(
                "driver",
                "driver__driver_profile",
                "driver__worker_location",
            )
            .filter(
                id=ride_id,
                client=request.user,
            )
            .first()
        )

        if not ride:
            return Response(
                {
                    "success": False,
                    "message": "Поездка не найдена."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(ride)

        return Response(
            {
                "success": True,
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

class TaxiArriveView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return taxi_action_response(
            request,
            kwargs.get("taxi_id"),
            mark_taxi_arrived
        )

class TaxiStartTripView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return taxi_action_response(
            request,
            kwargs.get("taxi_id"),
            mark_taxi_in_trip
        )

class TaxiCompleteView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return taxi_action_response(
            request,
            kwargs.get("taxi_id"),
            complete_taxi_trip
        )

