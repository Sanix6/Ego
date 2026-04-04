from django.contrib import admin
from django.utils.html import format_html

from apps.balance.models import *


@admin.register(WorkerWallet)
class WorkerWalletAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "worker_phone",
        "worker_name",
        "worker_type",
        "is_active",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "is_active",
        "worker__user_type",
        "created_at",
    )

    search_fields = (
        "worker__phone",
        "worker__first_name",
        "worker__last_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)

    fieldsets = (
        ("Работник", {
            "fields": (
                "worker",
            )
        }),

        ("Статус", {
            "fields": (
                "is_active",
            )
        }),

        ("Системные данные", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    def worker_phone(self, obj):
        return obj.worker.phone
    worker_phone.short_description = "Телефон"

    def worker_name(self, obj):
        name = f"{obj.worker.first_name or ''} {obj.worker.last_name or ''}".strip()
        return name if name else "-"
    worker_name.short_description = "ФИО"

    def worker_type(self, obj):
        if obj.worker.user_type == "driver":
            return format_html('<b style="color:blue;">Таксист</b>')
        elif obj.worker.user_type == "courier":
            return format_html('<b style="color:green;">Курьер</b>')
        return obj.worker.user_type
    worker_type.short_description = "Тип работника"


    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser



@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "worker_phone",
        "worker_name",
        "worker_type",
        "transaction_type",
        "status_badge",
        "channel",
        "signed_amount_view",
        "order_source",
        "withdrawal_request_view",
        "created_at",
    )

    list_filter = (
        "transaction_type",
        "status",
        "channel",
        "wallet__worker__user_type",
        "created_at",
    )

    search_fields = (
        "wallet__worker__phone",
        "wallet__worker__first_name",
        "wallet__worker__last_name",
        "comment",
        "taxi_ride__id",
        "delivery__id",
        "withdrawal_request__id",
    )

    readonly_fields = (
        "created_at",
        "signed_amount_readonly",
        "worker_info",
        "order_info",
    )

    ordering = ("-created_at", "-id")
    list_per_page = 30

    fieldsets = (
        ("Основное", {
            "fields": (
                "wallet",
                "worker_info",
                "transaction_type",
                "status",
                "channel",
            )
        }),
        ("Сумма", {
            "fields": (
                "amount",
                "sign",
                "signed_amount_readonly",
            )
        }),
        ("Связи", {
            "fields": (
                "taxi_ride",
                "delivery",
                "withdrawal_request",
                "order_info",
            )
        }),
        ("Дополнительно", {
            "fields": (
                "comment",
                "created_at",
            )
        }),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "wallet",
                "wallet__worker",
                "taxi_ride",
                "delivery",
                "withdrawal_request",
            )
        )

    @admin.display(description="Телефон")
    def worker_phone(self, obj):
        return obj.wallet.worker.phone if obj.wallet and obj.wallet.worker else "-"

    @admin.display(description="ФИО")
    def worker_name(self, obj):
        worker = obj.wallet.worker if obj.wallet else None
        if not worker:
            return "-"
        full_name = f"{worker.first_name or ''} {worker.last_name or ''}".strip()
        return full_name or "-"

    @admin.display(description="Тип")
    def worker_type(self, obj):
        worker = obj.wallet.worker if obj.wallet else None
        if not worker:
            return "-"

        if worker.user_type == "driver":
            return format_html('<b style="color: blue;">Таксист</b>')
        if worker.user_type == "courier":
            return format_html('<b style="color: green;">Курьер</b>')

        return worker.user_type

    @admin.display(description="Статус")
    def status_badge(self, obj):
        color_map = {
            "completed": "green",
            "pending": "orange",
            "canceled": "red",
            "failed": "red",
        }
        color = color_map.get(obj.status, "gray")

        display = obj.get_status_display() if hasattr(obj, "get_status_display") else obj.status
        return format_html('<b style="color:{};">{}</b>', color, display)

    @admin.display(description="Сумма")
    def signed_amount_view(self, obj):
        value = obj.signed_amount
        color = "green" if value >= 0 else "red"
        prefix = "+" if value >= 0 else ""
        return format_html('<b style="color:{};">{}{}</b>', color, prefix, value)

    @admin.display(description="Подписанная сумма")
    def signed_amount_readonly(self, obj):
        if not obj.pk:
            return "-"
        value = obj.signed_amount
        color = "green" if value >= 0 else "red"
        prefix = "+" if value >= 0 else ""
        return format_html('<b style="color:{};">{}{}</b>', color, prefix, value)

    @admin.display(description="Источник")
    def order_source(self, obj):
        if obj.taxi_ride_id:
            return f"TaxiRide #{obj.taxi_ride_id}"
        if obj.delivery_id:
            return f"Delivery #{obj.delivery_id}"
        return "-"

    @admin.display(description="Заявка на вывод")
    def withdrawal_request_view(self, obj):
        if obj.withdrawal_request_id:
            return f"#{obj.withdrawal_request_id}"
        return "-"

    @admin.display(description="Информация о работнике")
    def worker_info(self, obj):
        if not obj.pk or not obj.wallet_id or not obj.wallet.worker_id:
            return "-"

        worker = obj.wallet.worker
        full_name = f"{worker.first_name or ''} {worker.last_name or ''}".strip() or "-"
        return format_html(
            "<b>Телефон:</b> {}<br>"
            "<b>ФИО:</b> {}<br>"
            "<b>Тип:</b> {}",
            worker.phone,
            full_name,
            worker.get_user_type_display() if hasattr(worker, "get_user_type_display") else worker.user_type,
        )

    @admin.display(description="Информация по заказу")
    def order_info(self, obj):
        if obj.taxi_ride_id:
            return format_html("<b>TaxiRide ID:</b> {}", obj.taxi_ride_id)
        if obj.delivery_id:
            return format_html("<b>Delivery ID:</b> {}", obj.delivery_id)
        if obj.withdrawal_request_id:
            return format_html("<b>WithdrawalRequest ID:</b> {}", obj.withdrawal_request_id)
        return "-"

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser