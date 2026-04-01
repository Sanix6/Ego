from django.shortcuts import render
from rest_framework import generics, status, views
from .models import *
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q
from .tasks import *
from .dispatch import *
from .services import *
from apps.users.models import WorkerLocation
from .pricing import *
from services.matrix import RoutingService, RoutingServiceError
from datetime import timedelta
from django.utils import timezone



class DeliveryCreateView(generics.GenericAPIView):
    queryset = Delivery.objects.all()
    serializer_class = DeliveryCreateSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        delivery = serializer.save(
            client=request.user,
            delivery_status="searching_courier"
        )

        dispatch_delivery.delay(delivery.id)

        return Response({
            "success": True,
            "message": "Заказ создан, ищем курьера",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class MyActiveOffersView(generics.ListAPIView):
    serializer_class = DeliveryOfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.user_type != "courier":
            return DeliveryOffer.objects.none()

        return DeliveryOffer.objects.filter(
            courier=user,
            status="pending"
        ).select_related("delivery").order_by("-sent_at")

class AcceptOfferView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        offer_id = kwargs.get("offer_id")

        if user.user_type != "courier":
            return Response(
                {"success": False, "message": "Только курьер может принять заказ"},
                status=status.HTTP_403_FORBIDDEN
            )

        offer = DeliveryOffer.objects.select_related(
            "courier",
            "delivery",
            "delivery__slot",
        ).filter(id=offer_id).first()

        if not offer:
            return Response(
                {"success": False, "message": "Оффер не найден"},
                status=status.HTTP_404_NOT_FOUND
            )

        success, message = accept_delivery_offer(offer, user)

        if not success:
            return Response(
                {"success": False, "message": message},
                status=status.HTTP_400_BAD_REQUEST
            )

        offer.refresh_from_db()
        delivery = offer.delivery

        serializer = DeliveryOfferAcceptResponseSerializer(offer)

        eta_data = None
        worker_location = WorkerLocation.objects.filter(user=user).first()

        if (
            worker_location
            and delivery.pickup_lat is not None
            and delivery.pickup_lon is not None
        ):
            eta_data = build_eta_data(
                from_lat=worker_location.lat,
                from_lon=worker_location.lon,
                to_lat=float(delivery.pickup_lat),
                to_lon=float(delivery.pickup_lon),
                speed_kmh=25.0,
            )

        return Response(
            {
                "success": True,
                "message": message,
                "data": serializer.data,
                "tracking": {
                    "target": "point_a",
                    "eta": eta_data,
                }
            },
            status=status.HTTP_200_OK
        )
    

class DeliveryCancelByClientView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        delivery_id = kwargs.get("delivery_id")

        if user.user_type != "client":
            return Response(
                {"success": False, "message": "Только клиент может отменить заказ"},
                status=status.HTTP_403_FORBIDDEN
            )

        delivery = Delivery.objects.filter(id=delivery_id, client=user).first()
        if not delivery:
            return Response(
                {"success": False, "message": "Заказ не найден"},
                status=status.HTTP_404_NOT_FOUND
            )

        success, message = cancel_delivery_by_client(delivery, user)

        if not success:
            return Response(
                {"success": False, "message": message},
                status=status.HTTP_400_BAD_REQUEST
            )

        delivery.refresh_from_db()
        serializer = DeliveryTrackingSerializer(delivery)

        return Response(
            {"success": True, "message": message, "data": serializer.data},
            status=status.HTTP_200_OK
        )
        

class RejectOfferView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        offer_id = kwargs.get("offer_id")

        if user.user_type != "courier":
            return Response(
                {"success": False, "message": "Только курьер может отклонить заказ"},
                status=status.HTTP_403_FORBIDDEN
            )

        offer = DeliveryOffer.objects.filter(id=offer_id).first()
        if not offer:
            return Response(
                {"success": False, "message": "Оффер не найден"},
                status=status.HTTP_404_NOT_FOUND
            )

        success, delivery_id = reject_delivery_offer(offer, user)

        if success:
            dispatch_delivery.delay(delivery_id)

        return Response(
            {"success": success},
            status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST
        )

class DeliveryTrackingView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeliveryTrackingSerializer

    def get(self, request, *args, **kwargs):
        delivery_id = kwargs.get("delivery_id")

        delivery = (
            Delivery.objects
            .select_related(
                "courier",
                "courier__courier_profile",
                "courier__worker_location",
            )
            .filter(
                id=delivery_id,
                client=request.user,
            )
            .first()
        )

        if not delivery:
            return Response(
                {
                    "success": False,
                    "message": "Заказ не найден."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(delivery)

        return Response(
            {
                "success": True,
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )


class DeliveryArriveView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        delivery_id = kwargs.get("delivery_id")

        if user.user_type != "courier":
            return Response(
                {"success": False, "message": "Только курьер"},
                status=status.HTTP_403_FORBIDDEN
            )

        delivery = Delivery.objects.filter(id=delivery_id).first()
        if not delivery:
            return Response(
                {"success": False, "message": "Заказ не найден"},
                status=status.HTTP_404_NOT_FOUND
            )

        success, message = mark_delivery_arrived(delivery, user)

        if not success:
            return Response(
                {"success": False, "message": message},
                status=status.HTTP_400_BAD_REQUEST
            )

        delivery.refresh_from_db()
        serializer = DeliveryTrackingSerializer(delivery)

        return Response(
            {"success": True, "message": message, "data": serializer.data}
        )

class DeliveryPickupView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        delivery_id = kwargs.get("delivery_id")

        if user.user_type != "courier":
            return Response(
                {"success": False, "message": "Только курьер"},
                status=status.HTTP_403_FORBIDDEN
            )

        delivery = Delivery.objects.filter(id=delivery_id).first()
        if not delivery:
            return Response(
                {"success": False, "message": "Заказ не найден"},
                status=status.HTTP_404_NOT_FOUND
            )

        success, message = mark_delivery_picked_up(delivery, user)

        if not success:
            return Response(
                {"success": False, "message": message},
                status=status.HTTP_400_BAD_REQUEST
            )

        delivery.refresh_from_db()
        serializer = DeliveryTrackingSerializer(delivery)

        eta_data = None
        worker_location = WorkerLocation.objects.filter(user=user).first()

        if (
            worker_location
            and delivery.dropoff_lat is not None
            and delivery.dropoff_lon is not None
        ):
            eta_data = build_eta_data(
                from_lat=worker_location.lat,
                from_lon=worker_location.lon,
                to_lat=float(delivery.dropoff_lat),
                to_lon=float(delivery.dropoff_lon),
                speed_kmh=25.0,
            )

        return Response(
            {
                "success": True,
                "message": message,
                "data": serializer.data,
                "tracking": {
                    "target": "point_b",
                    "eta": eta_data,
                }
            }
        )


class DeliveryArrivePointBView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        delivery_id = kwargs.get("delivery_id")

        if user.user_type != "courier":
            return Response(
                {"success": False, "message": "Только курьер"},
                status=status.HTTP_403_FORBIDDEN
            )

        delivery = Delivery.objects.filter(id=delivery_id).first()
        if not delivery:
            return Response(
                {"success": False, "message": "Заказ не найден"},
                status=status.HTTP_404_NOT_FOUND
            )

        success, message = mark_delivery_arrived_b(delivery, user)

        if not success:
            return Response(
                {"success": False, "message": message},
                status=status.HTTP_400_BAD_REQUEST
            )

        delivery.refresh_from_db()
        serializer = DeliveryTrackingSerializer(delivery)

        return Response(
            {"success": True, "message": message, "data": serializer.data}
        )

class DeliveryCompleteView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        delivery_id = kwargs.get("delivery_id")

        if user.user_type != "courier":
            return Response(
                {"success": False, "message": "Только курьер"},
                status=status.HTTP_403_FORBIDDEN
            )

        delivery = Delivery.objects.filter(id=delivery_id).first()
        if not delivery:
            return Response(
                {"success": False, "message": "Заказ не найден"},
                status=status.HTTP_404_NOT_FOUND
            )

        success, message = complete_delivery(delivery, user)

        if not success:
            return Response(
                {"success": False, "message": message},
                status=status.HTTP_400_BAD_REQUEST
            )

        delivery.refresh_from_db()
        serializer = DeliveryTrackingSerializer(delivery)

        return Response(
            {"success": True, "message": message, "data": serializer.data}
        )

class SlotListView(generics.GenericAPIView):
    serializer_class = SlotSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        courier_profile = getattr(request.user, "courier_profile", None)

        if courier_profile and courier_profile.darkstore:
            slots = CourierSlot.objects.filter(
                Q(darkstore=courier_profile.darkstore) | Q(darkstore__isnull=True)
            ).order_by("start_at")
        else:
            slots = CourierSlot.objects.filter(
                darkstore__isnull=True
            ).order_by("start_at")

        serializer = self.get_serializer(slots, many=True)
        return Response(serializer.data)


class MyCourierSlotsView(generics.ListAPIView):
    serializer_class = SlotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.user_type != "courier":
            return CourierSlot.objects.none()

        queryset = CourierSlot.objects.filter(
            courier=user
        ).select_related(
            "courier"
        ).order_by("start_at")

        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset
    
class CourierSlotBookView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SlotSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        slot_id = kwargs.get("slot_id")

        if user.user_type != "courier":
            return Response(
                {
                    "success": False,
                    "message": "Только курьер может выбрать слот."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        with transaction.atomic():
            slot = (
                CourierSlot.objects
                .select_for_update()
                .filter(id=slot_id)
                .first()
            )

            if not slot:
                return Response(
                    {
                        "success": False,
                        "message": "Слот не найден."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            if slot.courier_id and slot.courier_id != user.id:
                return Response(
                    {
                        "success": False,
                        "message": "Слот уже занят другим курьером."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            has_conflict = CourierSlot.objects.filter(
                courier=user,
                start_at__lt=slot.end_at,
                end_at__gt=slot.start_at,
            ).exclude(id=slot.id).exists()

            if has_conflict:
                return Response(
                    {
                        "success": False,
                        "message": "У вас уже есть пересекающийся слот."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            slot.courier = user

            if slot.status == "planned":
                slot.status = "offered"

            slot.save(update_fields=["courier", "status"])

        return Response(
            {
                "success": True,
                "message": "Слот успешно выбран.",
                "data": self.get_serializer(slot).data
            },
            status=status.HTTP_200_OK
        )


class CourierSlotCancelView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SlotSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        slot_id = kwargs.get("slot_id")

        if user.user_type != "courier":
            return Response(
                {
                    "success": False,
                    "message": "Только курьер может отменить слот."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        with transaction.atomic():
            slot = (
                CourierSlot.objects
                .select_for_update()
                .filter(id=slot_id)
                .first()
            )

            if not slot:
                return Response(
                    {
                        "success": False,
                        "message": "Слот не найден."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            if slot.courier_id != user.id:
                return Response(
                    {
                        "success": False,
                        "message": "Этот слот не принадлежит вам."
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            now = timezone.now()
            cancel_deadline = slot.start_at - timedelta(hours=1)

            if now >= cancel_deadline:
                return Response(
                    {
                        "success": False,
                        "message": "Отменить слот можно не позже чем за 1 час до начала."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            slot.courier = None
            slot.status = "planned"
            slot.save(update_fields=["courier", "status"])

        return Response(
            {
                "success": True,
                "message": "Бронь слота успешно отменена.",
                "data": self.get_serializer(slot).data
            },
            status=status.HTTP_200_OK
        )

class DeliveryPricesPreviewView(views.APIView):
    def post(self, request):
        serializer = DeliveryPricesPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            route = RoutingService.get_route(
                pickup_lat=data["pickup_lat"],
                pickup_lon=data["pickup_lon"],
                dropoff_lat=data["dropoff_lat"],
                dropoff_lon=data["dropoff_lon"],
            )

            tariffs = DeliveryPricingService.get_prices_for_all_types(
                distance_km=route["distance_km"],
                duration_min=route["duration_min"],
            )

        except RoutingServiceError as exc:
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except DeliveryPricingError as exc:
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