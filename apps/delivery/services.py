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

def find_nearest_couriers(lat, lon, limit=10, radius=5):
    write_log(f"FIND NEAREST COURIERS: lat={lat}, lon={lon}, limit={limit}, radius={radius}km")

    redis_results = RedisGeoService.find_nearest(
        user_type="courier",
        lat=lat,
        lon=lon,
        radius_km=radius,
        limit=limit,
    )
    write_log(f"REDIS RESULTS: {redis_results}")

    if not redis_results:
        write_log("WARNING: NO COURIERS FOUND IN REDIS")
        return []

    user_ids = [uid for uid, _ in redis_results]

    couriers = User.objects.filter(
        id__in=user_ids,
        worker_status__is_online=True,
        worker_status__is_busy=False,
        courier_profile__status="approved",
    ).select_related("worker_status", "courier_profile")
    write_log(f"COURIERS AFTER FILTER: {[c.id for c in couriers]}")

    couriers_map = {c.id: c for c in couriers}

    result = []
    for uid, dist in redis_results:
        courier = couriers_map.get(uid)
        if courier:
            write_log(f"COURIER {uid} PASSED FILTER, distance={dist}km")
            result.append((dist, courier))
        else:
            write_log(f"WARNING: COURIER {uid} DID NOT PASS FILTER")

    write_log(f"TOTAL COURIERS RETURNED: {len(result)}")
    return result


def mark_delivery_arrived(delivery, courier):
    with transaction.atomic():
        delivery = Delivery.objects.select_for_update().get(id=delivery.id)

        if delivery.courier_id != courier.id:
            return False, "Этот заказ не назначен данному курьеру."

        if delivery.delivery_status != "courier_assigned":
            return False, "Курьер не назначен!"

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

        now = timezone.now()

        delivery.delivery_status = "in_delivery"
        delivery.pickup_at = now

        delivery.save(update_fields=[
            "delivery_status",
            "pickup_at",
        ])

    return True, "Заказ забран"

def mark_delivery_arrived_b(delivery, user):
    if delivery.courier_id != user.id:
        return False, "Это не ваш заказ."

    if delivery.delivery_status != "in_delivery":
        return False, "Нельзя отметить прибытие в точку назначения сейчас."

    delivery.delivery_status = "courier_arrived_b"

    update_fields = ["delivery_status"]

    if hasattr(delivery, "arrived_b_at"):
        delivery.arrived_b_at = timezone.now()
        update_fields.append("arrived_b_at")

    delivery.save(update_fields=update_fields)
    return True, "Курьер прибыл в точку назначения"


def complete_delivery(delivery, courier):
    with transaction.atomic():
        delivery = Delivery.objects.select_for_update().get(id=delivery.id)

        if delivery.courier_id != courier.id:
            return False, "Этот заказ не назначен данному курьеру."

        if delivery.delivery_status not in ["courier_arrived_b"]:
            return False, "Нельзя завершить заказ сейчас."

        now = timezone.now()

        delivery.delivery_status = "delivered"
        delivery.delivered_at = now

        delivery.save(update_fields=["delivery_status", "delivered_at"])

        worker_status, _ = WorkerStatus.objects.get_or_create(user=courier)
        worker_status.is_busy = False
        worker_status.save(update_fields=["is_busy", "last_seen"])
        
        User.objects.filter(id=courier.id).update(
            orders_count=F("orders_count") + 1
        )

    return True, "Заказ доставлен"

def cancel_delivery_by_client(delivery, user):
    if delivery.client != user:
        return False, "Нельзя отменить чужой заказ"

    if delivery.status != "courier_assigned":
        return False, "Этот заказ нельзя отменить"

    delivery.status = "canceled_by_client"
    delivery.save(update_fields=["status"])
    return True, "Заказ успешно отменён"


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

    zone = courier_profile.delivery_zones

    if not zone:
        write_log(f"MATCH OK courier={courier.id}: no zone")
        return True

    if delivery.dropoff_lat is None or delivery.dropoff_lon is None:
        write_log(f"MATCH FAIL courier={courier.id}: no dropoff coords")
        return False

    result = zone.contains_point(delivery.dropoff_lat, delivery.dropoff_lon)
    write_log(
        f"MATCH courier={courier.id} zone={zone.id} "
        f"dropoff=({delivery.dropoff_lat}, {delivery.dropoff_lon}) result={result}"
    )
    return result