from rest_framework import serializers
from .models import *


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


class SaveAddressSerializer(serializers.Serializer):
    address = serializers.CharField(max_length=255)


class PersonalInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "user_type",
            "home_address",
            "work_address",
        )


class WorkerLocationUpdateSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    is_online = serializers.BooleanField(required=False)

class CourierProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourierProfile
        fields = "__all__"

class DriverProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverProfile
        fields = "__all__"
