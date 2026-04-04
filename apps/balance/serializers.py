from rest_framework import serializers


class WalletDashboardSerializer(serializers.Serializer):
    balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    bonuses = serializers.DecimalField(max_digits=12, decimal_places=2)
    orders_count = serializers.IntegerField()
    hours_on_shift = serializers.IntegerField()
    cash_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    cashless_total = serializers.DecimalField(max_digits=12, decimal_places=2)

class DeliveryPaymentSerializer(serializers.Serializer):
    payment_id = serializers.CharField()
    qr = serializers.CharField(required=False, allow_null=True)
    qr_url = serializers.CharField(required=False, allow_null=True)
    deeplink = serializers.CharField(required=False, allow_null=True)