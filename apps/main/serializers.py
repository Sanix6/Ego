from rest_framework import serializers
from .models import Review
from .models import DeliveryZone
from apps.users.models import CourierProfile


class ReviewCreateSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True, default="")


class ReviewSerializer(serializers.ModelSerializer):
    from_user_name = serializers.SerializerMethodField()
    to_user_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id",
            "from_user",
            "from_user_name",
            "to_user",
            "to_user_name",
            "delivery",
            "ride",
            "rating",
            "comment",
            "created_at",
        ]

    def get_from_user_name(self, obj):
        return f"{obj.from_user.first_name} {obj.from_user.last_name}".strip()

    def get_to_user_name(self, obj):
        return f"{obj.to_user.first_name} {obj.to_user.last_name}".strip()


class DeliveryZoneListSerializer(serializers.ModelSerializer):
    darkstore_name = serializers.CharField(source="darkstore.name", read_only=True)

    class Meta:
        model = DeliveryZone
        fields = (
            "id",
            "name",
            "darkstore",
            "darkstore_name",
            "polygon",
            "is_active",
        )


class CourierOwnZoneSerializer(serializers.ModelSerializer):
    zone = DeliveryZoneListSerializer(source="delivery_zones", read_only=True)

    class Meta:
        model = CourierProfile
        fields = ("zone",)


class AssignDeliveryZoneSerializer(serializers.Serializer):
    zone_id = serializers.IntegerField()

    def validate_zone_id(self, value):
        try:
            zone = DeliveryZone.objects.get(id=value, is_active=True)
        except DeliveryZone.DoesNotExist:
            raise serializers.ValidationError("Зона не найдена или неактивна.")
        return value

    def save(self, **kwargs):
        courier_profile = self.context["courier_profile"]
        zone_id = self.validated_data["zone_id"]
        zone = DeliveryZone.objects.get(id=zone_id)

        if courier_profile.darkstore and zone.darkstore_id != courier_profile.darkstore_id:
            raise serializers.ValidationError({
                "zone_id": "Нельзя выбрать зону другого даркстора."
            })

        courier_profile.delivery_zones = zone
        courier_profile.save(update_fields=["delivery_zones"])
        return courier_profile