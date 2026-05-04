from django.contrib import admin
from django.utils.html import format_html
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "colored_status",
        "user",
        "amount_colored",
        "type_payment",
        "order_id",
        "short_transaction",
        "created_at_colored",
    )

    list_filter = (
        "status",
        "type_payment",
        "created_at",
    )

    search_fields = (
        "order_id",
        "transaction_id",
        "external_id",
        "user__email",
        "user__username",
    )

    readonly_fields = (
        "created_at",
        "payment_link_clickable",
        "external_id",
        "transaction_id",
    )

    list_per_page = 25
    date_hierarchy = "created_at"

    fieldsets = (
        ("Основное", {
            "fields": (
                "user",
                "status",
                "amount",
                "type_payment",
            )
        }),
        ("Идентификаторы", {
            "fields": (
                "order_id",
                "external_id",
                "transaction_id",
            )
        }),
        ("Ссылка на оплату", {
            "fields": (
                "payment_link_clickable",
            )
        }),
        ("Дата", {
            "fields": (
                "created_at",
            )
        }),
    )

    # ---------- КРАСИВЫЕ ОТОБРАЖЕНИЯ ----------

    def colored_status(self, obj):
        colors = {
            "pending": "#f39c12",   # желтый
            "success": "#27ae60",   # зеленый
            "failed": "#e74c3c",    # красный
        }
        return format_html(
            '<b style="color: {};">{}</b>',
            colors.get(obj.status, "black"),
            obj.get_status_display()
        )
    colored_status.short_description = "Статус"

    def amount_colored(self, obj):
        color = "#27ae60" if obj.status == "success" else "#e74c3c"
        return format_html(
            '<b style="color: {};">{} $</b>',
            color,
            obj.amount
        )
    amount_colored.short_description = "Сумма"

    def short_transaction(self, obj):
        if obj.transaction_id:
            return f"{obj.transaction_id[:10]}..."
        return "-"
    short_transaction.short_description = "Tx ID"

    def payment_link_clickable(self, obj):
        if obj.payment_link:
            return format_html(
                '<a href="{}" target="_blank" style="color:#2980b9;">Открыть ссылку</a>',
                obj.payment_link
            )
        return "-"
    payment_link_clickable.short_description = "Ссылка"

    def created_at_colored(self, obj):
        from django.utils.timezone import now
        delta = now() - obj.created_at

        if delta.days == 0:
            color = "#27ae60"  # сегодня
        elif delta.days == 1:
            color = "#f39c12"  # вчера
        else:
            color = "#7f8c8d"  # старые

        return format_html(
            '<span style="color:{};">{}</span>',
            color,
            obj.created_at.strftime("%Y-%m-%d %H:%M")
        )
    created_at_colored.short_description = "Дата"

    # ---------- ДОПОЛНИТЕЛЬНО ----------

    def has_add_permission(self, request):
        return False  # запрет создания вручную (обычно платежи создаются системой)