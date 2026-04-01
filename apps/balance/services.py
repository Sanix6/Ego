import os
import requests
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from datetime import datetime

from .models import OrderPayment, PaymentMethod, PaymentStatus, PaymentProvider

LOG_PATH = "logs/mkassa.logs"


def mkassa_log(message):
    os.makedirs("logs", exist_ok=True)

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} | {message}\n")


MKASSA_BASE_URL = os.getenv("MKASSA_BASE_URL", "https://api.mkassa.kg")
MKASSA_LOGIN = os.getenv("MKASSA_LOGIN")
MKASSA_PASSWORD = os.getenv("MKASSA_PASSWORD")
MKASSA_DEVICE_UUID = os.getenv("MKASSA_DEVICE_UUID", "PI")


class MKassaClient:
    TOKEN_CACHE_KEY = "mkassa:token"
    TOKEN_TTL = 55 * 60

    def __init__(self):
        self.login = MKASSA_LOGIN
        self.password = MKASSA_PASSWORD
        self.device_uuid = MKASSA_DEVICE_UUID

        if not self.login or not self.password:
            raise Exception("MKASSA_LOGIN или MKASSA_PASSWORD не заданы")

    def _login_and_cache_token(self) -> str:
        url = f"{MKASSA_BASE_URL}/api/users/login/"
        data = {
            "login": self.login,
            "password": self.password,
            "device_uuid": self.device_uuid,
        }

        mkassa_log(f"LOGIN REQUEST: login={self.login}, device_uuid={self.device_uuid}")

        response = requests.post(url, data=data, timeout=15)

        mkassa_log(f"LOGIN RESPONSE STATUS: {response.status_code}")
        mkassa_log(f"LOGIN RESPONSE BODY: {response.text}")

        response.raise_for_status()

        result = response.json()
        token = result.get("token")

        if not token:
            mkassa_log(f"LOGIN ERROR: {result}")
            raise Exception(f"Ошибка авторизации MKassa: {result}")

        cache.set(self.TOKEN_CACHE_KEY, token, timeout=self.TOKEN_TTL)
        mkassa_log("TOKEN SAVED TO REDIS")

        return token

    def auth(self, force_refresh: bool = False) -> str:
        if force_refresh:
            cache.delete(self.TOKEN_CACHE_KEY)
            mkassa_log("TOKEN DELETED FROM REDIS (force_refresh=True)")

        token = cache.get(self.TOKEN_CACHE_KEY)
        if token:
            mkassa_log("TOKEN LOADED FROM REDIS")
            return token

        mkassa_log("TOKEN NOT FOUND IN REDIS. LOGIN STARTED")
        return self._login_and_cache_token()

    def _request(self, method: str, path: str, retry_on_401: bool = True, **kwargs):
        token = self.auth()
        url = f"{MKASSA_BASE_URL}{path}"

        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"

        if "json" in kwargs:
            headers["Content-Type"] = "application/json"

        mkassa_log(f"REQUEST {method} {url}")
        mkassa_log(f"REQUEST HEADERS: {headers}")
        if "json" in kwargs:
            mkassa_log(f"REQUEST JSON: {kwargs['json']}")
        if "data" in kwargs:
            mkassa_log(f"REQUEST DATA: {kwargs['data']}")

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            timeout=15,
            **kwargs
        )

        mkassa_log(f"RESPONSE STATUS: {response.status_code}")
        mkassa_log(f"RESPONSE BODY: {response.text}")

        if response.status_code == 401 and retry_on_401:
            mkassa_log("401 RECEIVED. TRYING TOKEN REFRESH")

            new_token = self.auth(force_refresh=True)
            headers["Authorization"] = f"Bearer {new_token}"

            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=15,
                **kwargs
            )

            mkassa_log(f"RETRY RESPONSE STATUS: {response.status_code}")
            mkassa_log(f"RETRY RESPONSE BODY: {response.text}")

        response.raise_for_status()
        return response

    def create_payment(self, amount: float, currency: str = "KGS"):
        payload = {
            "payment_amount": {
                "value": int(amount),
                "currency": currency,
            }
        }

        mkassa_log(f"CREATE PAYMENT REQUEST: {payload}")

        response = self._request(
            method="POST",
            path="/api/v1/qr_payments/init_payment/",
            json=payload,
        )

        mkassa_log(f"CREATE PAYMENT RESPONSE: {response.text}")
        return response.json()

    def check_payment(self, payment_id: str):
        mkassa_log(f"CHECK PAYMENT REQUEST: payment_id={payment_id}")

        response = self._request(
            method="GET",
            path=f"/api/qr_payments/{payment_id}/check",
        )

        mkassa_log(f"CHECK PAYMENT RESPONSE: {response.text}")
        return response.json()


