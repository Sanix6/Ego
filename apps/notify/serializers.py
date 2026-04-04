from rest_framework import serializers
from .models import PushDevice


class PushDeviceRegisterSerializer(serializers.Serializer):
    onesignal_id = serializers.CharField(max_length=255)
    external_user_id = serializers.CharField(max_length=255)
    platform = serializers.ChoiceField(choices=["android", "ios"])

    def create(self, validated_data):
        user = self.context["request"].user

        device, created = PushDevice.objects.update_or_create(
            onesignal_id=validated_data["onesignal_id"],
            defaults={
                "user": user,
                "external_user_id": validated_data["external_user_id"],
                "platform": validated_data["platform"],
                "is_active": True,
            },
        )

        return device