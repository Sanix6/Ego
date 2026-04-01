from rest_framework import serializers


class DeliveryPaymentSerializer(serializers.Serializer):
    payment_id = serializers.CharField()
    qr = serializers.CharField(required=False, allow_null=True)
    qr_url = serializers.CharField(required=False, allow_null=True)
    deeplink = serializers.CharField(required=False, allow_null=True)