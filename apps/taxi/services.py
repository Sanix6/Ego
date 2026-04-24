from apps.users.models import User
from services.geo import RedisGeoService
from assets.helpers.loggers import write_log
from django.utils import timezone
from .models import TaxiRide
from .serializers import TaxiRideDetailSerializer
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction



def find_nearest_drivers(lat, lon, limit=10, radius=5):
    write_log(f"FIND NEAREST DRIVERS: lat={lat}, lon={lon}, limit={limit}, radius={radius}km")

    redis_results = RedisGeoService.find_nearest(
        user_type="driver",
        lat=lat,
        lon=lon,
        radius_km=radius,
        limit=limit,
    )
    write_log(f"REDIS RESULTS: {redis_results}")

    if not redis_results:
        write_log("WARNING: NO DRIVERS FOUND IN REDIS")
        return []

    user_ids = [uid for uid, _ in redis_results]

    drivers = User.objects.filter(
        id__in=user_ids,
        user_type="driver",
        worker_status__is_online=True,
        worker_status__is_busy=False,
        driver_profile__status="approved",
    ).select_related("worker_status", "driver_profile")

    write_log(f"DRIVERS AFTER FILTER: {[d.id for d in drivers]}")

    drivers_map = {d.id: d for d in drivers}

    result = []
    for uid, dist in redis_results:
        driver = drivers_map.get(uid)
        if driver:
            write_log(f"DRIVER {uid} PASSED FILTER, distance={dist}km")
            result.append((dist, driver))
        else:
            write_log(f"WARNING: DRIVER {uid} DID NOT PASS FILTER")

    write_log(f"TOTAL DRIVERS RETURNED: {len(result)}")
    return result



def mark_taxi_arrived(taxi, user):
    if taxi.driver_id != user.id:
        return False, "Это не ваша поездка."

    if taxi.status not in ["accepted", "driver_assigned"]:
        return False, "Нельзя отметить прибытие сейчас."

    taxi.status = "arrived"
    taxi.save(update_fields=["status"])
    return True, "Водитель прибыл"


def mark_taxi_in_trip(taxi, user):
    if taxi.driver_id != user.id:
        return False, "Это не ваша поездка."

    if taxi.status != "arrived":
        return False, "Нельзя начать поездку сейчас."

    taxi.status = "in_trip"

    if hasattr(taxi, "pickup_at"):
        taxi.pickup_at = timezone.now()
        taxi.save(update_fields=["status", "pickup_at"])
    else:
        taxi.save(update_fields=["status"])

    return True, "Поездка началась"


def complete_taxi_trip(taxi, user):
    if taxi.driver_id != user.id:
        return False, "Это не ваша поездка."

    if taxi.status != "in_trip":
        return False, "Нельзя завершить поездку сейчас."

    taxi.status = "completed"

    if hasattr(taxi, "completed_at"):
        taxi.completed_at = timezone.now()
        taxi.save(update_fields=["status", "completed_at"])
    elif hasattr(taxi, "delivered_at"):
        taxi.delivered_at = timezone.now()
        taxi.save(update_fields=["status", "delivered_at"])
    else:
        taxi.save(update_fields=["status"])

    return True, "Поездка завершена"


def taxi_action_response(request, taxi_id, action_func):
    user = request.user

    if user.user_type != "driver":
        return Response(
            {"success": False, "message": "Только водитель"},
            status=status.HTTP_403_FORBIDDEN
        )

    taxi = TaxiRide.objects.filter(id=taxi_id).first()
    if not taxi:
        return Response(
            {"success": False, "message": "Поездка не найдена"},
            status=status.HTTP_404_NOT_FOUND
        )

    success, message = action_func(taxi, user)

    if not success:
        return Response(
            {"success": False, "message": message},
            status=status.HTTP_400_BAD_REQUEST
        )

    taxi.refresh_from_db()
    serializer = TaxiRideDetailSerializer(taxi)

    return Response(
        {"success": True, "message": message, "data": serializer.data}
    )



def cancel_taxi_by_client(taxi, user, cancel_reason=""):
    with transaction.atomic():
        taxi = TaxiRide.objects.select_for_update().get(id=taxi.id)

        if taxi.client_id != user.id:
            return False, "Вы не можете отменить эту поездку."

        if taxi.status in ["completed", "canceled"]:
            return False, "Эту поездку уже нельзя отменить."

        taxi.status = "canceled"
        taxi.canceled_by = "client"
        taxi.cancel_reason = cancel_reason
        taxi.canceled_at = timezone.now()
        taxi.save(update_fields=["status", "canceled_by", "cancel_reason", "canceled_at"])

    return True, "Поездка успешно отменена"