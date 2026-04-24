from dataclasses import dataclass
from typing import List, Optional
from django.utils import timezone
from django.db import transaction

from apps.delivery.models import CourierRoute, CourierRouteStop
from apps.users.models import WorkerLocation, WorkerStatus
from assets.helpers.loggers import write_log

MAX_DETOUR_SECONDS = 8 * 60
MAX_DETOUR_KM = 3.0

#detour.py - отвечает за логику расчета маршрута курьера с учетом уже назначенных доставок и новой доставки, которую нужно вставить в маршрут. Также проверяет, что новый маршрут не нарушает дедлайны уже назначенных доставок и не создает слишком большой детур.
@dataclass
class RoutePoint:
    delivery_id: int
    stop_type: str
    lat: float
    lon: float
    sequence: int = 0


def calc_route_distance_km(points: List[RoutePoint]) -> float:
    from apps.delivery.services import haversine_km, estimate_eta_seconds
    if len(points) < 2:
        return 0.0

    total = 0.0
    for i in range(len(points) - 1):
        total += haversine_km(
            points[i].lat, points[i].lon,
            points[i + 1].lat, points[i + 1].lon,
        )
    return total


def calc_route_eta_seconds(points: List[RoutePoint], speed_kmh=25.0) -> int:
    from apps.delivery.services import haversine_km, estimate_eta_seconds
    distance = calc_route_distance_km(points)
    return estimate_eta_seconds(distance, speed_kmh=speed_kmh)


def generate_route_variants(current_points: List[RoutePoint], pickup: RoutePoint, dropoff: RoutePoint):
    variants = []
    n = len(current_points)

    for pickup_pos in range(n + 1):
        for dropoff_pos in range(pickup_pos + 1, n + 2):
            route = current_points.copy()
            route.insert(pickup_pos, pickup)
            route.insert(dropoff_pos, dropoff)
            variants.append(route)

    return variants


def choose_best_insertion(current_location, pending_points, new_pickup, new_dropoff):
    base_route = [current_location] + pending_points
    base_distance = calc_route_distance_km(base_route)
    base_eta = calc_route_eta_seconds(base_route)

    best = None
    variants = generate_route_variants(pending_points, new_pickup, new_dropoff)

    write_log(f"DETOUR variants={len(variants)}")

    for idx, variant in enumerate(variants, start=1):
        full_route = [current_location] + variant
        new_distance = calc_route_distance_km(full_route)
        new_eta = calc_route_eta_seconds(full_route)

        detour_km = new_distance - base_distance
        detour_sec = new_eta - base_eta

        if detour_km > MAX_DETOUR_KM:
            write_log(f"DETOUR variant={idx} rejected by km: {detour_km}")
            continue

        if detour_sec > MAX_DETOUR_SECONDS:
            write_log(f"DETOUR variant={idx} rejected by sec: {detour_sec}")
            continue

        # if not check_route_deadlines(full_route):
        #     write_log(f"DETOUR variant={idx} rejected by deadline")
        #     continue

        candidate = {
            "points": variant,
            "distance_km": new_distance,
            "eta_sec": new_eta,
            "detour_km": detour_km,
            "detour_sec": detour_sec,
        }

        write_log(
            f"DETOUR variant={idx} accepted "
            f"detour_km={detour_km} detour_sec={detour_sec}"
        )

        if best is None or candidate["detour_sec"] < best["detour_sec"]:
            best = candidate

    return best



def get_courier_pending_route_points(courier) -> List[RoutePoint]:
    route = CourierRoute.objects.filter(
        courier=courier,
        status="active",
    ).first()

    if not route:
        return []

    stops = route.stops.filter(
        status__in=["pending", "arrived"]
    ).order_by("sequence")

    result = []
    for stop in stops:
        result.append(
            RoutePoint(
                delivery_id=stop.delivery_id,
                stop_type=stop.stop_type,
                lat=stop.lat,
                lon=stop.lon,
                sequence=stop.sequence,
            )
        )
    return result


