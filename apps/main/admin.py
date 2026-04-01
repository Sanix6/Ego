from django.contrib import admin
from django_celery_beat.models import (
    PeriodicTask,
    IntervalSchedule,
    CrontabSchedule,
    SolarSchedule,
    ClockedSchedule
)
from .models import Tariff, DarkStore, DeliveryTariff, DeliveryZone
from .forms import DeliveryZoneAdminForm



admin.site.unregister(PeriodicTask)
admin.site.unregister(IntervalSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(SolarSchedule)
admin.site.unregister(ClockedSchedule)

@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ("car_class", "base_fare", "per_km_rate", "per_min_rate", "is_active")
    list_filter = ("car_class", "is_active")
    

@admin.register(DeliveryTariff)
class DeliveryTariffAdmin(admin.ModelAdmin):
    list_display = ("type_delivery", "base_fare", "per_km_rate", "per_min_rate", "is_active")
    list_filter = ("type_delivery", "is_active")
    

@admin.register(DarkStore)
class DarkStoreAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "created_at")
    search_fields = ("name", "address")



@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
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