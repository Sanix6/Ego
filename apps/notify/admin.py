from django.contrib import admin, messages
from django.db.models import Q
from django.utils.html import format_html
from django.utils import timezone
import json

from .models import PushDevice, PushNotification


@admin.register(PushDevice)
class PushDeviceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_link",
        "platform_badge",
        "external_user_id",
        "is_active_badge",
        "last_seen_at",
        "created_at",
    )
    list_display_links = list_display
    list_filter = ("platform", "is_active", "created_at", "last_seen_at")
    search_fields = (
        "player_id",
        "external_user_id",
        "user__phone",
        "user__first_name",
        "user__last_name",
        "user__email",
    )
    readonly_fields = ("created_at", "last_seen_at")
    list_per_page = 25
    ordering = ("-created_at",)

    fieldsets = (
        ("Основное", {
            "fields": (
                "user",
                "platform",
                "is_active",
            )
        }),
        ("OneSignal", {
            "fields": (
                "player_id",
                "external_user_id",
            )
        }),
        ("Даты", {
            "fields": (
                "last_seen_at",
                "created_at",
            )
        }),
    )

    @admin.display(description="Пользователь", ordering="user")
    def user_link(self, obj):
        full_name = f"{obj.user.first_name or ''} {obj.user.last_name or ''}".strip()
        label = full_name or obj.user.phone
        return format_html(
            "<b>{}</b><br><span style='color: gray;'>{}</span>",
            label,
            obj.user.phone
        )

    @admin.display(description="Платформа", ordering="platform")
    def platform_badge(self, obj):
        colors = {
            "android": "#34A853",
            "ios": "#111111",
            "web": "#4285F4",
        }
        color = colors.get(obj.platform, "#6c757d")
        return format_html(
            '<span style="padding:4px 8px;border-radius:8px;background:{};color:white;">{}</span>',
            color,
            obj.get_platform_display()
        )

    @admin.display(description="Активно", ordering="is_active")
    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="color:white;background:#198754;padding:4px 8px;border-radius:8px;">Да</span>'
            )
        return format_html(
            '<span style="color:white;background:#dc3545;padding:4px 8px;border-radius:8px;">Нет</span>'
        )

    actions = ("make_active", "make_inactive")

    @admin.action(description="Сделать выбранные устройства активными")
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Активировано устройств: {updated}", level=messages.SUCCESS)

    @admin.action(description="Сделать выбранные устройства неактивными")
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Деактивировано устройств: {updated}", level=messages.WARNING)


@admin.register(PushNotification)
class PushNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "recipient_link",
        "event_type",
        "status_badge",
        "title_short",
        "related_object",
        "scheduled_at",
        "sent_at",
        "created_at",
    )
    list_display_links = ("id", "title_short")
    list_filter = (
        "event_type",
        "status",
        "created_at",
        "scheduled_at",
        "sent_at",
        "failed_at",
    )
    search_fields = (
        "event_key",
        "title",
        "message",
        "provider_message_id",
        "error_message",
        "recipient__phone",
        "recipient__first_name",
        "recipient__last_name",
        "delivery__id",
        "delivery_offer__id",
        "slot__id",
        "ride__id",
        "taxi_offer__id",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "sent_at",
        "failed_at",
        "pretty_payload",
    )
    raw_id_fields = ("recipient", "slot", "delivery", "delivery_offer", "ride", "taxi_offer")
    list_per_page = 30
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    fieldsets = (
        ("Основное", {
            "fields": (
                "recipient",
                "event_type",
                "event_key",
                "status",
            )
        }),
        ("Контент", {
            "fields": (
                "title",
                "message",
                "payload",
                "pretty_payload",
            )
        }),
        ("Связанные объекты", {
            "fields": (
                "slot",
                "delivery",
                "delivery_offer",
                "ride",
                "taxi_offer",
            )
        }),
        ("Планирование / отправка", {
            "fields": (
                "scheduled_at",
                "sent_at",
                "failed_at",
                "provider_message_id",
                "error_message",
            )
        }),
        ("Служебное", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "recipient",
            "slot",
            "delivery",
            "delivery_offer",
            "ride",
            "taxi_offer",
        )

    @admin.display(description="Получатель", ordering="recipient")
    def recipient_link(self, obj):
        full_name = f"{obj.recipient.first_name or ''} {obj.recipient.last_name or ''}".strip()
        label = full_name or obj.recipient.phone
        user_type = getattr(obj.recipient, "user_type", "-")
        return format_html(
            "<b>{}</b><br><span style='color: gray;'>{} | {}</span>",
            label,
            obj.recipient.phone,
            user_type
        )

    @admin.display(description="Статус", ordering="status")
    def status_badge(self, obj):
        colors = {
            "pending": "#ffc107",
            "sent": "#198754",
            "failed": "#dc3545",
            "canceled": "#6c757d",
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="padding:4px 8px;border-radius:8px;background:{};color:white;">{}</span>',
            color,
            obj.get_status_display()
        )

    @admin.display(description="Заголовок")
    def title_short(self, obj):
        if not obj.title:
            return "-"
        return obj.title[:50] + "..." if len(obj.title) > 50 else obj.title

    @admin.display(description="Связь")
    def related_object(self, obj):
        if obj.slot_id:
            return format_html("<b>Slot</b> #{}", obj.slot_id)
        if obj.delivery_id:
            return format_html("<b>Delivery</b> #{}", obj.delivery_id)
        if obj.delivery_offer_id:
            return format_html("<b>DeliveryOffer</b> #{}", obj.delivery_offer_id)
        if obj.ride_id:
            return format_html("<b>TaxiRide</b> #{}", obj.ride_id)
        if obj.taxi_offer_id:
            return format_html("<b>TaxiOffer</b> #{}", obj.taxi_offer_id)
        return "-"

    @admin.display(description="Payload")
    def pretty_payload(self, obj):
        if not obj.payload:
            return "-"
        formatted = json.dumps(obj.payload, ensure_ascii=False, indent=2)
        return format_html(
            "<pre style='white-space: pre-wrap; max-width: 900px;'>{}</pre>",
            formatted
        )

    actions = (
        "mark_as_pending",
        "mark_as_sent",
        "mark_as_failed",
        "mark_as_canceled",
    )

    @admin.action(description="Отметить как pending")
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(status="pending", failed_at=None, error_message="")
        self.message_user(request, f"Обновлено уведомлений: {updated}", level=messages.SUCCESS)

    @admin.action(description="Отметить как sent")
    def mark_as_sent(self, request, queryset):
        now = timezone.now()
        updated = queryset.update(status="sent", sent_at=now, failed_at=None, error_message="")
        self.message_user(request, f"Отмечено как sent: {updated}", level=messages.SUCCESS)

    @admin.action(description="Отметить как failed")
    def mark_as_failed(self, request, queryset):
        now = timezone.now()
        updated = queryset.update(status="failed", failed_at=now)
        self.message_user(request, f"Отмечено как failed: {updated}", level=messages.WARNING)

    @admin.action(description="Отметить как canceled")
    def mark_as_canceled(self, request, queryset):
        updated = queryset.update(status="canceled")
        self.message_user(request, f"Отмечено как canceled: {updated}", level=messages.WARNING)