class PaymentService:
    def __init__(self):
        self.client = MKassaClient()

    @transaction.atomic
    def create_taxi_payment(self, ride):
        if ride.payment_method != "mbank":
            raise ValueError("Для online-оплаты у заказа должен быть payment_method='mbank'")

        if ride.payment_status == "paid":
            raise ValueError("Заказ уже оплачен")

        amount = ride.total_price or ride.price or ride.estimated_price
        if not amount or amount <= 0:
            raise ValueError("Сумма оплаты не найдена")

        existing_payment = ride.payments.filter(status=PaymentStatus.PENDING).first()
        if existing_payment:
            return existing_payment

        mkassa_response = self.client.create_payment(
            amount=float(amount),
            currency="KGS"
        )

        payment = OrderPayment.objects.create(
            taxi_ride=ride,
            provider=PaymentProvider.MKASSA,
            payment_method=PaymentMethod.MBANK,
            status=PaymentStatus.PENDING,
            amount=amount,
            currency="KGS",
            external_payment_id=mkassa_response.get("id") or mkassa_response.get("payment_id"),
            qr_url=mkassa_response.get("qr_url") or mkassa_response.get("qr"),
            deeplink=mkassa_response.get("deeplink"),
            raw_init_response=mkassa_response,
        )
        return payment

    @transaction.atomic
    def create_delivery_payment(self, delivery):
        if delivery.payment_method != "mbank":
            raise ValueError("Для online-оплаты у заказа должен быть payment_method='mbank'")

        if delivery.payment_status == "paid":
            raise ValueError("Заказ уже оплачен")

        amount = delivery.price
        if not amount or amount <= 0:
            raise ValueError("Сумма оплаты не найдена")

        existing_payment = delivery.payments.filter(status=PaymentStatus.PENDING).first()
        if existing_payment:
            return existing_payment

        mkassa_response = self.client.create_payment(
            amount=float(amount),
            currency="KGS"
        )

        payment = OrderPayment.objects.create(
            delivery=delivery,
            provider=PaymentProvider.MKASSA,
            payment_method=PaymentMethod.MBANK,
            status=PaymentStatus.PENDING,
            amount=amount,
            currency="KGS",
            external_payment_id=mkassa_response.get("id") or mkassa_response.get("payment_id"),
            qr_url=mkassa_response.get("qr_url") or mkassa_response.get("qr"),
            deeplink=mkassa_response.get("deeplink"),
            raw_init_response=mkassa_response,
        )

        return payment

    @transaction.atomic
    def sync_payment_status(self, payment: OrderPayment):
        if not payment.external_payment_id:
            raise ValueError("У платежа нет external_payment_id")

        result = self.client.check_payment(payment.external_payment_id)
        payment.raw_check_response = result

        remote_status = result.get("status")

        if remote_status in ["paid", "success", "completed"]:
            payment.status = PaymentStatus.PAID
            payment.paid_at = timezone.now()

            if payment.taxi_ride_id:
                payment.taxi_ride.payment_status = "paid"
                payment.taxi_ride.save(update_fields=["payment_status"])

            if payment.delivery_id:
                payment.delivery.payment_status = "paid"
                payment.delivery.save(update_fields=["payment_status"])

        elif remote_status in ["canceled", "cancelled"]:
            payment.status = PaymentStatus.CANCELED

        elif remote_status in ["failed", "error"]:
            payment.status = PaymentStatus.FAILED

        payment.save(update_fields=["status", "paid_at", "raw_check_response", "updated_at"])
        return payment