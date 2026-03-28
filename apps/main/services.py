from django.db.models import Avg, Count
from apps.users.models import User
from .models import Review


def update_user_rating(user: User) -> None:
    stats = Review.objects.filter(to_user=user).aggregate(
        avg=Avg("rating"),
        count=Count("id"),
    )

    user.rating_avg = round(stats["avg"] or 0, 2)
    user.rating_count = stats["count"] or 0
    user.save(update_fields=["rating_avg", "rating_count"])