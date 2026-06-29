from datetime import timedelta
from django.utils import timezone
from apps.users.models import User
from django.db.models import F
from services.geo import RedisGeoService
from assets.helpers.loggers import write_log
from django.db import transaction
from apps.delivery.models import Delivery
from apps.users.models import *
from math import radians, sin, cos, sqrt, atan2
from decimal import Decimal
from apps.balance.models import WorkerWallet, WalletTransaction, TransactionType, TransactionStatus
from .detour import mark_route_stop_arrived, complete_route_stop
from apps.payments.bonuses import *
from apps.balance.models import *
from apps.payments.models import *
from apps.payments.commission_service import *
from apps.payments.services import *
from .helpers import *


from .helpers import courier_has_min_balance


def find_nearest_couriers(
    lat,
    lon,
    limit=10,
    radius=5,
    payment_method=None,
    type_delivery=None
):

    write_log(
        f"FIND NEAREST COURIERS: "
        f"lat={lat}, lon={lon}, "
        f"limit={limit}, radius={radius}km"
    )

    redis_results = RedisGeoService.find_nearest(
        user_type="courier",
        lat=lat,
        lon=lon,
        radius_km=radius,
        limit=limit,
    )

    write_log(f"REDIS RESULTS: {redis_results}")

    if not redis_results:

        write_log(
            "WARNING: NO COURIERS FOUND IN REDIS"
        )

        return []

    user_ids = [uid for uid, _ in redis_results]

    couriers = User.objects.filter(
        id__in=user_ids,
        user_type="courier",
        worker_status__is_online=True,
        worker_status__is_busy=False,
        courier_profile__status="approved",
    ).select_related(
        "worker_status",
        "courier_profile"
    )

    write_log(
        f"COURIERS AFTER FILTER: "
        f"{[c.id for c in couriers]}"
    )

    couriers_map = {
        c.id: c for c in couriers
    }

    result = []

    for uid, dist in redis_results:

        courier = couriers_map.get(uid)

        if courier:

            if not courier_has_min_balance(
                courier=courier,
                type_delivery=type_delivery,
                payment_method=payment_method
            ):

                write_log(
                    f"COURIER {courier.id} LOW BALANCE"
                )

                continue

            write_log(
                f"COURIER {uid} PASSED FILTER, "
                f"distance={dist}km"
            )

            result.append(
                (dist, courier)
            )

        else:

            write_log(
                f"WARNING: COURIER {uid} "
                f"DID NOT PASS FILTER"
            )

    write_log(
        f"TOTAL COURIERS RETURNED: "
        f"{len(result)}"
    )

    return result

def mark_delivery_arrived(delivery, courier):
    with transaction.atomic():
        delivery = Delivery.objects.select_for_update().get(id=delivery.id)

        if delivery.courier_id != courier.id:
            return False, "Этот заказ не назначен данному курьеру."

        if delivery.delivery_status != "courier_assigned":
            return False, "Курьер не назначен!"

        ok, msg = mark_route_stop_arrived(courier, delivery, "pickup")
        if not ok:
            return False, msg

        now = timezone.now()

        delivery.delivery_status = "courier_arrived"
        delivery.arrived_at = now
        delivery.free_waiting_started_at = now

        delivery.save(update_fields=[
            "delivery_status",
            "arrived_at",
            "free_waiting_started_at",
        ])

    return True, "Курьер прибыл на точку"


def mark_delivery_picked_up(delivery, courier):
    with transaction.atomic():
        delivery = Delivery.objects.select_for_update().get(id=delivery.id)

        if delivery.courier_id != courier.id:
            return False, "Этот заказ не назначен данному курьеру."

        if delivery.delivery_status not in ["courier_arrived", "courier_assigned"]:
            return False, "Нельзя забрать заказ сейчас."

        ok, msg = complete_route_stop(courier, delivery, "pickup")
        if not ok:
            return False, msg

        now = timezone.now()

        delivery.delivery_status = "in_delivery"
        delivery.pickup_at = now

        delivery.save(update_fields=[
            "delivery_status",
            "pickup_at",
        ])

    return True, "Заказ забран"


def mark_delivery_arrived_b(delivery, user):
    with transaction.atomic():
        delivery = Delivery.objects.select_for_update().get(id=delivery.id)

        if delivery.courier_id != user.id:
            return False, "Это не ваш заказ."

        if delivery.delivery_status != "in_delivery":
            return False, "Нельзя отметить прибытие в точку назначения сейчас."

        ok, msg = mark_route_stop_arrived(user, delivery, "dropoff")
        if not ok:
            return False, msg

        delivery.delivery_status = "courier_arrived_b"

        update_fields = ["delivery_status"]

        if hasattr(delivery, "arrived_b_at"):
            delivery.arrived_b_at = timezone.now()
            update_fields.append("arrived_b_at")

        delivery.save(update_fields=update_fields)

    return True, "Курьер прибыл в точку назначения"

