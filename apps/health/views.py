from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncHour, TruncDay
from django.shortcuts import render
from django.utils import timezone

from apps.balance.models import (
    WalletTransaction,
    TransactionStatus,
    TransactionType,
)

from apps.delivery.models import (
    Delivery,
    DeliveryOffer,
)

from apps.users.models import (
    WorkerStatus,
    User,
)


@staff_member_required
def operations_health_dashboard(request):

    now = timezone.now()

    period = request.GET.get("period", "day")

    # =====================================================
    # PERIOD FILTER
    # =====================================================

    if period == "week":
        since = now - timedelta(days=7)
        trunc = TruncDay

    elif period == "month":
        since = now - timedelta(days=30)
        trunc = TruncDay

    elif period == "all":
        since = now - timedelta(days=3650)
        trunc = TruncDay

    else:
        period = "day"
        since = now - timedelta(hours=24)
        trunc = TruncHour

    # =====================================================
    # MAIN METRICS
    # =====================================================

    online_couriers = WorkerStatus.objects.filter(
        user__user_type="courier",
        is_online=True
    ).count()

    active_deliveries = Delivery.objects.filter(
        delivery_status__in=[
            "courier_assigned",
            "courier_arrived",
            "in_delivery",
            "courier_arrived_b",
        ]
    ).count()

    pending_orders = Delivery.objects.filter(
        delivery_status="pending"
    ).count()

    completed_orders = Delivery.objects.filter(
        delivered_at__isnull=False,
        created_at__gte=since,
    ).count()

    earnings_today = WalletTransaction.objects.filter(
        transaction_type=TransactionType.ORDER_EARNING,
        status=TransactionStatus.COMPLETED,
        created_at__date=now.date()
    ).aggregate(total=Sum("amount"))["total"] or 0

    # =====================================================
    # CHART
    # =====================================================

    offers_chart = (
        DeliveryOffer.objects
        .filter(sent_at__gte=since)
        .annotate(period_date=trunc("sent_at"))
        .values("period_date")
        .annotate(total=Count("id"))
        .order_by("period_date")
    )

    chart_labels = []
    chart_data = []

    for item in offers_chart:

        if period == "day":
            label = item["period_date"].strftime("%H:%M")
        else:
            label = item["period_date"].strftime("%d.%m")

        chart_labels.append(label)
        chart_data.append(item["total"])

    # =====================================================
    # ETA / DELIVERY TIMES
    # =====================================================

    avg_pickup_time = Delivery.objects.filter(
        pickup_at__isnull=False,
        created_at__gte=since,
    ).aggregate(
        avg=Avg("fact_duration_min")
    )["avg"] or 0

    avg_delivery_time = Delivery.objects.filter(
        delivered_at__isnull=False,
        created_at__gte=since,
    ).aggregate(
        avg=Avg("fact_duration_min")
    )["avg"] or 0

    # =====================================================
    # TOP COURIERS
    # =====================================================

    top_couriers = (
        User.objects.filter(
            user_type="courier"
        )
        .annotate(
            completed_count=Count(
                "deliveries",
                filter=Q(
                    deliveries__delivered_at__isnull=False,
                    deliveries__created_at__gte=since,
                )
            )
        )
        .filter(completed_count__gt=0)
        .order_by("-completed_count")[:10]
    )

    # =====================================================
    # PROBLEM DELIVERIES
    # =====================================================

    overdue_deliveries = Delivery.objects.filter(
        deadline_at__lt=now,
        delivery_status__in=[
            "pending",
            "courier_assigned",
            "in_delivery",
        ]
    )[:10]

    no_courier_deliveries = Delivery.objects.filter(
        courier__isnull=True,
        delivery_status="pending",
    )[:10]

    stuck_deliveries = Delivery.objects.filter(
        delivery_status="courier_arrived",
        free_waiting_started_at__lte=now - timedelta(minutes=15)
    )[:10]

    context = {
        "title": "Health Center",

        "period": period,

        "online_couriers": online_couriers,
        "active_deliveries": active_deliveries,
        "pending_orders": pending_orders,
        "completed_orders": completed_orders,
        "earnings_today": earnings_today,

        "avg_pickup_time": round(avg_pickup_time, 1),
        "avg_delivery_time": round(avg_delivery_time, 1),

        "chart_labels": chart_labels,
        "chart_data": chart_data,

        "top_couriers": top_couriers,

        "overdue_deliveries": overdue_deliveries,
        "no_courier_deliveries": no_courier_deliveries,
        "stuck_deliveries": stuck_deliveries,
    }

    return render(
        request,
        "admin/operations_health.html",
        context
    )