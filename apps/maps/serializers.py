from rest_framework import serializers


class GeocodeSerializer(serializers.Serializer):
    address = serializers.CharField(max_length=500)


class ReverseGeocodeSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lon = serializers.FloatField()


class SuggestQuerySerializer(serializers.Serializer):
    text = serializers.CharField(max_length=255)
    ll = serializers.CharField(required=False)
    ull = serializers.CharField(required=False)