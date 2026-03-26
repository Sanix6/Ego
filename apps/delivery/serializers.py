from rest_framework import serializers
from .models import *
from apps.users.models import WorkerLocation, User


class DeliveryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = [
            "id",
            "point_a",
            "point_b",
            "pickup_lat",
            "pickup_lon",
            "dropoff_lat",
            "dropoff_lon",
            "type_delivery",
            "price",
            "deadline_at",
            "client_comment",
            "door_to_door",

            "sender_name",
            "sender_phone",
            "recipient_name",
            "recipient_phone",

            "pickup_entrance",
            "pickup_floor",
            "pickup_apartment",
            "pickup_intercom",
            "pickup_comment",

            "dropoff_entrance",
            "dropoff_floor",
            "dropoff_apartment",
            "dropoff_intercom",
            "dropoff_comment",
        ]


class SlotSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()
    period = serializers.SerializerMethodField()
    weekday = serializers.SerializerMethodField()
    duration_hours = serializers.SerializerMethodField()

    class Meta:
        model = CourierSlot
        fields = [
            "id",
            "date",
            "start_time",
            "end_time",
            "period",
            "weekday",
            "duration_hours",
            "status",
            "courier",
            "created_at",
        ]

    def get_date(self, obj):
        return obj.start_at.strftime("%d.%m.%Y") if obj.start_at else None

    def get_start_time(self, obj):
        return obj.start_at.strftime("%H:%M") if obj.start_at else None

    def get_end_time(self, obj):
        return obj.end_at.strftime("%H:%M") if obj.end_at else None

    def get_period(self, obj):
        if obj.start_at and obj.end_at:
            return f"{obj.start_at.strftime('%H:%M')} - {obj.end_at.strftime('%H:%M')}"
        return None

    def get_weekday(self, obj):
        weekdays = {
            0: "Понедельник",
            1: "Вторник",
            2: "Среда",
            3: "Четверг",
            4: "Пятница",
            5: "Суббота",
            6: "Воскресенье",
        }
        return weekdays.get(obj.start_at.weekday()) if obj.start_at else None

    def get_duration_hours(self, obj):
        if obj.start_at and obj.end_at:
            diff = obj.end_at - obj.start_at
            return round(diff.total_seconds() / 3600, 2)
        return None

class BookCourierSlotSerializer(serializers.Serializer):
    slot_id = serializers.IntegerField()


class DeliveryShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = [
            "id",
            "point_a",
            "point_b",
            "price",
            "type_delivery",
            "created_at",
        ]


class DeliveryOfferSerializer(serializers.ModelSerializer):
    delivery = DeliveryShortSerializer(read_only=True)
    is_expired = serializers.SerializerMethodField()
    time_left = serializers.SerializerMethodField()

    class Meta:
        model = DeliveryOffer
        fields = [
            "id",
            "delivery",
            "status",
            "sent_at",
            "expires_at",
            "time_left",
        ]

    def get_time_left(self, obj):
        from django.utils import timezone

        if obj.expires_at:
            diff = obj.expires_at - timezone.now()
            seconds = int(diff.total_seconds())
            return max(seconds, 0)
        return 0

    def get_is_expired(self, obj):
        from django.utils import timezone
        return obj.expires_at <= timezone.now()

class CourierInfoSerializer(serializers.ModelSerializer):
    transport_type = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "phone",
            "transport_type",
        ]

    def get_transport_type(self, obj):
        profile = getattr(obj, "courier_profile", None)
        return profile.transport_type if profile else None


class CourierLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerLocation
        fields = [
            "lat",
            "lon",
            "updated_at",
        ]


class DeliveryTrackingSerializer(serializers.ModelSerializer):
    courier = CourierInfoSerializer(read_only=True)
    courier_location = serializers.SerializerMethodField()

    class Meta:
        model = Delivery
        fields = [
            "id",
            "delivery_status",
            "point_a",
            "point_b",
            "pickup_lat",
            "pickup_lon",
            "dropoff_lat",
            "dropoff_lon",
            "price",
            "door_to_door",
            "type_delivery",
            "pickup_comment",
            "dropoff_comment",
            "client_comment",
            "courier",
            "courier_location",
            "created_at",
        ]

    def get_courier_location(self, obj):
        courier = obj.courier
        if not courier:
            return None

        location = getattr(courier, "worker_location", None)
        if not location:
            return None

        return CourierLocationSerializer(location).data


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = [
            "id",
            "point_a",
            "point_b",
            "pickup_lat",
            "pickup_lon",
            "dropoff_lat",
            "dropoff_lon",
            "delivery_status",
            "type_delivery",
            "price",
            "pickup_at",
            "delivered_at",
            "time_left",
            "deadline_at",
            "door_to_door",
            "sender_name",
            "sender_phone",
            "recipient_name",
            "recipient_phone",
            "pickup_entrance",
            "pickup_floor",
            "pickup_apartment",
            "pickup_intercom",
            "pickup_comment",
            "dropoff_entrance",
            "dropoff_floor",
            "dropoff_apartment",
            "dropoff_intercom",
            "dropoff_comment",
            "client_comment",
            "created_at",
    
        ]

class DeliveryOfferAcceptResponseSerializer(serializers.ModelSerializer):
    delivery = DeliveryTrackingSerializer(read_only=True)
    courier = serializers.SerializerMethodField()

    class Meta:
        model = DeliveryOffer
        fields = [
            "id",
            "status",
            "sent_at",
            "responded_at",
            "expires_at",
            "delivery",
            "courier",
        ]

    def get_courier(self, obj):
        user = obj.courier
        if not user:
            return None

        return {
            "id": user.id,
            "full_name": getattr(user, "full_name", ""),
            "phone": getattr(user, "phone", ""),
            "user_type": getattr(user, "user_type", ""),
        }