def get_courier_current_point(courier) -> Optional[RoutePoint]:
    location = WorkerLocation.objects.filter(user=courier).first()
    if not location:
        return None

    return RoutePoint(
        delivery_id=0,
        stop_type="current",
        lat=location.lat,
        lon=location.lon,
        sequence=0,
    )


def build_delivery_points(delivery) -> Optional[tuple]:
    if (
        delivery.pickup_lat is None or
        delivery.pickup_lon is None or
        delivery.dropoff_lat is None or
        delivery.dropoff_lon is None
    ):
        return None

    pickup = RoutePoint(
        delivery_id=delivery.id,
        stop_type="pickup",
        lat=float(delivery.pickup_lat),
        lon=float(delivery.pickup_lon),
    )
    dropoff = RoutePoint(
        delivery_id=delivery.id,
        stop_type="dropoff",
        lat=float(delivery.dropoff_lat),
        lon=float(delivery.dropoff_lon),
    )
    return pickup, dropoff


def courier_has_capacity(courier, max_parallel_deliveries=5) -> bool:
    active_count = courier.deliveries.filter(
        delivery_status__in=[
            "courier_assigned",
            "courier_arrived",
            "in_delivery",
            "courier_arrived_b",
        ]
    ).count()

    return active_count < max_parallel_deliveries


def route_points_with_eta(points: List[RoutePoint], speed_kmh=25.0):
    from apps.delivery.services import haversine_km, estimate_eta_seconds
    """
    Возвращает список словарей с накопительным ETA до каждой точки.
    """
    if not points:
        return []

    result = []
    total_sec = 0

    result.append({
        "point": points[0],
        "eta_sec": 0,
    })

    for i in range(len(points) - 1):
        distance_km = haversine_km(
            points[i].lat, points[i].lon,
            points[i + 1].lat, points[i + 1].lon,
        )
        segment_sec = estimate_eta_seconds(distance_km, speed_kmh=speed_kmh)
        total_sec += segment_sec

        result.append({
            "point": points[i + 1],
            "eta_sec": total_sec,
        })

    return result


def check_route_deadlines(full_route_points: List[RoutePoint], speed_kmh=25.0) -> bool:
    eta_items = route_points_with_eta(full_route_points, speed_kmh=speed_kmh)
    now = timezone.now()

    delivery_ids = {
        item["point"].delivery_id
        for item in eta_items
        if item["point"].delivery_id
    }

    deliveries_map = {
        d.id: d
        for d in CourierRouteStop.delivery.field.related_model.objects.filter(id__in=delivery_ids)
    }

    for item in eta_items:
        point = item["point"]

        if point.stop_type != "dropoff":
            continue

        delivery = deliveries_map.get(point.delivery_id)
        if not delivery:
            continue

        if delivery.deadline_at:
            eta_at = now + timezone.timedelta(seconds=item["eta_sec"])
            if eta_at > delivery.deadline_at:
                return False

    return True

def try_attach_delivery_to_courier(courier, delivery):
    write_log(f"DETOUR START courier={courier.id} delivery={delivery.id}")

    current_point = get_courier_current_point(courier)
    if not current_point:
        write_log(f"DETOUR FAIL courier={courier.id}: no current location")
        return None

    built = build_delivery_points(delivery)
    if not built:
        write_log(f"DETOUR FAIL courier={courier.id}: delivery has no coords")
        return None

    new_pickup, new_dropoff = built
    pending_points = get_courier_pending_route_points(courier)

    write_log(
        f"DETOUR DATA courier={courier.id} pending_points={len(pending_points)} "
        f"pickup=({new_pickup.lat},{new_pickup.lon}) "
        f"dropoff=({new_dropoff.lat},{new_dropoff.lon})"
    )

    if not pending_points:
        full_route = [current_point, new_pickup, new_dropoff]
        return {
            "points": [new_pickup, new_dropoff],
            "distance_km": calc_route_distance_km(full_route),
            "eta_sec": calc_route_eta_seconds(full_route),
            "detour_km": 0,
            "detour_sec": 0,
        }

    # if not courier_has_capacity(courier):
    #     write_log(f"DETOUR FAIL courier={courier.id}: no capacity")
    #     return None

    best = choose_best_insertion(
        current_location=current_point,
        pending_points=pending_points,
        new_pickup=new_pickup,
        new_dropoff=new_dropoff,
    )

    write_log(f"DETOUR RESULT courier={courier.id}: {best}")
    return best


