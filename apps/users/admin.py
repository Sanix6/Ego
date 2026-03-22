from django.contrib import admin
from django.contrib.auth.models import Group
from .models import *
from django.utils.html import format_html


admin.site.unregister(Group)

class BaseUserAdmin(admin.ModelAdmin):
    search_fields = ["phone"]
    list_display = (
        'id',
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
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


@admin.register(Client)
class ClientAdmin(BaseUserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request)

    def save_model(self, request, obj, form, change):
        # obj.user_type = "client"
        obj.is_staff = False
        super().save_model(request, obj, form, change)


class CourierProfileInline(admin.StackedInline):
    model = CourierProfile
    extra = 0

@admin.register(CourierProfile)
class CourierProfileAdmin(admin.ModelAdmin):
    # autocomplete_fields = ["user"]
    list_display = (
        "id",
        "user",
        "transport_type",
        "car_number",
        "status",
        "created_at",
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
    )

    fieldsets = (
        ("Пользователь", {
            "fields": ("user",)
        }),

        ("Тип транспорта", {
            "fields": ("transport_type",)
        }),

        ("Документы", {
            "fields": (
                "selfie",
                "passport_front",
                "passport_back",
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
    )

    fieldsets = (
        ("Пользователь", {
            "fields": ("user",)
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

@admin.register(Operator)
class OperatorAdmin(BaseUserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(user_type="operator")

    def save_model(self, request, obj, form, change):
        obj.user_type = "operator"
        obj.is_staff = True  
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




@admin.register(WorkerStatus)
class WorkerStatusAdmin(admin.ModelAdmin):
    list_display = (
        "user_phone",
        "colored_online",
        "colored_busy",
        "last_seen_colored",
    )

    list_filter = ("is_online", "is_busy", "last_seen")
    search_fields = ("user__phone",)
    ordering = ("-last_seen",)
    list_per_page = 20

    readonly_fields = ("last_seen",)

    fieldsets = (
        ("Основная информация", {
            "fields": ("user",)
        }),
        ("Статус", {
            "fields": ("is_online", "is_busy"),
            "classes": ("collapse",)
        }),
        ("Системные данные", {
            "fields": ("last_seen",),
        }),
    )

    def user_phone(self, obj):
        return obj.user.phone
    user_phone.short_description = "Телефон"

    def colored_online(self, obj):
        color = "green" if obj.is_online else "red"
        text = "ONLINE" if obj.is_online else "OFFLINE"
        return format_html(
            f'<b style="color:{color}">{text}</b>'
        )
    colored_online.short_description = "Статус"

    def colored_busy(self, obj):
        color = "orange" if obj.is_busy else "green"
        text = "BUSY" if obj.is_busy else "FREE"
        return format_html(
            f'<b style="color:{color}">{text}</b>'
        )
    colored_busy.short_description = "Занятость"

    def last_seen_colored(self, obj):
        from django.utils.timezone import now
        delta = now() - obj.last_seen

        if delta.total_seconds() < 60:
            color = "green"
        elif delta.total_seconds() < 300:
            color = "orange"
        else:
            color = "red"

        return format_html(
            f'<span style="color:{color}">{obj.last_seen.strftime("%Y-%m-%d %H:%M:%S")}</span>'
        )
    last_seen_colored.short_description = "Последняя активность"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


@admin.register(WorkerLocation)
class WorkerLocationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user_phone",
        "lat",
        "lon",
        "map_link",
        "updated_at_colored",
    )
    readonly_fields = ("updated_at",)

    search_fields = ("user__phone",)
    ordering = ("-updated_at",)
    list_per_page = 20


    fieldsets = (
        ("Пользователь", {
            "fields": ("user",)
        }),
        ("Геолокация", {
            "fields": ("lat", "lon"),
        }),
        ("Система", {
            "fields": ("updated_at",),
        }),
    )


    def user_phone(self, obj):
        return obj.user.phone
    user_phone.short_description = "Телефон"

    def map_link(self, obj):
        url = f"https://www.google.com/maps?q={obj.lat},{obj.lon}"
        return format_html(
            f'<a href="{url}" target="_blank">📍 Открыть карту</a>'
        )
    map_link.short_description = "Карта"

    def updated_at_colored(self, obj):
        from django.utils.timezone import now
        delta = now() - obj.updated_at

        if delta.total_seconds() < 60:
            color = "green"
        elif delta.total_seconds() < 300:
            color = "orange"
        else:
            color = "red"

        return format_html(
            f'<span style="color:{color}">{obj.updated_at.strftime("%Y-%m-%d %H:%M:%S")}</span>'
        )
    updated_at_colored.short_description = "Обновлено"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")