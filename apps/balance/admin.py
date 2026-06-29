from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html

from apps.balance.models import *

@admin.register(WorkerWallet)
class WorkerWalletAdmin(ModelAdmin):
    list_display = (
        "id",
        "worker_phone",
        "worker_name",
        "worker_type",

        "balance_view",

        "online_earnings_view",
        "cash_earnings_view",

        "bonus_balance_view",
        "total_earnings_view",
        "total_withdrawals_view",

        "is_active",
        "created_at",
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

        "balance_readonly",

        "online_earnings_readonly",
        "cash_earnings_readonly",

        "bonus_balance_readonly",
        "total_earnings_readonly",
        "total_withdrawals_readonly",
    )

    ordering = ("-created_at",)

    fieldsets = (
        ("Работник", {
            "fields": (
                "worker",
            )
        }),

        ("Баланс", {
            "fields": (
                "balance_readonly",
                "bonus_balance_readonly",
            )
        }),

        ("Доходы", {
            "fields": (
                "total_earnings_readonly",
                "online_earnings_readonly",
                "cash_earnings_readonly",
                "total_withdrawals_readonly",
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
        name = (
            f"{obj.worker.first_name or ''} "
            f"{obj.worker.last_name or ''}"
        ).strip()

        return name if name else "-"
    worker_name.short_description = "ФИО"

    def worker_type(self, obj):
        if obj.worker.user_type == "driver":
            return format_html(
                '<b style="color:blue;">Таксист</b>'
            )

        elif obj.worker.user_type == "courier":
            return format_html(
                '<b style="color:green;">Курьер</b>'
            )

        return obj.worker.user_type
    worker_type.short_description = "Тип"

    def balance_view(self, obj):
        return format_html(
            '<b style="color:green;">{} сом</b>',
            obj.balance
        )
    balance_view.short_description = "Доступно"

    def online_earnings_view(self, obj):
        return format_html(
            '<b style="color:#198754;">{} сом</b>',
            obj.online_earnings
        )
    online_earnings_view.short_description = "Онлайн"

    def cash_earnings_view(self, obj):
        return format_html(
            '<b style="color:#fd7e14;">{} сом</b>',
            obj.cash_earnings
        )
    cash_earnings_view.short_description = "Наличные"

    def bonus_balance_view(self, obj):
        return format_html(
            '<b style="color:orange;">{} сом</b>',
            obj.total_bonuses
        )
    bonus_balance_view.short_description = "Бонусы"

    def total_earnings_view(self, obj):
        return format_html(
            '<b style="color:#0d6efd;">{} сом</b>',
            obj.total_earnings
        )
    total_earnings_view.short_description = "Всего заработано"

    def total_withdrawals_view(self, obj):
        return format_html(
            '<b style="color:red;">{} сом</b>',
            obj.total_withdrawals
        )
    total_withdrawals_view.short_description = "Выведено"

    def balance_readonly(self, obj):
        return self.balance_view(obj)

    def online_earnings_readonly(self, obj):
        return self.online_earnings_view(obj)

    def cash_earnings_readonly(self, obj):
        return self.cash_earnings_view(obj)

    def bonus_balance_readonly(self, obj):
        return self.bonus_balance_view(obj)

    def total_earnings_readonly(self, obj):
        return self.total_earnings_view(obj)

    def total_withdrawals_readonly(self, obj):
        return self.total_withdrawals_view(obj)

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
class WalletTransactionAdmin(ModelAdmin):
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

@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(ModelAdmin):

    list_display = (
        "id",
        "wallet",
        "amount",
        "final_amount",
        "status",
        "card_number",
        "created_at",
        "processed_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "wallet__worker__phone",
        "card_number",
        "card_holder",
    )

    readonly_fields = (
        "created_at",
        "processed_at",
        "commission_amount",
        "final_amount",
    )

    list_editable = (
        "status",
    )

    ordering = ("-created_at",)

    actions = [
        "approve_withdrawals",
        "reject_withdrawals"
    ]

    def save_model(self, request, obj, form, change):

        old_status = None

        if obj.pk:
            old_status = (
                WithdrawalRequest.objects
                .filter(pk=obj.pk)
                .values_list("status", flat=True)
                .first()
            )

        super().save_model(request, obj, form, change)

        if (
            obj.status == "approved"
            and old_status != "approved"
        ):

            already_exists = WalletTransaction.objects.filter(
                withdrawal_request=obj,
                transaction_type=TransactionType.WITHDRAWAL,
            ).exists()

            if not already_exists:

                WalletTransaction.objects.create(
                    wallet=obj.wallet,
                    withdrawal_request=obj,
                    transaction_type=TransactionType.WITHDRAWAL,
                    status=TransactionStatus.COMPLETED,
                    amount=obj.amount,
                    sign=-1,
                    comment=f"withdraw:{obj.id}",
                )

    def approve_withdrawals(self, request, queryset):

        updated = 0

        for withdrawal in queryset:

            withdrawal.status = "approved"
            withdrawal.save()

            already_exists = WalletTransaction.objects.filter(
                withdrawal_request=withdrawal,
                transaction_type=TransactionType.WITHDRAWAL,
            ).exists()

            if not already_exists:

                WalletTransaction.objects.create(
                    wallet=withdrawal.wallet,
                    withdrawal_request=withdrawal,
                    transaction_type=TransactionType.WITHDRAWAL,
                    status=TransactionStatus.COMPLETED,
                    amount=withdrawal.amount,
                    sign=-1,
                    comment=f"withdraw:{withdrawal.id}",
                )

            updated += 1

        self.message_user(
            request,
            f"{updated} заявок одобрено"
        )

    approve_withdrawals.short_description = (
        "Approve selected withdrawals"
    )

    def reject_withdrawals(self, request, queryset):

        updated = 0

        for withdrawal in queryset:

            withdrawal.status = "rejected"
            withdrawal.save()

            updated += 1

        self.message_user(
            request,
            f"{updated} заявок отклонено"
        )

    reject_withdrawals.short_description = (
        "Reject selected withdrawals"
    )


@admin.register(BonusRule)
class BonusRuleAdmin(ModelAdmin):
    list_display = (
        "id",
        "title",
        "bonus_type",
        "reward_display",
        "requirements",
        "is_active_colored",
        "period",
        "created_at",
    )

    list_filter = (
        "bonus_type",
        "is_active",
        "created_at",
    )

    search_fields = (
        "title",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = ("-id",)

    fieldsets = (
        ("Основная информация", {
            "fields": (
                "title",
                "bonus_type",
                "is_active",
            )
        }),

        ("Условия", {
            "fields": (
                "required_orders",
                "required_online_hours",
                "required_rating",
            )
        }),

        ("Награда", {
            "fields": (
                "reward_amount",
                "reward_percent",
            )
        }),

        ("Период действия", {
            "fields": (
                "starts_at",
                "ends_at",
            )
        }),

        ("Системная информация", {
            "fields": (
                "created_at",
            )
        }),
    )

    def reward_display(self, obj):
        if obj.reward_percent:
            return f"{obj.reward_percent}%"
        return f"{obj.reward_amount} сом"

    reward_display.short_description = "Награда"

    def requirements(self, obj):
        parts = []

        if obj.required_orders:
            parts.append(f"Заказов: {obj.required_orders}")

        if obj.required_online_hours:
            parts.append(f"Онлайн: {obj.required_online_hours} ч")

        if obj.required_rating:
            parts.append(f"Рейтинг: {obj.required_rating}")

        return " | ".join(parts) if parts else "-"

    requirements.short_description = "Условия"

    def is_active_colored(self, obj):
        color = "green" if obj.is_active else "red"
        text = "Активен" if obj.is_active else "Выключен"

        return format_html(
            '<b style="color:{};">{}</b>',
            color,
            text
        )

    is_active_colored.short_description = "Статус"

    def period(self, obj):
        if obj.starts_at and obj.ends_at:
            return f"{obj.starts_at:%d.%m.%Y} - {obj.ends_at:%d.%m.%Y}"
        return "-"

    period.short_description = "Период"




@admin.register(BonusMission)
class BonusMissionAdmin(ModelAdmin):
    list_display = (
        "id",
        "title",
        "required_orders",
        "reward_amount",
        "progress_count",
        "is_active_colored",
        "mission_period",
        "created_at",
    )

    list_filter = (
        "is_active",
        "starts_at",
        "ends_at",
    )

    search_fields = (
        "title",
        "description",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = ("-id",)

    fieldsets = (
        ("Основное", {
            "fields": (
                "title",
                "description",
                "is_active",
            )
        }),

        ("Условия", {
            "fields": (
                "required_orders",
            )
        }),

        ("Награда", {
            "fields": (
                "reward_amount",
            )
        }),

        ("Сроки", {
            "fields": (
                "starts_at",
                "ends_at",
            )
        }),

        ("Системная информация", {
            "fields": (
                "created_at",
            )
        }),
    )

    def progress_count(self, obj):
        return obj.workers.count()

    progress_count.short_description = "Участников"

    def is_active_colored(self, obj):
        color = "green" if obj.is_active else "red"
        text = "Активна" if obj.is_active else "Выключена"

        return format_html(
            '<b style="color:{};">{}</b>',
            color,
            text
        )

    is_active_colored.short_description = "Статус"

    def mission_period(self, obj):
        return f"{obj.starts_at:%d.%m.%Y} - {obj.ends_at:%d.%m.%Y}"

    mission_period.short_description = "Период"



@admin.register(WorkerMissionProgress)
class WorkerMissionProgressAdmin(ModelAdmin):
    list_display = (
        "id",
        "worker_info",
        "mission",
        "completed_orders",
        "progress_percent",
        "is_completed_colored",
        "rewarded_colored",
        "rewarded_at",
    )

    list_filter = (
        "is_completed",
        "rewarded",
        "mission",
    )

    search_fields = (
        "worker__phone",
        "worker__first_name",
        "worker__last_name",
        "mission__title",
    )

    raw_id_fields = (
        "worker",
        "mission",
    )

    readonly_fields = (
        "rewarded_at",
    )

    ordering = ("-id",)

    def worker_info(self, obj):
        return f"{obj.worker.phone} | {obj.worker.first_name}"

    worker_info.short_description = "Работник"

    def progress_percent(self, obj):
        if obj.mission.required_orders == 0:
            return "0%"

        percent = int(
            (obj.completed_orders / obj.mission.required_orders) * 100
        )

        color = "green" if percent >= 100 else "orange"

        return format_html(
            '<b style="color:{};">{}%</b>',
            color,
            percent
        )

    progress_percent.short_description = "Прогресс"

    def is_completed_colored(self, obj):
        color = "green" if obj.is_completed else "gray"
        text = "Да" if obj.is_completed else "Нет"

        return format_html(
            '<b style="color:{};">{}</b>',
            color,
            text
        )

    is_completed_colored.short_description = "Завершено"

    def rewarded_colored(self, obj):
        color = "green" if obj.rewarded else "red"
        text = "Начислен" if obj.rewarded else "Нет"

        return format_html(
            '<b style="color:{};">{}</b>',
            color,
            text
        )

    rewarded_colored.short_description = "Бонус"


@admin.register(BonusReward)
class BonusRewardAdmin(ModelAdmin):
    list_display = (
        "id",
        "worker_info",
        "bonus_type",
        "amount_colored",
        "description",
        "source",
        "status_colored",
        "expires_at",
        "created_at",
    )

    list_filter = (
        "bonus_type",
        "is_canceled",
        "created_at",
    )

    search_fields = (
        "worker__phone",
        "worker__first_name",
        "worker__last_name",
        "description",
    )

    raw_id_fields = (
        "worker",
        "rule",
        "mission",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = ("-created_at",)

    fieldsets = (
        ("Основная информация", {
            "fields": (
                "worker",
                "bonus_type",
                "amount",
                "description",
            )
        }),

        ("Источник", {
            "fields": (
                "rule",
                "mission",
            )
        }),

        ("Статус", {
            "fields": (
                "is_canceled",
                "expires_at",
            )
        }),

        ("Системная информация", {
            "fields": (
                "created_at",
            )
        }),
    )

    def worker_info(self, obj):
        return f"{obj.worker.phone} | {obj.worker.first_name}"

    worker_info.short_description = "Работник"

    def amount_colored(self, obj):
        return format_html(
            '<b style="color:green;">+{} сом</b>',
            obj.amount
        )

    amount_colored.short_description = "Сумма"

    def source(self, obj):
        if obj.rule:
            return f"Rule: {obj.rule.title}"

        if obj.mission:
            return f"Mission: {obj.mission.title}"

        return "-"

    source.short_description = "Источник"

    def status_colored(self, obj):
        if obj.is_canceled:
            return format_html(
                '<b style="color:red;">Отменен</b>'
            )

        if obj.expires_at:
            return format_html(
                '<b style="color:orange;">Сгораемый</b>'
            )

        return format_html(
            '<b style="color:green;">Активен</b>'
        )

    status_colored.short_description = "Статус"



