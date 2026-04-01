from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.utils.timezone import now

from .models import (
    Client,
    Operator,
    Admin,
    CourierProfile,
    DriverProfile,
    WorkerStatus,
    WorkerLocation,
    CourierDispatch,
    DriverDispatch,
)
from .forms import CourierDispatchForm, DriverDispatchForm

admin.site.unregister(Group)


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
    list_filter = ("is_active", "is_staff")
    search_fields = ("phone", "first_name", "last_name")
    ordering = ("-date_joined",)

    readonly_fields = ("date_joined",)

    fieldsets = (
        ("Основное", {
            "fields": ("phone", "verification_code")
        }),
        ("Персональные данные", {
            "fields": ("first_name", "last_name", "email")
        }),
        ("Адреса", {
            "fields": ("home_address", "work_address")
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


@admin.register(CourierProfile)
class CourierProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "darkstore",
        "transport_type",
        "car_number",
        "status",
        "created_at",
        "delivery_zones"
    )

    list_filter = (
        "transport_type",
        "status",
        "created_at",
    )

    search_fields = (
        "user__phone",
        "car_number",
    )

    readonly_fields = (
        "created_at",
        "user_verification_code"
    )

    fieldsets = (
        ("Пользователь", {
            "fields": ("user",  "user_verification_code")
        }),
        ("Даркстор", {
            "fields": ("darkstore", "delivery_zones")
        }),
        ("Тип транспорта", {
            "fields": ("transport_type",)
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
        ("Машина", {
            "fields": (
                "car_brand",
                "car_model",
                "car_color",
                "car_number",
            )
        }),
        ("Статус", {
            "fields": ("status",)
        }),
        ("Системные данные", {
            "fields": ("created_at",)
        }),
    )
    @admin.display(description="Код подтверждения")
    def user_verification_code(self, obj):
        return obj.user.verification_code if obj.user else "-"

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


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "car_number",
        "car_brand",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "user__phone",
        "car_number",
        "car_brand",
    )

    readonly_fields = (
        "created_at",
        "user_verification_code"
    )

    fieldsets = (
        ("Пользователь", {
            "fields": ("user", "user_verification_code")
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
                "car_brand",
                "car_model",
                "car_color",
                "car_number",
                "car_type",
                "car_photo",
            )
        }),
        ("Статус", {
            "fields": ("status",)
        }),
        ("Системные данные", {
            "fields": ("created_at",)
        }),
    )
    @admin.display(description="Код подтверждения")
    def user_verification_code(self, obj):
        return obj.user.verification_code if obj.user else "-"

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


# @admin.register(WorkerStatus)
# class WorkerStatusAdmin(admin.ModelAdmin):
#     list_display = ("id", "user", "is_online", "is_busy", "last_seen")
#     list_filter = ("is_online", "is_busy", "last_seen")
#     search_fields = ("user__phone", "user__first_name", "user__last_name")
#     readonly_fields = ("last_seen",)

#     def has_module_permission(self, request):
#         return request.user.is_superuser

#     def has_view_permission(self, request, obj=None):
#         return request.user.is_superuser

#     def has_add_permission(self, request):
#         return request.user.is_superuser

#     def has_change_permission(self, request, obj=None):
#         return request.user.is_superuser

#     def has_delete_permission(self, request, obj=None):
#         return request.user.is_superuser


# @admin.register(WorkerLocation)
# class WorkerLocationAdmin(admin.ModelAdmin):
#     list_display = ("id", "user", "lat", "lon", "updated_at")
#     search_fields = ("user__phone", "user__first_name", "user__last_name")
#     readonly_fields = ("updated_at",)

#     def has_module_permission(self, request):
#         return request.user.is_superuser

#     def has_view_permission(self, request, obj=None):
#         return request.user.is_superuser

#     def has_add_permission(self, request):
#         return request.user.is_superuser

#     def has_change_permission(self, request, obj=None):
#         return request.user.is_superuser

#     def has_delete_permission(self, request, obj=None):
#         return request.user.is_superuser


class DispatchAdminMixin(admin.ModelAdmin):
    readonly_fields = (
        "last_seen_view",
        "map_preview",
        "location_updated_view",
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


@admin.register(CourierDispatch)
class CourierDispatchAdmin(DispatchAdminMixin, admin.ModelAdmin):
    form = CourierDispatchForm

    list_display = (
        "id",
        "phone",
        "full_name",
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
        "car_info",
    )

    list_filter = (
        "is_active",
        "worker_status__is_online",
        "worker_status__is_busy",
        "courier_profile__status",
        "courier_profile__transport_type",
        "courier_profile__darkstore",
    )

    search_fields = (
        "phone",
        "first_name",
        "last_name",
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
                "is_active",
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
        ("Профиль курьера", {
            "fields": (
                "courier_profile_status",
                "transport_type",
                "darkstore",
                ("car_brand", "car_model"),
                ("car_color", "car_number"),
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
            )
        )

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
        return format_html(
            '<b style="color:{}">{}</b>',
            color,
            profile.get_status_display()
        )
    courier_profile_status_badge.short_description = "Статус профиля"

    def transport_type_view(self, obj):
        profile = getattr(obj, "courier_profile", None)
        if not profile:
            return "-"
        return profile.get_transport_type_display()
    transport_type_view.short_description = "Транспорт"

    def darkstore_view(self, obj):
        profile = getattr(obj, "courier_profile", None)
        if not profile or not profile.darkstore:
            return "-"
        return str(profile.darkstore)
    darkstore_view.short_description = "Даркстор"

    def car_info(self, obj):
        profile = getattr(obj, "courier_profile", None)
        if not profile:
            return "-"
        parts = [
            profile.car_brand,
            profile.car_model,
            profile.car_color,
            profile.car_number,
        ]
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
        "colored_online",
        "colored_busy",
        "last_seen_colored",
        "lat",
        "lon",
        "map_link",
        "location_updated_at_colored",
        "driver_profile_status_badge",
        "car_info",
    )

    list_filter = (
        "is_active",
        "worker_status__is_online",
        "worker_status__is_busy",
        "driver_profile__status",
    )

    search_fields = (
        "phone",
        "first_name",
        "last_name",
        "driver_profile__car_number",
        "driver_profile__car_brand",
        "driver_profile__car_model",
        "driver_profile__passport_number",
    )

    ordering = ("-worker_status__last_seen",)

    fieldsets = (
        ("Пользователь", {
            "fields": (
                "phone",
                "email",
                "first_name",
                "last_name",
                "is_active",
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
        ("Профиль таксиста", {
            "fields": (
                "driver_profile_status",
                ("car_brand", "car_model"),
                ("car_color", "car_number"),
                "car_type",
                "passport_number",
                "seria_and_number",
                "issuing_authority",
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
        return format_html(
            '<b style="color:{}">{}</b>',
            color,
            profile.get_status_display()
        )
    driver_profile_status_badge.short_description = "Статус профиля"

    def car_info(self, obj):
        profile = getattr(obj, "driver_profile", None)
        if not profile:
            return "-"
        parts = [
            profile.car_brand,
            profile.car_model,
            profile.car_color,
            profile.car_number,
        ]
        parts = [p for p in parts if p]
        return " / ".join(parts) if parts else "-"
    car_info.short_description = "Авто"

    def save_model(self, request, obj, form, change):
        form.save()