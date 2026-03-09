from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import Delivery, CourierSlot
from django.utils.html import format_html
from .forms import DeliveryAdminForm, CourierSlotAdminForm
from django.utils import timezone
from django.utils.dateparse import parse_datetime




@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    form = DeliveryAdminForm

    list_display = (
        "id",
        "delivery_status",
        "courier",
        "point_a",
        "point_b",
        "deadline_at",
        "time_left",
        "pickup_at",
        "delivered_at",
        "created_at",
    )
    list_display_links = list_display
    list_filter = ("delivery_status", "created_at")
    search_fields = (
        "id",
        "point_a__address",
        "point_b__address",
        "courier__phone",
        "courier__first_name",
        "courier__last_name",
    )
    ordering = ("-created_at",)

    readonly_fields = ("created_at",)

    fieldsets = (
        ("Основное", {
            "fields": ("delivery_status", "courier")
        }),
        ("Маршрут", {
            "fields": ("point_a", "point_b", "deadline_at")
        }),
        ("Времена", {
            "fields": ("pickup_at", "delivered_at", "time_left")
        }),
        ("Комментарий клиента", {
            "fields": ("client_comment",)
        }),
        ("Служебное", {
            "fields": ("created_at",)
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "courier":
            qs = kwargs.get("queryset", db_field.remote_field.model.objects.all())
            kwargs["queryset"] = qs.filter(user_type="courier", is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(CourierSlot)
class CourierSlotAdmin(admin.ModelAdmin):
    form = CourierSlotAdminForm
    list_display = (
        "id",
        "period",
        "status_colored",
        "reserved_for",
        "booked_by",
        "is_free_display",
        "created_at",
    )
    list_display_links = list_display

    list_filter = (
        "status",
        "reserved_for",
        "booked_by",
        "start_at",
    )

    search_fields = (
        "reserved_for__phone",
        "booked_by__phone",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = ("-start_at",)

    date_hierarchy = "start_at"

    actions = (
        "mark_in_work",
        "mark_closed_early",
        "mark_no_show",
    )

    fieldsets = (
        ("Время", {
            "fields": ("start_at", "end_at")
        }),
        ("Статус", {
            "fields": ("status",)
        }),
        ("Назначение", {
            "fields": ("reserved_for", "booked_by")
        }),
        ("Система", {
            "fields": ("created_at",)
        }),
    )


    @admin.display(description="Период")
    def period(self, obj):
        return f"{obj.start_at:%d.%m %H:%M} — {obj.end_at:%H:%M}"

    @admin.display(description="Статус")
    def status_colored(self, obj):
        colors = {
            "planned": "#9CA3AF",        
            "offered": "#3B82F6",        
            "in_work": "#10B981",       
            "closed_early": "#F59E0B",   
            "paid_break": "#6366F1",     
            "unpaid_break": "#A855F7",  
            "no_show": "#EF4444",       
        }
        color = colors.get(obj.status, "#111827")
        return format_html(
            '<b style="color:{}">{}</b>',
            color,
            obj.get_status_display()
        )

    @admin.display(boolean=True, description="Свободен")
    def is_free_display(self, obj):
        return obj.is_free


    @admin.action(description="Пометить как «в работе»")
    def mark_in_work(self, request, queryset):
        updated = queryset.update(status="in_work")
        self.message_user(request, f"Обновлено слотов: {updated}")

    @admin.action(description="Закрыт досрочно")
    def mark_closed_early(self, request, queryset):
        updated = queryset.update(status="closed_early")
        self.message_user(request, f"Обновлено слотов: {updated}")

    @admin.action(description="Неявка (no show)")
    def mark_no_show(self, request, queryset):
        updated = queryset.update(status="no_show")
        self.message_user(request, f"Обновлено слотов: {updated}")


    def get_readonly_fields(self, request, obj=None):
        if obj and obj.booked_by:
            return self.readonly_fields + ("start_at", "end_at")
        return self.readonly_fields
