from rest_framework import serializers
from .models import TaxiRide


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
            user.save()

        return user


class TaxiRideCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxiRide
        fields = [
            "id",
            'point_a',
            'point_b',
            'car_class',
            'payment_method',
            "pickup_lat",
            "pickup_lon",
            "dropoff_lat",
            "dropoff_lon",
        ]


class TaxiRideDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxiRide
        fields = "__all__"


class TaxiPricesPreviewSerializer(serializers.Serializer):
    pickup_lat = serializers.FloatField()
    pickup_lon = serializers.FloatField()
    dropoff_lat = serializers.FloatField()
    dropoff_lon = serializers.FloatField()
    city = serializers.CharField(required=False, allow_blank=True, max_length=100)