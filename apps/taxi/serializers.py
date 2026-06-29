from rest_framework import serializers
from .models import TaxiRide
from apps.users.models import User, WorkerLocation
from .pricing import PricingService, PricingError
from services.matrix import RoutingService, RoutingServiceError
from apps.delivery.services import build_eta_data



class DriverRegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    phone = serializers.CharField(max_length=15)
    email = serializers.EmailField(required=False, allow_blank=True)

    def validate_phone(self, value):
        phone = value.strip()
        if not phone.startswith("+"):
            raise serializers.ValidationError("Телефон должен начинаться с '+'")
        return phone

    def create(self, validated_data):
        phone = validated_data["phone"]

        user, created = User.objects.get_or_create(
            phone=phone,
            defaults={
                "first_name": validated_data.get("first_name", ""),
                "last_name": validated_data.get("last_name", ""),
                "email": validated_data.get("email", ""),
                "user_type": "driver",
                "is_active": True,
            }
        )

        if not created:
            user.first_name = validated_data.get("first_name", user.first_name)
            user.last_name = validated_data.get("last_name", user.last_name)
            user.email = validated_data.get("email", user.email)
            user.user_type = "driver"
            user.save()

        return user


class TaxiRideCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxiRide
        fields = [
            "id",
            "point_a",
            "point_b",
            "car_class",
            "payment_method",
            "pickup_lat",
            "pickup_lon",
            "dropoff_lat",
            "dropoff_lon",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        try:
            route = RoutingService.get_route(
                pickup_lat=validated_data["pickup_lat"],
                pickup_lon=validated_data["pickup_lon"],
                dropoff_lat=validated_data["dropoff_lat"],
                dropoff_lon=validated_data["dropoff_lon"],
            )

            pricing = PricingService.get_price_details_for_tariff(
                car_class=validated_data["car_class"],
                distance_km=route["distance_km"],
                duration_min=route["duration_min"],
            )

        except RoutingServiceError as exc:
            raise serializers.ValidationError({"message": str(exc)})
        except PricingError as exc:
            raise serializers.ValidationError({"message": str(exc)})

        tariff = pricing["tariff"]

        ride = TaxiRide.objects.create(
            **validated_data,
            status="searching_driver",
            distance_km=pricing["distance_km"],
            duration_min=pricing["duration_min"],
            price=pricing["price"],
            estimated_price=pricing["estimated_price"],
            total_price=pricing["total_price"],
            base_fare=tariff.base_fare,
            per_km_rate=tariff.per_km_rate,
            per_min_rate=tariff.per_min_rate,
            included_km=tariff.included_km,
            included_min=tariff.included_min,
            commission_amount=pricing["commission_amount"],
            driver_payout=pricing["driver_payout"],
        )
        return ride

class TaxiRideDetailSerializer(serializers.ModelSerializer):
    driver_arrival_eta = serializers.SerializerMethodField()

    class Meta:
        model = TaxiRide
        fields = "__all__"
        extra_fields = ("driver_arrival_eta",)

    def get_field_names(self, declared_fields, info):
        fields = super().get_field_names(declared_fields, info)
        return fields + list(getattr(self.Meta, "extra_fields", []))

    def get_driver_arrival_eta(self, ride):
        if not ride.driver_id:
            return None

        if ride.status == "arrived":
            return {
                "distance_km": 0,
                "eta_sec": 0,
                "eta_min": 0,
            }

        if ride.status not in ("assigned", "accepted"):
            return None

        location = getattr(ride.driver, "worker_location", None)
        if not location:
            return None

        if None in (
            location.lat,
            location.lon,
            ride.pickup_lat,
            ride.pickup_lon,
        ):
            return None

        eta_data = build_eta_data(
            from_lat=location.lat,
            from_lon=location.lon,
            to_lat=ride.pickup_lat,
            to_lon=ride.pickup_lon,
            speed_kmh=35.0,
        )

        return {
            "distance_km": eta_data["distance_km"],
            "eta_sec": eta_data["eta_sec"],
            "eta_min": round(eta_data["eta_sec"] / 60),
        }


class TaxiPricesPreviewSerializer(serializers.Serializer):
    pickup_lat = serializers.FloatField()
    pickup_lon = serializers.FloatField()
    dropoff_lat = serializers.FloatField()
    dropoff_lon = serializers.FloatField()


class DriverInfoSerializer(serializers.ModelSerializer):
    car_brand = serializers.SerializerMethodField()
    car_model = serializers.SerializerMethodField()
    car_color = serializers.SerializerMethodField()
    car_number = serializers.SerializerMethodField()
    car_type = serializers.SerializerMethodField()
    selfie = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "phone",
            "car_brand",
            "car_model",
            "car_color",
            "car_number",
            "car_type",
            "rating_avg",
            "selfie",
        ]

    def get_selfie(self, obj):
        profile = getattr(obj, "driver_profile", None)

        if not profile or not profile.selfie:
            return None

        return profile.selfie.url
    

    def get_car_brand(self, obj):
        profile = getattr(obj, "driver_profile", None)
        return profile.car_brand if profile else None

    def get_car_model(self, obj):
        profile = getattr(obj, "driver_profile", None)
        return profile.car_model if profile else None

    def get_car_color(self, obj):
        profile = getattr(obj, "driver_profile", None)
        return profile.car_color if profile else None

    def get_car_number(self, obj):
        profile = getattr(obj, "driver_profile", None)
        return profile.car_number if profile else None

    def get_car_type(self, obj):
        profile = getattr(obj, "driver_profile", None)
        return profile.car_type if profile else None


class DriverLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkerLocation
        fields = [
            "lat",
            "lon",
            "updated_at",
        ]

class TaxiTrackingSerializer(serializers.ModelSerializer):
    driver = DriverInfoSerializer(read_only=True)
    driver_location = serializers.SerializerMethodField()
    driver_assigned = serializers.SerializerMethodField()
    tracking = serializers.SerializerMethodField()

    class Meta:
        model = TaxiRide
        fields = [
            "id",
            "order_code",
            "status",
            "point_a",
            "point_b",
            "pickup_lat",
            "pickup_lon",
            "dropoff_lat",
            "dropoff_lon",
            "car_class",
            "passengers",
            "client_comment",
            "distance_km",
            "duration_min",
            "price",
            "estimated_price",
            "total_price",
            "payment_method",
            "payment_status",
            "requested_at",
            "assigned_at",
            "accepted_at",
            "arrived_at",
            "started_at",
            "completed_at",
            "canceled_at",
            "driver_assigned",
            "driver",
            "driver_location",
            "tracking",
        ]

    def get_driver_assigned(self, obj):
        return obj.driver_id is not None

    def get_driver_location(self, obj):
        driver = obj.driver
        if not driver:
            return None

        location = getattr(driver, "worker_location", None)
        if not location:
            return None

        return DriverLocationSerializer(location).data

    def get_tracking(self, obj):
        driver = obj.driver
        if not driver:
            return {
                "target": None,
                "eta": None,
            }

        location = getattr(driver, "worker_location", None)
        if not location:
            return {
                "target": None,
                "eta": None,
            }

        if obj.status in ("assigned", "accepted"):
            if obj.pickup_lat is None or obj.pickup_lon is None:
                return {
                    "target": "point_a",
                    "eta": None,
                }

            eta = build_eta_data(
                from_lat=float(location.lat),
                from_lon=float(location.lon),
                to_lat=float(obj.pickup_lat),
                to_lon=float(obj.pickup_lon),
                speed_kmh=35.0,
            )

            return {
                "target": "point_a",
                "eta": {
                    "distance_km": eta["distance_km"],
                    "eta_sec": eta["eta_sec"],
                    "eta_min": round(eta["eta_sec"] / 60),
                },
            }

        if obj.status == "arrived":
            return {
                "target": "point_a",
                "eta": {
                    "distance_km": 0,
                    "eta_sec": 0,
                    "eta_min": 0,
                },
            }

        if obj.status == "in_trip":
            if obj.dropoff_lat is None or obj.dropoff_lon is None:
                return {
                    "target": "point_b",
                    "eta": None,
                }

            eta = build_eta_data(
                from_lat=float(location.lat),
                from_lon=float(location.lon),
                to_lat=float(obj.dropoff_lat),
                to_lon=float(obj.dropoff_lon),
                speed_kmh=35.0,
            )

            return {
                "target": "point_b",
                "eta": {
                    "distance_km": eta["distance_km"],
                    "eta_sec": eta["eta_sec"],
                    "eta_min": round(eta["eta_sec"] / 60),
                },
            }

        return {
            "target": None,
            "eta": None,
        }



class DriverRideHistorySerializer(serializers.ModelSerializer):
    order_date = serializers.DateTimeField(source="requested_at")
    from_address = serializers.CharField(source="point_a")
    to_address = serializers.CharField(source="point_b")
    amount = serializers.SerializerMethodField()
    earnings = serializers.SerializerMethodField()

    class Meta:
        model = TaxiRide
        fields = [
            "id",
            "order_date",
            "status",
            "from_address",
            "to_address",
            "distance_km",
            "duration_min",
            "amount",
            "earnings",
            "payment_method",
            "payment_status",
        ]

    def get_amount(self, obj):
        return obj.total_price or obj.price or "0.00"

    def get_earnings(self, obj):
        return obj.driver_payout or "0.00"


class TaxiCancelByClientSerializer(serializers.Serializer):
    cancel_reason = serializers.CharField(required=False, allow_blank=True, default="")