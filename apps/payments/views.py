from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from .models import Payment
import uuid
from django.conf import settings
from .serializers import *
from .services import NambaPayService, NambaDriverPayService
from rest_framework.generics import CreateAPIView
from decimal import Decimal
from rest_framework.permissions import IsAuthenticated
from apps.payments.webhook import *
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
                webhook_url="https://ego.kg/api/payment/webhook/namba/"
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



class DepositAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DepositSerializer

    def post(self, request, *args, **kwargs):
        user = request.user

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]

        external_id = str(uuid.uuid4())

        payment = Payment.objects.create(
            user=user,
            order_id=None,
            amount=amount,
            type_payment="deposit",
            external_id=external_id,
            status="pending"
        )

        try:
            response = NambaDriverPayService.create_payment(
                amount=int(Decimal(amount) * 100),
                external_id=external_id,
                webhook_url=settings.NAMBA_WEBHOOK_URL
            )

            if response.get("status") != "OK":
                raise Exception(response)

            payment.payment_link = response["data"]["token"]
            payment.save()

            return Response({
                "payment_url": payment.payment_link,
                "external_id": external_id
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            payment.status = "failed"
            payment.save()

            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class NambaWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        try:
            write_payment_log(
                f"[WEBHOOK] RAW DATA: {request.data}"
            )

            data = request.data.get("data", {})

            external_id = data.get("externalId")
            payment_status = data.get("status")

            write_payment_log(
                f"[WEBHOOK] external_id={external_id} "
                f"status={payment_status}"
            )

            if not external_id:
                write_payment_log(
                    "[WEBHOOK] external_id is empty"
                )

                return Response(
                    {"error": "external_id required"},
                    status=400
                )

            with transaction.atomic():

                payment = (
                    Payment.objects
                    .select_for_update()
                    .filter(external_id=external_id)
                    .first()
                )

                if not payment:
                    write_payment_log(
                        f"[WEBHOOK] PAYMENT NOT FOUND "
                        f"external_id={external_id}"
                    )

                    return Response(
                        {"error": "not found"},
                        status=404
                    )

                write_payment_log(
                    f"[WEBHOOK] PAYMENT FOUND "
                    f"payment_id={payment.id} "
                    f"current_status={payment.status}"
                )

                if payment.status in ["success", "failed"]:
                    write_payment_log(
                        f"[WEBHOOK] SKIP already processed "
                        f"payment_id={payment.id}"
                    )

                    return Response({"ok": True})

                if payment_status == "COMPLETED":

                    payment.status = "success"

                    payment.save(
                        update_fields=["status"]
                    )

                    write_payment_log(
                        f"[WEBHOOK] payment_id={payment.id} "
                        f"marked SUCCESS"
                    )

                    handle_payment_success(payment)

                elif payment_status in [
                    "FAILED",
                    "CANCELED",
                    "EXPIRED"
                ]:

                    payment.status = "failed"

                    payment.save(
                        update_fields=["status"]
                    )

                    write_payment_log(
                        f"[WEBHOOK] payment_id={payment.id} "
                        f"marked FAILED"
                    )

                else:
                    write_payment_log(
                        f"[WEBHOOK] UNKNOWN STATUS "
                        f"{payment_status}"
                    )

            return Response(
                {"ok": True},
                status=200
            )

        except Exception as e:
            write_payment_log(
                f"[WEBHOOK] ERROR: {str(e)}"
            )

            return Response(
                {"error": str(e)},
                status=500
            )