def complete_delivery(delivery, courier):

    commission_info = None

    with transaction.atomic():

        delivery = (
            Delivery.objects
            .select_for_update()
            .get(id=delivery.id)
        )

        if delivery.courier_id != courier.id:
            return False, "Этот заказ не назначен данному курьеру."

        if delivery.delivery_status not in ["courier_arrived_b"]:
            return False, "Нельзя завершить заказ сейчас."

        if delivery.payment_method == "card":

            payment = (
                Payment.objects
                .filter(
                    order_id=str(delivery.id),
                    type_payment="delivery"
                )
                .order_by("-id")
                .first()
            )

            if not payment:
                return False, "Платёж ещё не создан."

            if payment.status != "success":
                return False, (
                    "Заказ не оплачен. "
                    "Дождитесь поступления оплаты на счет."
                )

        ok, msg = complete_route_stop(
            courier,
            delivery,
            "dropoff"
        )

        if not ok:
            return False, msg

        now = timezone.now()

        delivery.delivery_status = "delivered"
        delivery.delivered_at = now

        delivery.save(
            update_fields=[
                "delivery_status",
                "delivered_at",
            ]
        )

        active_left = Delivery.objects.filter(
            courier=courier,
            delivery_status__in=[
                "courier_assigned",
                "courier_arrived",
                "in_delivery",
                "courier_arrived_b",
            ]
        ).exclude(id=delivery.id).exists()

        worker_status, _ = WorkerStatus.objects.get_or_create(
            user=courier
        )

        worker_status.is_busy = active_left

        worker_status.save(
            update_fields=[
                "is_busy",
                "last_seen",
            ]
        )

        User.objects.filter(
            id=courier.id
        ).update(
            orders_count=F("orders_count") + 1
        )

        courier.refresh_from_db(
            fields=["orders_count"]
        )

        process_worker_bonuses(courier)

        wallet, _ = WorkerWallet.objects.get_or_create(
            worker=courier
        )

        earning_amount = (
            getattr(delivery, "courier_fee", None)
            or delivery.price
            or Decimal("0.00")
        )

        channel = (
            "online"
            if delivery.payment_method == "card"
            else "cash"
        )

        if earning_amount > 0:

            transaction_type = (
                TransactionType.ORDER_EARNING_ONLINE
                if delivery.payment_method == "card"
                else TransactionType.ORDER_EARNING_CASH
            )

            already_exists = WalletTransaction.objects.filter(
                wallet=wallet,
                transaction_type=transaction_type,
                delivery=delivery,
            ).exists()

            if not already_exists:

                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type=transaction_type,
                    status=TransactionStatus.COMPLETED,
                    channel=channel,
                    amount=earning_amount,
                    sign=1,
                    delivery=delivery,
                    comment=f"Доход за доставку #{delivery.id}",
                )

        commission_exists = WalletTransaction.objects.filter(
            wallet=wallet,
            delivery=delivery,
            transaction_type=TransactionType.COMMISSION
        ).exists()

        if not commission_exists:

            commission_rule = (
                DeliveryCommission.objects.filter(
                    type_delivery=delivery.type_delivery,
                    payment_method=delivery.payment_method,
                    is_active=True
                ).first()
            )

            if not commission_rule:

                commission_rule = (
                    DeliveryCommission.objects.filter(
                        type_delivery=delivery.type_delivery,
                        payment_method__isnull=True,
                        is_active=True
                    ).first()
                )

            if not commission_rule:

                commission_rule = (
                    DeliveryCommission.objects.filter(
                        type_delivery=delivery.type_delivery,
                        payment_method="",
                        is_active=True
                    ).first()
                )

            if commission_rule:

                commission_amount = (
                    earning_amount *
                    commission_rule.commission_percent
                ) / Decimal("100")

                if commission_amount < commission_rule.min_commission:
                    commission_amount = commission_rule.min_commission

                if (
                    commission_rule.max_commission
                    and
                    commission_amount > commission_rule.max_commission
                ):
                    commission_amount = commission_rule.max_commission

                commission_amount = commission_amount.quantize(
                    Decimal("0.01")
                )

                commission_transaction = WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type=TransactionType.COMMISSION,
                    status=TransactionStatus.COMPLETED,
                    channel=channel,
                    amount=commission_amount,
                    sign=-1,
                    delivery=delivery,
                    comment=f"Комиссия за доставку #{delivery.id}",
                )

                transfer_response = None
                transfer_status = "failed"

                try:
                    transfer_response = NambaPayService.transfer_money(
                        amount=int(commission_amount * 100),
                        account=courier.phone,
                        comment=f"delivery:{delivery.id}"
                    )

                    if transfer_response.get("status") == "OK":
                        transfer_status = "success"
                    else:
                        transfer_status = "failed"

                except Exception as e:
                    transfer_response = {
                        "error": str(e)
                    }
                    transfer_status = "failed"

                NambaTransfer.objects.create(
                    wallet_transaction=commission_transaction,
                    amount=commission_amount,
                    status=transfer_status,
                    raw_response=transfer_response
                )

                commission_info = {
                    "percent": commission_rule.commission_percent,
                    "commission_amount": commission_amount,
                    "message": (
                        f"С вашего счёта будет списана комиссия "
                        f"{commission_rule.commission_percent}% "
                        f"({commission_amount} сом)"
                    )
                }

        else:
            commission_transaction = WalletTransaction.objects.filter(
                wallet=wallet,
                delivery=delivery,
                transaction_type=TransactionType.COMMISSION
            ).order_by("-id").first()

            if commission_transaction:
                commission_info = {
                    "percent": None,
                    "commission_amount": commission_transaction.amount,
                    "message": (
                        f"Комиссия за этот заказ уже была списана "
                        f"({commission_transaction.amount} сом)"
                    )
                }

    return True, {
        "text": "Заказ доставлен",
        "commission_info": commission_info
    }

    
