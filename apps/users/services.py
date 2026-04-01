from django.db import transaction

from .models import (
    WorkerStatus,
    WorkerLocation,
    CourierProfile,
    DriverProfile,
)


@transaction.atomic
def save_courier_dispatch(user, cleaned_data):
    user.user_type = "courier"
    user.save()

    worker_status, _ = WorkerStatus.objects.get_or_create(user=user)
    worker_status.is_online = cleaned_data.get("is_online", False)
    worker_status.is_busy = cleaned_data.get("is_busy", False)
    worker_status.save()

    lat = cleaned_data.get("lat")
    lon = cleaned_data.get("lon")

    if lat is not None and lon is not None:
        worker_location, _ = WorkerLocation.objects.get_or_create(
            user=user,
            defaults={"lat": lat, "lon": lon},
        )
        worker_location.lat = lat
        worker_location.lon = lon
        worker_location.save()

    courier_profile, _ = CourierProfile.objects.get_or_create(
        user=user,
        defaults={
            "transport_type": cleaned_data.get("transport_type") or "bike",
            "status": cleaned_data.get("courier_profile_status") or "pending",
        }
    )

    transport_type = cleaned_data.get("transport_type") or courier_profile.transport_type or "bike"

    courier_profile.status = cleaned_data.get("courier_profile_status") or courier_profile.status
    courier_profile.transport_type = transport_type
    courier_profile.darkstore = cleaned_data.get("darkstore")

    if transport_type in ("car", "auto"):
        courier_profile.car_brand = cleaned_data.get("car_brand", "")
        courier_profile.car_model = cleaned_data.get("car_model", "")
        courier_profile.car_color = cleaned_data.get("car_color", "")
        courier_profile.car_number = cleaned_data.get("car_number", "")
    else:
        courier_profile.car_brand = ""
        courier_profile.car_model = ""
        courier_profile.car_color = ""
        courier_profile.car_number = ""

    courier_profile.save()
    return user


@transaction.atomic
def save_driver_dispatch(user, cleaned_data):
    """
    Аналогично для таксиста.
    """
    user.user_type = "driver"
    user.save()

    worker_status, _ = WorkerStatus.objects.get_or_create(user=user)
    worker_status.is_online = cleaned_data.get("is_online", False)
    worker_status.is_busy = cleaned_data.get("is_busy", False)
    worker_status.save()

    lat = cleaned_data.get("lat")
    lon = cleaned_data.get("lon")

    if lat is not None and lon is not None:
        worker_location, _ = WorkerLocation.objects.get_or_create(
            user=user,
            defaults={"lat": lat, "lon": lon},
        )
        worker_location.lat = lat
        worker_location.lon = lon
        worker_location.save()

    driver_profile, _ = DriverProfile.objects.get_or_create(
        user=user,
        defaults={
            "status": cleaned_data.get("driver_profile_status") or "pending",
        }
    )

    driver_profile.status = cleaned_data.get("driver_profile_status") or driver_profile.status
    driver_profile.car_brand = cleaned_data.get("car_brand", "")
    driver_profile.car_model = cleaned_data.get("car_model", "")
    driver_profile.car_color = cleaned_data.get("car_color", "")
    driver_profile.car_number = cleaned_data.get("car_number", "")
    driver_profile.car_type = cleaned_data.get("car_type", "")
    driver_profile.passport_number = cleaned_data.get("passport_number", "")
    driver_profile.seria_and_number = cleaned_data.get("seria_and_number", "")
    driver_profile.issuing_authority = cleaned_data.get("issuing_authority", "")
    driver_profile.save()

    return user