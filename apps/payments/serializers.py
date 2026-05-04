from rest_framework import serializers


class CreatePaymentSerializer(serializers.Serializer):
    type_payment = serializers.CharField()
    order_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)