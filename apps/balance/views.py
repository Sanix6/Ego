from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from apps.delivery.models import Delivery
from apps.taxi.models import TaxiRide
from .services import *
from django.db.models.functions import Coalesce
from decimal import Decimal
from django.db.models import Sum, F, DecimalField, ExpressionWrapper, Q
from rest_framework import generics, status

from .models import WorkerWallet, WalletTransaction
from .serializers import *
from .choices import *
from .models import *
from decimal import Decimal
from django.db.models import Sum, Q
from django.utils import timezone
from apps.main.models import *


class WalletDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WalletDashboardSerializer

    def get(self, request, *args, **kwargs):
        worker = request.user
        wallet, _ = WorkerWallet.objects.get_or_create(worker=worker)

        today = timezone.localdate()

        today_transactions = wallet.transactions.filter(
            status=TransactionStatus.COMPLETED,
            sign=1,
            created_at__date=today,
        )

        orders_count = today_transactions.filter(
            Q(taxi_ride__isnull=False) |
            Q(delivery__isnull=False)
        ).count()

        today_income = today_transactions.aggregate(
            total=Coalesce(Sum("amount"), Decimal("0.00"))
        )["total"]

        commission_percent = Decimal("0.00")

        if worker.user_type == "courier":
            delivery_profile = getattr(worker, "delivery_profile", None)

            type_delivery = getattr(delivery_profile, "type_delivery", None)

            commission = DeliveryCommission.objects.filter(
                is_active=True,
                type_delivery=type_delivery,
            ).filter(
                Q(payment_method__isnull=True) |
                Q(payment_method="")
            ).order_by("-id").first()

            if commission:
                commission_percent = commission.commission_percent

        elif worker.user_type == "driver":
            driver_profile = getattr(worker, "driver_profile", None)

            car_class = getattr(driver_profile, "car_class", None)

            commission = TaxiCommission.objects.filter(
                is_active=True,
                car_class=car_class,
            ).filter(
                Q(payment_method__isnull=True) |
                Q(payment_method="")
            ).order_by("-id").first()

            if commission:
                commission_percent = commission.commission_percent

        data = {
            "balance": wallet.balance,
            "total_income": wallet.total_earnings,
            "bonuses": wallet.total_bonuses,

            "orders_count": orders_count,
            "today_income": today_income,

            "hours_on_shift": 0,

            "cash_total": wallet.cash_earnings,
            "cashless_total": wallet.online_earnings,

            "commission_percent": commission_percent,
        }

        serializer = self.get_serializer(data)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

        

class WithdrawalRequestCreateAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WithdrawalRequestSerializer

    def post(self, request, *args, **kwargs):
        user = request.user

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]
        card_number = serializer.validated_data["card_number"]
        card_holder = serializer.validated_data.get("card_holder")

        wallet = WorkerWallet.objects.filter(worker=user).first()

        if not wallet:
            return Response(
                {"error": "Wallet not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if wallet.balance < amount:
            return Response({"error": "Нехватает средств в вашем балансе"}, status=400)

        withdrawal = WithdrawalRequest.objects.create(
            wallet=wallet,
            amount=amount,
            card_number=card_number,
            card_holder=card_holder,
            status="pending"
        )

        return Response(
            {
                "id": withdrawal.id,
                "status": withdrawal.status,
                "amount": withdrawal.amount,
                "card_number": withdrawal.card_number,
            },
            status=status.HTTP_201_CREATED
        )


class WalletHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet = request.user.wallet

        topups = wallet.transactions.filter(
            status="COMPLETED",
            sign=1
        )

        withdrawals = wallet.withdrawal_requests.all()

        history = []
        for t in topups:
            history.append({
                "type": "topup",
                "status": t.status.lower(),
                "amount": str(t.amount),
                "date": format_date(t.created_at),
                "created_at": t.created_at
            })

        for w in withdrawals:
            history.append({
                "type": "withdrawal",
                "status": w.status.lower(),
                "amount": str(w.amount),
                "date": format_date(w.created_at),
                "created_at": w.created_at
            })

        history.sort(key=lambda x: x["created_at"], reverse=True)

        for i in history:
            i.pop("created_at")

        return Response({
            "balance": wallet.balance,
            "results": history
        })