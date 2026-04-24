from django.db.transaction import on_commit
from rest_framework import generics, status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import *
from .serializers import *
from .tasks import *
from .dispatch import *
from .services import *
from services.matrix import *
from apps.taxi.pricing import *
from .paginations import *


class TaxiRideCreateView(generics.CreateAPIView):
    serializer_class = TaxiRideCreateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TaxiRide.objects.select_related("client", "driver")

    def perform_create(self, serializer):
        ride = serializer.save(client=self.request.user)
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

        offer = TaxiOffer.objects.select_related("ride").filter(id=offer_id).first()
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
                    "data": serializer.data,
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

        offer = TaxiOffer.objects.select_related("ride").filter(id=offer_id).first()
        if not offer:
            return Response(
                {"success": False, "message": "Оффер не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        success, ride_id = reject_taxi_offer(offer, user)

        if success:
            on_commit(lambda: dispatch_taxi.delay(ride_id))

        return Response(
            {"success": success},
            status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST,
        )


class TaxiPricesPreviewView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TaxiPricesPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            route = RoutingService.get_route(
                pickup_lat=data["pickup_lat"],
                pickup_lon=data["pickup_lon"],
                dropoff_lat=data["dropoff_lat"],
                dropoff_lon=data["dropoff_lon"],
            )

            tariffs = PricingService.get_prices_for_city(
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
            TaxiRide.objects.select_related(
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
                    "message": "Поездка не найдена.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.get_serializer(ride)

        return Response(
            {
                "success": True,
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class TaxiArriveView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return taxi_action_response(
            request,
            kwargs.get("taxi_id"),
            mark_taxi_arrived,
        )


class TaxiStartTripView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return taxi_action_response(
            request,
            kwargs.get("taxi_id"),
            mark_taxi_in_trip,
        )


class TaxiCompleteView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return taxi_action_response(
            request,
            kwargs.get("taxi_id"),
            complete_taxi_trip,
        )



class DriverRideHistoryView(generics.ListAPIView):
    serializer_class = DriverRideHistorySerializer
    permission_classes = [IsAuthenticated]
    # pagination_class = DriverRideHistoryPagination

    def get_queryset(self):
        user = self.request.user

        queryset = TaxiRide.objects.filter(
            driver=user
        ).order_by("-requested_at")

        status_param = self.request.query_params.get("status")
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")

        if status_param:
            queryset = queryset.filter(status=status_param)

        if date_from:
            dt_from = timezone.make_aware(
                datetime.combine(
                    datetime.strptime(date_from, "%Y-%m-%d").date(),
                    time.min
                )
            )
            queryset = queryset.filter(requested_at__gte=dt_from)

        if date_to:
            dt_to = timezone.make_aware(
                datetime.combine(
                    datetime.strptime(date_to, "%Y-%m-%d").date(),
                    time.max
                )
            )
            queryset = queryset.filter(requested_at__lte=dt_to)

        return queryset


class TaxiCancelByClientView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TaxiCancelByClientSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        taxi_id = kwargs.get("taxi_id")

        if user.user_type != "client":
            return Response(
                {"success": False, "message": "Только клиент может отменить поездку"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        taxi = TaxiRide.objects.filter(id=taxi_id, client=user).first()
        if not taxi:
            return Response(
                {"success": False, "message": "Поездка не найдена"},
                status=status.HTTP_404_NOT_FOUND
            )

        cancel_reason = serializer.validated_data.get("cancel_reason", "")

        success, message = cancel_taxi_by_client(
            taxi=taxi,
            user=user,
            cancel_reason=cancel_reason,
        )

        if not success:
            return Response(
                {"success": False, "message": message},
                status=status.HTTP_400_BAD_REQUEST
            )

        taxi.refresh_from_db()
        response_serializer = TaxiRideDetailSerializer(taxi)

        return Response(
            {
                "success": True,
                "message": message,
                "data": response_serializer.data,
            },
            status=status.HTTP_200_OK
        )