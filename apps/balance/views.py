from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from apps.delivery.models import Delivery
from apps.taxi.models import TaxiRide
from .services import PaymentService


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