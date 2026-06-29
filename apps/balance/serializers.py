from rest_framework import serializers

class WalletDashboardSerializer(serializers.Serializer):
    balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    bonuses = serializers.DecimalField(max_digits=12, decimal_places=2)

    orders_count = serializers.IntegerField()
    today_income = serializers.DecimalField(max_digits=12, decimal_places=2)

    hours_on_shift = serializers.IntegerField()

    cash_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    cashless_total = serializers.DecimalField(max_digits=12, decimal_places=2)

    commission_percent = serializers.DecimalField(max_digits=5, decimal_places=2)

    
class DeliveryPaymentSerializer(serializers.Serializer):
    payment_id = serializers.CharField()
    qr = serializers.CharField(required=False, allow_null=True)
    qr_url = serializers.CharField(required=False, allow_null=True)
    deeplink = serializers.CharField(required=False, allow_null=True)


class WithdrawalRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    card_number = serializers.CharField(max_length=32)
    card_holder = serializers.CharField(max_length=255, required=False, allow_blank=True)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value
