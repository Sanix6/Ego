from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from apps.delivery.models import Delivery
from apps.taxi.models import TaxiRide
from .services import PaymentService
from decimal import Decimal
from django.db.models import Sum, F, DecimalField, ExpressionWrapper, Q
from rest_framework import generics, status

from .models import WorkerWallet, WalletTransaction
from .serializers import *
from .choices import *


class WalletDashboardView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WalletDashboardSerializer

    def get(self, request, *args, **kwargs):
        wallet, _ = WorkerWallet.objects.get_or_create(worker=request.user)

        signed_amount_expr = ExpressionWrapper(
            F("amount") * F("sign"),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )

        completed_transactions = WalletTransaction.objects.filter(
            wallet=wallet,
            status=TransactionStatus.COMPLETED
        )

        balance = completed_transactions.aggregate(
            total=Sum(signed_amount_expr)
        )["total"] or Decimal("0.00")

        total_income = completed_transactions.filter(
            transaction_type=TransactionType.ORDER_EARNING,
            sign=1
        ).aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00")

        cash_total = completed_transactions.filter(
            transaction_type=TransactionType.ORDER_EARNING,
            sign=1,
            channel=PaymentChannel.CASH
        ).aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00")

        cashless_total = completed_transactions.filter(
            transaction_type=TransactionType.ORDER_EARNING,
            sign=1
        ).exclude(
            channel=PaymentChannel.CASH
        ).aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00")

        data = {
            "balance": balance,
            "total_income": total_income,
            "bonuses": Decimal("0.00"),
            "orders_count": getattr(request.user, "orders_count", 0) or 0,
            "hours_on_shift": 0,
            "cash_total": cash_total,
            "cashless_total": cashless_total,
        }

        serializer = self.get_serializer(data)
        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)


class CreateDeliveryPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, delivery_id):
        delivery = get_object_or_404(
            Delivery,
            id=delivery_id,
            client=request.user
        )

        try:
            payment = PaymentService().create_delivery_payment(delivery)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        delivery.payment_status = "pending"
        delivery.save(update_fields=["payment_status"])

        return Response(
            {
                "delivery_id": delivery.id,
                "amount": str(payment.amount),
                "payment_id": payment.id,
                "external_payment_id": payment.external_payment_id,
                "qr_url": payment.qr_url,
                "deeplink": payment.deeplink,
                "status": payment.status,
                "mkassa_response": payment.raw_init_response,
            },
            status=status.HTTP_200_OK
        )


class CreateTaxiPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, ride_id):
        ride = get_object_or_404(
            TaxiRide,
            id=ride_id,
            client=request.user
        )

        try:
            payment = PaymentService().create_taxi_payment(ride)
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        ride.payment_status = "pending"
        ride.save(update_fields=["payment_status"])

        return Response(
            {
                "ride_id": ride.id,
                "amount": str(payment.amount),
                "payment_id": payment.id,
                "external_payment_id": payment.external_payment_id,
                "qr_url": payment.qr_url,
                "deeplink": payment.deeplink,
                "status": payment.status,
                "mkassa_response": payment.raw_init_response,
            },
            status=status.HTTP_200_OK
        )