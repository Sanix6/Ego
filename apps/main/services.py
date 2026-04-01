from django.db.models import Avg, Count
from apps.users.models import User
from .models import Review, DeliveryZone


def detect_delivery_zone_by_dropoff(darkstore, dropoff_lat, dropoff_lon):
    if not darkstore or dropoff_lat is None or dropoff_lon is None:
        return None

    zones = DeliveryZone.objects.filter(
        darkstore=darkstore,
        is_active=True,
    )

    for zone in zones:
        if zone.contains_point(dropoff_lat, dropoff_lon):
            return zone

    return None


def update_user_rating(user: User) -> None:
    stats = Review.objects.filter(to_user=user).aggregate(
        avg=Avg("rating"),
        count=Count("id"),
    )

    user.rating_avg = round(stats["avg"] or 0, 2)
    user.rating_count = stats["count"] or 0
    user.save(update_fields=["rating_avg", "rating_count"])