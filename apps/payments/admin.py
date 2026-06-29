from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.html import format_html
from .models import Payment, NambaTransfer


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
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


    def colored_status(self, obj):
        colors = {
            "pending": "#f39c12",   
            "success": "#27ae60",   
            "failed": "#e74c3c",  
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
            '<b style="color: {};">{} сом</b>',
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
            color = "#27ae60" 
        elif delta.days == 1:
            color = "#f39c12"
        else:
            color = "#7f8c8d" 

        return format_html(
            '<span style="color:{};">{}</span>',
            color,
            obj.created_at.strftime("%Y-%m-%d %H:%M")
        )
    created_at_colored.short_description = "Дата"


    def has_add_permission(self, request):
        return False  #




@admin.register(NambaTransfer)
class NambaTransferAdmin(ModelAdmin):

    list_display = (
        "id",
        "wallet_transaction",
        "amount",
        "colored_status",
        "external_id",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "id",
        "external_id",
        "wallet_transaction__id",
        "wallet_transaction__comment",
    )

    readonly_fields = (
        "wallet_transaction",
        "amount",
        "status",
        "external_id",
        "raw_response",
        "created_at",
    )

    ordering = (
        "-id",
    )

    list_per_page = 50

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "wallet_transaction",
                    "amount",
                    "status",
                    "external_id",
                    "created_at",
                )
            },
        ),
        (
            "Ответ Namba",
            {
                "fields": (
                    "raw_response",
                ),
                "classes": (
                    "tab",
                ),
            },
        ),
    )

    @admin.display(description="Статус")
    def colored_status(self, obj):

        colors = {
            "success": "#16a34a",
            "failed": "#dc2626",
            "pending": "#ca8a04",
        }

        color = colors.get(obj.status, "#6b7280")

        return (
            f'<span style="'
            f'padding:4px 10px;'
            f'border-radius:8px;'
            f'font-weight:600;'
            f'color:white;'
            f'background:{color};'
            f'">'
            f'{obj.status}'
            f'</span>'
        )

    colored_status.allow_tags = True