@transaction.atomic
def save_courier_route_plan(courier, points: List[RoutePoint]):
    route, _ = CourierRoute.objects.get_or_create(
        courier=courier,
        defaults={"status": "active"},
    )

    if route.status != "active":
        route.status = "active"
        route.save(update_fields=["status", "updated_at"])

    route.stops.filter(status__in=["pending", "arrived"]).delete()

    new_stops = []
    for idx, point in enumerate(points, start=1):
        if point.stop_type not in ["pickup", "dropoff"]:
            continue

        new_stops.append(
            CourierRouteStop(
                route=route,
                delivery_id=point.delivery_id,
                stop_type=point.stop_type,
                sequence=idx,
                lat=point.lat,
                lon=point.lon,
                status="pending",
            )
        )

    CourierRouteStop.objects.bulk_create(new_stops)

    return route


def renumber_pending_stops(route):
    pending_stops = route.stops.filter(
        status__in=["pending", "arrived"]
    ).order_by("sequence", "id")

    for idx, stop in enumerate(pending_stops, start=1):
        if stop.sequence != idx:
            stop.sequence = idx
            stop.save(update_fields=["sequence"])


def close_route_if_finished(route):
    has_active_stops = route.stops.filter(
        status__in=["pending", "arrived"]
    ).exists()

    if not has_active_stops and route.status != "completed":
        route.status = "completed"
        route.save(update_fields=["status", "updated_at"])


def get_next_active_stop(route):
    return route.stops.filter(
        status__in=["pending", "arrived"]
    ).order_by("sequence", "id").first()


@transaction.atomic
def mark_route_stop_arrived(courier, delivery, stop_type: str):
    route = CourierRoute.objects.select_for_update().filter(
        courier=courier,
        status="active",
    ).first()

    if not route:
        return False, "Активный маршрут не найден."

    stop = route.stops.select_for_update().filter(
        delivery=delivery,
        stop_type=stop_type,
        status="pending",
    ).order_by("sequence", "id").first()

    if not stop:
        return False, "Точка маршрута не найдена или уже обработана."

    # next_stop = get_next_active_stop(route)
    # if not next_stop or next_stop.id != stop.id:
    #     return False, "Сейчас нельзя отмечать эту точку."

    stop.status = "arrived"
    stop.arrived_at = timezone.now()
    stop.save(update_fields=["status", "arrived_at"])

    return True, "Точка маршрута отмечена как arrived."


@transaction.atomic
def complete_route_stop(courier, delivery, stop_type: str):
    route = CourierRoute.objects.select_for_update().filter(
        courier=courier,
        status="active",
    ).first()

    if not route:
        return False, "Активный маршрут не найден."

    stop = route.stops.select_for_update().filter(
        delivery=delivery,
        stop_type=stop_type,
        status__in=["pending", "arrived"],
    ).order_by("sequence", "id").first()

    if not stop:
        return False, "Точка маршрута не найдена или уже завершена."

    # next_stop = get_next_active_stop(route)
    # if not next_stop or next_stop.id != stop.id:
    #     return False, "Сейчас нельзя завершать эту точку."

    now = timezone.now()

    if stop.status != "arrived":
        stop.arrived_at = now

    stop.status = "done"
    stop.completed_at = now
    stop.save(update_fields=["status", "arrived_at", "completed_at"])

    renumber_pending_stops(route)
    close_route_if_finished(route)

    return True, "Точка маршрута завершена."