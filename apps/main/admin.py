from django.contrib import admin
from unfold.admin import ModelAdmin
from django_celery_beat.models import (
    PeriodicTask,
    IntervalSchedule,
    CrontabSchedule,
    SolarSchedule,
    ClockedSchedule
)
from django.utils.html import format_html

from .models import *
from .forms import DeliveryZoneAdminForm



admin.site.unregister(PeriodicTask)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(SolarSchedule)
admin.site.unregister(ClockedSchedule)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "colored_rating",
        "from_user",
        "to_user",
        "target_type",
        "target_object",
        "short_comment",
        "created_at",
    )

    list_filter = (
        "rating",
        "created_at",
    )

    search_fields = (
        "from_user__phone",
        "to_user__phone",
        "from_user__first_name",
        "to_user__first_name",
        "comment",
    )

    readonly_fields = (
        "created_at",
    )

    # autocomplete_fields = (
    #     "from_user",
    #     "to_user",
    #     "delivery",
    #     "ride",
    # )

    fieldsets = (
        (
            "Пользователи",
            {
                "fields": (
                    "from_user",
                    "to_user",
                )
            }
        ),

        (
            "Цель отзыва",
            {
                "fields": (
                    "delivery",
                    "ride",
                )
            }
        ),

        (
            "Отзыв",
            {
                "fields": (
                    "rating",
                    "comment",
                )
            }
        ),

        (
            "Система",
            {
                "fields": (
                    "created_at",
                )
            }
        ),
    )

    def target_type(self, obj):
        if obj.delivery_id:
            return "Delivery"

        if obj.ride_id:
            return "Taxi"

        return "-"

    target_type.short_description = "Тип"

    def target_object(self, obj):
        if obj.delivery_id:
            return f"Delivery #{obj.delivery_id}"

        if obj.ride_id:
            return f"Ride #{obj.ride_id}"

        return "-"

    target_object.short_description = "Объект"

    def short_comment(self, obj):
        if not obj.comment:
            return "-"

        if len(obj.comment) > 50:
            return obj.comment[:50] + "..."

        return obj.comment

    short_comment.short_description = "Комментарий"

    def colored_rating(self, obj):

        color = "#dc3545"

        if obj.rating >= 4:
            color = "#198754"

        elif obj.rating == 3:
            color = "#ffc107"

        return format_html(
            '<b style="color:{};">{} ★</b>',
            color,
            obj.rating
        )

    colored_rating.short_description = "Рейтинг"

@admin.register(Tariff)
class TariffAdmin(ModelAdmin):
    list_display = ("car_class", "base_fare", "per_km_rate", "per_min_rate", "is_active")
    list_filter = ("car_class", "is_active")
    

@admin.register(DeliveryTariff)
class DeliveryTariffAdmin(ModelAdmin):
    list_display = ("type_delivery", "base_fare", "per_km_rate", "per_min_rate", "is_active")
    list_filter = ("type_delivery", "is_active")
    

@admin.register(DarkStore)
class DarkStoreAdmin(ModelAdmin):
    list_display = ("name", "address", "created_at")
    search_fields = ("name", "address")



@admin.register(DeliveryZone)
class DeliveryZoneAdmin(ModelAdmin):
    form = DeliveryZoneAdminForm
    change_form_template = "admin/delivery/deliveryzone/change_form.html"
    list_display = ("id", "name", "darkstore", "is_active", "created_at")
    list_filter = ("darkstore", "is_active")
    search_fields = ("name", "darkstore__name")

    class Media:
        css = {
            "all": (
                "https://api.mapbox.com/mapbox-gl-js/v3.1.2/mapbox-gl.css",
                "https://api.mapbox.com/mapbox-gl-js/plugins/mapbox-gl-draw/v1.4.3/mapbox-gl-draw.css",
            )
        }
        js = (
            "https://api.mapbox.com/mapbox-gl-js/v3.1.2/mapbox-gl.js",
            "https://api.mapbox.com/mapbox-gl-js/plugins/mapbox-gl-draw/v1.4.3/mapbox-gl-draw.js",
            "admin/js/delivery_zone_map.js",
        )



@admin.register(TaxiCommission)
class TaxiCommissionAdmin(ModelAdmin):
    list_display = (
        "id",
        "title",
        "car_class",
        "payment_method",
        "commission_percent",
        "minimum_balance",
        "is_active",
        "created_at",
    )

    list_filter = (
        "car_class",
        "payment_method",
        "is_active",
    )

    search_fields = (
        "title",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "title",
                    "car_class",
                    "payment_method",
                    "is_active",
                )
            }
        ),

        (
            "Комиссия",
            {
                "fields": (
                    "commission_percent",
                    "min_commission",
                    "max_commission",
                )
            }
        ),

        (
            "Баланс",
            {
                "fields": (
                    "minimum_balance",
                )
            }
        ),

        (
            "Системная информация",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            }
        ),
    )


@admin.register(DeliveryCommission)
class DeliveryCommissionAdmin(ModelAdmin):
    list_display = (
        "id",
        "title",
        "type_delivery",
        "payment_method",
        "commission_percent",
        "minimum_balance",
        "is_active",
        "created_at",
    )

    list_filter = (
        "type_delivery",
        "payment_method",
        "is_active",
    )

    search_fields = (
        "title",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Основная информация",
            {
                "fields": (
                    "title",
                    "type_delivery",
                    "payment_method",
                    "is_active",
                )
            }
        ),

        (
            "Комиссия",
            {
                "fields": (
                    "commission_percent",
                    "min_commission",
                    "max_commission",
                )
            }
        ),

        (
            "Баланс",
            {
                "fields": (
                    "minimum_balance",
                )
            }
        ),

        (
            "Системная информация",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            }
        ),
    )