from rest_framework import serializers


class CreatePaymentSerializer(serializers.Serializer):
    type_payment = serializers.CharField()
    order_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)


class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value