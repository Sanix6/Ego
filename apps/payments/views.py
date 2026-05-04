from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Payment
import uuid
from django.conf import settings
from .serializers import CreatePaymentSerializer
from .services import NambaPayService
from .models import Payment
from rest_framework.generics import CreateAPIView
from decimal import Decimal
from rest_framework.permissions import IsAuthenticated

from decimal import Decimal
import traceback


class CreatePaymentView(CreateAPIView):
    serializer_class = CreatePaymentSerializer
    queryset = Payment.objects.all()
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data["order_id"]
        amount = serializer.validated_data["amount"]
        type_payment = serializer.validated_data["type_payment"]

        external_id = str(uuid.uuid4())

        payment = Payment.objects.create(
            user=request.user,
            type_payment=type_payment,
            order_id=order_id,
            amount=amount,
            external_id=external_id,
            status="pending"
        )

        try:
            response = NambaPayService.create_payment(
                amount=int(Decimal(amount) * 100),
                external_id=external_id,
                webhook_url=f"{settings.DOMAIN}/api/payments/webhook/namba/"
            )

            if response.get("status") != "OK":
                raise Exception(response)

            payment.payment_link = response["data"]["token"]
            payment.save()

            return Response({
                "payment_url": payment.payment_link,
                "external_id": external_id
            })

        except Exception as e:
            traceback.print_exc()

            payment.status = "failed"
            payment.save()

            return Response(
                {"error": str(e)},
                status=400
            )


class NambaWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        data = request.data.get("data", {})

        external_id = data.get("externalId")
        payment_status = data.get("status")

        payment = Payment.objects.filter(
            external_id=external_id
        ).first()

        if not payment:
            return Response({"error": "not found"}, status=404)

        if payment_status == "COMPLETED":
            payment.status = "success"
        elif payment_status in ["FAILED", "CANCELED", "EXPIRED"]:
            payment.status = "failed"

        payment.save()

        return Response({"ok": True}, status=200)