from apps.users.models import User
from services.geo import RedisGeoService
from assets.helpers.loggers import write_log
from django.utils import timezone
from .models import TaxiRide
from .serializers import TaxiRideDetailSerializer
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from apps.payments.bonuses import process_worker_bonuses
from apps.balance.models import *
from apps.payments.models import *
from apps.payments.commission_service import *
from .helpers import *
from decimal import Decimal
from django.db.models import Q



def find_nearest_drivers(
    lat,
    lon,
    limit=10,
    radius=5,
    payment_method=None,
    car_class=None
):
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
            if not driver_has_min_balance(
                driver=driver,
                car_class=car_class,
                payment_method=payment_method
            ):

                write_log(
                    f"DRIVER {driver.id} LOW BALANCE"
                )

                continue

            result.append((dist, driver))
        else:
            write_log(f"WARNING: DRIVER {uid} DID NOT PASS FILTER")

    write_log(f"TOTAL DRIVERS RETURNED: {len(result)}")
    return result



def mark_taxi_arrived(taxi, user):

    if taxi.driver_id != user.id:
        return False, "Это не ваша поездка."

    if taxi.status not in ["accepted", "assigned"]:
        return False, "Нельзя отметить прибытие сейчас."

    taxi.status = "arrived"
    taxi.arrived_at = timezone.now()

    taxi.save(update_fields=[
        "status",
        "arrived_at",
    ])

    return True, "Водитель прибыл"


def mark_taxi_in_trip(taxi, user):

    if taxi.driver_id != user.id:
        return False, "Это не ваша поездка."

    if taxi.status != "arrived":
        return False, "Нельзя начать поездку сейчас."

    taxi.status = "in_trip"
    taxi.started_at = timezone.now()

    taxi.save(update_fields=[
        "status",
        "started_at",
    ])

    return True, "Поездка началась"

def complete_taxi_trip(taxi, user):

    if taxi.driver_id != user.id:
        return False, "Это не ваша поездка."

    if taxi.status != "in_trip":
        return False, "Нельзя завершить поездку сейчас."

    payment = (
        Payment.objects
        .filter(
            order_id=str(taxi.id),
            type_payment="taxi"
        )
        .order_by("-id")
        .first()
    )

    if taxi.payment_method == "card":

        if not payment:
            return False, "Платёж ещё не создан."

        if payment.status != "success":
            return False, "Поездка не оплачена."

    taxi.status = "completed"

    now = timezone.now()

    if hasattr(taxi, "completed_at"):
        taxi.completed_at = now
        taxi.save(update_fields=["status", "completed_at"])

    elif hasattr(taxi, "delivered_at"):
        taxi.delivered_at = now
        taxi.save(update_fields=["status", "delivered_at"])

    else:
        taxi.save(update_fields=["status"])

    driver = user

    if hasattr(driver, "worker_status"):
        driver.worker_status.is_busy = False
        driver.worker_status.save(update_fields=["is_busy"])

    driver.orders_count += 1
    driver.save(update_fields=["orders_count"])

    process_worker_bonuses(driver)

    CommissionService.process_taxi_commission(taxi)

    taxi.refresh_from_db()

    commission = (
        TaxiCommission.objects
        .filter(
            is_active=True,
            car_class=taxi.car_class,
        )
        .filter(
            Q(payment_method=taxi.payment_method) |
            Q(payment_method__isnull=True) |
            Q(payment_method="")
        )
        .order_by(
            "-payment_method",
            "-id"
        )
        .first()
    )

    commission_percent = Decimal("0.00")

    if commission:
        commission_percent = commission.commission_percent

    commission_amount = getattr(taxi, "commission_amount", Decimal("0.00")) or Decimal("0.00")

    return True, {
        "text": "Поездка завершена",
        "commission_info": {
            "percent": commission_percent,
            "commission_amount": commission_amount,
            "message": (
                f"С вашего счёта будет списана комиссия "
                f"{commission_percent}% от суммы поездки."
            )
        }
    }



def taxi_action_response(request, taxi_id, action_func, notify_func=None):
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

    success, result = action_func(taxi, user)

    if not success:
        return Response(
            {"success": False, "message": result},
            status=status.HTTP_400_BAD_REQUEST
        )

    if notify_func:
        notify_func(taxi)

    taxi.refresh_from_db()
    serializer = TaxiRideDetailSerializer(taxi)

    message = result
    commission_info = None

    if isinstance(result, dict):
        message = result.get("text", "Успешно")
        commission_info = result.get("commission_info")

    response_data = {
        "success": True,
        "message": message,
        "data": serializer.data,
    }

    if commission_info:
        response_data["commission_info"] = commission_info

    return Response(response_data)



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

        taxi.save(
            update_fields=[
                "status",
                "canceled_by",
                "cancel_reason",
                "canceled_at",
            ]
        )

        driver = taxi.driver

        if driver and hasattr(driver, "worker_status"):

            driver.worker_status.is_busy = False

            driver.worker_status.save(
                update_fields=["is_busy"]
            )

    return True, "Поездка успешно отменена"