def cancel_delivery_by_client(delivery, user, cancel_reason=""):

    with transaction.atomic():

        delivery = Delivery.objects.select_for_update().get(id=delivery.id)

        if delivery.client_id != user.id:
            return False, "Вы не можете отменить этот заказ."

        if delivery.delivery_status in ["delivered", "canceled"]:
            return False, "Этот заказ уже нельзя отменить."

        delivery.delivery_status = "canceled"
        delivery.cancel_reason = cancel_reason

        delivery.save(
            update_fields=[
                "delivery_status",
                "cancel_reason",
            ]
        )

        courier = delivery.courier

        if courier:

            worker_status, _ = WorkerStatus.objects.get_or_create(
                user=courier
            )

            active_left = Delivery.objects.filter(
                courier=courier,
                delivery_status__in=[
                    "courier_assigned",
                    "courier_arrived",
                    "in_delivery",
                    "courier_arrived_b",
                ]
            ).exclude(id=delivery.id).exists()

            worker_status.is_busy = active_left

            worker_status.save(
                update_fields=["is_busy", "last_seen"]
            )

    return True, "Заказ успешно отменен"

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return r * c


def estimate_eta_seconds(distance_km: float, speed_kmh: float = 25.0) -> int:
    if distance_km <= 0:
        return 0
    return max(60, int((distance_km / speed_kmh) * 3600))


def build_eta_data(from_lat: float, from_lon: float, to_lat: float, to_lon: float, speed_kmh: float = 25.0) -> dict:
    distance_km = haversine_km(from_lat, from_lon, to_lat, to_lon)
    eta_sec = estimate_eta_seconds(distance_km, speed_kmh=speed_kmh)

    return {
        "distance_km": round(distance_km, 2),
        "eta_sec": eta_sec,
    }

    
def courier_matches_delivery(delivery, courier):
    courier_profile = getattr(courier, "courier_profile", None)
    if not courier_profile:
        write_log(f"MATCH FAIL courier={courier.id}: no profile")
        return False

    delivery_darkstore_id = getattr(delivery, "darkstore_id", None)
    courier_darkstore_id = courier_profile.darkstore_id

    if delivery_darkstore_id:
        if courier_darkstore_id != delivery_darkstore_id:
            write_log(
                f"MATCH FAIL courier={courier.id}: "
                f"courier_darkstore={courier_darkstore_id} "
                f"delivery_darkstore={delivery_darkstore_id}"
            )
            return False

    if delivery.type_transport and courier_profile.transport_type != delivery.type_transport:
        write_log(
            f"MATCH FAIL courier={courier.id}: "
            f"courier_transport={courier_profile.transport_type} "
            f"delivery_transport={delivery.type_transport}"
        )
        return False

    zone = courier_profile.delivery_zones

    if not zone:
        write_log(f"MATCH OK courier={courier.id}: no zone restriction")
        return True

    if delivery.dropoff_lat is None or delivery.dropoff_lon is None:
        write_log(f"MATCH FAIL courier={courier.id}: no dropoff coords")
        return False

    result = zone.contains_point(delivery.dropoff_lat, delivery.dropoff_lon)

    write_log(
        f"MATCH courier={courier.id} "
        f"zone_id={zone.id} "
        f"dropoff_lat={delivery.dropoff_lat} "
        f"dropoff_lon={delivery.dropoff_lon} "
        f"result={result}"
    )

    return result