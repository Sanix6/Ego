from django.shortcuts import render
from rest_framework import generics, status
from .models import *
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q
from .tasks import *
from .dispatch import *
from .services import *


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
        serializer = DeliveryOfferAcceptResponseSerializer(offer)

        return Response(
            {
                "success": True,
                "message": message,
                "data": serializer.data,
            },
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

        return Response(
            {"success": True, "message": message, "data": serializer.data}
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

class SlotListView(generics.ListAPIView):
    queryset = CourierSlot.objects.all()
    serializer_class = SlotSerializer
    permission_classes = [IsAuthenticated]

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

            if not slot.can_be_booked_by(user):
                return Response(
                    {
                        "success": False,
                        "message": "Этот слот недоступен для бронирования."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            has_conflict = CourierSlot.objects.filter(
                booked_by=user,
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

            slot.booked_by = user

            if slot.status == "planned":
                slot.status = "offered"

            slot.save()

        return Response(
            {
                "success": True,
                "message": "Слот успешно выбран.",
                "data": self.get_serializer(slot).data
            },
            status=status.HTTP_200_OK
        )

class MyCourierSlotsView(generics.ListAPIView):
    serializer_class = SlotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.user_type != "courier":
            return CourierSlot.objects.none()

        queryset = CourierSlot.objects.filter(
            Q(booked_by=user) | Q(reserved_for=user)
        ).select_related(
            "reserved_for",
            "booked_by",
        ).order_by("start_at")

        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response(
            {
                "success": True,
                "count": queryset.count(),
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )