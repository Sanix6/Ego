import requests
import uuid
import json
from django.conf import settings
from .signature import NambaSignatureService


class NambaPayService:

    @staticmethod
    def create_payment(amount, external_id, webhook_url):
        path = f"/public/merchant/payment/v1/{settings.NAMBA_MERCHANT_ID}/one-time"
        url = f"{settings.NAMBA_BASE_URL}{path}"

        payload = {
            "externalId": external_id,
            "webhookUrl": webhook_url,
            "amount": str(amount),
            "amountCanBeChanged": False
        }

        body = json.dumps(payload, separators=(',', ':'))

        salt = str(uuid.uuid4())

        signature = NambaSignatureService.generate_signature(
            secret=settings.NAMBA_SECRET,
            path=path,
            body=body,
            salt=salt
        )

        headers = {
            "Content-Type": "application/json",
            "x-merchant-api-salt": salt,
            "x-merchant-api-signature": signature
        }

        response = requests.post(url, data=body, headers=headers, timeout=15)
        response.raise_for_status()

        return response.json()

    @staticmethod
    def check_payment(external_id):
        path = f"/public/merchant/payment/v1/{settings.NAMBA_MERCHANT_ID}/one-time/{external_id}"
        url = f"{settings.NAMBA_BASE_URL}{path}"

        salt = str(uuid.uuid4())

        signature = NambaSignatureService.generate_signature(
            secret=settings.NAMBA_SECRET,
            path=path,
            body="",  # 🔥 ВАЖНО: пустое тело
            salt=salt
        )

        headers = {
            "x-merchant-api-salt": salt,
            "x-merchant-api-signature": signature
        }

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        return response.json()