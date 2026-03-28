from rest_framework import serializers
from .models import Review


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