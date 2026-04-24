from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import Delivery, CourierSlot, DeliveryOffer
from django.utils.html import format_html
from .forms import DeliveryAdminForm, CourierSlotAdminForm
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from django.contrib import admin
from django.utils.html import format_html
from django.db import transaction
from .models import Delivery, CourierSlot, CourierRoute, CourierRouteStop, DeliveryOffer
from .forms import CourierSlotAdminForm
# from .services import find_nearest_couriers, courier_matches_delivery, has_offer_been


@admin.register(DeliveryOffer)
class DeliveryOfferAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "delivery_link",
        "courier",
        "status",
        "sent_at",
        "responded_at",
        "expires_at",
    )
    list_display_links = ("id", "delivery_link", "courier")

    list_filter = (
        "status",
        "sent_at",
        "expires_at",
    )

    search_fields = (
        "id",
        "delivery__id",
        "delivery__point_a",
        "delivery__point_b",
        "courier__phone",
        "courier__first_name",
        "courier__last_name",
    )

    ordering = ("-sent_at",)

    readonly_fields = (
        "sent_at",
        "responded_at",
        "delivery_main_info",
        "delivery_route_info",
        "delivery_contacts_info",
        "delivery_comments_info",
        "delivery_time_info",
    )

    fieldsets = (
        ("Оффер", {
            "fields": (
                "delivery",
                "courier",
                "status",
                "expires_at",
                "sent_at",
                "responded_at",
            )
        }),
        ("Доставка — основное", {
            "fields": (
                "delivery_main_info",
            )
        }),
        ("Доставка — маршрут", {
            "fields": (
                "delivery_route_info",
            )
        }),
        ("Доставка — контакты", {
            "fields": (
                "delivery_contacts_info",
            )
        }),
        ("Доставка — время", {
            "fields": (
                "delivery_time_info",
            )
        }),
        ("Доставка — комментарии", {
            "fields": (
                "delivery_comments_info",
            )
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("delivery", "courier")

    @admin.display(description="Доставка")
    def delivery_link(self, obj):
        if not obj.delivery_id:
            return "-"
        return format_html(
            '<a href="/admin/delivery/delivery/{}/change/">Доставка #{}</a>',
            obj.delivery_id,
            obj.delivery_id,
        )

    @admin.display(description="Основная информация по доставке")
    def delivery_main_info(self, obj):
        d = obj.delivery
        if not d:
            return "-"

        return format_html(
            """
            <div style="line-height:1.8;">
                <b>ID:</b> {}<br>
                <b>Статус:</b> {}<br>
                <b>Тип доставки:</b> {}<br>
                <b>Цена:</b> {}<br>
                <b>Door to door:</b> {}<br>
                <b>Слот:</b> {}<br>
                <b>Курьер:</b> {}<br>
                <b>Клиент:</b> {}<br>
                <b>Создана:</b> {}
            </div>
            """,
            d.id,
            d.get_delivery_status_display(),
            d.get_type_delivery_display(),
            d.price if d.price is not None else "-",
            "Да" if d.door_to_door else "Нет",
            d.slot if d.slot else "-",
            d.courier if d.courier else "-",
            d.client if d.client else "-",
            d.created_at.strftime("%d.%m.%Y %H:%M") if d.created_at else "-",
        )

    @admin.display(description="Маршрут")
    def delivery_route_info(self, obj):
        d = obj.delivery
        if not d:
            return "-"

        return format_html(
            """
            <div style="line-height:1.8;">
                <b>Адрес откуда:</b> {}<br>
                <b>Адрес куда:</b> {}<br>
                <b>Широта забора:</b> {}<br>
                <b>Долгота забора:</b> {}<br>
                <b>Широта доставки:</b> {}<br>
                <b>Долгота доставки:</b> {}
            </div>
            """,
            d.point_a or "-",
            d.point_b or "-",
            d.pickup_lat if d.pickup_lat is not None else "-",
            d.pickup_lon if d.pickup_lon is not None else "-",
            d.dropoff_lat if d.dropoff_lat is not None else "-",
            d.dropoff_lon if d.dropoff_lon is not None else "-",
        )

    @admin.display(description="Контакты")
    def delivery_contacts_info(self, obj):
        d = obj.delivery
        if not d:
            return "-"

        return format_html(
            """
            <div style="line-height:1.8;">
                <b>Отправитель:</b> {}<br>
                <b>Телефон отправителя:</b> {}<br>
                <b>Получатель:</b> {}<br>
                <b>Телефон получателя:</b> {}
            </div>
            """,
            d.sender_name or "-",
            d.sender_phone or "-",
            d.recipient_name or "-",
            d.recipient_phone or "-",
        )

    @admin.display(description="Время")
    def delivery_time_info(self, obj):
        d = obj.delivery
        if not d:
            return "-"

        return format_html(
            """
            <div style="line-height:1.8;">
                <b>Доставить до:</b> {}<br>
                <b>Прибыл:</b> {}<br>
                <b>Бесплатное ожидание с:</b> {}<br>
                <b>Минут бесплатного ожидания:</b> {}<br>
                <b>Платное ожидание с:</b> {}<br>
                <b>Время забора:</b> {}<br>
                <b>Время доставки:</b> {}<br>
                <b>Осталось времени:</b> {}
            </div>
            """,
            d.deadline_at.strftime("%d.%m.%Y %H:%M") if d.deadline_at else "-",
            d.arrived_at.strftime("%d.%m.%Y %H:%M") if d.arrived_at else "-",
            d.free_waiting_started_at.strftime("%d.%m.%Y %H:%M") if d.free_waiting_started_at else "-",
            d.free_waiting_minutes,
            d.paid_waiting_started_at.strftime("%d.%m.%Y %H:%M") if d.paid_waiting_started_at else "-",
            d.pickup_at.strftime("%d.%m.%Y %H:%M") if d.pickup_at else "-",
            d.delivered_at.strftime("%d.%m.%Y %H:%M") if d.delivered_at else "-",
            d.time_left,
        )

    @admin.display(description="Комментарии и детали")
    def delivery_comments_info(self, obj):
        d = obj.delivery
        if not d:
            return "-"

        return format_html(
            """
            <div style="line-height:1.8;">
                <b>Комментарий клиента:</b><br>{}<br><br>

                <b>Подъезд откуда:</b> {}<br>
                <b>Этаж откуда:</b> {}<br>
                <b>Квартира/офис откуда:</b> {}<br>
                <b>Домофон откуда:</b> {}<br>
                <b>Комментарий откуда:</b><br>{}<br><br>

                <b>Подъезд куда:</b> {}<br>
                <b>Этаж куда:</b> {}<br>
                <b>Квартира/офис куда:</b> {}<br>
                <b>Домофон куда:</b> {}<br>
                <b>Комментарий куда:</b><br>{}
            </div>
            """,
            d.client_comment or "-",
            d.pickup_entrance or "-",
            d.pickup_floor or "-",
            d.pickup_apartment or "-",
            d.pickup_intercom or "-",
            d.pickup_comment or "-",
            d.dropoff_entrance or "-",
            d.dropoff_floor or "-",
            d.dropoff_apartment or "-",
            d.dropoff_intercom or "-",
            d.dropoff_comment or "-",
        )


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "delivery_status",
        "courier",
        "client",
        "point_a",
        "point_b",
        "deadline_at",
        "created_at",
    )

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        selected_courier = obj.courier

        super().save_model(request, obj, form, change)
        if is_new and not selected_courier:
            from .tasks import dispatch_delivery
            transaction.on_commit(lambda: dispatch_delivery.delay(obj.id))


        elif is_new and selected_courier:
            from .dispatch import send_offer_to_courier
            transaction.on_commit(lambda: send_offer_to_courier(obj, selected_courier))


@admin.register(CourierSlot)
class CourierSlotAdmin(admin.ModelAdmin):
    form = CourierSlotAdminForm

    list_display = (
        "id",
        "darkstore",
        "transport_with_icon",
        "courier_display",
        "status_colored",
        "period_start",
        "period_end",
        "duration_display",
        "is_free_display",
        "created_at",
    )
    list_display_links = ("id", "transport_with_icon", "courier_display")

    list_filter = (
        "type_slot",
        "status",
        "courier",
        "start_at",
    )

    search_fields = (
        "id",
        "courier__phone",
        "courier__first_name",
        "courier__last_name",
        "courier__username",
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
        "mark_done",
        "clear_courier",
    )

    fieldsets = (
        ("Время", {
            "fields": ("start_at", "end_at")
        }),
        ("Даркстор", {
            "fields": ("darkstore", )
        }),
        ("Слот", {
            "fields": ("type_slot", "status", "courier")
        }),
        ("Система", {
            "fields": ("created_at",)
        }),
    )

    @admin.display(description="Тип слота")
    def transport_with_icon(self, obj):
        return obj.get_type_slot_display()

    @admin.display(description="Курьер")
    def courier_display(self, obj):
        if not obj.courier:
            return format_html(
                '<span style="color:#9CA3AF;">Общий слот</span>'
            )

        name = obj.courier.get_full_name().strip() if hasattr(obj.courier, "get_full_name") else ""
        phone = getattr(obj.courier, "phone", "")

        if name and phone:
            return format_html("<b>{}</b><br><span style='color:#6B7280;'>{}</span>", name, phone)
        if name:
            return format_html("<b>{}</b>", name)
        if phone:
            return format_html("<b>{}</b>", phone)

        return str(obj.courier)

    @admin.display(description="Дата и время начала")
    def period_start(self, obj):
        return f"{obj.start_at:%d.%m.%Y %H:%M}"

    @admin.display(description="Дата и время окончания")
    def period_end(self, obj):
        return f"{obj.end_at:%d.%m.%Y %H:%M}"

    @admin.display(description="Длительность")
    def duration_display(self, obj):
        total_seconds = int((obj.end_at - obj.start_at).total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        if hours and minutes:
            return f"{hours} ч {minutes} мин"
        if hours:
            return f"{hours} ч"
        return f"{minutes} мин"

    @admin.display(description="Статус")
    def status_colored(self, obj):
        colors = {
            "planned": "#9CA3AF",        
            "offered": "#F59E0B",   
            "in_work": "#2563EB",        
            "closed_early": "#F97316",  
            "paid_break": "#6366F1",    
            "unpaid_break": "#A855F7",  
            "no_show": "#EF4444",       
            "done": "#16A34A",           
        }

        color = colors.get(obj.status, "#E5E7EB")  
        return format_html(
            '<span style="color:{}; font-weight:600;">{}</span>',
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

    @admin.action(description="Пометить как «закрыт досрочно»")
    def mark_closed_early(self, request, queryset):
        updated = queryset.update(status="closed_early")
        self.message_user(request, f"Обновлено слотов: {updated}")

    @admin.action(description="Пометить как «неявка»")
    def mark_no_show(self, request, queryset):
        updated = queryset.update(status="no_show")
        self.message_user(request, f"Обновлено слотов: {updated}")

    @admin.action(description="Пометить как «выполнен»")
    def mark_done(self, request, queryset):
        updated = queryset.update(status="done")
        self.message_user(request, f"Обновлено слотов: {updated}")

    @admin.action(description="Очистить курьера (сделать слот общим)")
    def clear_courier(self, request, queryset):
        updated = queryset.update(courier=None)
        self.message_user(request, f"Сделано общими слотов: {updated}")

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status in ("in_work", "done", "closed_early"):
            return self.readonly_fields + ("start_at", "end_at", "type_slot")
        return self.readonly_fields


class CourierRouteStopInline(admin.TabularInline):
    model = CourierRouteStop
    extra = 0
    fields = (
        "delivery",
        "stop_type",
        "sequence",
        "lat",
        "lon",
        "status",
        "eta_at",
        "arrived_at",
        "completed_at",
    )
    readonly_fields = (
        "delivery",
        "stop_type",
        "sequence",
        "lat",
        "lon",
        "eta_at",
        "arrived_at",
        "completed_at",
    )
    ordering = ("sequence",)


@admin.register(CourierRoute)
class CourierRouteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "courier",
        "status_colored",
        "stops_count",
        "created_at",
        "updated_at",
    )

    list_filter = ("status",)
    search_fields = ("courier__id", "courier__phone")
    inlines = [CourierRouteStopInline]

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    def stops_count(self, obj):
        return obj.stops.count()
    stops_count.short_description = "Stops"

    def status_colored(self, obj):
        color = "green" if obj.status == "active" else "gray"
        return format_html(
            '<b style="color:{};">{}</b>',
            color,
            obj.status
        )
    status_colored.short_description = "Status"


@admin.register(CourierRouteStop)
class CourierRouteStopAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "route",
        "delivery",
        "stop_type",
        "sequence",
        "status_colored",
        "eta_at",
    )

    list_filter = (
        "stop_type",
        "status",
    )

    search_fields = (
        "delivery__id",
        "route__courier__id",
    )

    ordering = ("route", "sequence")

    def status_colored(self, obj):
        colors = {
            "pending": "orange",
            "arrived": "blue",
            "done": "green",
            "skipped": "red",
        }

        return format_html(
            '<b style="color:{};">{}</b>',
            colors.get(obj.status, "black"),
            obj.status
        )

    status_colored.short_description = "Status"