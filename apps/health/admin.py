from datetime import timedelta

from django.contrib import admin
from django.db.models import Count, Avg, Q
from django.db.models import DurationField, ExpressionWrapper, F
from django.shortcuts import render
from django.urls import path
from django.utils import timezone

from apps.delivery.models import Delivery
from apps.users.models import WorkerStatus, User


def format_duration(td):
    if not td:
        return "0 мин"

    total_seconds = int(td.total_seconds())

    minutes = total_seconds // 60
    seconds = total_seconds % 60

    return f"{minutes} мин {seconds} сек"


def operations_health_dashboard(request):

    now = timezone.now()

    period = request.GET.get("period", "day")

    if period == "week":
        since = now - timedelta(days=7)

    elif period == "month":
        since = now - timedelta(days=30)

    else:
        period = "day"
        since = now - timedelta(hours=24)

    online_couriers = WorkerStatus.objects.filter(
        user__user_type="courier",
        is_online=True
    ).count()

    busy_couriers = WorkerStatus.objects.filter(
        user__user_type="courier",
        is_online=True,
        is_busy=True
    ).count()

    free_couriers = WorkerStatus.objects.filter(
        user__user_type="courier",
        is_online=True,
        is_busy=False
    ).count()

    live_couriers = WorkerStatus.objects.select_related(
        "user"
    ).filter(
        user__user_type="courier",
        is_online=True
    ).order_by("-last_seen")[:20]


    active_deliveries = Delivery.objects.filter(
        delivery_status__in=[
            "courier_assigned",
            "courier_arrived",
            "in_delivery",
        ]
    ).count()

    pending_orders = Delivery.objects.filter(
        delivery_status="pending"
    ).count()

    completed_orders = Delivery.objects.filter(
        delivered_at__isnull=False,
        created_at__gte=since
    ).count()

    avg_cte = (
        Delivery.objects.filter(
            delivered_at__isnull=False,
            created_at__gte=since
        )
        .annotate(
            cte=ExpressionWrapper(
                F("delivered_at") - F("created_at"),
                output_field=DurationField()
            )
        )
        .aggregate(avg=Avg("cte"))["avg"]
    )

    avg_pickup_time = (
        Delivery.objects.filter(
            arrived_at__isnull=False,
            pickup_at__isnull=False,
            created_at__gte=since
        )
        .annotate(
            pickup_time=ExpressionWrapper(
                F("pickup_at") - F("arrived_at"),
                output_field=DurationField()
            )
        )
        .aggregate(avg=Avg("pickup_time"))["avg"]
    )

    avg_delivery_time = (
        Delivery.objects.filter(
            pickup_at__isnull=False,
            delivered_at__isnull=False,
            created_at__gte=since
        )
        .annotate(
            delivery_time=ExpressionWrapper(
                F("delivered_at") - F("pickup_at"),
                output_field=DurationField()
            )
        )
        .aggregate(avg=Avg("delivery_time"))["avg"]
    )

    top_couriers = (
        User.objects.filter(
            user_type="courier"
        )
        .annotate(
            completed_count=Count(
                "deliveries",
                filter=Q(
                    deliveries__delivered_at__isnull=False,
                    deliveries__created_at__gte=since
                )
            )
        )
        .filter(completed_count__gt=0)
        .order_by("-completed_count")[:10]
    )

    active_orders = Delivery.objects.select_related(
        "courier",
        "darkstore"
    ).filter(
        delivery_status__in=[
            "courier_assigned",
            "courier_arrived",
            "in_delivery",
        ]
    ).order_by("-created_at")[:20]

    overdue_deliveries = Delivery.objects.filter(
        deadline_at__lt=now,
        delivered_at__isnull=True
    )[:10]

    no_courier_deliveries = Delivery.objects.filter(
        courier__isnull=True,
        delivery_status="pending"
    )[:10]

    stuck_deliveries = Delivery.objects.filter(
        free_waiting_started_at__lte=now - timedelta(minutes=10),
        delivered_at__isnull=True
    )[:10]

    context = admin.site.each_context(request)

    context.update({
        "title": "Operations Health",

        "period": period,

        "online_couriers": online_couriers,
        "busy_couriers": busy_couriers,
        "free_couriers": free_couriers,

        "active_deliveries": active_deliveries,
        "pending_orders": pending_orders,
        "completed_orders": completed_orders,

        "avg_cte": format_duration(avg_cte),
        "avg_pickup_time": format_duration(avg_pickup_time),
        "avg_delivery_time": format_duration(avg_delivery_time),

        "top_couriers": top_couriers,
        "active_orders": active_orders,

        "live_couriers": live_couriers,

        "overdue_deliveries": overdue_deliveries,
        "no_courier_deliveries": no_courier_deliveries,
        "stuck_deliveries": stuck_deliveries,
    })

    return render(
        request,
        "admin/operations_health.html",
        context
    )


original_get_urls = admin.site.get_urls


def custom_get_urls():
    urls = original_get_urls()

    custom_urls = [
        path(
            "health/",
            admin.site.admin_view(operations_health_dashboard),
            name="operations-health",
        ),
    ]

    return custom_urls + urls


admin.site.get_urls = custom_get_urls