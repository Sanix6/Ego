from rest_framework import serializers
from .models import *
from apps.taxi.models import TaxiRide
from apps.delivery.models import Delivery
from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta
from django.utils.timezone import localtime
import calendar

class SendCodeSerializer(serializers.Serializer):
    phone = serializers.CharField()


class VerifyCodeSerializer(serializers.Serializer):
    phone = serializers.CharField()
    code = serializers.CharField()


class DriverRegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    phone = serializers.CharField(max_length=15)
    email = serializers.EmailField(required=False, allow_blank=True)

    def validate_phone(self, value):
        phone = value.strip()
        if not phone.startswith('+'):
            raise serializers.ValidationError("Телефон должен начинаться с '+'")
        return phone

    def create(self, validated_data):
        phone = validated_data['phone']

        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={
                'first_name': validated_data.get('first_name', ''),
                'last_name': validated_data.get('last_name', ''),
                'email': validated_data.get('email', ''),
                'user_type': 'driver',
                'is_active': True,
            }
        )

        if not created:
            user.first_name = validated_data.get('first_name', user.first_name)
            user.last_name = validated_data.get('last_name', user.last_name)
            user.email = validated_data.get('email', user.email)
            user.user_type = 'driver'
            user.is_active = True
            user.save()

        DriverProfile.objects.get_or_create(user=user)

        return user



class VerifyCodeDriverSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=4)


class ResendCodeDriverSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)


class ScanPersonalDriverSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverProfile
        fields = [
            'id',
            'passport_front',
            'passport_back',
            'selfie',
            'passport_number'
        ]

class ScanDriversLicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverProfile
        fields = [
            'id',
            'driver_license_front',
            'driver_license_back',
            'seria_and_number',
            'date_of_issue',
            'issuing_authority'
        ]

class ScanDriversAutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverProfile
        fields = [
            'id',
            'car_brand',
            'car_model',
            'car_color',
            'car_number',
            "car_type",
            'car_photo', 
        ]

    def create(self, validated_data):
        driver_profile = super().create(validated_data)
        driver_profile.status = 'pending'
        driver_profile.save()
        return driver_profile




class PersonalInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "phone",
            "first_name",
            "last_name",
            "rating_avg",
            "user_type",
        )


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = "__all__"
        read_only_fields = ["user"]

class WorkerLocationUpdateSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    is_online = serializers.BooleanField(required=False)

class CourierProfileSerializer(serializers.ModelSerializer):
    rating_avg = serializers.DecimalField(
        source="user.rating_avg",
        max_digits=3,
        decimal_places=2,
        read_only=True
    )
    rating_count = serializers.IntegerField(
        source="user.rating_count",
        read_only=True
    )
    orders_count = serializers.IntegerField(
        source="user.orders_count",
        read_only=True
    )
    class Meta:
        model = CourierProfile
        fields = "__all__"

class DriverProfileSerializer(serializers.ModelSerializer):
    rating_avg = serializers.DecimalField(
        source="user.rating_avg",
        max_digits=3,
        decimal_places=2,
        read_only=True
    )
    rating_count = serializers.IntegerField(
        source="user.rating_count",
        read_only=True
    )
    orders_count = serializers.IntegerField(
        source="user.orders_count",
        read_only=True
    )
    class Meta:
        model = DriverProfile
        fields = "__all__"

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone", "first_name", "last_name"]


class MyOrderListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    status = serializers.CharField()

    from_address = serializers.CharField()
    to_address = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)

    distance_km = serializers.SerializerMethodField()
    duration_min = serializers.SerializerMethodField()

    human_date = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    def get_distance_km(self, obj):
        return obj.get("distance_km")

    def get_duration_min(self, obj):
        return obj.get("duration_min")

    def get_human_date(self, obj):
        dt = timezone.localtime(obj["created_at"])
        today = timezone.localdate()
        order_date = dt.date()

        if order_date == today:
            return "Сегодня"

        if order_date == today - timedelta(days=1):
            return "Вчера"

        months = {
            1: "янв",
            2: "фев",
            3: "мар",
            4: "апр",
            5: "май",
            6: "июн",
            7: "июл",
            8: "авг",
            9: "сен",
            10: "окт",
            11: "ноя",
            12: "дек",
        }

        return f"{order_date.day} {months[order_date.month]}"

    def get_created_at(self, obj):
        dt = timezone.localtime(obj["created_at"])
        return dt.strftime("%H:%M")

class TaxiRideDetailSerializer(serializers.ModelSerializer):
    driver_name = serializers.SerializerMethodField()
    driver_phone = serializers.SerializerMethodField()
    car_info = serializers.SerializerMethodField()
    car_number = serializers.SerializerMethodField()
    started_at = serializers.SerializerMethodField()
    car_class = serializers.SerializerMethodField()

    class Meta:
        model = TaxiRide
        fields = [
            "id",
            "status",
            "point_a",
            "point_b",
            "price",
            "started_at",
            "driver_name",
            "driver_phone",
            "car_info",
            "car_number",
            "duration_min",
            "car_class",
        ]

    def get_car_class(self, obj):
        return obj.get_car_class_display() if obj.car_class else None

    def get_driver_phone(self, obj):
        if obj.driver:
            return obj.driver.phone
        return None
        
    def get_started_at(self, obj):
        if obj.started_at:
            return obj.started_at.strftime("%d.%m.%Y %H:%M")
        return None

    def get_driver_name(self, obj):
        if obj.driver:
            return f"{obj.driver.first_name} {obj.driver.last_name}".strip()
        return None

    def get_car_info(self, obj):
        profile = getattr(obj.driver, "driver_profile", None)

        if not profile:
            return None

        parts = [
            profile.car_color,
            profile.car_brand,
            profile.car_model,
        ]

        return " ".join([p for p in parts if p])

    def get_car_number(self, obj):
        profile = getattr(obj.driver, "driver_profile", None)
        return profile.car_number if profile else None


class DeliveryDetailSerializer(serializers.ModelSerializer):
    courier_name = serializers.SerializerMethodField()
    courier_phone = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    courier = serializers.SerializerMethodField()
    car_info = serializers.SerializerMethodField()
    type_delivery = serializers.SerializerMethodField()
    type_transport = serializers.SerializerMethodField()
    delivery_status = serializers.SerializerMethodField()

    class Meta:
        model = Delivery
        fields = [
            "id",
            "courier",
            "client",
            "point_a",
            "point_b",
            "delivery_status",
            "type_delivery",
            "type_transport",
            "price",
            "created_at",
            "courier_name",
            "courier_phone",
            "car_info",
            "fact_duration_min",
            "fact_distance_km",

        ]

    def get_delivery_status(self, obj):
        return obj.get_delivery_status_display()

    def get_type_delivery(self, obj):
        return obj.get_type_delivery_display()

    def get_type_transport(self, obj):
        return obj.get_type_transport_display()

    def get_car_info(self, obj):
        profile = getattr(obj.courier, "courier_profile", None)

        if not profile:
            return None

        parts = [
            profile.car_color,
            profile.car_brand,
            profile.car_model,
        ]

        return " ".join([p for p in parts if p])

    def get_courier_name(self, obj):
        if obj.courier:
            return f"{obj.courier.first_name} {obj.courier.last_name}".strip()
        return None

    def get_courier_phone(self, obj):
        if obj.courier:
            return obj.courier.phone
        return None

    def get_courier(self, obj):
        if obj.courier:
            return f"{obj.courier.first_name} {obj.courier.last_name}".strip()
        return None


    def get_created_at(self, obj):
        if obj.created_at:
            return localtime(obj.created_at).strftime("%d.%m.%Y")
        return None


    


class LogoProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'logo'
        ]
