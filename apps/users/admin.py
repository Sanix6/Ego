from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.utils.timezone import now

from .models import (
    Client,
    Operator,
    Admin,
    CourierDispatch,
    DriverDispatch,
)
from .forms import CourierDispatchForm, DriverDispatchForm

try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass


class BaseUserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "phone",
        "first_name",
        "last_name",
        "user_type",
        "is_active",
        "is_staff",
        "date_joined",
    )
    list_filter = ("is_active", "is_staff", "user_type")
    search_fields = ("phone", "first_name", "last_name", "email")
    ordering = ("-date_joined",)

    readonly_fields = ("date_joined",)

    fieldsets = (
        ("Основное", {
            "fields": ("phone", "verification_code")
        }),
        ("Персональные данные", {
            "fields": ("first_name", "last_name", "email")
        }),
        ("Доступ", {
            "fields": ("user_type", "is_active", "is_staff", "is_superuser")
        }),
        ("Даты", {
            "fields": ("date_joined",)
        }),
        ("Рейтинг", {
            "fields": ("rating_avg", "rating_count", "orders_count")
        }),
    )

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


@admin.register(Client)
class ClientAdmin(BaseUserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(user_type="client")

    def save_model(self, request, obj, form, change):
        obj.user_type = "client"
        obj.is_staff = False
        obj.is_superuser = False
        super().save_model(request, obj, form, change)


@admin.register(Operator)
class OperatorAdmin(BaseUserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(user_type="operator")

    def save_model(self, request, obj, form, change):
        obj.user_type = "operator"
        obj.is_staff = True
        obj.is_superuser = False
        super().save_model(request, obj, form, change)


@admin.register(Admin)
class AdminUserAdmin(BaseUserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(user_type="admin")

    def save_model(self, request, obj, form, change):
        obj.user_type = "admin"
        obj.is_staff = True
        obj.is_superuser = True
        super().save_model(request, obj, form, change)


class DispatchAdminMixin(admin.ModelAdmin):
    readonly_fields = (
        "date_joined",
        "last_seen_view",
        "map_preview",
        "location_updated_view",
        "profile_created_at_view",
    )
    list_per_page = 25

    def full_name(self, obj):
        full_name = f"{obj.first_name or ''} {obj.last_name or ''}".strip()
        return full_name or "-"
    full_name.short_description = "ФИО"

    def colored_online(self, obj):
        worker_status = getattr(obj, "worker_status", None)
        is_online = getattr(worker_status, "is_online", False)
        color = "green" if is_online else "red"
        text = "ONLINE" if is_online else "OFFLINE"
        return format_html('<b style="color:{}">{}</b>', color, text)
    colored_online.short_description = "Статус"

    def colored_busy(self, obj):
        worker_status = getattr(obj, "worker_status", None)
        is_busy = getattr(worker_status, "is_busy", False)
        color = "orange" if is_busy else "green"
        text = "BUSY" if is_busy else "FREE"
        return format_html('<b style="color:{}">{}</b>', color, text)
    colored_busy.short_description = "Занятость"

    def last_seen_colored(self, obj):
        worker_status = getattr(obj, "worker_status", None)
        if not worker_status or not worker_status.last_seen:
            return "-"

        delta = now() - worker_status.last_seen
        if delta.total_seconds() < 60:
            color = "green"
        elif delta.total_seconds() < 300:
            color = "orange"
        else:
            color = "red"

        return format_html(
            '<span style="color:{}">{}</span>',
            color,
            worker_status.last_seen.strftime("%Y-%m-%d %H:%M:%S")
        )
    last_seen_colored.short_description = "Последняя активность"

    def last_seen_view(self, obj):
        return self.last_seen_colored(obj)
    last_seen_view.short_description = "Последняя активность"

    def lat(self, obj):
        worker_location = getattr(obj, "worker_location", None)
        return worker_location.lat if worker_location else "-"
    lat.short_description = "Lat"

    def lon(self, obj):
        worker_location = getattr(obj, "worker_location", None)
        return worker_location.lon if worker_location else "-"
    lon.short_description = "Lon"

    def map_link(self, obj):
        worker_location = getattr(obj, "worker_location", None)
        if not worker_location:
            return "-"
        url = f"https://www.google.com/maps?q={worker_location.lat},{worker_location.lon}"
        return format_html('<a href="{}" target="_blank">📍 Открыть карту</a>', url)
    map_link.short_description = "Карта"

    def map_preview(self, obj):
        return self.map_link(obj)
    map_preview.short_description = "Карта"

    def location_updated_at_colored(self, obj):
        worker_location = getattr(obj, "worker_location", None)
        if not worker_location or not worker_location.updated_at:
            return "-"

        delta = now() - worker_location.updated_at
        if delta.total_seconds() < 60:
            color = "green"
        elif delta.total_seconds() < 300:
            color = "orange"
        else:
            color = "red"

        return format_html(
            '<span style="color:{}">{}</span>',
            color,
            worker_location.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        )
    location_updated_at_colored.short_description = "Гео обновлено"

    def location_updated_view(self, obj):
        return self.location_updated_at_colored(obj)
    location_updated_view.short_description = "Гео обновлено"

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


@admin.register(CourierDispatch)
class CourierDispatchAdmin(DispatchAdminMixin, admin.ModelAdmin):
    form = CourierDispatchForm

    list_display = (
        "id",
        "phone",
        "full_name",
        "verification_code_view",
        "colored_online",
        "colored_busy",
        "last_seen_colored",
        "lat",
        "lon",
        "map_link",
        "location_updated_at_colored",
        "courier_profile_status_badge",
        "transport_type_view",
        "darkstore_view",
        "delivery_zone_view",
        "car_info",
        "active_deliveries_count_view",
        "max_parallel_deliveries_view",
    )

    list_filter = (
        "is_active",
        "worker_status__is_online",
        "worker_status__is_busy",
        "courier_profile__status",
        "courier_profile__transport_type",
        "courier_profile__darkstore",
        "courier_profile__delivery_zones",
    )

    search_fields = (
        "phone",
        "email",
        "first_name",
        "last_name",
        "verification_code",
        "courier_profile__car_number",
        "courier_profile__car_brand",
        "courier_profile__car_model",
    )

    ordering = ("-worker_status__last_seen",)

    fieldsets = (
        ("Пользователь", {
            "fields": (
                "phone",
                "email",
                "first_name",
                "last_name",
                "verification_code",
                "is_active",
                "date_joined",
            )
        }),
        ("Рейтинг и статистика", {
            "fields": (
                "rating_avg",
                "rating_count",
                "orders_count",
            )
        }),
        ("Онлайн-статусы", {
            "fields": (
                "is_online",
                "is_busy",
                "last_seen_view",
            )
        }),
        ("Геолокация", {
            "fields": (
                ("lat", "lon"),
                "map_preview",
                "location_updated_view",
            )
        }),
        ("Документы", {
            "fields": (
                "selfie",
                "passport_front",
                "passport_back",
                "driver_license_front",
                "driver_license_back",
            )
        }),
        ("Профиль курьера", {
            "fields": (
                "courier_profile_status",
                "transport_type",
                "darkstore",
                "delivery_zones",
                ("car_brand", "car_model"),
                ("car_color", "car_number"),
                "profile_created_at_view",
            )
        }),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(user_type="courier")
            .select_related(
                "worker_status",
                "worker_location",
                "courier_profile",
                "courier_profile__darkstore",
                "courier_profile__delivery_zones",
            )
        )

    @admin.display(description="Активные доставки", ordering="worker_status__active_deliveries_count")
    def active_deliveries_count_view(self, obj):
        status = getattr(obj, "worker_status", None)
        return status.active_deliveries_count if status else 0

    @admin.display(description="Макс. параллельные доставки", ordering="worker_status__max_parallel_deliveries")
    def max_parallel_deliveries_view(self, obj):
        status = getattr(obj, "worker_status", None)
        return status.max_parallel_deliveries if status else 0

    def verification_code_view(self, obj):
        return obj.verification_code or "-"
    verification_code_view.short_description = "Код"

    def courier_profile_status_badge(self, obj):
        profile = getattr(obj, "courier_profile", None)
        if not profile:
            return "-"

        color_map = {
            "approved": "green",
            "pending": "orange",
            "rejected": "red",
        }
        color = color_map.get(profile.status, "gray")
        return format_html('<b style="color:{}">{}</b>', color, profile.get_status_display())
    courier_profile_status_badge.short_description = "Статус профиля"

    def transport_type_view(self, obj):
        profile = getattr(obj, "courier_profile", None)
        if not profile or not profile.transport_type:
            return "-"
        return profile.get_transport_type_display()
    transport_type_view.short_description = "Транспорт"

    def darkstore_view(self, obj):
        profile = getattr(obj, "courier_profile", None)
        if not profile or not profile.darkstore:
            return "-"
        return str(profile.darkstore)
    darkstore_view.short_description = "Даркстор"

    def delivery_zone_view(self, obj):
        profile = getattr(obj, "courier_profile", None)
        if not profile or not profile.delivery_zones:
            return "-"
        return str(profile.delivery_zones)
    delivery_zone_view.short_description = "Зона"

    def profile_created_at_view(self, obj):
        profile = getattr(obj, "courier_profile", None)
        if not profile or not profile.created_at:
            return "-"
        return profile.created_at.strftime("%Y-%m-%d %H:%M:%S")
    profile_created_at_view.short_description = "Создан профиль"

    def car_info(self, obj):
        profile = getattr(obj, "courier_profile", None)
        if not profile:
            return "-"
        parts = [profile.car_brand, profile.car_model, profile.car_color, profile.car_number]
        parts = [p for p in parts if p]
        return " / ".join(parts) if parts else "-"
    car_info.short_description = "Авто"

    def save_model(self, request, obj, form, change):
        form.save()


@admin.register(DriverDispatch)
class DriverDispatchAdmin(DispatchAdminMixin, admin.ModelAdmin):
    form = DriverDispatchForm

    list_display = (
        "id",
        "phone",
        "full_name",
        "verification_code_view",
        "colored_online",
        "colored_busy",
        "last_seen_colored",
        "lat",
        "lon",
        "map_link",
        "location_updated_at_colored",
        "driver_profile_status_badge",
        "passport_number_view",
        "car_info",
    )

    list_filter = (
        "is_active",
        "worker_status__is_online",
        "worker_status__is_busy",
        "driver_profile__status",
        "driver_profile__car_type",
    )

    search_fields = (
        "phone",
        "email",
        "first_name",
        "last_name",
        "verification_code",
        "driver_profile__car_number",
        "driver_profile__car_brand",
        "driver_profile__car_model",
        "driver_profile__passport_number",
        "driver_profile__seria_and_number",
    )

    ordering = ("-worker_status__last_seen",)

    fieldsets = (
        ("Пользователь", {
            "fields": (
                "phone",
                "email",
                "first_name",
                "last_name",
                "verification_code",
                "is_active",
                "date_joined",
            )
        }),
        ("Рейтинг и статистика", {
            "fields": (
                "rating_avg",
                "rating_count",
                "orders_count",
            )
        }),
        ("Онлайн-статусы", {
            "fields": (
                "is_online",
                "is_busy",
                "last_seen_view",
            )
        }),
        ("Геолокация", {
            "fields": (
                ("lat", "lon"),
                "map_preview",
                "location_updated_view",
            )
        }),
        ("Документы", {
            "fields": (
                "selfie",
                "passport_front",
                "passport_back",
                "passport_number",
            )
        }),
        ("Водительские права", {
            "fields": (
                "seria_and_number",
                "date_of_issue",
                "issuing_authority",
                "driver_license_front",
                "driver_license_back",
            )
        }),
        ("Машина", {
            "fields": (
                ("car_brand", "car_model"),
                ("car_color", "car_number"),
                "car_type",
                "car_photo",
            )
        }),
        ("Профиль таксиста", {
            "fields": (
                "driver_profile_status",
                "profile_created_at_view",
            )
        }),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(user_type="driver")
            .select_related(
                "worker_status",
                "worker_location",
                "driver_profile",
            )
        )

    def verification_code_view(self, obj):
        return obj.verification_code or "-"
    verification_code_view.short_description = "Код"

    def passport_number_view(self, obj):
        profile = getattr(obj, "driver_profile", None)
        return profile.passport_number if profile and profile.passport_number else "-"
    passport_number_view.short_description = "Паспорт"

    def driver_profile_status_badge(self, obj):
        profile = getattr(obj, "driver_profile", None)
        if not profile:
            return "-"

        color_map = {
            "approved": "green",
            "pending": "orange",
            "rejected": "red",
        }
        color = color_map.get(profile.status, "gray")
        return format_html('<b style="color:{}">{}</b>', color, profile.get_status_display())
    driver_profile_status_badge.short_description = "Статус профиля"

    def profile_created_at_view(self, obj):
        profile = getattr(obj, "driver_profile", None)
        if not profile or not profile.created_at:
            return "-"
        return profile.created_at.strftime("%Y-%m-%d %H:%M:%S")
    profile_created_at_view.short_description = "Создан профиль"

    def car_info(self, obj):
        profile = getattr(obj, "driver_profile", None)
        if not profile:
            return "-"
        parts = [profile.car_brand, profile.car_model, profile.car_color, profile.car_number]
        parts = [p for p in parts if p]
        return " / ".join(parts) if parts else "-"
    car_info.short_description = "Авто"

    def save_model(self, request, obj, form, change):
        form.save()